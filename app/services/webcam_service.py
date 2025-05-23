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

def start_camera_stream():
    global ffmpeg_process, streaming_flag
    if ffmpeg_process is None:
        ffmpeg_process = subprocess.Popen(
            'libcamera-vid -t 0 --inline --width 640 --height 480 --framerate 25 --codec yuv420 -o - | '
            'ffmpeg -f rawvideo -pix_fmt yuv420p -s 640x480 -i - -f mjpeg pipe:1',
            shell=True,
            stdout=subprocess.PIPE
        )
        streaming_flag = True
    return ffmpeg_process

def stop_camera_stream():
    global ffmpeg_process, streaming_flag
    if ffmpeg_process is not None:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
            ffmpeg_process.wait()
        ffmpeg_process = None
    streaming_flag = False

def get_camera_stream():
    global ffmpeg_process, streaming_flag
    return ffmpeg_process if streaming_flag else None

# def video_feed():
#     global streaming_flag

#     def generate():
#         buffer = b""
#         proc = get_camera_stream()
#         if proc is None:
#             return

#         while streaming_flag:
#             if proc.poll() is not None:
#                 break
#             try:
#                 chunk = proc.stdout.read(1024)
#                 if not chunk:
#                     break

#                 buffer += chunk
#                 while b"\xff\xd9" in buffer:
#                     frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
#                     frame_bytes += b"\xff\xd9"

#                     np_arr = np.frombuffer(frame_bytes, np.uint8)
#                     frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
#                     if frame is None:
#                         continue

#                     _, jpeg_frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])

#                     yield (b"--frame\r\n"
#                            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_frame.tobytes() + b"\r\n")
#             except Exception as e:
#                 print(f"Streaming error: {e}")
#                 break
#         print("Streaming stopped.")

#     return Response(stream_with_context(generate()),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')
					
# def video_feed():
# 	global streaming_flag

# 	def generate():
# 		buffer = b""
# 		proc = get_camera_stream()
# 		if proc is None:
# 			return

# 		frame_count = 0

# 		while streaming_flag:
# 			if proc.poll() is not None:
# 				break
# 			try:
# 				chunk = proc.stdout.read(1024)
# 				if not chunk:
# 					break

# 				buffer += chunk
# 				while b"\xff\xd9" in buffer:
# 					frame_bytes, buffer = buffer.split(b"\xff\xd9", 1)
# 					frame_bytes += b"\xff\xd9"

# 					np_arr = np.frombuffer(frame_bytes, np.uint8)
# 					frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
# 					if frame is None:
# 						continue

# 					# frame_count += 1
# 					# if frame_count % 2 == 0:
# 					# small_frame = cv2.resize(frame, (320, 320))
# 					# results = model(frame)
# 					# annotated_small = results.render()[0]
# 					# annotated_frame = cv2.resize(frame, (frame.shape[1], frame.shape[0]))
# 					# else:
					
# 					annotated_frame = frame

# 					_, jpeg_frame = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])

# 					yield (b"--frame\r\n"
# 						b"Content-Type: image/jpeg\r\n\r\n" + jpeg_frame.tobytes() + b"\r\n")
# 			except Exception as e:
# 				print(f"Streaming error: {e}")
# 				break
# 		print("Streaming stopped.")

# 	return Response(stream_with_context(generate()),
# 					mimetype='multipart/x-mixed-replace; boundary=frame')

streaming_flag = False
frame_lock = threading.Lock()
latest_frame = None
raw_frame_buffer = None

def get_camera_stream():
    import subprocess
    return subprocess.Popen(
        ["libcamera-vid", "-t", "0", "-o", "-", "--codec", "mjpeg", "--width", "640", "--height", "480"],
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
    while streaming_flag:
        frame = None
        with frame_lock:
            if raw_frame_buffer is not None:
                frame = raw_frame_buffer.copy()
                raw_frame_buffer = None
        if frame is not None:
            # 추론 & 주석
            results = model(frame)
            annotated = results.render()[0]
            # annotated = frame  # 테스트용으로 주석 생략
            with frame_lock:
                latest_frame = annotated.copy()
        else:
            time.sleep(0.01)

def start_camera_stream():
    global streaming_flag
    streaming_flag = True
    threading.Thread(target=camera_thread_func, daemon=True).start()
    threading.Thread(target=model_thread_func, daemon=True).start()

def video_feed():
    def generate():
        while streaming_flag:
            with frame_lock:
                frame = latest_frame.copy() if latest_frame is not None else None
            if frame is not None:
                _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
            time.sleep(0.01)
        print("Streaming stopped.")
    return Response(stream_with_context(generate()), mimetype='multipart/x-mixed-replace; boundary=frame')
