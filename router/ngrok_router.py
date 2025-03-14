from flask import Blueprint, jsonify
import subprocess
import time
import requests
from firebase_admin import db

ngrok_bp = Blueprint("ngrok", __name__)

@ngrok_bp.route("/start_ngrok", methods=["GET"])
def start_ngrok():
    subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)

    response = requests.get("http://127.0.0.1:4040/api/tunnels")
    if response.status_code == 200:
        tunnels = response.json()["tunnels"]
        public_url = tunnels[0]["public_url"]

        ref = db.reference("server/ngrok_url")
        ref.set(public_url)
        return jsonify({"ngrok_url": public_url})

    return jsonify({"error": "Failed to start ngrok"}), 500
