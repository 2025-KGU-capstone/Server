# app/gpio/gpio_init.py
import atexit
import RPi.GPIO as GPIO
import os
import threading
import time

PIR_PIN = 21
BUZZER_PIN = 18
LED_PIN = 4

buzzer_pwm = None
buzzer_pwm_started = False
siren_active = False
siren_thread = None	

def initialized_gpio():
    global PIR_PIN, BUZZER_PIN, LED_PIN, buzzer_pwm, buzzer_pwm_started, siren_active, siren_thread

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.setup(LED_PIN, GPIO.OUT)

    buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)
    buzzer_pwm_started = False
    siren_active = False
    siren_thread = None

    print("✅ GPIO 초기화 완료")
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(PIR_PIN, GPIO.IN)
# GPIO.setup(BUZZER_PIN, GPIO.OUT)
# GPIO.setup(LED_PIN, GPIO.OUT)

# PIR 이벤트 감지 등록
# GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=control_siren, bouncetime=300)

# buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)
# buzzer_pwm_started = False
# siren_active = False
# siren_thread = None

def _siren_loop():
    global siren_active, buzzer_pwm_started, buzzer_pwm, LED_PIN
    if not buzzer_pwm_started:
        buzzer_pwm.start(50)
        buzzer_pwm_started = True

    while siren_active:
        # for freq in [440, 880]:
        for freq in [220, 440]:
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

@atexit.register
def cleanup_gpio():
    print("🔌 프로그램 종료: GPIO 정리")
    if buzzer_pwm_started:
        buzzer_pwm.stop()
    GPIO.cleanup()