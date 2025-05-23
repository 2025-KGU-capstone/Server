from flask import Blueprint, jsonify, Response, stream_with_context
from app.services.webcam_service import capture_images, get_camera_stream, start_camera_stream, stop_camera_stream, video_feed, streaming_flag
from flask_apispec import doc


webcam_bp = Blueprint("webcam", __name__)

@webcam_bp.route("/capture_images", methods=["GET"])
@doc(description='사진 촬영', tags=['webcam'])
def capture_picture():
	return capture_images()

@webcam_bp.route("/start", methods=["POST"])
@doc(description='카메라 시작', tags=['webcam'])
def start():
	"""Start the camera stream."""
	start_camera_stream()
	return {"status": "started"}

@webcam_bp.route("/stop", methods=["POST"])
@doc(description='카메라 정지', tags=['webcam'])
def stop():
	"""Stop the camera stream."""
	stop_camera_stream()
	return {"status": "stopped"}

@webcam_bp.route("/video_feed")
@doc(description='카메라 비디오 피드', tags=['webcam'])
def video_feed_route():
	"""Video feed from the camera."""
	global streaming_flag
	if not streaming_flag:
		start_camera_stream()
		# streaming_flag = True
	return video_feed()
