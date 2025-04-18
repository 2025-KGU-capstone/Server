from flask import Blueprint, jsonify, Response, stream_with_context
import cv2
import base64
from app.services.webcam_service import capture_images, get_camera_stream, start_camera_stream, stop_camera_stream, video_feed

webcam_bp = Blueprint("webcam", __name__)

@webcam_bp.route("/capture_images", methods=["GET"])
def capture_picture():
	return capture_images()

@webcam_bp.route("/start", methods=["POST"])
def start():
    start_camera_stream()
    return {"status": "started"}

@webcam_bp.route("/stop", methods=["POST"])
def stop():
    stop_camera_stream()
    return {"status": "stopped"}

@webcam_bp.route("/video_feed")
def video_feed():
    def generate():
        buffer = b""
        proc = get_camera_stream()
        if proc is None:
            return  # 스트림이 종료된 상태면 아무것도 안 보냄

        while True:
            try:
                chunk = proc.stdout.read(1024)
                if not chunk:
                    break

                buffer += chunk
                while b"\xff\xd9" in buffer:
                    frame, buffer = buffer.split(b"\xff\xd9", 1)
                    frame += b"\xff\xd9"
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            except Exception as e:
                print(f"Streaming error: {e}")
                break

    return Response(stream_with_context(generate()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
