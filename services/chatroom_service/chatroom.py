from flask import Flask, request, jsonify, session, render_template, redirect, url_for, abort, make_response
from database import db
from model import Chatroom, ChatroomMembers, ChatroomMessages
import yaml
import datetime
from flask_wtf.csrf import CSRFProtect
import requests

with open("config/chatroom_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

port = str(config["flask"]["port"])
PROFILE_SERVICE_URL = config['profile-service']['url']
CHATROOM_SERVICE_URL = "localhost:"+port

SECRET_KEY = config['flask']['secret_key']
app.secret_key = SECRET_KEY

app.config['SQLALCHEMY_BINDS'] = {
    'profile': config['profile-service']['uri'],  
}

db.init_app(app)

@app.route("/", methods=['GET'])
def home():
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")
    return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))

@app.route('/create_chatroom', methods=['GET', 'POST'])
def create_chatroom():
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")
    if not profile_id or not access_token:
        print("Profile ID or Access Token missing.")
        abort(400, description="Both profile_id and access_token are required.")

    # Check for valid access token
    auth_response = requests.post("http://"+config['auth-service']['url']+"/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })

    if auth_response.status_code != 200:
        return make_response(jsonify({"error": "Token authentication failed"}), 400)
    
    if request.method == 'POST':
        # when submission to create chatroom
        chatroom_name = request.form['chatroom_name']
        description = request.form['description']

        # Create a new Chatroom instance
        new_chatroom = Chatroom(chatroom_name=chatroom_name, description=description)
        db.session.add(new_chatroom)
        db.session.commit()

        # Add the creator as a member of the new chatroom
        new_member = ChatroomMembers(chatroom_id=new_chatroom.chatroom_id, profile_id=profile_id)
        db.session.add(new_member)
        db.session.commit()
        # redirect user back to chatrooms page
        return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))

    return render_template('create_chatroom.html')  # Render the form for GET requests
   
@app.route('/chatrooms', methods=["GET", "POST"])
def chatrooms():
    print("inside chatrooms")
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    if not profile_id or not access_token:
        abort(400, description="Both profile_id and access_token are required.")

    # verify token
    auth_response = requests.post("http://"+config['auth-service']['url']+"/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })

    if auth_response.status_code != 200:
        return make_response(jsonify({"error": "Token authentication failed"}), 400)

    username = ""
    response = requests.get(f'http://'+config['profile-service']['url']+'/get_username/{profile_id}')
    if response.status_code == 200:
        username = response.json().get('username')

    rooms = Chatroom.query.all()
    chatroomMembers = ChatroomMembers.query.all()
    return render_template(
            'chatrooms.html', 
            rooms=rooms, 
            chatroomMembers=chatroomMembers, 
            current_user=profile_id,
            current_username=username,
            profile_service_url=f"http://{PROFILE_SERVICE_URL}", 
            chatroom_service_url=f"http://{CHATROOM_SERVICE_URL}"
        )

@app.route('/chatroom/<int:room_id>', methods=['GET', 'POST'])
def chatroom(room_id):
    # Get profile id and access_token
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    if not profile_id or not access_token:
        print("Profile ID or Access Token missing.")
        abort(400, description="Both profile_id and access_token are required.")

    auth_response = requests.post("http://"+config['auth-service']['url']+"/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })

    if auth_response.status_code != 200:
        return make_response(jsonify({"error": "Token authentication failed"}), 400)
    
    room = Chatroom.query.get(room_id)

    # Fetch the chatroom members and check if the user is a member
    member_ids = ChatroomMembers.query.filter_by(chatroom_id=room_id).all()
    member_ids = [member.profile_id for member in member_ids]

    # if the user is not in the chatroom, return as is!
    if int(profile_id) not in member_ids:
        print("Error: You are not a member of this chatroom.")
        return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))

    # Query to fetch messages with sender's username and profile ID
    messages = db.session.query(
        ChatroomMessages.message,
        ChatroomMessages.timestamp,
        ChatroomMessages.sent_by
    ).filter(ChatroomMessages.chatroom_id == room_id).all()
    
    message_data = []
    for message, timestamp, sent_by in messages:        
        message_data.append({'message': message, 'timestamp': timestamp, 'user': sent_by})

    # get username
    response = requests.get(f'http://'+config['profile-service']['url']+'/get_username/{profile_id}')
    if response.status_code == 200:
        username = response.json().get('username')
    else:
        return make_response(jsonify({"error": "Username not found"}), 402)

    # Add message to db
    if request.method == 'POST':
        message_text = request.form['message']
        new_message = ChatroomMessages(
            chatroom_id=room_id,
            sent_by=username,
            message=message_text,
            timestamp=datetime.datetime.now()
        )
        db.session.add(new_message)
        db.session.commit()
        # Redirect to chatroom page
        return redirect(url_for('chatroom', room_id=room_id, profile_id=profile_id, access_token=access_token))
    
    return render_template('chatroom.html', room=room, messages=message_data) # Render the form for GET requests


@app.route('/join_chatroom/<int:room_id>', methods=['POST'])
def join_chatroom(room_id):
    # Get args
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    # Check if the user is already a member
    existing_member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=profile_id).first()
    if not existing_member:
        # Add the user to the ChatroomMembers table
        new_member = ChatroomMembers(chatroom_id=room_id, profile_id=profile_id)
        db.session.add(new_member)
        db.session.commit()
    return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))  # Redirect to the list of chatrooms


# Leave a chatroom
@app.route('/leave_chatroom/<int:room_id>', methods=['POST'])
def leave_chatroom(room_id):
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    # Remove the user from the ChatroomMembers table
    member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=profile_id).first()
    if member:
        db.session.delete(member)
        db.session.commit()

    return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))  # Redirect to the list of chatrooms


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Chatroom Service!")
    app.run(port=port,debug=True)
