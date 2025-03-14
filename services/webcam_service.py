import cv2
import base64
from flask import jsonify

# 카메라 초기화
camera1 = cv2.VideoCapture(0)
camera2 = cv2.VideoCapture(2)

def capture_images():
    success1, frame1 = camera1.read()
    success2, frame2 = camera2.read()

    if success1 and success2:
        _, buffer1 = cv2.imencode(".jpg", frame1)
        _, buffer2 = cv2.imencode(".jpg", frame2)

        return jsonify({
            "status": "success",
            "image1": base64.b64encode(buffer1).decode("utf-8"),
            "image2": base64.b64encode(buffer2).decode("utf-8"),
        })
    return jsonify({"status": "error", "message": "Failed to capture images"})
