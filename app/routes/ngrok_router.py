from flask import Blueprint, jsonify
import subprocess
import time
import requests
import os
from pyngrok import ngrok
from firebase_admin import db

ngrok_bp = Blueprint("ngrok", __name__)

def start_ngrok():
    # if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        ngrok.kill()
        
        public_url = ngrok.connect(5000).public_url
        print(f"Ngrok public URL: {public_url}")

        ref = db.reference("server/ngrok_url")
        ref.set(public_url)