from database import db

class Profile(db.Model):
    profile_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    bio = db.Column(db.String(200))
    profile_pic = db.Column(db.String(200))
