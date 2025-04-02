import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
from google.colab.patches import cv2_imshow  # For displaying images in Colab

# Load YOLOv8 model
model = YOLO("/content/detection/runs/detect/train2/weights/best.pt")  

# Initialize PaddleOCR
ocr = PaddleOCR(lang="en")  

# Load the video file
video_path = "/content/WhatsApp Video 2025-03-20 at 13.11.50_c0c529f8.mp4"
cap = cv2.VideoCapture(video_path)

# Get video properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define the codec and create VideoWriter object
output_path = "/content/output_video.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # Stop if video ends

    # Run YOLOv8 detection
    results = model.predict(source=frame, conf=0.5)

    for r in results:
        for box in r.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            plate_img = frame[y1:y2, x1:x2]

            # Perform OCR if a plate is detected
            text_results = ocr.ocr(plate_img, cls=True)

            if text_results:
                for res in text_results:
                    if res:
                        for line in res:
                            plate_text = line[1][0]
                            cv2.putText(frame, plate_text, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Write frame to output video
    out.write(frame)

cap.release()
out.release()

print(f"Processed video saved at: {output_path}")
