import cv2
import sys
from ultralytics import YOLO
from paddleocr import PaddleOCR
from google.colab.patches import cv2_imshow

# Check if video path is provided
if len(sys.argv) < 2:
    print("Usage: python real_time_detection.py <video_path>")
    sys.exit(1)

video_path = sys.argv[1]  # Get video path from command-line argument

# Load YOLOv8 model
model = YOLO("/content/detection/runs/detect/train2/weights/best.pt")  

# Initialize PaddleOCR
ocr = PaddleOCR(lang="en")  

# Load the video file
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    sys.exit(1)

# Get video properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define video writer to save output
out = cv2.VideoWriter('/content/output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

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

            # Convert for OCR and recognize text
            text_results = ocr.ocr(plate_img, cls=True)

            # Draw bounding box and text on frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            for res in text_results:
                if res is not None:
                    for line in res:
                        plate_text = line[1][0]
                        cv2.putText(frame, plate_text, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    
    # Write frame to output video
    out.write(frame)
    
    # Show the processed frame in Colab
    cv2_imshow(frame)

cap.release()
out.release()

print("Processing complete. Video saved as /content/output.mp4")
