from ultralytics import YOLO
from paddleocr import PaddleOCR
import cv2

# Load YOLOv8 model
model = YOLO("runs/detect/train/weights/best.pt")  

# Initialize PaddleOCR
ocr = PaddleOCR(lang="en")  

# Function to detect license plates and recognize text
def detect_and_recognize(image_path):
    results = model.predict(source=image_path, conf=0.5)
    
    # Load image
    img = cv2.imread(image_path)

    # Loop through detected objects
    for r in results:
        for box in r.boxes.xyxy:  # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box)
            plate_img = img[y1:y2, x1:x2]  # Crop license plate
            
            # Save cropped image (optional)
            cv2.imwrite("cropped_plate.jpg", plate_img)
            
            # Convert cropped image for OCR
            text_results = ocr.ocr(plate_img, cls=True)
            
            # Print recognized text
            for res in text_results:
                for line in res:
                    print("License Plate:", line[1][0])
    
# Test on an image
detect_and_recognize("your_test_image.jpg")
