from flask import jsonify, Response, stream_with_context
import subprocess
import base64
import os
from datetime import datetime
import threading
import time
import numpy as np
import cv2
import torch
from app.services.push_notification import send_push_notification
from dotenv import load_dotenv

load_dotenv()

CONFIDENCE_THRESHOLD = 0.8
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN")

# 전역 변수 선언
ffmpeg_process = None
streaming_flag = False  # 스트리밍 상태 확인용

STREAM_CAMERA_INDEX = 0
CAP_CAMERA_INDEX = 1
SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)



# YOLO 모델 로드 (최상단에 위치)
model = torch.hub.load(
    "/home/admin/workspace/Server/yolov5",
    "custom",
    path="/home/admin/workspace/Server/pt_files/best_windows.pt",
    source="local"
)
model.to("cpu")

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

def stop_camera_stream():
    global ffmpeg_process, ffmpeg_process2
    global streaming_flag, streaming_flag2

    # 첫 번째 카메라 종료
    if ffmpeg_process is not None:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
        ffmpeg_process = None

    streaming_flag = False

    # 두 번째 카메라 종료
    if ffmpeg_process2 is not None:
        ffmpeg_process2.terminate()
        try:
            ffmpeg_process2.wait(timeout=1)
        except subprocess.TimeoutExpired:
            ffmpeg_process2.kill()
        ffmpeg_process2 = None

    streaming_flag2 = False

    print("All camera streams stopped.")


streaming_flag = False
frame_lock = threading.Lock()
latest_frame = None
raw_frame_buffer = None

def get_camera_stream():
    import subprocess
    return subprocess.Popen(
        ["libcamera-vid", "-t", "0", "-o", "-", "--codec", "mjpeg", "--width", "640", "--height", "860"],
        stdout=subprocess.PIPE
    )

def camera_thread_func():
    global latest_frame, raw_frame_buffer
    proc = get_camera_stream()
    buffer = b""

    while streaming_flag:
        chunk = proc.stdout.read(1024)
        if not chunk:
            break
        buffer += chunk

        while b"\xff\xd9" in buffer:
            frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
            frame_bytes += b"\xff\xd9"
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                with frame_lock:
                    latest_frame = frame.copy()
                    raw_frame_buffer = frame.copy()
    print("Camera thread ended.")


def model_thread_func():
	global latest_frame, raw_frame_buffer
	last_notified_time = 0  # 최근 알림 시각 (timestamp)

	while streaming_flag:
		frame = None
		with frame_lock:
			if raw_frame_buffer is not None:
				frame = raw_frame_buffer.copy()
				raw_frame_buffer = None

		if frame is not None:
			results = model(frame)
			annotated = results.render()[0]

			current_time = time.time()
			for *box, conf, cls in results.xyxy[0]:  # [x1, y1, x2, y2, conf, class_id]
				if conf < 0.6 and (current_time - last_notified_time) >= 10:
					label = results.names[int(cls)]
					send_push_notification(
						DEVICE_TOKEN, f"{label} 감지됨", f"신뢰도 {conf:.2f}"
					)
					# capture_from_stream1()
					# capture_from_stream2()
					last_notified_time = current_time
					break  # 하나만 감지되면 알림 보내고 종료

			with frame_lock:
				latest_frame = annotated.copy()
		else:
			time.sleep(0.01)


def start_camera_stream():
    global streaming_flag, streaming_flag2
    streaming_flag = True
    threading.Thread(target=camera_thread_func, daemon=True).start()
    threading.Thread(target=model_thread_func, daemon=True).start() #욜로 감지 쓰레딩 시작 부분
	
	# if streaming_flag2 == False:
	# 	# 두 번째 카메라가 시작되지 않았다면 시작
	# 	start_camera_stream2()


def video_feed():
    def generate():
        while streaming_flag:
            with frame_lock:
                frame = latest_frame.copy() if latest_frame is not None else None
            if frame is not None:
                _, jpeg = cv2.imencode(
                    ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                )
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )
            time.sleep(0.01)
        print("Streaming stopped.")

    return Response(
        stream_with_context(generate()),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

CAP_CAMERA_INDEX_2 = 1  # 새 인덱스
streaming_flag2 = False
latest_frame2 = None
raw_frame_buffer2 = None
frame_lock2 = threading.Lock()

def get_camera_stream2():
    import subprocess
    return subprocess.Popen(
        ["libcamera-vid",
         "--camera", str(CAP_CAMERA_INDEX_2),
         "-t", "0",
         "-o", "-",
         "--codec", "mjpeg",
         "--width", "640", "--height", "860"],
        stdout=subprocess.PIPE
    )

def camera_thread_func2():
    global latest_frame2, raw_frame_buffer2
    proc = get_camera_stream2()
    buffer = b""

    while streaming_flag2:
        chunk = proc.stdout.read(1024)
        if not chunk:
            break
        buffer += chunk

        while b"\xff\xd9" in buffer:
            frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
            frame_bytes += b"\xff\xd9"
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                with frame_lock2:
                    latest_frame2 = frame.copy()
                    raw_frame_buffer2 = frame.copy()
    print("Camera 2 thread ended.")

def model_thread_func2():
    global latest_frame2, raw_frame_buffer2
    while streaming_flag2:
        frame = None
        with frame_lock2:
            if raw_frame_buffer2 is not None:
                frame = raw_frame_buffer2.copy()
                raw_frame_buffer2 = None
        if frame is not None:
            results = model(frame)
            detections = results.xyxy[0].cpu().numpy()
            for det in detections:
                conf = det[4]
                cls_id = int(det[5])
                if conf < 0.3:
                    print(f"[Camera 0] Low Confidence: class={cls_id}, conf={conf:.2f}")

            annotated = results.render()[0]

            with frame_lock2:
                latest_frame2 = annotated.copy()
        else:
            time.sleep(0.01)

def start_camera_stream2():
    global streaming_flag2
    streaming_flag2 = True
    threading.Thread(target=camera_thread_func2, daemon=True).start()
    # threading.Thread(target=model_thread_func2, daemon=True).start()

def video_feed2():
    def generate():
        while streaming_flag2:
            with frame_lock2:
                frame = latest_frame2.copy() if latest_frame2 is not None else None
            if frame is not None:
                _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
            time.sleep(0.01)
        print("Streaming 2 stopped.")
    return Response(stream_with_context(generate()), mimetype='multipart/x-mixed-replace; boundary=frame')

from flask import jsonify

def capture_from_stream1():
    global latest_frame
    try:
        with frame_lock:
            if latest_frame is None:
                return jsonify({"status": "error", "message": "No frame available"})

            frame_copy = latest_frame.copy()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"stream1_capture_{timestamp}.jpg")
        # filename = os.path.join(SAVE_DIR, f"1.jpg")

        success = cv2.imwrite(filename, frame_copy)
        if not success:
            return jsonify({"status": "error", "message": "Failed to write image"})

        with open(filename, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        return jsonify({
            "status": "success",
            "image1": img_base64
        })
    except Exception as e:
        print(f"[capture_from_stream1 ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)})

def capture_from_stream2():
    global latest_frame2
    try:
        with frame_lock2:
            if latest_frame2 is None:
                return jsonify({"status": "error", "message": "No frame available"})

            frame_copy = latest_frame2.copy()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"stream2_capture_{timestamp}.jpg")
        # filename = os.path.join(SAVE_DIR, f"2.jpg")

        success = cv2.imwrite(filename, frame_copy)
        if not success:
            return jsonify({"status": "error", "message": "Failed to write image"})

        with open(filename, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        return jsonify({
            "status": "success",
            "image2": img_base64
        })
    except Exception as e:
        print(f"[capture_from_stream2 ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)})
