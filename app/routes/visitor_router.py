from flask import Blueprint, request, jsonify
import os

visitor_bp = Blueprint("visitor", __name__)

VISITOR_DIR = "visitor"
os.makedirs(VISITOR_DIR, exist_ok=True)

@visitor_bp.route("/upload", methods=["POST"])
def upload():
    name = request.form.get("name")
    file = request.files.get("file")

    if name and file:
        file_path = os.path.join(VISITOR_DIR, f"{name}.jpg")
        file.save(file_path)
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error", "message": "Invalid data"}), 400
