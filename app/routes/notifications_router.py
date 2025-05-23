# app/routes/notifications_router.py
from flask import Blueprint, jsonify, request
from flask_apispec import doc
import RPi.GPIO as GPIO
import threading
import time
import os


# from app.gpio.gpio_init import BUZZER_PIN, LED_PIN, buzzer_pwm_started,\
# siren_active, siren_thread, initialize_gpio, get_buzzer_pwm

notifications_bp = Blueprint("notifications", __name__)
BUZZER_PIN = 18
LED_PIN = 4

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_PIN, GPIO.OUT)

buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)
buzzer_pwm_started = False

siren_active = False
siren_thread = None


@notifications_bp.route("/notifications", methods=["GET"])
@doc(description='푸시 알림 테스트', tags=['notifications'])
def init_notification():
	return {"status": "success", "message": "Notification system initialized."}

def _siren_loop():
    global siren_active, buzzer_pwm_started, LED_PIN, buzzer_pwm
    if not buzzer_pwm_started:
        buzzer_pwm.start(50)
        buzzer_pwm_started = True

    while siren_active:
        for freq in [440, 880]:  # 주파수 범위 조정
            if not siren_active:
                break
            buzzer_pwm.ChangeFrequency(freq)
            GPIO.output(LED_PIN, not GPIO.input(LED_PIN))
            time.sleep(0.2)

    buzzer_pwm.stop()
    buzzer_pwm_started = False
    GPIO.output(LED_PIN, GPIO.LOW)

def start_siren():
    global siren_active, siren_thread
    if not siren_active:
        siren_active = True
        siren_thread = threading.Thread(target=_siren_loop)
        siren_thread.start()
        print("🚨 사이렌 ON")

def stop_siren():
    global siren_active, siren_thread
    siren_active = False
    if siren_thread:
        siren_thread.join()
        print("🛑 사이렌 OFF")


@notifications_bp.route("/send_notification", methods=["POST"])
@doc(description='푸시 알림 전송', tags=['notifications'])
def send_notification():
    data = request.json
    token = data.get("token")
    title = data.get("title")
    body = data.get("body")

    if token and title and body:
        response = send_push_notification(token, title, body)
        return {"status": "success", "response": response}

    return {"status": "error", "message": "Missing required fields"}, 400


@notifications_bp.route("/siren", methods=["POST"])
@doc(description='사이렌 제어', tags=['notifications'])
def control_siren():
    action = request.args.get("action", "")
    if action == "start":
        start_siren()
        return "Siren started", 200
    elif action == "stop":
        stop_siren()
        return "Siren stopped", 200
    else:
        return "Invalid action", 400
	