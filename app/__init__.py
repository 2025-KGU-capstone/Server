from flask import Flask
from app.routes.webcam_router import webcam_bp
from app.routes.visitor_router import visitor_bp
from app.routes.ngrok_router import ngrok_bp
from app.routes.notifications_router import notifications_bp
from app.services.firebase import initialize_firebase
from app.routes.ngrok_router import start_ngrok
import os
from dotenv import load_dotenv
from flasgger import Swagger
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from app.routes import *
from app.gpio.gpio_init import initialized_gpio
from app.services.webcam_service import setup_pir_event

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
FLASK_ENV = os.getenv("FLASK_ENV", "production")

# PYTHONPATH 설정
PYTHONPATH = os.getenv("PYTHONPATH")
if PYTHONPATH:
    import sys
    sys.path.append(PYTHONPATH)

def create_app():
	app = Flask(__name__)
	load_dotenv()

	# Firebase 및 ngrok 시작
	initialize_firebase()

	# Blueprint 등록
	app.register_blueprint(webcam_bp)
	app.register_blueprint(visitor_bp)
	# app.register_blueprint(ngrok_bp)
	app.register_blueprint(notifications_bp)

	# API 문서 설정
	app.config.update({
		'APISPEC_SPEC': APISpec(
			title="Webcam API",
			version="v1",
			openapi_version="2.0",
			plugins=[MarshmallowPlugin()],
		),
		'APISPEC_SWAGGER_UI_URL': '/apidocs',
	})

	docs = FlaskApiSpec(app)

	# View 함수 등록
	docs.register(capture_picture, blueprint='webcam')
	docs.register(start, blueprint='webcam')
	docs.register(stop, blueprint='webcam')
	docs.register(video_feed_route, blueprint='webcam')

	docs.register(delete, blueprint='visitor')
	docs.register(get_image, blueprint='visitor')
	docs.register(get_images, blueprint='visitor')
	docs.register(upload, blueprint='visitor')

	# docs.register(ngrok_status, blueprint='ngrok')

	docs.register(send_notification, blueprint='notifications')
	# docs.register(control_siren, blueprint='notifications')

	initialized_gpio()
	# setup_pir_event()
	return app


import atexit
import RPi.GPIO as GPIO

@atexit.register
def cleanup_gpio():
    GPIO.cleanup()
