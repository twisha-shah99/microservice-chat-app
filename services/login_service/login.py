from flask import Flask, request, render_template, redirect, url_for, jsonify, abort, make_response
import requests  # Use requests instead of httpx

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

class RegisterForm:
    def __init__(self, user_name, password, bio=None):
        self.user_name = user_name
        self.password = password
        self.bio = bio

@app.route("/", methods=['GET'])
def home():
    # redirect to login
    return redirect(url_for('get_login'))

@app.route("/register", methods=["GET"])
def get_register():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    form_data = request.form
    print("Registration started...")
    print(form_data)
    register_form = RegisterForm(
        form_data["username"], 
        form_data["password"], 
        form_data.get("bio", None)
    )

    profile_response = requests.post("http://localhost:5001/new_profile", json={
        "user_name": register_form.user_name,
        "password": register_form.password,
        "bio": register_form.bio
    })

    print(profile_response)

    if profile_response.status_code != 200:
        return make_response(jsonify({"error": "Profile creation failed"}), 400)
    
    profile_data = profile_response.json()
    profile_id = profile_data.get("profile_id")
    
    if not profile_id:
        return make_response(jsonify({"error": "Invalid profile response"}), 400)

    token_response = requests.post("http://localhost:8000/create_access_token", json={"profile_id": profile_id})
    if token_response.status_code != 200:
        return make_response(jsonify({"error": "Token creation failed"}), 400)

    access_token = token_response.json().get("access_token")
    # Redirect to login page after registered
    return redirect(url_for('get_login'))
    
@app.route("/login", methods=["GET"])
def get_login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    # Get form data
    form_data = request.form
    username = form_data.get("username")
    password = form_data.get("password")
    # make this endpoint return profile id
    profile_response = requests.post("http://localhost:5001/validate_user", json={
        "user_name": username,
        "password": password
    })
    profile_response = profile_response.json()
    profile_id = profile_response["profile_id"]
    if profile_id:
        access_token_response = requests.post("http://localhost:8000/retrieve_token", json={
            "profile_id": profile_id
        })

        if access_token_response.status_code == 200:
            access_token = access_token_response.json().get("access_token")
            
            if access_token:
                print("Redirecting to chatrooms...")
                # Redirect directly with the profile_id and access_token as query parameters
                return redirect(f"http://localhost:5002/chatrooms?profile_id={profile_id}&access_token={access_token}")

    # If profile ID or access token is not found, redirect back to login page
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8002)
