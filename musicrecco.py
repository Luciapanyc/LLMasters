from flask import Flask, request, render_template, redirect, url_for, jsonify
from h2ogpte import H2OGPTE
import numpy as np
import pandas as pd
import os
from datetime import datetime
import re


app = Flask(__name__)

#h2o Model
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-985GNVY6C2hOrmixYxL9uJ9DtpLZFrNb42NmPAf5TN4WXXgu',
)

# Create Personal collection
collection_id = client.create_collection(
name='Musicrecco',
description='Music Recommender',
)
chat_session_id = client.create_chat_session(collection_id)

# Ingest Data
songs = pd.read_csv('/app/data/songs_short.csv')
songs_txt = songs.to_csv(index=False)
songs_data = client.upload('songs_short.txt', songs_txt.encode())
client.ingest_uploads(collection_id, [songs_data])
user_id = " "


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
    
def recommended_history(response, user_id, timestamp):
    pattern = r'\"([^\"]*)\" by ([A-Za-z\s&./]+)'
    matches = re.findall(pattern, response)
    data = []

    for match in matches:
        song_name = match[0]
        artist_name = match[1]
        if 'And' in artist_name:
            artist_name = artist_name.split('And')[0].strip()
        data.append([user_id, song_name, artist_name, timestamp])

    df = pd.DataFrame(data, columns=['UserID', 'song_name', 'artist_name', 'timestamp'])
    print(df)

    try:
        if not os.path.exists('/app/data/recommender_history.csv'):
            df.to_csv('/app/data/recommender_history.csv', index=False)
            print("recommended_history saved")
        else:
            df.to_csv('/app/data/recommender_history.csv', mode='a', index=False, header=False)
            print("recommended_history saved")
    except Exception as e:
        print(f"Error saving recommender history to CSV: {e}")

    
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

        global user_id
        user_id = username

        if authenticated:
            # Retrived Data
            user = pd.read_csv('/app/data/user.csv')
            user = user[user['UserID'] == username]

            history = pd.read_csv('/app/data/listening history.csv')
            history = history[history['UserID'] == username]

            # Converted to Text
            user_txt = user.to_csv(index=False)
            history_txt = history.to_csv(index=False)

            # Upload
            user_data = client.upload('user.txt', user_txt.encode())
            history_data = client.upload('listening_history.txt', history_txt.encode())

            # Ingest the uploaded data
            client.ingest_uploads(collection_id, [user_data, history_data])

            return redirect(url_for('chatbot')), 302
        else:
            return "Invalid UserID or Password", 401
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {e}"}), 500

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

# Chatbot Page
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'GET':
        try:
            return render_template('chatbot.html'), 200
        except Exception as e:
            error_message = f"Error rendering chatbot template: {e}"
            return jsonify({'error': error_message}), 500
    
    else:
        try:
            user_message = request.form['message']
            
            with client.connect(chat_session_id) as session:
                answer = session.query(
                    message=user_message,
                    system_prompt='Assume music and song to be the same word. When a question asks for similar music, recommend fewer than 5 songs unless told otherwise. Find similar music based on genre and other factors such as danceability, loudness, speechiness, and more. Just return the song name unless stated otherwise. Do not give too many details',
                    rag_config={"rag_type": "rag"},
                ).content
                
                bot_response = answer

        except Exception as e:
            bot_response = f"Error: {str(e)}"

        # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # recommended_history(bot_response, user_id, timestamp)

        return jsonify({'response': bot_response})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000", debug=True)