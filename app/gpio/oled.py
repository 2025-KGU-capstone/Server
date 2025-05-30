import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# OLED 초기화
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# 큰 폰트 불러오기 (한글 폰트 파일 필요하면 경로 넣어줘)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except IOError:
    font = ImageFont.load_default()  # 폰트 없으면 기본 폰트 fallback

# 화면 클리어 함수
def clear_oled():
    oled.fill(0)
    oled.show()

# 안전모드 표시 함수 (큰 글씨)
def display_safe_mode():
    oled.fill(0)
    oled.show()
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((10, 5), "SAFE\nMODE", font=font, fill=255)  # 위치 조절
    oled.image(image)
    oled.show()
