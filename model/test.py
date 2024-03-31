# 0. Imports
from h2ogpte import H2OGPTE
import numpy as np
import pandas as pd
import os

# 1. Data Sets
songs = pd.read_csv('../data/songs_short.csv')
user = pd.read_csv('../data/user.csv')
history = pd.read_csv('../data/listening history.csv')

# 2. h2o Model
client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-e4vXVj35STQ15msFSdaeZPDo0xvCElTK4Q0hw9F1LUjgTJov',
)

## Create Collection
collection_id = client.create_collection(
    name="MusicRecco",
    description="Music Reccommender",
)

## Convert Data to Readable Format
songs_txt = songs.to_csv(index=False)
user_txt = user.to_csv(index=False)
history_txt = history.to_csv(index=False)

## Upload
songs_data = client.upload('songs_short.txt', songs_txt.encode())
user_data = client.upload('user.txt', user_txt.encode())
history_data = client.upload('listening_history.txt', history_txt.encode())

## Ingest the uploaded data
client.ingest_uploads(collection_id, [songs_data, user_data, history_data])

# 3. ChatBot Page
#Initiate Chat
chat_session_id = client.create_chat_session(collection_id)
with client.connect(chat_session_id) as session:
    # Simple Question for Document Collection
        answer = session.query(
        message="I am user sibyl. Reccomend me songs similar to my taste",  #Input from html
        system_prompt = 'Assume music and song to be the same word. When a question as for a similar music, recommend less than 5 music unless told otherwise. Find similar music based on genre and other factors such as danceability, loudness, speechiness and more. Just return the song name, unless stated otherwise.' ,
        rag_config={
            "rag_type": "rag",
        },
        ).content
        print(answer) #Output from html
