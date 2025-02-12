from flask import Flask, request, jsonify, session, render_template, redirect, url_for, make_response
from model import Profile
from database import db
import yaml
from datetime import datetime, timedelta

with open("config/profile_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

app.config['SQLALCHEMY_BINDS'] = {
    'profile': config["database"]["uri"],  # Profile database URI
    'chatroom': config["chatroom-service"]["uri"]  # Chatroom database URI
}

port = config['flask']['port']
SECRET_KEY = config['flask']['secret_key']
app.secret_key = SECRET_KEY

db.init_app(app)

@app.route("/new_profile", methods=["POST"])
def new_profile():
    profile_data = request.json
    print("Creating new profile..")

    if not all(k in profile_data for k in ("user_name", "password", "bio")):
       return make_response(jsonify({"error": "Missing  fields in requested data"}), 400)

    new_profile = Profile(
        username=profile_data["user_name"],
        password=profile_data["password"],
        date_created=datetime.now(),  # Set the current date and time
        bio=profile_data.get("bio", "")  # Default to empty string if not provided
    )

    db.session.add(new_profile)
    db.session.commit()

    # Return the profile ID
    return jsonify({"profile_id": new_profile.profile_id})

@app.route("/validate_user", methods = ["GET", "POST"])
def validate_user():
    user_data = request.get_json()
    user = Profile.query.filter_by(username=user_data["user_name"], password=user_data["password"]).first()
    if user:
        print ("Found user")
        return jsonify({"profile_id": user.profile_id})
    print("Not found user")
    return jsonify({"profile_id": None})
    

@app.route('/get_username/<int:profile_id>', methods=['GET'])
def get_username(profile_id):
    user = Profile.query.get(profile_id)
    if user:
        return jsonify({'username': user.username}), 200
    else:
        return jsonify({'message': 'User not found'}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Profile Service!")
    app.run(port=port,debug=True)
