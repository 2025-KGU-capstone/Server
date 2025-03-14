from flask import Flask
from run.routes.webcam_router import webcam_bp
from run.routes.visitor_router import visitor_bp
from run.routes.ngrok_router import ngrok_bp
from run.routes.notifications_router import notifications_bp
from run.services.firebase import initialize_firebase

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
