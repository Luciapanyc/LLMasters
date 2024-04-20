from flask import Flask, request, render_template, redirect, url_for, jsonify
from h2ogpte import H2OGPTE
import numpy as np
import pandas as pd
import re
import requests
import datetime

app = Flask(__name__)

### 0.h2o Model 
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-yG5q6JxtLgMS1Twv0mwZKbIVmJw5pNKGL6uU57p5IfYYJUq7',
)

# Creating Collection and Ingesting Documents
def ingest_documents(client: H2OGPTE):
    collection_id = None
    name = 'Musicrecco'

    print("Recent collections:")
    recent_collections = client.list_recent_collections(0, 1000)
    for c in recent_collections:
        if c.name == name and c.document_count:
            collection_id = c.id
            break

    # Create Collection
    if collection_id is None:
        print(f"Creating collection: {name} ...")
        collection_id = client.create_collection(
            name=name,
            description='Music Recommender',
        )
        print(f"New collection: {collection_id} ...")

        # Upload file into collection
        song_data = client.upload('song.xlsx', open('/app/data/song.xlsx', 'rb'))
        history_data = client.upload('listening_history.xlsx', open('/app/data/listening_history.xlsx', 'rb'))
        client.ingest_uploads(collection_id, [song_data, history_data])

        print(f"DONE: {collection_id}")
    return collection_id


collection_id = ingest_documents(client)

# Prompt Training
pre_prompt = "song.pdf: 300 rows of song data including Spotify ID, Song, Artist, Rank, Genre, danceability, energy, loudness, speechiness, acousticness, liveness, valence, tempo. listening_history.pdf: User ID and Spotify ID of songs they've listened to. Task: Understand the data and recommend songs based on genre, followed by features and rank, tailored to users' favorite genre."
prompt = "As an AI chatbot, you recommend songs based on user queries. Songs reccommended MUST only be from song.pdf.  First, I analyze the user's favorite genre which is provided and listening history, accessed in listening_history.pdf using the provided user ID. When recommending songs, I provide the song name within double quotations, the artist name, and the Spotify ID a 22 alphanumeric word, formatted as \"Song name\" by Artist. Spotify ID: [spotify id]"
front_prompt = "Reccommend me a max of 5 songs based on my favourite genre with spotify id that is not in my lsitening history."

prompt_template_id = client.create_prompt_template(
    name="Song Recommendation Template",
    description="Template for recommending songs",
    system_prompt = prompt,
    pre_prompt_query= pre_prompt,
    prompt_query= front_prompt
)

client.set_collection_prompt_template(collection_id, prompt_template_id)

# Global Variables
user_id = " "
name = " "
chat_Session_id = " "

###########################################################################################################################

### 1. Login Page
# Load user credentials from Excel file
def load_user_credentials():
    try:
        df = pd.read_csv('/app/data/user.csv')
        user_credentials = df.set_index('UserID').to_dict()['Password']
        return user_credentials
    except Exception as e:
        print(f"Error loading user credentials: {e}")
        return {}


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


# Redirect to Login Page
@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            return render_template('login.html'), 200
        elif request.method == 'POST':
            username = request.form['UserID']
            password = request.form['Password']

            authenticated = authenticate(username, password)

            global user_id, chat_session_id
            user_id = username
            chat_session_id = client.create_chat_session(collection_id)

            if authenticated:
                return redirect(url_for('dashboard')), 302
            else:
                return "Invalid UserID or Password", 401
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {e}"}), 500

###########################################################################################################################

### 2. Sign Up 
# Add user credentials to Excel file
def save_user_data_to_csv(data):
    try:
        df = pd.DataFrame(data)
        df.to_csv('/app/data/user.csv', mode='a', index=False, header=False)
        return True
    except Exception as e:
        print(f"Error saving user data to CSV: {e}")
        return False

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        try:
            return render_template('signup.html'), 200
        except Exception as e:
            error_message = f"Error rendering signup template: {e}"
            return jsonify({'error': error_message}), 500
    
    elif request.method == 'POST':
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
                'Genre_1': [''],
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

###########################################################################################################################

### 3. Dashboard Page

# Get Spotify Access Token
url = "https://accounts.spotify.com/api/token"
payload = {
    "grant_type": "client_credentials",
    "client_id": "31e6d0a4c512492685193069c8450433",
    "client_secret": "054e3779e1974c038b277f4f2b5460ae"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)

access_token = response.json()['access_token']

# Function to convert id to name and album
def get_spotify_track_info(track_id, access_token):    
    # Spotify API endpoint for retrieving track information
    endpoint = f"https://api.spotify.com/v1/tracks/{track_id}"
    
    # Set up the request headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Make the GET request to Spotify API
    response = requests.get(endpoint, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        track_info = response.json()
        
        # Extract the track name and image URL from the response
        track_name = track_info['name']
        image_url = track_info['album']['images'][0]['url']  # Get the first image (largest size)
        
        return track_name, image_url
    else:
        # If the request failed, print the error message
        print(f"Error: {response.status_code} - {response.text}")
        return None, None


# Get list of song and cover
def get_song_list():
    global user_id, chat_session_id
    print(user_id, chat_session_id) # Debug statement

    # Read to get User's favourite genre
    user = pd.read_csv('/app/data/user.csv')
    user_datas = user[user['UserID'] == user_id]
    genre = user_datas.iloc[:, -3:].to_csv(index=False, header=False).strip()
    print("User's favorite genres:", genre)  # Debug statement
    
    # Query to get suggestion for genre
    recc_query = 'My user_id is' + user_id + 'and I like the genres' + genre + ', recommend me 1 song from each of the genre I like.'
    print(recc_query) # Debug Statement
    with client.connect(chat_session_id) as session:
        answer = session.query(
            message=recc_query,
            rag_config={"rag_type": "rag"},
        ).content

        bot_response = answer

    print(bot_response) # Debug statement

    #Convert query to spotify id
    pattern = r'\w{22}'

    spotify_ids = re.findall(pattern, bot_response)
    print("Spotify IDs:", spotify_ids)  # Debug statement

    # In case, id fails, use backup of top ranked song 
    music_genres = {
        "country": "4H2TRR9FjnnIwxGnIt9stO",
        "electronic": "6s0yNmp4Hd32wGx40T6uL8",
        "folk": "0fjYN9BylnRXMA3or3QSld",
        "hip hop": "5ByAIlEEnxYdvpnezg7HTX",
        "jazz": "7pKWTcPfT9mg2iAhobFHpS",
        "k-pop": "5FLuHcyUiAlq2wCoqVuqUa",
        "metal": "55tGzbf7CA1fnnlTy8HgDX",
        "pop": "3TGRqZ0a2l1LRblBkJoaDx",
        "r&b": "6mz1fBdKATx6qP4oP1I65G",
        "rap": "59e7E2LMPZ2bhW5G6aCwX8",
        "rock": "5QTxFnGygVM4jFQiBovmRo",
        "soul": "2sCf9tz6LHByczuVT7rqIx"
    }

    backup = genre.split(',')
    backup = [music_genres[genre] for genre in backup if genre in music_genres]
    spotify_ids.extend(backup)

    # Convert Id into names and album pics
    track_info_list = []

    for track_id in spotify_ids:
        track_name, image_url = get_spotify_track_info(track_id, access_token)
        track_web = f'https://open.spotify.com/track/{track_id}'
        if track_name and image_url:
            track_info_list.append({"track_id": track_web, "track_name": track_name, "image_url": image_url})
            if len(track_info_list) >= 3:
                break
    return track_info_list


# Redirect to dashboard page
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        track_info_list = get_song_list()
        return render_template('dashboard.html', track_info_list=track_info_list), 200
    except Exception as e:
        error_message = f"Error rendering dashboard template: {e}"
        return jsonify({'error': error_message}), 500

#################################################################################################################################################################

### 4. Chatbot Page
# Save Reccommended
def save_user_data_to_csv_recc(data):
    try:
        df = pd.DataFrame(data)
        df.to_csv('/app/data/recommendation_history.csv', mode='a', index=False, header=False)
        return True
    except Exception as e:
        print(f"Error saving user data to CSV: {e}")
        return False

def convert_data(x):
    user_data = {
        'UserID': [],
        'Song': [],
        'Web': [],
        'Date' : [],
        'Time' : []
    }
    
    global user_id

    current_datetime = datetime.datetime.now()

    date = current_datetime.strftime("%A, %d %B %Y")
    time = current_datetime.strftime("%H:%M:%S")

    for song_title in x:
        user_data['UserID'].append(user_id)
        user_data['Song'].append(song_title)
        user_data['Web'].append(convert_to_youtube_search_query(song_title))
        user_data['Date'].append(date)
        user_data['Time'].append(time)
        
    return user_data

# Youtube
def convert_to_youtube_search_query(x):
    input_string = re.sub(r'[^a-zA-Z0-9\s]', '', x)
    cleaned_string = ''.join(char for char in input_string if char.isalnum() or char.isspace())
    query = '+'.join(cleaned_string.split())
    youtube_search_query = f"https://www.youtube.com/results?search_query={query}"
    return youtube_search_query



@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'GET':
        return render_template('chatbot.html')
    
    elif request.method == 'POST':
        try:
            global user_id, chat_session_id

            # From user
            user_message = request.form['message']

            # Extra Query
            user = pd.read_csv('/app/data/user.csv')
            user_datas = user[user['UserID'] == user_id]
            genre = user_datas.iloc[:, -3:].to_csv(index=False, header=False).strip()
            print("User's favorite genres:", genre)  # Debug statement

            # Final Query
            recc_query = 'My user_id is' + user_id + 'and I like the genres' + genre + '.' + user_message
            print(recc_query) # Debug Statement

            with client.connect(chat_session_id) as session:
                answer = session.query(
                    message=recc_query,
                    rag_config={"rag_type": "rag"},
                ).content

                bot_response = answer
                print(bot_response)  #Debug statement

                # Saving responses
                pattern = r'"([^"]+)"'
                song_titles = re.findall(pattern, bot_response)

                data = convert_data(song_titles)
                save_user_data_to_csv_recc(data)

        except Exception as e:
            bot_response = f"Error: {str(e)}"

        return jsonify({'response': bot_response})


#######################################################################################################################################################################

### 5. Recommendation Page        
@app.route('/recommended', methods=['GET'])
def recommender():
    try:
        global user_id
        
        # Read the CSV file containing the recommended song
        df = pd.read_csv('/app/data/recommendation_history.csv')
        df = df[df['UserID'] == user_id]
        df = df.sort_values(by=['Date', 'Time'], ascending=False)
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%I:%M:%S %p')

        # Convert the DataFrame to a list of dictionaries
        recommendation_data = df.to_dict('records')
        
        # Pass the recommendation data to the template for rendering
        return render_template('recommended.html', recommendations=recommendation_data), 200
    except Exception as e:
        error_message = f"Error rendering template: {e}"
        return jsonify({'error': error_message}), 500

################################################################################################################################################################

### 6. Logout
@app.route('/logout', methods=['GET'])
def logout():
    try:
        # Perform logout actions such as clearing session data, etc.
        # For example:
        # Clear user session data
        global user_id
        user_id = ""
        # Redirect to the login page
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {e}"}), 500

###############################################################################################################################################################
@app.route('/redirect_custom', methods=['GET'])
def redirect_custom():
    page = request.args.get('page')
    if page == 'dashboard':
        return jsonify({'redirect': '/dashboard'})
    elif page == 'chatbot':
        return jsonify({'redirect': '/chatbot'})
    elif page == 'recommended':
        return jsonify({'redirect': '/recommended'})
    elif page == 'settings':
        return jsonify({'redirect': '/settings'})
    elif page == 'logout':
        return jsonify({'redirect': '/logout'})
    else:
        return jsonify({'error': 'Invalid page'}), 400


if __name__ == "__main__":
    app.run(host='0.0.0.0', port="9001", debug=True)