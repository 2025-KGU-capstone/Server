from flask import Flask
from app.routes.webcam_router import webcam_bp
from app.routes.visitor_router import visitor_bp
from app.routes.ngrok_router import ngrok_bp
from app.routes.notifications_router import notifications_bp
from app.services.firebase import initialize_firebase

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))  # 기본값 0
FLASK_ENV = os.getenv("FLASK_ENV", "production")

# PYTHONPATH 설정
PYTHONPATH = os.getenv("PYTHONPATH")
if PYTHONPATH:
    import sys
    sys.path.append(PYTHONPATH)

def create_app():
    app = Flask(__name__)

    # Firebase 초기화
    initialize_firebase()

    # Blueprint 등록
    app.register_blueprint(webcam_bp)
    app.register_blueprint(visitor_bp)
    app.register_blueprint(ngrok_bp)
    app.register_blueprint(notifications_bp)

    return app
