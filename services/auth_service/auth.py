from flask import Flask, request, jsonify, redirect, url_for, abort
from sqlalchemy.orm import Session
from uuid import uuid4
from database import db  
from model import Auth
import yaml

app = Flask(__name__)

with open("services/auth_service/config/auth_config.yaml", "r") as file:
    config = yaml.safe_load(file)



app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]
# Initialize the database
db.init_app(app)

@app.route("/create_access_token", methods=["POST"])
def create_access_token():

    profile_data = request.json
    print("Creating access token...")
    profile_id = profile_data.get("profile_id")
    if not profile_id:
        abort(400, description="Missing profile_id")

    # Generate access token
    access_token = str(uuid4())
    print(f"Generated Access Token: {access_token}")

    # Store in Auth database
    new_auth = Auth(profile_id=profile_id, access_token=access_token)
    print(f"Saving new Auth: {new_auth}")
    db.session.add(new_auth)
    db.session.commit()
    print("Commit success")

    auth_record = db.session.query(Auth).filter_by(profile_id=profile_id).first()
    print(f"Stored Auth Record: {auth_record}")

    print(access_token)
    # Redirect to /login page
    # return redirect(url_for("login", access_token=access_token, profile_id=profile_id))
    # redirect_url = url_for("login", access_token=access_token, profile_id=profile_id)
    redirect_url = f"http://localhost:8002{url_for('login', access_token=access_token, profile_id=profile_id)}"
    print(f"Redirecting to: {redirect_url}")  # Debugging line
    return redirect(redirect_url)


@app.route("/authenticate_token", methods=["POST"])
def authenticate_token():
    auth_data = request.json
    access_token = auth_data.get("access_token")
    profile_id = auth_data.get("profile_id")

    if not access_token or not profile_id:
        abort(400, description="Both access_token and profile_id are required")

    # Query the Auth table to find a match for profile_id and access_token
    auth_record = db.session.query(Auth).filter(Auth.profile_id == profile_id, Auth.access_token == access_token).first()

    if not auth_record:
        abort(401, description="Invalid token or profile_id")

    # Token is valid, proceed with authentication
    return jsonify({"message": "Authentication successful"})

@app.route("/login")
def login():
    # Placeholder for login page logic
    return jsonify({"message": "Redirected to login page"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Profile Service!")
    app.run(debug=True, host="0.0.0.0", port=8000)
