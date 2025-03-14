from flask import Flask, jsonify, send_file, request
import cv2
import base64
from pyngrok import ngrok
import os
from firebase_admin import credentials, initialize_app, db

def initialize_firebase():
    cred = credentials.Certificate("/home/mobilio/Downloads/safe-delivery-3f862-firebase-adminsdk-3izrv-d512e142b4.json")
    initialize_app(cred, {"databaseURL": "https://safe-delivery-3f862-default-rtdb.firebaseio.com"})

def update_ngrok_url(public_url):
    try:
        ref = db.reference("server/ngrok_url")
        ref.set(public_url)
        print("Ngrok URL updated in Firebase.")
    except Exception as e:
        print(f"Failed to update Firebase: {str(e)}")



app = Flask(__name__)

# 방문자 데이터 저장 경로
VISITOR_DIR = "visitor"
os.makedirs(VISITOR_DIR, exist_ok=True)

sent_files = []

# 저장된 이미지 디렉토리
IMAGE_DIR = "saved_images"

# 두 대의 카메라 초기화
camera1 = cv2.VideoCapture(0)  # 첫 번째 카메라
camera2 = cv2.VideoCapture(2)  # 두 번째 카메라

@app.route('/capture_images', methods=['GET'])
def capture_images():
    # 카메라 1에서 프레임 캡처
    success1, frame1 = camera1.read()
    # 카메라 2에서 프레임 캡처
    success2, frame2 = camera2.read()

    if success1 and success2:
        # 카메라 1 이미지 Base64 인코딩
        _, buffer1 = cv2.imencode('.jpg', frame1)
        image1_base64 = base64.b64encode(buffer1).decode('utf-8')

        # 카메라 2 이미지 Base64 인코딩
        _, buffer2 = cv2.imencode('.jpg', frame2)
        image2_base64 = base64.b64encode(buffer2).decode('utf-8')

        # JSON 응답으로 반환
        return jsonify({
            'status': 'success',
            'image1': image1_base64,
            'image2': image2_base64
        })
    else:
        return jsonify({'status': 'error', 'message': 'Failed to capture images'})
    

    
@app.route("/get_images", methods=["GET"])
def get_images():
    global sent_files
    images_to_send = []

    # saved_images 디렉토리에서 아직 전송되지 않은 파일 검색
    for filename in os.listdir(IMAGE_DIR):
        if filename not in sent_files and filename.endswith((".png", ".jpg", ".jpeg")):
            images_to_send.append(filename)
            sent_files.append(filename)  # 전송 목록에 추가

    return jsonify({"images": images_to_send})



@app.route("/get_image/<filename>", methods=["GET"])
def get_image(filename):
    file_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="image/jpeg")
    else:
        return jsonify({"error": "File not found"}), 404
    
    
    
@app.route('/upload', methods=['POST'])
def upload():
    name = request.form.get('name')
    file = request.files.get('file')

    if name and file:
        file_path = os.path.join(VISITOR_DIR, f"{name}.jpg")
        file.save(file_path)
        return {"status": "success"}, 200
    return {"status": "error", "message": "Invalid data"}, 400


@app.route('/delete', methods=['POST'])
def delete():
    name = request.json.get('name')  # 삭제할 이름

    if name:
        file_path = os.path.join(VISITOR_DIR, f"{name}.jpg")
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success"}, 200
        else:
            return {"status": "error", "message": "File not found"}, 404
    return {"status": "error", "message": "Invalid data"}, 400

    

if __name__ == '__main__':
    # Firebase 초기화
    initialize_firebase()

    # Ngrok으로 Flask 서버 노출
    public_url = ngrok.connect(5000).public_url
    print(f"Ngrok public URL: {public_url}")

    # Ngrok URL을 Firebase에 저장
    update_ngrok_url(public_url)

    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)
