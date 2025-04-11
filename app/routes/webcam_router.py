from flask import Blueprint, jsonify
import cv2
import base64
from app.services.webcam_service import capture_images
from app.services.webcam_service import start_stream
from app.services.webcam_service import stop_stream
from app.services.webcam_service import video_feed

webcam_bp = Blueprint("webcam", __name__)

@webcam_bp.route("/capture_images", methods=["GET"])
def capture_picture():
    return capture_images()

@webcam_bp.route("/start", methods=["POST"])
def capture_live_start():
    return start_stream()

@webcam_bp.route("/stop", methods=["POST"])
def capture_live_stop():
    return stop_stream()

# 📺 영상 송출
@webcam_bp.route("/video_feed")
def capture_video_feed():
    return video_feed()
