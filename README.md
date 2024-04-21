# MusicRecco

## Project Description
MusicRecco is an innovative web-based application designed to revolutionize the music discovery experience. By harnessing the immense capabilities of Large Language Models (LLMs) and tapping into the expansive Spotify dataset, MusicRecco delivers unparalleled personalized music recommendations. Through advanced analysis of users' listening histories, MusicRecco extracts intricate music attributes, including genre and artists, to curate tailor-made suggestions that enrich the auditory journey of every user.

## Installation
To run MusicRecco locally, follow these steps:

1. Clone the entire repository:

```bash
git clone [repository_url]
```

Build and start the Docker containers:
```bash
docker-compose build
```
```bash
docker-compose up
```

Once the containers are running, go to localhost:9001 in your web browser.
Create a new account with your user ID and password, and select three of your top preferred genres.

## Usage
MusicRecoo offers three interactive pages:

1. **Home Page**: Provides daily music recommendations tailored to each user's preferred genres. These recommendations are presented as clickable links, allowing users to easily access the music on Spotify.

2. **Chatbot Page**: Utilizes the RAG LLM (Large Language Model) to recommend music based on user queries.

3. **History Page**: Stores all music recommendations made by the chatbot for easy reference by the user. Song names are presented as clickable links, allowing users to easily access the music on Youtube.
