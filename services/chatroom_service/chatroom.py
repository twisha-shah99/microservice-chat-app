from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from database import db
from model import Chatroom, ChatroomMembers, ChatroomMessages
import yaml
import jwt

with open("services/chatroom_service/config/chatroom_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates")
app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

PROFILE_SERVICE_URL = config['profile-service']['url']

app.config['SQLALCHEMY_BINDS'] = {
    'profile': 'sqlite:///profile.db',  # Profile database URI
    # 'chatroom': 'sqlite:///chatrooms.db'  # Chatroom database URI
}

# Initialize the database
db.init_app(app)

@app.route('/create_chatroom', methods=['GET', 'POST'])
def create_chatroom():
    if 'user_id' not in session:  # Ensure the user is logged in
        # return redirect(url_for('login'))
        return redirect(f"{PROFILE_SERVICE_URL}/login")

    if request.method == 'POST':
        chatroom_name = request.form['chatroom_name']
        description = request.form['description']

        # Create a new Chatroom instance
        new_chatroom = Chatroom(chatroom_name=chatroom_name, description=description)
        db.session.add(new_chatroom)
        db.session.commit()

        # Add the creator as a member of the new chatroom
        new_member = ChatroomMembers(chatroom_id=new_chatroom.chatroom_id, profile_id=session['user_id'])
        db.session.add(new_member)
        db.session.commit()

        return redirect(url_for('chatrooms'))  # Redirect to chatrooms list after creation
    return render_template('create_chatroom.html')  # Render the form for GET requests

@app.route('/chatrooms')
def chatrooms():
    print("inside /chatrooms")
    app.logger.info('Chatrooms route accessed')
    token = request.args.get('token')  # Extract token from the query parameter
    print(token)
    # if not token:
    #     print("No token provided, redirecting to login")
    #     return redirect(f"{PROFILE_SERVICE_URL}/login")

    # try:
    #     # Decode the token to extract the user_id
    #     decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    #     user_id = decoded['user_id']
    # except jwt.ExpiredSignatureError:
    #     print("Token expired, redirecting to login")
    #     return redirect(f"{PROFILE_SERVICE_URL}/login")
    # except jwt.InvalidTokenError:
    #     print("Invalid token, redirecting to login")
    #     return redirect(f"{PROFILE_SERVICE_URL}/login")

    # Now, you have the `user_id` available for your logic in chatroom
    rooms = Chatroom.query.all()
    chatroomMembers = ChatroomMembers.query.all()
    return render_template('chatrooms.html', rooms=rooms, chatroomMembers=chatroomMembers)
    # if 'user_id' not in session:
    #     print("inside /chatrooms: redirecting, user_id not in session")
    #     # return redirect(url_for('login'))
    #     print(f"Redirecting to {PROFILE_SERVICE_URL}/login")
    #     return redirect(f"{PROFILE_SERVICE_URL}/login")
    # rooms = Chatroom.query.all()
    # chatroomMembers = ChatroomMembers.query.all()
    # return render_template('chatrooms.html', rooms=rooms, chatroomMembers=chatroomMembers)

@app.route('/chatroom/<int:room_id>', methods=['GET', 'POST'])
def chatroom(room_id):
    if 'user_id' not in session:
        return redirect(f"{PROFILE_SERVICE_URL}/login")
        # return redirect(url_for('login'))
    
    room = Chatroom.query.get(room_id)
    
    # Query to fetch messages with sender's username and profile ID
    messages = db.session.query(
        ChatroomMessages.message,
        ChatroomMessages.timestamp,
        Profile.username,
        Profile.profile_id
    ).join(Profile, ChatroomMessages.sent_by == Profile.profile_id) \
     .filter(ChatroomMessages.chatroom_id == room_id).all()
    
    if request.method == 'POST':
        message_text = request.form['message']
        new_message = ChatroomMessages(
            chatroom_id=room_id,
            sent_by=session['user_id'],
            message=message_text,
            timestamp=datetime.now()
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chatroom', room_id=room_id))

    return render_template('chatroom.html', room=room, messages=messages)

# Join a chatroom
@app.route('/join_chatroom/<int:room_id>', methods=['POST'])
def join_chatroom(room_id):
    if 'user_id' not in session:  # Ensure the user is logged in
        # return redirect(url_for('login'))
        return redirect(f"{PROFILE_SERVICE_URL}/login")

    # Check if the user is already a member
    existing_member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=session['user_id']).first()
    if not existing_member:
        # Add the user to the ChatroomMembers table
        new_member = ChatroomMembers(chatroom_id=room_id, profile_id=session['user_id'])
        db.session.add(new_member)
        db.session.commit()

    return redirect(url_for('chatrooms'))  # Redirect to the list of chatrooms


# Leave a chatroom
@app.route('/leave_chatroom/<int:room_id>', methods=['POST'])
def leave_chatroom(room_id):
    if 'user_id' not in session:  # Ensure the user is logged in
        # return redirect(url_for('login'))
        return redirect(f"{PROFILE_SERVICE_URL}/login")

    # Remove the user from the ChatroomMembers table
    print("In leave python function")
    member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=session['user_id']).first()
    if member:
        db.session.delete(member)
        db.session.commit()

    return redirect(url_for('chatrooms'))  # Redirect to the list of chatrooms


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Chatroom Service!")
    app.run(port=5002,debug=True)
