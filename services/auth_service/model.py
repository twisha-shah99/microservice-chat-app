from database import db

class Auth(db.Model):
    profile_id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(500), nullable=False)