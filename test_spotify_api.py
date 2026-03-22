import sys
import os
import random
sys.path.append(r'c:\Users\DELL\OneDrive\Desktop\moodify')
import app

def test_spotify():
    print(f"Checking Spotify API for 'happy' mood...")
    try:
        # Re-initialize or use existing
        sp = app.sp
        query = "Hindi happy Bollywood songs"
        results = sp.search(q=query, type='track', limit=5)
        
        if results and 'tracks' in results and results['tracks']['items']:
            print(f"✅ SUCCESS: Found {len(results['tracks']['items'])} tracks.")
            for track in results['tracks']['items']:
                print(f" - {track['name']} by {track['artists'][0]['name']} (URL: {track['external_urls']['spotify']})")
        else:
            print("❌ FAILURE: No tracks found.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_spotify()
