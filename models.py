from extensions import db

class Profile(db.Model):
    profile_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    bio = db.Column(db.String(200))
    profile_pic = db.Column(db.String(200))

class Chatroom(db.Model):
    chatroom_id = db.Column(db.Integer, primary_key=True)
    chatroom_name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))

class ChatroomMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.profile_id'), nullable=False)

class ChatroomMessages(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
    sent_by = db.Column(db.Integer, db.ForeignKey('profile.profile_id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
