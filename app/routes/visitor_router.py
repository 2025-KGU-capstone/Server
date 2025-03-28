from flask import Blueprint, request, jsonify, send_file
import os

visitor_bp = Blueprint("visitor", __name__)

VISITOR_DIR = "visitor"
os.makedirs(VISITOR_DIR, exist_ok=True)

sent_files = []

# 저장된 이미지 디렉토리
IMAGE_DIR = "saved_images"

@visitor_bp.route("/upload", methods=["POST"])
def upload():
    name = request.form.get("name")
    file = request.files.get("file")

    if name and file:
        file_path = os.path.join(VISITOR_DIR, f"{name}.jpg")
        file.save(file_path)
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error", "message": "Invalid data"}), 400

@visitor_bp.route("/get_images", methods=["GET"])
def get_images():
    global sent_files
    images_to_send = []

    # saved_images 디렉토리에서 아직 전송되지 않은 파일 검색
    for filename in os.listdir(IMAGE_DIR):
        if filename not in sent_files and filename.endswith((".png", ".jpg", ".jpeg")):
            images_to_send.append(filename)
            sent_files.append(filename)  # 전송 목록에 추가

    return jsonify({"images": images_to_send})

@visitor_bp.route("/get_image/<filename>", methods=["GET"])
def get_image(filename):
    file_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="image/jpeg")
    else:
        return jsonify({"error": "File not found"}), 404

@visitor_bp.route('/delete', methods=['POST'])
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