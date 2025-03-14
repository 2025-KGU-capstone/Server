from flask import Blueprint, request, jsonify
from app.services.push_notification import send_push_notification

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/send_notification", methods=["POST"])
def send_notification():
    data = request.json
    token = data.get("token")
    title = data.get("title")
    body = data.get("body")

    if token and title and body:
        response = send_push_notification(token, title, body)
        return jsonify({"status": "success", "response": response})

    return jsonify({"status": "error", "message": "Missing required fields"}), 400
