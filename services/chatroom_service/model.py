from database import db

class Chatroom(db.Model):
    chatroom_id = db.Column(db.Integer, primary_key=True)
    chatroom_name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))

class ChatroomMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
    # profile_id = db.Column(db.Integer, db.ForeignKey('profile.profile_id'), nullable=False)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
    profile_id = db.Column(db.Integer, nullable=False)

class ChatroomMessages(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
    # sent_by = db.Column(db.Integer, db.ForeignKey('profile.profile_id'), nullable=False)
    sent_by = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
