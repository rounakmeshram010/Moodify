import sys
import os
sys.path.append(r'c:\Users\DELL\OneDrive\Desktop\moodify')
import app

def diag():
    cid = app.SPOTIFY_CLIENT_ID
    secret = app.SPOTIFY_CLIENT_SECRET
    print(f"DEBUG: Client ID length: {len(cid)}")
    print(f"DEBUG: Secret length: {len(secret)}")
    print(f"DEBUG: Client ID starts with: {cid[:4]}")
    print(f"DEBUG: Secret starts with: {secret[:4]}")
    
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    try:
        auth_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
        token = auth_manager.get_access_token(as_dict=False)
        print("✅ SUCCESS: Token retrieved!")
    except Exception as e:
        print(f"❌ FAILURE: {e}")

if __name__ == "__main__":
    diag()
