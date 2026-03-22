import sys
import os

# Add the directory to sys.path to import app
sys.path.append(r'c:\Users\DELL\OneDrive\Desktop\moodify')

try:
    from app import FALLBACK_MUSIC
    print("Successfully imported FALLBACK_MUSIC from app.py")
    
    total_songs = 0
    for mood, songs in FALLBACK_MUSIC.items():
        count = len(songs)
        print(f"Mood: {mood}, Songs: {count}")
        total_songs += count
        
        # Verify fields
        for i, song in enumerate(songs):
            if 'image' in song:
                print(f"  ERROR: Song at index {i} in '{mood}' still has 'image' field: {song}")
            if not song.get('spotify_url').startswith('https://open.spotify.com/'):
                print(f"  ERROR: Song at index {i} in '{mood}' has invalid spotify_url: {song.get('spotify_url')}")
            if not all(k in song for k in ('name', 'artist', 'spotify_url')):
                print(f"  ERROR: Song at index {i} in '{mood}' is missing fields: {song}")
    
    print(f"\nTotal songs in fallback dictionary: {total_songs}")
    if total_songs == 140:
        print("PERFECT: 140 songs (20 songs for each of the 7 moods).")
    else:
        print(f"WARNING: Expected 140 songs, but found {total_songs}.")

except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
