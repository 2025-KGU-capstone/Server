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
    success1, frame1 = camera1.read()
    #success2, frame2 = camera2.read()
    
    if success1:
    #    _, buffer2 = cv2.imencode(".jpg", frame2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename1 = os.path.join(SAVE_DIR, f"camera1_{timestamp}.jpg")
        
        cv2.imwrite(filename1, frame1)
        _, buffer1 = cv2.imencode(".jpg", frame1)

        camera1.release()
        cv2.destroyAllWindows()

        return jsonify({
            "status": "success",
            "image1": base64.b64encode(buffer1).decode("utf-8"),
    #        "image2": base64.b64encode(buffer2).decode("utf-8"),
        })
    return jsonify({"status": "error", "message": "Failed to capture images", "saved_path": filename1})
