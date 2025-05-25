from firebase_admin import messaging
import threading
import time
from app.gpio.gpio_init import _siren_loop, start_siren, stop_siren

cooldown_seconds = 10
startup_block_seconds = 30
startup_time = time.time()
last_trigger_time = 0

def send_push_notification(token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        )
        return messaging.send(message)
    except Exception as e:
        return str(e)

def control_siren(pir):
	global last_trigger_time

	current_time = time.time()

	# 앱 시작 후 30초 동안 차단
	if pir:
		if current_time - startup_time < startup_block_seconds:
			print("❎ PIR 감지됨: 앱 시작 후 30초 동안은 사이렌 작동 X")
			return

		# 쿨다운 체크
		if current_time - last_trigger_time < cooldown_seconds:
			print("⚠️ 최근 감지됨: 쿨다운 중, 무시")
			return

	last_trigger_time = current_time
	if pir:
		print("🔔 PIR 감지됨! 사이렌 작동 중...")
	start_siren()

	def stop_after_delay():
		time.sleep(5)
		stop_siren()
		print("🔕 사이렌 종료")

	threading.Thread(target=stop_after_delay, daemon=True).start()

