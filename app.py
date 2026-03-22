from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import cv2
import numpy as np
import base64
import os
from datetime import datetime
import random
import json

app = Flask(__name__)
CORS(app)

# Load Spotify credentials from environment variables
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

def get_spotify_client():
    try:
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            print("Spotify credentials not found in environment.")
            return None

        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

sp = get_spotify_client()

# Mood → Genre mapping
MOOD_TO_GENRE = {
    'happy': ['pop', 'dance'],
    'sad': ['acoustic', 'blues'],
    'angry': ['rock'],
    'neutral': ['chill'],
    'surprise': ['edm'],
    'fear': ['ambient'],
    'disgust': ['alternative']
}

# Fallback songs
FALLBACK_MUSIC = {
    "happy": [
        {"name": "Balam Pichkari", "artist": "Vishal Dadlani"},
        {"name": "Gallan Goodiyaan", "artist": "Shankar Mahadevan"}
    ],
    "sad": [
        {"name": "Channa Mereya", "artist": "Arijit Singh"},
        {"name": "Agar Tum Saath Ho", "artist": "Arijit Singh"}
    ],
    "neutral": [
        {"name": "Qaafirana", "artist": "Arijit Singh"}
    ]
}

HISTORY_FILE = "history.json"

def log_emotion(user_id, emotion):
    try:
        history = []

        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)

        history.append({
            "user_id": user_id,
            "emotion": emotion,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)

    except Exception as e:
        print(f"Logging error: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_face():
    try:
        data = request.json
        image_data = data["image"].split(",")[1]
        user_email = data.get("user_email", "anonymous")

        # Decode image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Save temp image
        if not os.path.exists("images"):
            os.makedirs("images")

        filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join("images", filename)
        cv2.imwrite(filepath, img)

        # Analyze emotion
        result = DeepFace.analyze(filepath, actions=["emotion"], enforce_detection=False)

        if isinstance(result, list):
            emotion_data = result[0]["emotion"]
        else:
            emotion_data = result["emotion"]

        emotion_data = {k: float(v) for k, v in emotion_data.items()}
        dominant_emotion = max(emotion_data, key=emotion_data.get)

        # Get songs
        songs = get_music_recommendations(dominant_emotion)

        # Log history
        log_emotion(user_email, dominant_emotion)

        return jsonify({
            "success": True,
            "emotion": dominant_emotion,
            "scores": emotion_data,
            "songs": songs
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def get_music_recommendations(emotion):
    try:
        if not sp:
            return FALLBACK_MUSIC.get(emotion, FALLBACK_MUSIC["neutral"])

        query = f"{emotion} hindi songs"
        results = sp.search(q=query, type="track", limit=10)

        songs = []
        for track in results["tracks"]["items"]:
            songs.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "spotify_url": f"https://open.spotify.com/track/{track['id']}"
            })

        return songs if songs else FALLBACK_MUSIC.get(emotion, [])

    except Exception as e:
        print(f"Spotify error: {e}")
        return FALLBACK_MUSIC.get(emotion, FALLBACK_MUSIC["neutral"])

# IMPORTANT FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)