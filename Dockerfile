FROM python:3.11-slim

# OS 패키지 설치 (libcamera-apps 제거)
RUN apt update && apt install -y \
    libjpeg-dev \
    ffmpeg \
    libcamera-dev \
    libcamera-tools \
    libcamera-v4l2 \
    v4l-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY . /app
COPY ./bin/libcamera-vid /usr/local/bin/libcamera-vid
COPY ./bin/libcamera-jpeg /usr/local/bin/libcamera-jpeg
RUN chmod +x /usr/local/bin/libcamera-vid /usr/local/bin/libcamera-jpeg


# 파이썬 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 실행 스크립트에 실행 권한 부여
RUN chmod +x start.sh

CMD ["bash", "./start.sh"]
