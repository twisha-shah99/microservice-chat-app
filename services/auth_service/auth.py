from flask import Flask, request, jsonify, abort
from sqlalchemy.orm import Session
from uuid import uuid4
from database import db  
from model import Auth
import yaml

app = Flask(__name__)

with open("config/auth_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

db.init_app(app)

port = config["flask"]["port"]

# Create a new access token for a profile
@app.route("/create_access_token", methods=["POST"])
def create_access_token():
    profile_data = request.json
    profile_id = profile_data.get("profile_id")
    if not profile_id:
        abort(400, description="Missing profile_id")
    access_token = str(uuid4())
    new_auth = Auth(profile_id=profile_id, access_token=access_token)
    db.session.add(new_auth)
    db.session.commit()
    return jsonify({"access_token": access_token, "profile_id": profile_id}), 200

# Authenticate an access token
@app.route("/authenticate_token", methods=["POST"])
def authenticate_token():
    auth_data = request.json
    access_token = auth_data.get("access_token")
    profile_id = auth_data.get("profile_id")
    if not access_token or not profile_id:
        abort(400, description="Both access_token and profile_id are required")
    auth_record = db.session.query(Auth).filter(Auth.profile_id == profile_id, Auth.access_token == access_token).first()
    if not auth_record:
        abort(401, description="Invalid token or profile_id")
    return jsonify({"message": "Authentication successful"})

# Retrieve an existing access token for a profile
@app.route("/retrieve_token", methods=["GET", "POST"])
def retrieve_token():
    auth_data = request.json
    profile_id = auth_data.get("profile_id")
    if not profile_id:
        abort(400, description="profile_id is required")

    auth_record = db.session.query(Auth).filter(Auth.profile_id == profile_id).first()
    if not auth_record:
        abort(404, description="No token found for the given profile_id")

    return jsonify({"access_token": auth_record.access_token})

if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Profile Service!")
    app.run(debug=True, host="0.0.0.0", port=port)
