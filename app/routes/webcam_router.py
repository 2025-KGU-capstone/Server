from flask import Blueprint, jsonify, Response, stream_with_context
import cv2
import base64

from app.services.webcam_service import capture_images, get_camera_stream, start_camera_stream, stop_camera_stream, video_feed, is_streaming
import numpy as np
import torch
import pathlib
pathlib.PosixPath = pathlib.WindowsPath

model = torch.hub.load(
    r"C:\Users\seong\Desktop\캡스톤\Server\yolov5",  # YOLOv5 경로
    "custom",
    path=r"C:\Users\seong\Desktop\캡스톤\Server\app\pt_files\best_windows.pt",
    source="local",
)

webcam_bp = Blueprint("webcam", __name__)

# 모듈 최상단에 한 번만 선언
# ffmpeg_process = None
# streaming_flag = False

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
            return  # 스트림 종료

        while True:
            try:
                chunk = proc.stdout.read(1024)
                if not chunk:
                    break

                buffer += chunk
                while b"\xff\xd9" in buffer:
                    frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
                    frame_bytes += b"\xff\xd9"

                    # JPEG 바이트 → OpenCV 이미지
                    np_arr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    # YOLO 추론
                    results = model(frame)

                    # 바운딩 박스 그리기
                    annotated_frame = results.render()[0]

                    # 다시 JPEG 인코딩
                    _, jpeg_frame = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])

                    yield (b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg_frame.tobytes() + b"\r\n")
            except Exception as e:
                print(f"Streaming error: {e}")
                break

    return Response(stream_with_context(generate()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@webcam_bp.route('/')
def video_feed2():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
