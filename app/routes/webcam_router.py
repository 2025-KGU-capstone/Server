from flask import Blueprint, jsonify, Response, stream_with_context
from app.services.webcam_service import capture_images, get_camera_stream, start_camera_stream, stop_camera_stream, video_feed, streaming_flag,\
	start_camera_stream2, video_feed2, streaming_flag2, capture_from_stream2, capture_from_stream1,\
	start_streams, setup_pir_event, stop_all_camera_stream
from flask_apispec import doc


webcam_bp = Blueprint("webcam", __name__)

@webcam_bp.route("/capture_images", methods=["GET"])
@doc(description='사진 촬영', tags=['webcam'])
def capture_picture():
	return capture_images()

@webcam_bp.route("/start")
@doc(description='카메라 시작', tags=['webcam'])
def start():
	"""Start the camera stream."""
	start_camera_stream()
	return {"status": "started"}

@webcam_bp.route("/stop")
@doc(description='카메라 정지', tags=['webcam'])
def stop():
	"""Stop the camera stream."""
	stop_all_camera_stream()
	return {"status": "stopped"}

@webcam_bp.route("/video_feed1")
@doc(description='카메라 0번 비디오 피드', tags=['webcam'])
def video_feed_route():
    return video_feed()

@webcam_bp.route("/video_feed2")
@doc(description='카메라 1번 비디오 피드', tags=['webcam'])
def video_feed_route2():
    return video_feed2()

@webcam_bp.route("/start_all_streams")
@doc(description='두 개의 카메라 스트림 동시에 시작', tags=['webcam'])
def start_all_streams():
	return start_streams()

@webcam_bp.route("/capture")
@doc(description='스트리밍 중인 카메라1, 2에서 캡처', tags=['webcam'])
def capture_from_stream_route():
    res1 = capture_from_stream1()
    res2 = capture_from_stream2()

    data1 = res1.get_json()
    data2 = res2.get_json()

    return jsonify({
        "status": "success",
        "image1": data1.get("image1") if data1 else None,
        "image2": data2.get("image2") if data2 else None,
        "error1": data1.get("message") if data1 and data1.get("status") == "error" else None,
        "error2": data2.get("message") if data2 and data2.get("status") == "error" else None,
    })

@webcam_bp.route("/pir")
@doc(description='PIR 이벤트 시작', tags=['webcam'])
def pir_event_start():
	"""Start the PIR event detection."""
	# setup_pir_event()  # Uncomment if you want to set up PIR event detection
	return setup_pir_event()
