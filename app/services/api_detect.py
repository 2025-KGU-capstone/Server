from inference import InferencePipeline
import cv2
import os


def my_sink(result, video_frame):
    from inference.core.interfaces.camera.entities import VideoFrame

    if isinstance(video_frame, VideoFrame):
        image = video_frame.image  # numpy array (BGR)

        # 박스 정보 가져오기
        predictions = result.get("predictions")
        if predictions and predictions.xyxy.shape[0] > 0:
            for i in range(len(predictions.xyxy)):
                x1, y1, x2, y2 = predictions.xyxy[i]
                conf = predictions.confidence[i]
                label = predictions.data["class_name"][i]

                # 박스 그리기
                cv2.rectangle(
                    image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2
                )
                cv2.putText(
                    image,
                    f"{label} ({conf:.2f})",
                    (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

        # 화면 출력
        cv2.imshow("Workflow Detection", image)
        cv2.waitKey(1)

        # 이미지 파일로 저장
        output_image_path = (
            r"D:\Desktop\kgu\4_year\Server\app\services\output_image.jpg"
        )
        cv2.imwrite(output_image_path, image)
        print(f"Image saved at {output_image_path}")


# 이미지를 사용하려면 'video_reference'에 이미지 파일 경로를 넣어줍니다.
image_path = r"D:\Desktop\kgu\4_year\Server\app\services\2.jpg"

# 확인해서 이미지가 존재하는지 체크
if not os.path.exists(image_path):
    raise ValueError(f"Image file not found: {image_path}")

# initialize a pipeline object with image input
pipeline = InferencePipeline.init_with_workflow(
    api_key="0gON1KVPHmvEgAP9wyLA",
    workspace_name="deepcap",
    workflow_id="custom-workflow-2",
    video_reference=image_path,  # 이미지 경로를 넣어줍니다.
    max_fps=30,
    on_prediction=my_sink,
)
pipeline.start()  # start the pipeline
pipeline.join()  # wait for the pipeline thread to finish
