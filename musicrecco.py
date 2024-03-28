from flask import Flask, request, render_template, redirect, url_for, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Load user credentials from Excel file
def load_user_credentials():
    try:
        df = pd.read_csv('~/data/user.csv')
        return df.set_index('ID').to_dict()['Password']
    except Exception as e:
        print(f"Error loading user credentials: {e}")
        return {}

# Authenticate user
def authenticate(username, password):
    user_credentials = load_user_credentials()
    print("User Credentials:", user_credentials)  # Debug statement
    if username in user_credentials and user_credentials[username] == password:
        return True, 'user'
    return False, None

# Login Page
@app.route('/', methods=['GET'])
def home():
    try:
        return render_template('login.html'), 200
    except Exception as e:
        error_message = f"Error rendering template: {e}"
        return jsonify({'error': error_message}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['UserID']
        password = request.form['Password']
        print("Username:", username)  # Debug statement
        print("Password:", password)  # Debug statement

        authenticated, role = authenticate(username, password)

        if authenticated:
            return redirect(url_for('chatbot')), 302
        else:
            return "Invalid UserID or Password", 401
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {e}"}), 500

# Chatbot Page
@app.route('/chatbot', methods=['GET'])
def chatbot():
    try:
        return render_template('chatbot.html'), 200
    except Exception as e:
        error_message = f"Error rendering chatbot template: {e}"
        return jsonify({'error': error_message}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000", debug=True)