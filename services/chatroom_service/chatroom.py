from flask import Flask, request, jsonify, session, render_template, redirect, url_for, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from database import db
from model import Chatroom, ChatroomMembers, ChatroomMessages
import yaml
from flask_jwt_extended import jwt_required, JWTManager, get_jwt_identity, get_jwt
import jwt as jtt
import datetime
from flask_wtf.csrf import CSRFProtect
import requests

with open("config/chatroom_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

PROFILE_SERVICE_URL = config['profile-service']['url']
CHATROOM_SERVICE_URL = "localhost:5002"

SECRET_KEY = config['flask']['secret_key']
app.secret_key = SECRET_KEY

app.config['SQLALCHEMY_BINDS'] = {
    'profile': 'sqlite:///profile.db',  # Profile database URI
}

app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False  # True if using HTTPS
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

app.config['WTF_CSRF_ENABLED'] = False

jwt = JWTManager(app)

csrf = CSRFProtect(app)

# Initialize the database
db.init_app(app)


@app.route("/", methods=['GET'])
def home():
    # Get profile id and access token
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")
    # redirect to chatrooms when home is pushed
    return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))

@app.route('/create_chatroom', methods=['GET', 'POST'])
#@jwt_required(locations=["cookies"]) 
def create_chatroom():
    print("Cretaing chatroom....")
    

    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    print("profile: ", profile_id, " | accessToken: " + access_token)

    if not profile_id or not access_token:
        print("Profile ID or Access Token missing.")
        abort(400, description="Both profile_id and access_token are required.")

    # TODO check for valid access token /authenticate token
    auth_response = requests.post("http://localhost:8000/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })
    print(auth_response)

    # TODO redirect to login? when to redirect to login?
    if auth_response.status_code != 200:
        return make_response(jsonify({"error": "Token authentication failed"}), 400)
    
    print("Token authentication success!")

  
    print(request)
    print("Request method:", request.method)
    if request.method == 'POST':
        print("POST")
        chatroom_name = request.form['chatroom_name']
        description = request.form['description']

        print(f"Chatroom Name: {chatroom_name}, Description: {description}")

        # Create a new Chatroom instance
        new_chatroom = Chatroom(chatroom_name=chatroom_name, description=description)
        db.session.add(new_chatroom)
        db.session.commit()

        # Add the creator as a member of the new chatroom
        new_member = ChatroomMembers(chatroom_id=new_chatroom.chatroom_id, profile_id=profile_id)
        db.session.add(new_member)
        db.session.commit()

        return redirect(url_for('chatrooms', profile_id=profile_id, access_token=access_token))

    return render_template('create_chatroom.html')  # Render the form for GET requests
   
@app.route('/chatrooms', methods=["GET", "POST"])
def chatrooms():
    print("inside /chatrooms")
   # Get the profile_id and access_token from the request body
    # Get the profile_id and access_token from the URL query parameters
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")
    print("profile: ", profile_id, " | accessToken: " + access_token)

    if not profile_id or not access_token:
        print("Profile ID or Access Token missing.")
        abort(400, description="Both profile_id and access_token are required.")

    # TODO: call get_user_details -in profile to get username based on profile_id
    # then query the table and render!

    username = ""
    response = requests.get(f'http://localhost:5001/get_username/{profile_id}')
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
    # PREFORM TOKEN AUTHENTICATION
    print("I AM IN A CHATROOM")
    profile_id = request.args.get("profile_id")
    access_token = request.args.get("access_token")

    print("profile: ", profile_id, " | accessToken: " + access_token)

    if not profile_id or not access_token:
        print("Profile ID or Access Token missing.")
        abort(400, description="Both profile_id and access_token are required.")

    auth_response = requests.post("http://localhost:8000/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })
    print(auth_response)

    # TODO redirect to login? when to redirect to login?
    if auth_response.status_code != 200:
        return make_response(jsonify({"error": "Token authentication failed"}), 400)
    
    print("Token authentication success!")

    print("Going inside chatroom...")
    
    room = Chatroom.query.get(room_id)

    # Fetch the chatroom members and check if the user is a member
    member_ids = ChatroomMembers.query.filter_by(chatroom_id=room_id).all()
    member_ids = [member.profile_id for member in member_ids]
    
    # Query to fetch messages with sender's username and profile ID
    messages = db.session.query(
        ChatroomMessages.message,
        ChatroomMessages.timestamp,
        ChatroomMessages.sent_by
    ).filter(ChatroomMessages.chatroom_id == room_id).all()
    
    message_data = []
    for message, timestamp, sent_by in messages:
        # response = requests.get(f'http://{PROFILE_SERVICE_URL}/get_username/{sent_by}')
        # if response.status_code == 200:
        #     username = response.json().get('username')
        # else:
        #     username = 'Unknown'
        
        message_data.append({'message': message, 'timestamp': timestamp, 'user': sent_by})

    # get username to have as sent by
    response = requests.get(f'http://localhost:5001/get_username/{profile_id}')
    if response.status_code == 200:
        username = response.json().get('username')
    # what if username not present
    else:
        return make_response(jsonify({"error": "Username not found"}), 402)

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
        return redirect(url_for('chatroom', room_id=room_id, profile_id=profile_id, access_token=access_token))
    
    return render_template('chatroom.html', room=room, messages=message_data)

# Join a chatroom
@app.route('/join_chatroom/<int:room_id>', methods=['POST'])
@jwt_required(locations=["cookies"])
def join_chatroom(room_id):
    current_user = get_jwt_identity() 
    if not current_user:
        return redirect(f"http://{PROFILE_SERVICE_URL}/login")

    # Check if the user is already a member
    existing_member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=current_user).first()
    if not existing_member:
        # Add the user to the ChatroomMembers table
        new_member = ChatroomMembers(chatroom_id=room_id, profile_id=current_user)
        db.session.add(new_member)
        db.session.commit()

    return redirect(url_for('chatrooms'))  # Redirect to the list of chatrooms


# Leave a chatroom
@app.route('/leave_chatroom/<int:room_id>', methods=['POST'])
@jwt_required(locations=["cookies"])
def leave_chatroom(room_id):
    current_user = get_jwt_identity() 
    if not current_user:
        return redirect(f"http://{PROFILE_SERVICE_URL}/login")
    # Remove the user from the ChatroomMembers table
    member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=current_user).first()
    if member:
        db.session.delete(member)
        db.session.commit()

    return redirect(url_for('chatrooms'))  # Redirect to the list of chatrooms


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Chatroom Service!")
    app.run(port=5002,debug=True)
