import cv2
import time
from ultralytics import YOLO

# YOLOv8 모델 로드
model = YOLO("yolov8n.pt")  # YOLOv8 Nano 모델 (자동 다운로드)

# 비디오 캡처 초기화
cap = cv2.VideoCapture(0)  # 첫 번째 카메라 사용

if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# 캡처 간격 설정 (초 단위)
capture_interval = 5  # 3초
last_capture_time = time.time()  # 마지막 캡처 시간 초기화

# 비디오 스트림 처리
while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    # YOLOv8으로 객체 탐지
    results = model.predict(source=frame, save=False, show=False, verbose=False)

    # 사람이 감지되었는지 확인
    person_detected = False
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])  # 클래스 ID
            if cls_id == 0:  # 클래스 ID가 0이면 사람
                person_detected = True
                break
        if person_detected:
            break

    # 사람이 감지되고 캡처 간격이 지났으면 저장
    current_time = time.time()
    if person_detected and (current_time - last_capture_time >= capture_interval):
        last_capture_time = current_time  # 마지막 캡처 시간 업데이트
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # 현재 시간으로 파일 이름 생성
        file_name = f"saved_images/capture_{timestamp}.jpg"
        cv2.imwrite(file_name, frame)  # 프레임 저장
        print(f"이미지 저장: {file_name}")

    # 결과 화면 표시
    cv2.imshow("YOLO Person Detection", frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
