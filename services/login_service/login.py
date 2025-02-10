from flask import Flask, request, render_template, redirect, url_for, jsonify, abort, make_response
import requests  # Use requests instead of httpx

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

class RegisterForm:
    def __init__(self, user_name, password, bio):
        self.user_name = user_name
        self.password = password
        self.bio = bio

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
        form_data["bio"]
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
    # TODO: redirect to login page.
    return render_template('login.html')
    # return jsonify({"access_token": access_token, "profile_id": profile_id})


@app.route("/login", methods=["GET"])
def get_login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    print("login...")
    form_data = request.form
    access_token = form_data.get("access_token")
    profile_id = form_data.get("profile_id")

    if not access_token or not profile_id:
        abort(400, description="Both access_token and profile_id are required")

    auth_response = requests.post("http://localhost:8000/authenticate_token", json={
        "access_token": access_token,
        "profile_id": profile_id
    })

    if auth_response.status_code != 200:
        abort(400, description="Authentication failed")
    
    return redirect("http://localhost:8003/chatrooms")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8002)
