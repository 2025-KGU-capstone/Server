import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        database_url = os.getenv("FIREBASE_DATABASE_URL")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        print("✅ Firebase initialized.")
