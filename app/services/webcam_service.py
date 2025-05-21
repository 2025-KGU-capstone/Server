import subprocess
import base64
import os
import time
import threading
import requests
import subprocess
# import io
# from picamera2 import Picamera2, Preview
from flask import Response, stream_with_context, jsonify
from datetime import datetime

import numpy as np
import cv2

import torch
import pathlib
pathlib.PosixPath = pathlib.WindowsPath

model = torch.hub.load(
    r"C:\Users\seong\Desktop\캡스톤\Server\yolov5",  # YOLOv5 경로
    "custom",
    path=r"C:\Users\seong\Desktop\캡스톤\Server\app\pt_files\best_windows.pt",
    source="local",
)

# 카메라 초기화
# camera1 = cv2.VideoCapture(1)
#camera2 = cv2.VideoCapture(2)
# 카메라 스트리밍 시작 및 중지
ffmpeg_process = None
streaming_flag = False  # 추가: 스트리밍 중인지 상태 확인용

STREAM_CAMERA_INDEX = 0
CAP_CAMERA_INDEX = 1
SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

is_streaming = False
frame_lock = threading.Lock()
current_frame = None

def capture_images():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SAVE_DIR, f"photo_{timestamp}.jpg")

    subprocess.run([
        "libcamera-jpeg",
        "--camera", str(CAP_CAMERA_INDEX),
        "-o", filename,
        "--width", "640",
        "--height", "480",
        "-n"
    ], check=True)

    with open(filename, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    return jsonify({
        "status": "success",
        "image1": img_base64
    })


def start_camera_stream():
    global ffmpeg_process, streaming_flag
    if ffmpeg_process is None:
        ffmpeg_process = subprocess.Popen(
            'libcamera-vid -t 0 --inline --width 640 --height 480 --framerate 25 --codec yuv420 -o - | '
            'ffmpeg -f rawvideo -pix_fmt yuv420p -s 640x480 -i - -f mjpeg pipe:1',
            shell=True,
            stdout=subprocess.PIPE
        )
        streaming_flag = True  # global 선언 덕분에 여기서 변경됨
    return ffmpeg_process

def stop_camera_stream():
    global ffmpeg_process, streaming_flag
    if ffmpeg_process is not None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait(timeout=1)
        ffmpeg_process = None
    streaming_flag = False  # 역시 전역 변수에 쓰기

def get_camera_stream():
    # 읽기 전용이니까 global 선언 안 해도 OK
    return ffmpeg_process if streaming_flag else None

def is_streaming():
    return streaming_flag

def video_feed():
    def generate():
        buffer = b""
        proc = get_camera_stream()
        if proc is None:
            return

        while is_streaming():
            if proc.poll() is not None:
                break
            try:
                chunk = proc.stdout.read(1024)
                if not chunk:
                    break

                buffer += chunk
                while b"\xff\xd9" in buffer:
                    frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
                    frame_bytes += b"\xff\xd9"

                    # JPEG 바이트를 OpenCV 이미지로 변환
                    np_arr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    # YOLO 모델 추론
                    results = model(frame)

                    # 바운딩 박스 그리기
                    annotated_frame = results.render()[0]

                    # 다시 JPEG 인코딩
                    _, jpeg_frame = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    yield (b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg_frame.tobytes() + b"\r\n")
            except Exception as e:
                print("streaming error:", e)
                break

        print("✅ generate() 종료됨")

    return Response(stream_with_context(generate()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# def generate_frames():
#     picam2 = Picamera2()
#     # 해상도 설정 (640×480), JPEG 포맷으로 전송
#     config = picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
#     picam2.configure(config)
#     picam2.start()
    
#     while True:
#         # NumPy 배열로 프레임 획득
#         frame = picam2.capture_array()
#         # JPEG로 인코딩
#         ret, jpeg = cv2.imencode('.jpg', frame)
#         if not ret:
#             continue
#         data = jpeg.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
