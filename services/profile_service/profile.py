from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from model import Profile
from database import db
import yaml
from datetime import datetime, timedelta
import jwt
# from flask_socketio import SocketIO, emit

with open("services/profile_service/config/profile_config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__, template_folder="../../templates")
app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]["uri"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"]["track_modifications"]

app.config['SQLALCHEMY_BINDS'] = {
    'profile': 'sqlite:///profile.db',  # Profile database URI
    'chatroom': 'sqlite:///chatrooms.db'  # Chatroom database URI
}

CHATROOM_SERVICE_URL = config['chatroom-service']['url']
SECRET_KEY = config['flask']['secret_key']
app.secret_key = SECRET_KEY

# socketio = SocketIO(app)

# Initialize the database
db.init_app(app)

@app.route('/')
def index():
    # if 'user_id' in session:
    #     return redirect(url_for('chatrooms'))
    return redirect(url_for('login'))

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
            print("User logged in, session user_id:", session.get('user_id'))
            # return redirect(url_for('chatrooms'))
            # return redirect(f"{CHATROOM_SERVICE_URL}/chatrooms")
            token = jwt.encode({
                'user_id': user.profile_id,
                'exp': datetime.utcnow() + timedelta(hours=1)  # Token expiration time
            }, SECRET_KEY, algorithm='HS256')
            print("redirecting...")
            # Return the token to the client (this can be passed via URL or set as a cookie)
            return redirect(f"{CHATROOM_SERVICE_URL}/chatrooms?token={token}")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        db.create_all() 
        print("Database Tables created for Profile Service!")
    app.run(port=5001,debug=True)
    # socketio.run(app, host='0.0.0.0', port=5001)
