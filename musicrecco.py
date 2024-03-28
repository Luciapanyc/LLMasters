from flask import Flask, request, render_template, redirect, url_for, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Load user credentials from Excel file
def load_user_credentials():
    try:
        df = pd.read_csv('/app/data/user.csv')
        user_credentials = df.set_index('UserID').to_dict()['Password']
        return user_credentials
    except Exception as e:
        print(f"Error loading user credentials: {e}")
        return {}

# Add user credentials to Excel file
def save_user_data_to_csv(data):
    try:
        df = pd.DataFrame(data)
        df.to_csv('/app/data/user.csv', mode='a', index=False, header=False)
        return True
    except Exception as e:
        print(f"Error saving user data to CSV: {e}")
        return False


# Authenticate user
def authenticate(username, password):
    try:
        user_credentials = load_user_credentials()
        print("User Credentials:", user_credentials)  # Debug statement
        if username in user_credentials:
            if user_credentials[username] == password:
                print("Authentication successful for user:", username)  # Debug statement
                return True
            print("Authentication failed for user:", username)  # Debug statement
        print("Authentication failed:", username, "No such user.") # Debug statement
        return False
    except Exception as e:
        print("Error during authentication:", e)  # Debug statement
        return False

    
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

        authenticated = authenticate(username, password)

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


# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Extract form data
            user_id = request.form['UserID']
            password = request.form['Password']
            name = request.form['Name']
            favorite_genres = request.form.getlist('Favourite_Genres[]')

            print("User ID:", user_id)
            print("Password:", password)
            print("Name:", name)
            print("Favorite Genres:", favorite_genres)

            # Prepare data to save to CSV
            user_data = {
                'UserID': [user_id],
                'Password': [password],
                'Name': [name],
                'Genre_1': [''],  # Initialize empty values for all three genres
                'Genre_2': [''],
                'Genre_3': ['']
            }
            
            for i, genre in enumerate(favorite_genres[:3]):
                user_data[f'Genre_{i+1}'] = [genre]
    
            # Save user data to CSV
            if save_user_data_to_csv(user_data):
                # Redirect to the login page upon successful signup
                return redirect(url_for('home'))
            else:
                return "Failed to save user data. Please try again.", 500
        except Exception as e:
            return jsonify({'error': f"Internal Server Error: {e}"}), 500
    else:
        try:
            return render_template('signup.html'), 200
        except Exception as e:
            error_message = f"Error rendering signup template: {e}"
            return jsonify({'error': error_message}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000", debug=True)