# app/gpio/gpio_init.py
import atexit
import RPi.GPIO as GPIO
import os
import threading
import time

class GPIOController:
    def __init__(self):
        self.BUZZER_PIN = 18
        self.LED_PIN = 4
        self.buzzer_pwm_started = False
        self.siren_active = False
        self.siren_thread = None
        self.buzzer_pwm = None

    def initialize(self):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.BUZZER_PIN, GPIO.OUT)
            GPIO.setup(self.LED_PIN, GPIO.OUT)
            GPIO.output(self.LED_PIN, GPIO.LOW)
            GPIO.output(self.BUZZER_PIN, GPIO.LOW)
            self.buzzer_pwm = GPIO.PWM(self.BUZZER_PIN, 440)

    def _siren_loop(self):
        if not self.buzzer_pwm_started and self.buzzer_pwm:
            self.buzzer_pwm.start(50)
            self.buzzer_pwm_started = True

        while self.siren_active:
            GPIO.output(self.LED_PIN, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(self.LED_PIN, GPIO.LOW)
            time.sleep(0.5)

        if self.buzzer_pwm:
            self.buzzer_pwm.stop()
            self.buzzer_pwm_started = False

    def start_siren(self):
        if not self.siren_active:
            self.siren_active = True
            self.siren_thread = threading.Thread(target=self._siren_loop)
            self.siren_thread.start()

    def stop_siren(self):
        self.siren_active = False
        if self.siren_thread and self.siren_thread.is_alive():
            self.siren_thread.join()
        if self.buzzer_pwm and self.buzzer_pwm_started:
            self.buzzer_pwm.stop()
            self.buzzer_pwm_started = False

@atexit.register(GPIO.cleanup)
def cleanup_gpio():
	GPIO.cleanup()
