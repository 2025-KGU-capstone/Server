import firebase_admin
from firebase_admin import credentials, messaging
import cv2
import time
from ultralytics import YOLO
import face_recognition
import os

# ------------------- Firebase 초기화 -------------------
def initialize_firebase():
    cred = credentials.Certificate("/home/mobilio/Downloads/safe-delivery-3f862-firebase-adminsdk-3izrv-d512e142b4.json")
    firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully.")

# ------------------- 푸시 알림 전송 -------------------
def send_push_notification(token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending message: {str(e)}")

# ------------------- 얼굴 비교 함수 -------------------
def compare_faces(captured_image_path, visitor_dir="visitor"):
    captured_image = face_recognition.load_image_file(captured_image_path)
    captured_encoding = face_recognition.face_encodings(captured_image)

    if not captured_encoding:
        return None  # 얼굴이 감지되지 않음
    captured_encoding = captured_encoding[0]

    for visitor_file in os.listdir(visitor_dir):
        visitor_path = os.path.join(visitor_dir, visitor_file)
        visitor_image = face_recognition.load_image_file(visitor_path)
        visitor_encoding = face_recognition.face_encodings(visitor_image)

        if visitor_encoding:
            visitor_encoding = visitor_encoding[0]
            match = face_recognition.compare_faces([visitor_encoding], captured_encoding)
            if match[0]:
                return os.path.splitext(visitor_file)[0]  # 파일명 반환 (확장자 제거)

    return None  # 매칭되지 않음

# ------------------- YOLO 및 사람 감지 -------------------
def detect_person_and_notify():
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    capture_interval = 10
    last_capture_time = time.time()
    os.makedirs("saved_images", exist_ok=True)
    device_token = "c3Y64FuOQLOe7W9oY8Dsze:APA91bEZvkbGrm2weEiEk7x-NfjVAmQDcenOKHiufpxo29w-qJ1Xx9F7_Odf9Ru4q2YF7N_lOOzGo2ypsk7glz9837D7QTNZPRg-6OyWIIy3OoNIxtD__W4"

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        results = model.predict(source=frame, save=False, show=False, verbose=False)
        person_detected = False
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id == 0:  # 사람 감지
                    person_detected = True
                    break
            if person_detected:
                break

        current_time = time.time()
        if person_detected and (current_time - last_capture_time >= capture_interval):
            last_capture_time = current_time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"saved_images/capture_{timestamp}.jpg"
            cv2.imwrite(file_name, frame)
            print(f"이미지 저장: {file_name}")

            # 얼굴 비교
            visitor_name = compare_faces(file_name)
            if visitor_name:
                message = f"{visitor_name}이/가 방문하셨습니다."
            else:
                message = "외부인이 방문했습니다."

            send_push_notification(device_token, "방문자 알림", message)

        cv2.imshow("YOLO Person Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# ------------------- 메인 실행 -------------------
if __name__ == "__main__":
    initialize_firebase()
    detect_person_and_notify()
