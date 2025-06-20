import torch
import cv2

import pathlib

# Windows 호환 경로 처리
pathlib.PosixPath = pathlib.WindowsPath

global model

# 웹캠 열기
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 객체 탐지
    results = model(frame)

    # 결과 시각화 (바운딩 박스 그려진 이미지)
    annotated_frame = results.render()[0]
    cv2.imshow("YOLOv5 Detection", annotated_frame)

    # 'q' 키 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
