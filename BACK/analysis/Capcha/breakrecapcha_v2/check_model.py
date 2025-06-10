# check_model.py

import os
from ultralytics import YOLO
import cv2
from matplotlib import pyplot as plt

# ——— 설정 ———
# 1) 학습된 YOLOv8 분류 모델 가중치 경로
WEIGHTS_PATH = 'weights/best copy.pt'

# 2) 샘플 타일 이미지가 저장된 디렉토리 경로
#    예: debug_tiles/debug_tile_3x3_0.png 등
TILE_IMAGE_DIR = './captured_tiles'
# ——————————

# 1) YOLOv8 모델 로드
model = YOLO(WEIGHTS_PATH)

# 2) 검출 결과를 이미지에 그려주는 헬퍼 함수
def draw_detections(img, results):
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf  = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = results.names[cls_id]

        # 바운딩 박스 그리기
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 라벨+신뢰도 표시
        cv2.putText(img, f"{label} {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return img

# 3) 디렉토리 내 모든 이미지에 대해 추론 실행
for fname in os.listdir(TILE_IMAGE_DIR):
    if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue

    img_path = os.path.join(TILE_IMAGE_DIR, fname)
    # OpenCV로 이미지 읽기 (BGR)
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print(f"[Warning] {img_path} 를 읽을 수 없습니다.")
        continue

    # BGR → RGB로 변환 (YOLO가 RGB 입력을 기대)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 4) 모델 추론 (이미지 크기는 256×256 기준)
    results = model.predict(source=img_rgb, imgsz=256, conf=0.1)

    # 5) 결과 프린트 및 시각화
    res = results[0]

    print(f"\n==== {fname} ====")
    if len(res.boxes) == 0:
        print("  • 검출된 객체 없음")
    else:
        for box in res.boxes:
            cls_id = int(box.cls[0])
            conf  = float(box.conf[0])
            label = res.names[cls_id]
            print(f"  • {label}: {conf:.2f}")

    # 바운딩 박스를 그린 이미지
    annotated = draw_detections(img_bgr.copy(), res)

    # matplotlib으로 화면에 출력
    plt.figure(figsize=(4, 4))
    plt.imshow(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    plt.title(f"Detections in {fname}")
    plt.axis('off')
    plt.show()
