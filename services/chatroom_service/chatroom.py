from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from database import db
from model import Chatroom, ChatroomMembers, ChatroomMessages
import yaml
from flask_jwt_extended import jwt_required, JWTManager, get_jwt_identity, get_jwt
import jwt as jtt
import datetime
from flask_wtf.csrf import CSRFProtect
import requests

with open("services/chatroom_service/config/chatroom_config.yaml", "r") as file:
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

@app.route('/create_chatroom', methods=['GET', 'POST'])
@jwt_required(locations=["cookies"]) 
def create_chatroom():
    print("Cretaing chatroom....")
    token = request.cookies.get('access_token')
    print("Token in cookies:", token)  

    try:
        decoded_token = jtt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print("Decoded token:", decoded_token)
    except jtt.ExpiredSignatureError:
        print("Token has expired.")
        return jsonify(message="Token expired"), 401
    except jtt.InvalidTokenError:
        print("Invalid token.")
        return jsonify(message="Invalid token"), 401
    
    current_user = get_jwt_identity()
    print("Current user:", current_user)
    
    decoded_token = jtt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print("DECODED!!!:", decoded_token)

    # Get the expiration time (exp) from the token and convert it to a datetime object
    exp_timestamp = decoded_token.get('exp')
    expiration_time = datetime.datetime.utcfromtimestamp(exp_timestamp)

    # Check if the token has expired
    current_time = datetime.datetime.utcnow()

    if expiration_time < current_time:
        print("Token has expired")
    else:
        print(f"Token is valid until {expiration_time}")
    print(1)
    if not current_user:  # Ensure the user is authenticated
        print(2)
        return redirect(f"http://{PROFILE_SERVICE_URL}/login")
    print(3)
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
        new_member = ChatroomMembers(chatroom_id=new_chatroom.chatroom_id, profile_id=current_user)
        db.session.add(new_member)
        db.session.commit()

        return redirect(url_for('chatrooms'))  # Redirect to chatrooms list after creation
    
    return render_template('create_chatroom.html')  # Render the form for GET requests
   
@app.route('/chatrooms')
@jwt_required(locations=["cookies"])
def chatrooms():
    print("inside /chatrooms")
    current_user = get_jwt_identity()
    current_username = get_jwt()["username"]
    print("Current user:", current_user)

    if not current_user:
        print(f"Redirecting to {PROFILE_SERVICE_URL}/login")
        return redirect(f"{PROFILE_SERVICE_URL}/login")

    # Now, you have the `user_id` available for your logic in chatroom
    rooms = Chatroom.query.all()
    chatroomMembers = ChatroomMembers.query.all()
    return render_template(
            'chatrooms.html', 
            rooms=rooms, 
            chatroomMembers=chatroomMembers, 
            current_user=current_user,
            current_username=current_username,
            profile_service_url=f"http://{PROFILE_SERVICE_URL}", 
            chatroom_service_url=f"http://{CHATROOM_SERVICE_URL}"
        )

@app.route('/chatroom/<int:room_id>', methods=['GET', 'POST'])
@jwt_required(locations=["cookies"])
def chatroom(room_id):
    print("Going inside chatroom...")
    current_user = get_jwt_identity() 
    current_username = get_jwt()["username"]
    if not current_user:
        return redirect(f"http://{PROFILE_SERVICE_URL}/login")
    
    room = Chatroom.query.get(room_id)

    # Fetch the chatroom members and check if the user is a member
    member_ids = ChatroomMembers.query.filter_by(chatroom_id=room_id).all()
    member_ids = [member.profile_id for member in member_ids]

    if int(current_user) not in [int(member) for member in member_ids]:
        return redirect(url_for('chatrooms'))
    
    # Query to fetch messages with sender's username and profile ID
    messages = db.session.query(
        ChatroomMessages.message,
        ChatroomMessages.timestamp,
        ChatroomMessages.sent_by
    ).filter(ChatroomMessages.chatroom_id == room_id).all()
    
    message_data = []
    for message, timestamp, sent_by in messages:
        response = requests.get(f'http://{PROFILE_SERVICE_URL}/get_username/{sent_by}')
        if response.status_code == 200:
            username = response.json().get('username')
        else:
            username = 'Unknown'
        message_data.append({'message': message, 'timestamp': timestamp, 'username': username, 'user': sent_by})


    if request.method == 'POST':
        message_text = request.form['message']
        new_message = ChatroomMessages(
            chatroom_id=room_id,
            sent_by=current_user,
            message=message_text,
            timestamp=datetime.datetime.now()
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chatroom', room_id=room_id))

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
