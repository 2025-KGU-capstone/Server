from flask import Blueprint, jsonify
import subprocess
import time
import requests
from pyngrok import ngrok
from firebase_admin import db

ngrok_bp = Blueprint("ngrok", __name__)

# @ngrok_bp.route("/start_ngrok", methods=["GET"])
# def start_ngrok():
#     subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     time.sleep(5)

#     response = requests.get("http://127.0.0.1:4040/api/tunnels")
#     if response.status_code == 200:
#         tunnels = response.json()["tunnels"]
#         public_url = tunnels[0]["public_url"]

#         ref = db.reference("server/ngrok_url")
#         ref.set(public_url)
#         return jsonify({"ngrok_url": public_url})

#     return jsonify({"error": "Failed to start ngrok"}), 500

@ngrok_bp.route("/start_ngrok", methods=["GET"])
def start_ngrok():
    ngrok.kill()  # 기존 세션 종료 (중복 에러 방지)

    tunnel = ngrok.connect(5000, "http")  # ✅ 이건 NgrokTunnel 객체임
    public_url = tunnel.public_url       # ✅ 문자열로 꺼내야 함
    print("🌍 ngrok URL:", public_url)

    ref = db.reference("server/ngrok_url")
    ref.set(public_url)

    return jsonify({"ngrok_url": public_url})