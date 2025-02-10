from flask import Flask, request, jsonify, session, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from model import Profile
from database import db
import yaml
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, create_access_token

with open("services/profile_service/config/profile_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

app.config['SQLALCHEMY_BINDS'] = {
    'profile': 'sqlite:///profile.db',  # Profile database URI
    'chatroom': 'sqlite:///chatrooms.db'  # Chatroom database URI
}

CHATROOM_SERVICE_URL = config['chatroom-service']['url']
SECRET_KEY = config['flask']['secret_key']
app.secret_key = SECRET_KEY

jwt = JWTManager(app)

db.init_app(app)

@app.route("/new_profile", methods=["POST"])
def new_profile():
    profile_data = request.json
    print("Creating new profile..")
    print(profile_data)

    if not all(k in profile_data for k in ("user_name", "password", "bio")):
       print("Missing fields...")
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
    print("Validating user..")
    user_data = request.get_json()
    print(user_data)
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


# @app.route('/')
# def index():
#     return redirect(url_for('login'))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         bio = request.form['bio']
#         new_user = Profile(username=username, password=password, bio=bio, date_created=datetime.now())
#         db.session.add(new_user)
#         db.session.commit()
#         return redirect(url_for('login'))
#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         print(1)
#         username = request.form['username']
#         password = request.form['password']
#         user = Profile.query.filter_by(username=username, password=password).first()
#         print("User: ", user)
#         if user:
#             access_token = create_access_token(identity=str(user.profile_id), expires_delta=timedelta(days=1), additional_claims={"username": user.username})
#             print("User logged in, session user_id:", user.profile_id)
#             response = make_response(redirect(f"http://{CHATROOM_SERVICE_URL}/chatrooms"))
#             response.set_cookie('access_token', access_token, httponly=True, secure=False)  # `secure=True` if HTTPS is enabled
#             print("redirecting...")
#             return response
#     return render_template('login.html')

# @app.route('/get_username/<int:profile_id>', methods=['GET'])
# def get_username(profile_id):
#     user = Profile.query.get(profile_id)
#     if user:
#         return jsonify({'username': user.username}), 200
#     else:
#         return jsonify({'message': 'User not found'}), 404


# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        print("Database Tables created for Profile Service!")
    app.run(port=5001,debug=True)
