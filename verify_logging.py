import requests
import base64
import os
import json

def test_analyze_logging():
    # Use a real image from the project
    image_path = "images/capture_20260313_062814.jpg"
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    dummy_image_data = f"data:image/jpeg;base64,{encoded_string}"
    
    url = "http://127.0.0.1:5000/analyze"
    payload = {
        "image": dummy_image_data,
        "user_email": "test@example.com"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Wait a bit for the file to be written
        if os.path.exists('history.json'):
            with open('history.json', 'r') as f:
                history = json.load(f)
                print("\nContent of history.json:")
                print(json.dumps(history, indent=4))
        else:
            print("\nError: history.json was NOT created.")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_analyze_logging()
