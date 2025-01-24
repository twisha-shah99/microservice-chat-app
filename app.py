from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extensions import db

# Adding an admin view
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Import models from models.py
from models import Profile, Chatroom, ChatroomMembers, ChatroomMessages


# -------- ADMIN SETUP --------
# Initialize Flask-Admin
admin = Admin(app, name='Chat App Admin', template_mode='bootstrap3')

# Add views for each model
admin.add_view(ModelView(Profile, db.session))
admin.add_view(ModelView(Chatroom, db.session))
admin.add_view(ModelView(ChatroomMembers, db.session))
admin.add_view(ModelView(ChatroomMessages, db.session))
# -------- ADMIN SETUP --------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chatrooms'))
    return redirect(url_for('login'))

@app.route('/create_chatroom', methods=['GET', 'POST'])
def create_chatroom():
    if 'user_id' not in session:  # Ensure the user is logged in
        return redirect(url_for('login'))

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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rooms = Chatroom.query.all()
    return render_template('chatrooms.html', rooms=rooms)

# [TK] - deprecated
# @app.route('/chatroom/<int:room_id>', methods=['GET', 'POST'])
# def chatroom(room_id):
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     room = Chatroom.query.get(room_id)
#     messages = ChatroomMessages.query.filter_by(chatroom_id=room_id).all()
    
#     if request.method == 'POST':
#         message_text = request.form['message']
#         new_message = ChatroomMessages(
#             chatroom_id=room_id,
#             sent_by=session['user_id'],
#             message=message_text,
#             timestamp=datetime.now()
#         )
#         db.session.add(new_message)
#         db.session.commit()
    
#     return render_template('chatroom.html', room=room, messages=messages)
# [TK] - deprecated

@app.route('/chatroom/<int:room_id>', methods=['GET', 'POST'])
def chatroom(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
        return redirect(url_for('login'))

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
        return redirect(url_for('login'))

    # Remove the user from the ChatroomMembers table
    member = ChatroomMembers.query.filter_by(chatroom_id=room_id, profile_id=session['user_id']).first()
    if member:
        db.session.delete(member)
        db.session.commit()

    return redirect(url_for('chatrooms'))  # Redirect to the list of chatrooms


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        bio = request.form['bio']
        new_user = Profile(username=username, password=password, bio=bio, date_created=datetime.now())
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Profile.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.profile_id
            return redirect(url_for('chatrooms'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized!")
    app.run(debug=True)
