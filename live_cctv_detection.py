import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR

# Load YOLOv8 model (adjust path if needed)
yolo_model = YOLO("runs/detect/train2/weights/best.pt")

# Initialize PaddleOCR
ocr_model = PaddleOCR(use_angle_cls=True, lang='en')

# Open the default webcam (use IP camera URL if needed)
cap = cv2.VideoCapture(0)  # Change 0 to your IP cam stream if needed

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = yolo_model(frame)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped = frame[y1:y2, x1:x2]

            if cropped.size == 0:
                continue

            ocr_result = ocr_model.ocr(cropped, cls=True)
            text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""

            # Draw bounding box and text
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show the output
    cv2.imshow("Live CCTV License Plate Detection", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
