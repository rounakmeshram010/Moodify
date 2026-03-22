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
import socket
import json

app = Flask(__name__)
CORS(app)

# Spotify API credentials
# Using provided credentials
SPOTIFY_CLIENT_ID ='62135b50074945d78054ee48d512db22'
SPOTIFY_CLIENT_SECRET ='ca00638e290b4d798aec0a98b3290172'

def get_spotify_client():
    """Return an authenticated Spotify client."""
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

sp = get_spotify_client()

def check_spotify_connection():
    """Check if Spotify servers are reachable"""
    print("--- Spotify Connection Diagnostics ---")
    try:
        host = "accounts.spotify.com"
        socket.gethostbyname(host)
        print(f"✅ DNS Check: Successfully resolved {host}")
    except socket.gaierror:
        print(f"❌ DNS Check: Failed to resolve accounts.spotify.com")
        print("   This is a network/DNS issue on your computer.")
        print("   Suggestions: Check internet, disable VPN/Firewall, or try using 8.8.8.8 DNS.")
    
    try:
        # Test basic authentication attempt
        sp.auth_manager.get_access_token()
        print("✅ Auth Check: API Credentials are valid and connection is active.")
    except Exception as e:
        print(f"⚠️ Auth/Connection Check: Failed to authenticate with Spotify.")
        print(f"   Error: {str(e)}")
    print("--------------------------------------")

# Check connection on startup
check_spotify_connection()

# Mood to music genre mapping
MOOD_TO_GENRE = {
    'happy': ['pop', 'dance', 'party'],
    'sad': ['sad', 'acoustic', 'blues'],
    'angry': ['rock', 'metal', 'hardcore'],
    'neutral': ['indie', 'chill', 'ambient'],
    'surprise': ['electronic', 'edm', 'pop'],
    'fear': ['ambient', 'classical', 'chill'],
    'disgust': ['rock', 'alternative', 'grunge']
}

# Fallback music data for when API is unreachable (Hindi/Bollywood focus)
FALLBACK_MUSIC = {
    'happy': [
        {'name': 'Mummy Ji', 'artist': 'Vedaa', 'spotify_url': 'https://open.spotify.com/track/4jVn4PEY1I0G3zE854MdxL'},
        {'name': 'Agar Ho Tum', 'artist': 'Jubin Nautiyal', 'spotify_url': 'https://open.spotify.com/track/2JS0RFqBJvBtvG1GIsZmjW'},
        {'name': 'Dekhha Tenu', 'artist': 'Mohammad Faiz', 'spotify_url': 'https://open.spotify.com/track/10U1hU4c1s5l3P0X0V2X3Y'},
        {'name': 'Dil Jhoom', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/622hK4u7u0MhRdx7fGzS91'},
        {'name': 'Apna Bana Le', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/4C0hU81D7Gg6c5u1xXq6r5'},
        {'name': 'Satranga', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/2i626w1M0XU2T7g3J2K1J4'},
        {'name': 'O Maahi', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/0vKz4g2J9k8X6X8Z4W8L2k'},
        {'name': 'Ghungroo', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/4Qx2K7tM1h1U9h2J7J0T9C'},
        {'name': 'Aankh Marey', 'artist': 'Neha Kakkar', 'spotify_url': 'https://open.spotify.com/track/7s7kC901eGkCj9m30Jp4dD'},
        {'name': 'Badtameez Dil', 'artist': 'Benny Dayal', 'spotify_url': 'https://open.spotify.com/track/6I1Hq1o38KkM1T3w2yJgM6'},
        {'name': 'Balam Pichkari', 'artist': 'Vishal Dadlani', 'spotify_url': 'https://open.spotify.com/track/6gC8u2P2L2S0M7f5R2N05N'},
        {'name': 'Gallan Goodiyaan', 'artist': 'Shankar Mahadevan', 'spotify_url': 'https://open.spotify.com/track/622hK4u7u0MhRdx7fGzS91'},
        {'name': 'London Thumakda', 'artist': 'Labh Janjua', 'spotify_url': 'https://open.spotify.com/track/0cDP69z3bN3J28P2Z3y50g'}
    ],
    'sad': [
        {'name': 'Channa Mereya', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/0x5H605N411K63fKxWqK60'},
        {'name': 'Hamari Adhuri Kahani', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/3ZtP46gL31TjQ2fXJpYfCj'},
        {'name': 'Agar Tum Saath Ho', 'artist': 'Alka Yagnik, Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/3hf79Yp9vPhA6u9v8m7uR2'},
        {'name': 'Tujhe Kitna Chahne Lage', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/2fGzMhUq3z5L1c7z4C2a0N'},
        {'name': 'Humraah', 'artist': 'Sachet Tandon', 'spotify_url': 'https://open.spotify.com/track/5nB2R1K1l1l1Q4C5N5W0H0'},
        {'name': 'Phir Bhi Tumko Chaahunga', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/0Y4lC8XG8Z2L3J3Xk7Y8mQ'},
        {'name': 'Abhi Mujh Mein Kahin', 'artist': 'Sonu Nigam', 'spotify_url': 'https://open.spotify.com/track/0wM0P4C21r7n908N5c0Q9e'},
        {'name': 'Jag Soona Soona Lage', 'artist': 'Rahat Fateh Ali Khan', 'spotify_url': 'https://open.spotify.com/track/6q00P7bH6n8R7s5tN4c53T'},
        {'name': 'Aadat', 'artist': 'Atif Aslam', 'spotify_url': 'https://open.spotify.com/track/6E936Ld1X6P3sU14Vd4uR2'}
    ],
    'angry': [
        {'name': 'Sadda Haq', 'artist': 'Mohit Chauhan', 'spotify_url': 'https://open.spotify.com/track/30gBcfjWwB9k4v2K4nZc25'},
        {'name': 'Aarambh Hai Prachand', 'artist': 'Piyush Mishra', 'spotify_url': 'https://open.spotify.com/track/1a2R0g9bVwK0mC0i0tN5Bw'},
        {'name': 'Machi Bhasad', 'artist': 'Bloodywood', 'spotify_url': 'https://open.spotify.com/track/1LGgRybx6vnACSRnYcGmMl'},
        {'name': 'Gaddaar', 'artist': 'Bloodywood', 'spotify_url': 'https://open.spotify.com/track/4jD2Z6vY5j1Z0Q0R5X5C6z'},
        {'name': 'Ziddi Dil', 'artist': 'Vishal Dadlani', 'spotify_url': 'https://open.spotify.com/track/3hf79Yp9vPhA6u9v8m7uR2'},
        {'name': 'Kar Har Maidan Fateh', 'artist': 'Sukhwinder Singh', 'spotify_url': 'https://open.spotify.com/track/4jV44hJ70p761a29x2Xj5W'},
        {'name': 'Khoon Chala', 'artist': 'A.R. Rahman', 'spotify_url': 'https://open.spotify.com/track/2fGzMhUq3z5L1c7z4C2a0N'}
    ],
    'neutral': [
        {'name': 'Nazm Nazm', 'artist': 'Arko', 'spotify_url': 'https://open.spotify.com/track/4h9A0f8u89Cg8u6790C9gB'},
        {'name': 'Qaafirana', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/1Apk7v87QHLNYqrsT0zhE8'},
        {'name': 'Iktara', 'artist': 'Amit Trivedi', 'spotify_url': 'https://open.spotify.com/track/6E936Ld1X6P3sU14Vd4uR2'},
        {'name': 'Pal Pal Dil Ke Paas', 'artist': 'Arijit Singh', 'spotify_url': 'https://open.spotify.com/track/3hf79Yp9vPhA6u9v8m7uR2'},
        {'name': 'Ranjheya Ve', 'artist': 'Antara Mitra', 'spotify_url': 'https://open.spotify.com/track/10U1hU4c1s5l3P0X0V2X3Y'},
        {'name': 'Heer', 'artist': 'Harshdeep Kaur', 'spotify_url': 'https://open.spotify.com/track/6vKz4g2J9k8X6X8Z4W8L2k'}
    ],
    'surprise': [
        {'name': 'Aaj Ki Raat', 'artist': 'Madhubanti Bagchi', 'spotify_url': 'https://open.spotify.com/track/2JS0RFqBJvBtvG1GIsZmjW'},
        {'name': 'Tauba Tauba', 'artist': 'Karan Aujla', 'spotify_url': 'https://open.spotify.com/track/4C0hU81D7Gg6c5u1xXq6r5'},
        {'name': 'Jamal Kudu', 'artist': 'Harshavardhan Rameshwar', 'spotify_url': 'https://open.spotify.com/track/2i626w1M0XU2T7g3J2K1J4'},
        {'name': 'Bhool Bhulaiyaa 3 Title', 'artist': 'Pitbull, Diljit Dosanjh', 'spotify_url': 'https://open.spotify.com/track/0vKz4g2J9k8X6X8Z4W8L2k'},
        {'name': 'Sher Khul Gaye', 'artist': 'Vishal-Shekhar', 'spotify_url': 'https://open.spotify.com/track/622hK4u7u0MhRdx7fGzS91'},
        {'name': 'Aayi Nai', 'artist': 'Pawan Singh', 'spotify_url': 'https://open.spotify.com/track/4Qx2K7tM1h1U9h2J7J0T9C'}
    ],
    'fear': [
        {'name': 'Aake Teri Bahon Mein', 'artist': 'Raaz', 'spotify_url': 'https://open.spotify.com/track/0wM0P4C21r7n908N5c0Q9e'},
        {'name': 'Bheegi Bheegi', 'artist': 'James', 'spotify_url': 'https://open.spotify.com/track/6E936Ld1X6P3sU14Vd4uR2'},
        {'name': 'Jia Dhadak Dhadak Jaye', 'artist': 'Rahat Fateh Ali Khan', 'spotify_url': 'https://open.spotify.com/track/6q00P7bH6n8R7s5tN4c53T'},
        {'name': 'Aa Bhi Ja Aa Bhi Ja', 'artist': 'Lucky Ali', 'spotify_url': 'https://open.spotify.com/track/3hf79Yp9vPhA6u9v8m7uR2'},
        {'name': 'Lori of Death', 'artist': 'Mangalavaaram', 'spotify_url': 'https://open.spotify.com/track/2JS0RFqBJvBtvG1GIsZmjW'}
    ],
    'disgust': [
        {'name': 'Bhaag D.K. Bose', 'artist': 'Ram Sampath', 'spotify_url': 'https://open.spotify.com/track/6gC8u2P2L2S0M7f5R2N05N'},
        {'name': 'Emotional Atyachar', 'artist': 'Bappi Lahiri', 'spotify_url': 'https://open.spotify.com/track/622hK4u7u0MhRdx7fGzS91'},
        {'name': 'Udta Punjab', 'artist': 'Amit Trivedi', 'spotify_url': 'https://open.spotify.com/track/0cDP69z3bN3J28P2Z3y50g'},
        {'name': 'Panga', 'artist': 'Diljit Dosanjh', 'spotify_url': 'https://open.spotify.com/track/5S4JvQh1G1r36sWbZq20v3'}
    ]
}

# File for storing user emotion history
HISTORY_FILE = 'history.json'

def log_emotion(user_id, emotion):
    """Log user emotion with timestamp to a JSON file."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
            
        new_entry = {
            'user_id': user_id,
            'emotion': emotion,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        history.append(new_entry)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
            
        return True
    except Exception as e:
        print(f"Error logging to JSON: {str(e)}")
        return False

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_face():
    try:
        # Get image data and user info from request
        data = request.json
        image_data = data['image'].split(',')[1]
        user_email = data.get('user_email', 'anonymous')
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save image persistently with timestamp
        if not os.path.exists('images'):
            os.makedirs('images')
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"capture_{timestamp}.jpg"
        persistent_path = os.path.join('images', image_filename)
        cv2.imwrite(persistent_path, img)
        
        # Analyze emotion using DeepFace
        result = DeepFace.analyze(persistent_path, actions=['emotion'], enforce_detection=False)
        
        # Get dominant emotion
        if isinstance(result, list):
            emotion_data = result[0]['emotion']
        else:
            emotion_data = result['emotion']
        
        # Convert numpy float32 to regular Python float
        emotion_data = {k: float(v) for k, v in emotion_data.items()}
            
        dominant_emotion = max(emotion_data, key=emotion_data.get)
        print(f"Detected dominant emotion: {dominant_emotion}")
        
        # Get music recommendations based on emotion
        songs = get_music_recommendations(dominant_emotion)
        print(f"Retrieved {len(songs)} songs for mood {dominant_emotion}")
        
        # Log the emotion history
        log_emotion(user_email, dominant_emotion)
        
        return jsonify({
            'success': True,
            'emotion': dominant_emotion,
            'emotion_scores': emotion_data,
            'songs': songs,
            'image_path': persistent_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_music_recommendations(emotion):
    """Get Spotify music recommendations based on emotion"""
    try:
        # Check if Spotify credentials are set
        if SPOTIFY_CLIENT_ID == 'your_client_id_here' or SPOTIFY_CLIENT_SECRET == 'your_client_secret_here':
            print("ERROR: Spotify credentials not set!")
            return []
        
        # Search for tracks with randomization
        songs = []
        # Mixed search queries for variety (Prioritizing Hindi)
        search_queries = [
            f"Hindi {emotion} Bollywood songs",
            f"Top {emotion} Hindi hits",
            f"Random {emotion} Bollywood tracks",
            f"Latest {emotion} Hindi songs"
        ]
        
        for query in search_queries:
            try:
                # Add random offset to get different songs each time
                random_offset = random.randint(0, 50)
                print(f"Searching Spotify for: {query} (offset: {random_offset})")
                
                results = sp.search(q=query, type='track', limit=20, offset=random_offset)
                
                if results and 'tracks' in results and results['tracks']['items']:
                    items = results['tracks']['items']
                    random.shuffle(items)
                    
                    for track in items:
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        # Format YouTube search URL
                        search_query = f"{track_name} {artist_name}".replace(" ", "+")
                        youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
                        
                        songs.append({
                            'name': track_name,
                            'artist': artist_name,
                            'preview_url': track['preview_url'],
                            'spotify_url': f"https://open.spotify.com/track/{track['id']}",
                            'youtube_url': youtube_url,
                            'image': track['album']['images'][0]['url'] if track['album']['images'] else None
                        })
                
                if len(songs) >= 20:
                    break
            except Exception as search_error:
                print(f"Error searching for query {query}: {search_error}")
                if "403" in str(search_error):
                    print("Detected 403 Forbidden. This account may require Premium for certain API calls.")
                    break
                continue
        
        # If no songs were found or API restricted, use the refreshed fallback list
        if not songs:
            print(f"No songs found from API. Using high-quality fallback for mood: {emotion}")
            fallbacks = FALLBACK_MUSIC.get(emotion.lower(), FALLBACK_MUSIC['neutral'])
            
            # Add youtube_url to fallback songs
            for s in fallbacks:
                if 'youtube_url' not in s:
                    q = f"{s['name']} {s['artist']}".replace(" ", "+")
                    s['youtube_url'] = f"https://www.youtube.com/results?search_query={q}"
            
            return fallbacks
            
        return songs[:20]
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        # Return fallback music if API fails
        print(f"Using fallback recommendations for mood: {emotion}")
        return FALLBACK_MUSIC.get(emotion.lower(), FALLBACK_MUSIC['neutral'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)