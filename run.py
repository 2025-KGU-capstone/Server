import sys
import os
import subprocess
import time
import requests
from pyngrok import ngrok
from firebase_admin import db
from flask import jsonify

from app.routes.ngrok_router import start_ngrok

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
