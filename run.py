import sys
import os
import subprocess
import time
import requests
from pyngrok import ngrok
from firebase_admin import db
from flask import jsonify
from app import create_app
import RPi.GPIO as GPIO
from app.routes.ngrok_router import start_ngrok

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

app = create_app()

@app.route("/")
def index():
    return "<h1>누군가의 소중한 상자를 지켜주는 서비스 NoTouch입니다.</h1>"

if __name__ == "__main__":
	# initialize_gpio()
	try:
		start_ngrok()
		app.run(host="0.0.0.0", port=5000, use_reloader=False)
	except KeyboardInterrupt:
		print("Shutting down the server...")
		GPIO.cleanup()


