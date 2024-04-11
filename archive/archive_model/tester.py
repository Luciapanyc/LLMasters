from h2ogpte import H2OGPTE
import numpy as np
import pandas as pd
import os


songs = pd.read_excel('../../data/songs_short.xlsx')
user = pd.read_csv('../../data/user.csv')
history = pd.read_csv('../../data/listening_history.csv')

songs_txt = songs.to_csv(index=False)
user_txt = user.to_csv(index=False)
history_txt = history.to_csv(index=False)


client = H2OGPTE(
    address='https://h2ogpte.genai.h2o.ai',
    api_key='sk-cfLVheKJ5GJMA7oEJoPKXPOul4aWtCk9fnMD0BiYBYjaH53J',
)


collection_id = client.create_collection(
    name="MusicRecco",
    description="Music Reccommender",
)


songs_data = client.upload('songs_short.xlsx', open('../../data/songs_short.xlsx', 'rb'))
user_data = client.upload('user.txt', user_txt.encode())
history_data = client.upload('listening_history.txt', history_txt.encode())

client.ingest_uploads(collection_id, [songs_data, user_data, history_data])

chat_session_id = client.create_chat_session(collection_id)

user = pd.read_csv('../../data/user.csv')
genre = user[user['UserID'] == 'sibyl'].iloc[:, -3:].to_csv(index=False, header=False).strip()
query = 'I like the genres ' + genre + ', recommend me 1 song each genre with its Spotify ID. The Spotify ID should be a 22-character alphanumeric code.'

with client.connect(chat_session_id) as session:
    answer = session.query(
        message=query,
        system_prompt= 'Recommend 1 music each. MUST return spotify id at the end of each song.',
        rag_config={"rag_type": "rag"},
    ).content

    bot_response = answer

print(bot_response)