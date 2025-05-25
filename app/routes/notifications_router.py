# app/routes/notifications_router.py
from flask import Blueprint, jsonify, request
from flask_apispec import doc
import RPi.GPIO as GPIO
import threading
import time
import os
from app.services.push_notification import send_push_notification, control_siren

notifications_bp = Blueprint("notifications", __name__)

# app/routes/notifications_router.py
from flask import Blueprint, jsonify, request
from flask_apispec import doc


notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications", methods=["GET"])
@doc(description='푸시 알림 테스트', tags=['notifications'])
def init_notification():
    return {"status": "success", "message": "Notification system initialized."}

@notifications_bp.route("/siren", methods=["GET"])
@doc(description='사이렌 제어', tags=['notifications'])
def trigger_siren_via_http():
    control_siren(False)
    return "Siren will stop in 5 seconds", 200

@notifications_bp.route("/send_notification", methods=["POST"])
@doc(description='푸시 알림 전송', tags=['notifications'])
def send_notification():
    data = request.json
    token = data.get("token")
    title = data.get("title")
    body = data.get("body")

    if token and title and body:
        response = send_push_notification(token, title, body)
        return {"status": "success", "response": response}

    return {"status": "error", "message": "Missing required fields"}, 400
