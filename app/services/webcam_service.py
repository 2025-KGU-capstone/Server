import cv2
import base64
import os
from datetime import datetime
from flask import jsonify

# 카메라 초기화
camera1 = cv2.VideoCapture(1)
#camera2 = cv2.VideoCapture(2)

SAVE_DIR = "captured_images"
os.makedirs(SAVE_DIR, exist_ok=True)

def capture_images():
    # 매 요청마다 새로 카메라 열기
    camera = cv2.VideoCapture(1)
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
