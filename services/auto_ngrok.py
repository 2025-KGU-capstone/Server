import requests
import subprocess
from firebase_admin import credentials, initialize_app, db
import time

# Firebase 초기화
def initialize_firebase():
    cred = credentials.Certificate("/home/mobilio/Downloads/safe-delivery-3f862-firebase-adminsdk-3izrv-d512e142b4.json")
    initialize_app(cred, {"databaseURL": "https://safe-delivery-3f862-default-rtdb.firebaseio.com"})

# Ngrok 실행 및 URL 가져오기
def start_ngrok():
    try:
        # Ngrok 실행 (포트 5000 예시)
        subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Ngrok started. Waiting for the public URL...")
        time.sleep(5)  # Ngrok 터널이 준비될 때까지 대기
    except Exception as e:
        print(f"Failed to start ngrok: {str(e)}")

# Ngrok URL Firebase에 저장
def update_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json()["tunnels"]
            public_url = tunnels[0]["public_url"]  # 첫 번째 터널의 URL 가져오기
            print(f"Ngrok Public URL: {public_url}")

            # Firebase Database에 저장
            ref = db.reference("server/ngrok_url")
            ref.set(public_url)
            print("Ngrok URL updated in Firebase.")
        else:
            print("Failed to fetch ngrok URL.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    initialize_firebase()
    start_ngrok()
    update_ngrok_url()
