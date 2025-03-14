import firebase_admin
from firebase_admin import credentials, messaging,db,initialize_app

# 1. Firebase 초기화
def initialize_firebase():
    # 서비스 계정 키 파일 경로
    cred = credentials.Certificate("/home/mobilio/Downloads/safe-delivery-3f862-firebase-adminsdk-3izrv-d512e142b4.json")
    # Firebase Admin SDK 초기화
    initialize_app(cred, {"databaseURL": "https://safe-delivery-3f862-default-rtdb.firebaseio.com"})
    print("Firebase initialized successfully.")

# 2. 푸시 알림 전송 함수
def send_push_notification(token, title, body):
    try:
        # 알림 메시지 생성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,  # FCM 토큰 (대상 디바이스)
        )

        # 메시지 전송
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending message: {str(e)}")


# FCM 토큰 가져오기 (특정 유저)
def fetch_fcm_token(user_id):
    try:
        # Firebase Realtime Database에서 특정 유저 ID의 FCM 토큰 가져오기
        ref = db.reference(f"server/fcm_tokens/{user_id}")
        token = ref.get()
        
        if token:
            print(f"FCM Token for {user_id}: {token}")
            return token
        else:
            print(f"No FCM token found for user ID: {user_id}")
            return None
    except Exception as e:
        print(f"Error fetching FCM token for user ID {user_id}: {str(e)}")
        return None


# 3. 메인 실행
if __name__ == "__main__":
    # Firebase 초기화
    initialize_firebase()

    # 특정 유저의 FCM 토큰 가져오기
    user_id = "test"  # 테스트용 유저 ID
    device_token = fetch_fcm_token(user_id)

    print(device_token)

    # 푸시 알림 전송
    send_push_notification(
        device_token,
        "Test Notification",  # 알림 제목
        "This is a test notification sent via Firebase Admin SDK",  # 알림 본문
    )
