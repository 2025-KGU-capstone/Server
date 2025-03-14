from flask import Blueprint, jsonify
import cv2
import base64
from app.services.webcam_service import capture_images

webcam_bp = Blueprint("webcam", __name__)

@webcam_bp.route("/capture_images", methods=["GET"])
def capture():
    return capture_images()
