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
from dotenv import load_dotenv
from app.services.push_notification import control_siren
from app.services.face_man import recognize_person_from_image, load_visitor_encodings
from PIL import Image

from app.gpio.oled import display_safe_mode, clear_oled
load_dotenv()

CONFIDENCE_THRESHOLD = 0.8
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN")

# 전역 변수 선언
streaming_flag = False  # 스트리밍 상태 확인용

STREAM_CAMERA_INDEX = 0
CAP_CAMERA_INDEX = 1
SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# 전역 선언
camera1_proc = None
camera2_proc = None

stream_lock1 = threading.Lock()
stream_lock2 = threading.Lock()

box_present = False      # 상자가 현재 있는지 여부
matched_person_timestamp = 0
PERSON_RECOGNITION_VALID_DURATION = 10
last_face_check_time = 0
FACE_CHECK_INTERVAL = 1.0

# YOLO 모델 로드 (최상단에 위치)
model = torch.hub.load(
    "/home/admin/workspace/Server/yolov5",
    "custom",
    path="/home/admin/workspace/Server/pt_files/best_windows.pt",
    source="local"
)
model.to("cpu")

# YOLO 모델 로드(사람)
model2 = torch.hub.load(
    "/home/admin/workspace/Server/yolov5",
    "custom",
    path="/home/admin/workspace/Server/pt_files/best_window.pt",
    source="local"
)
model2.to("cpu")

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
	global streaming_flag, camera1_proc

	streaming_flag = False

	if camera1_proc is not None:
		camera1_proc.terminate()
		try:
			camera1_proc.wait(timeout=1)
		except subprocess.TimeoutExpired:
			camera1_proc.kill()
		camera1_proc = None

	print("Camera1 stream stopped.")

def stop_all_camera_stream():
    global streaming_flag, streaming_flag2, camera1_proc, camera2_proc

    streaming_flag = False
    streaming_flag2 = False

    if camera1_proc is not None:
        camera1_proc.terminate()
        try:
            camera1_proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            camera1_proc.kill()
        camera1_proc = None

    if camera2_proc is not None:
        camera2_proc.terminate()
        try:
            camera2_proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            camera2_proc.kill()
        camera2_proc = None

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
    global latest_frame, raw_frame_buffer, camera1_proc
    camera1_proc = get_camera_stream()
    buffer = b""

    while streaming_flag:
        chunk = camera1_proc.stdout.read(1024)
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
    global latest_frame, raw_frame_buffer, matched_person_timestamp, box_present
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
            detections = results.xyxy[0]

            # ✅ NEW: 상자 감지 여부 확인
            if any(conf >= 0.6 for *box, conf, cls in detections):
                box_present = True
            else:
                if box_present:  # 이전에 상자가 있었는데 지금은 없음
                    if (current_time - last_notified_time) >= 10:
                        if current_time - matched_person_timestamp <= PERSON_RECOGNITION_VALID_DURATION:
                            print("[INFO] Recently known person, box removed -> no siren.")
                        else:
                            print("[ALERT] Unknown or outdated person, box removed -> siren")
                            control_siren(True)

                        capture_from_stream1()
                        capture_from_stream2()
                        last_notified_time = current_time

                    box_present = False

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
    global streaming_flag

    with stream_lock1:
        if not streaming_flag:
            start_camera_stream()
            streaming_flag = True
    def generate():
        global streaming_flag
        try:
            while streaming_flag:
                with frame_lock:
                    frame = latest_frame.copy() if latest_frame is not None else None
                if frame is not None:
                    _, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                    )
                time.sleep(0.01)
        finally:
            with stream_lock1:
                streaming_flag = False
                stop_camera_stream()
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
    global latest_frame2, raw_frame_buffer2, camera2_proc
    camera2_proc = get_camera_stream2()
    buffer = b""

    while streaming_flag2:
        chunk = camera2_proc.stdout.read(1024)
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

visitor_encodings = load_visitor_encodings()

def model_thread_func2():
    global latest_frame2, raw_frame_buffer2, matched_person_timestamp, last_face_check_time
    while streaming_flag2:
        frame = None
        with frame_lock2:
            if raw_frame_buffer2 is not None:
                frame = raw_frame_buffer2.copy()
                raw_frame_buffer2 = None

        if frame is not None:
            results = model2(frame)
            detections = results.xyxy[0].cpu().numpy()

            if len(detections) > 0:
                print(f"[DEBUG] {len(detections)} object(s) detected")

                # ✅ 주기 제한 체크
                current_time = time.time()
                if current_time - last_face_check_time >= FACE_CHECK_INTERVAL:
                    try:
                        image_pil = Image.fromarray(frame).convert('RGB')
                        rgb_frame = np.array(image_pil).copy()

                        if rgb_frame.dtype != np.uint8:
                            rgb_frame = rgb_frame.astype(np.uint8)

                        matched_name = recognize_person_from_image(rgb_frame, visitor_encodings)

                        if matched_name:
                            matched_person_timestamp = time.time()
                            print(f"[INFO] Visitor identified: {matched_name}")
                        else:
                            print("[INFO] Visitor not recognized")

                    except Exception as e:
                        print(f"[ERROR] Face recognition error: {e}")

                    last_face_check_time = current_time  # ✅ 마지막 체크 시각 업데이트

            annotated = results.render()[0]

            with frame_lock2:
                latest_frame2 = annotated.copy()
        else:
            time.sleep(0.01)


def start_camera_stream2():
    global streaming_flag2
    streaming_flag2 = True
    threading.Thread(target=camera_thread_func2, daemon=True).start()
    threading.Thread(target=model_thread_func2, daemon=True).start()

def stop_camera_stream2():
	global camera2_proc, streaming_flag2
	streaming_flag2 = False
	if camera2_proc is not None:
		camera2_proc.terminate()
		try:
			camera2_proc.wait(timeout=1)
		except subprocess.TimeoutExpired:
			camera2_proc.kill()
		camera2_proc = None
	print("Camera 2 stream stopped.")


def video_feed2():
    global streaming_flag2

    with stream_lock2:
        if not streaming_flag2:
            start_camera_stream2()
            streaming_flag2 = True

    def generate():
        global streaming_flag2
        try:
            while streaming_flag2:
                with frame_lock2:
                    frame = latest_frame2.copy() if latest_frame2 is not None else None
                if frame is not None:
                    _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
                time.sleep(0.01)
        finally:
            with stream_lock2:
                streaming_flag2 = False
                stop_camera_stream2()
                print("Streaming 2 stopped.")

    return Response(
        stream_with_context(generate()),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
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
        return {"status": "error", "message": str(e)}

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
        return {"status": "error", "message": str(e)}


def start_streams():
	video_feed()
	video_feed2()
	return jsonify({
		"status": "started",
		"streams": {
			"video_feed": streaming_flag,
			"video_feed2": streaming_flag2
		}
	})

event_detected = False

def setup_pir_event():
	import RPi.GPIO as GPIO
	from app.gpio.gpio_init import PIR_PIN
	global event_detected

	if event_detected:
		GPIO.remove_event_detect(PIR_PIN)
		clear_oled()
		stop_all_camera_stream()
		print("PIR 이벤트 제거")
	else:
		GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=lambda pir: start_streams(), bouncetime=300)
		display_safe_mode()
		print("PIR 이벤트 감지 등록 완료")

	event_detected = not event_detected
	return {
		"status": "success",
		"event_detected": event_detected
	}
		
	# GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=control_siren(pir=True), bouncetime=300)
