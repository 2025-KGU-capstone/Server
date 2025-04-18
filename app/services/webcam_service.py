import cv2
import base64
import os
import time
import threading
from datetime import datetime
from flask import jsonify, Response

# 카메라 초기화
camera1 = cv2.VideoCapture(1)
#camera2 = cv2.VideoCapture(2)

CAMERA_INDEX = 1
SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

is_streaming = False
frame_lock = threading.Lock()
current_frame = None

# 라이브 프레임 캡처 함수
def capture_stream():
    global current_frame
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    while is_streaming:
        success, frame = cap.read()
        if success:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            with frame_lock:
                current_frame = buffer.tobytes()
        time.sleep(0.01)

    cap.release()

# 라이브 시작
def start_stream():
    global is_streaming
    if not is_streaming:
        is_streaming = True
        threading.Thread(target=capture_stream, daemon=True).start()
        return jsonify({"status": "started"})
    return jsonify({"status": "already streaming"})

# 라이브 정지
def stop_stream():
    global is_streaming
    is_streaming = False
    return jsonify({"status": "stopped"})

# 정지 이미지 캡처
def capture_images():
    # 매 요청마다 새로 카메라 열기
    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    success, frame = camera.read()

    if success:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"camera1_{timestamp}.jpg")

        cv2.imwrite(filename, frame)
        _, buffer = cv2.imencode(".jpg", frame)

        camera.release()
        cv2.destroyAllWindows()

        return jsonify({
            "status": "success",
            "image1": base64.b64encode(buffer).decode("utf-8"),
        })

    camera.release()
    cv2.destroyAllWindows()
    return jsonify({"status": "error", "message": "Failed to capture images"})

def video_feed():
    last_frame = None

    def generate():
        nonlocal last_frame
        while is_streaming:
            with frame_lock:
                frame = current_frame
            if frame and frame != last_frame:
                last_frame = frame
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.01)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame", headers={
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    })