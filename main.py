from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR

# Initialize FastAPI app
app = FastAPI()

# Load YOLOv8 model (change path if needed)
yolo_model = YOLO("runs/detect/train2/weights/best.pt")

# Initialize PaddleOCR
ocr_model = PaddleOCR(use_angle_cls=True, lang='en')

# Create output directory if it doesn't exist
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

@app.post("/upload-image/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    # Save uploaded image to disk
    image_filename = f"temp_{uuid.uuid4().hex}.jpg"
    image_path = os.path.join(output_dir, image_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load image
    image = cv2.imread(image_path)
    results = yolo_model(image)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_plate = image[y1:y2, x1:x2]
            if cropped_plate.size == 0:
                continue

            # OCR
            ocr_result = ocr_model.ocr(cropped_plate, cls=True)
            text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""

            # Draw box and text
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    output_filename = f"output_{image_filename}"
    output_path = os.path.join(output_dir, output_filename)
    cv2.imwrite(output_path, image)

    download_url = request.url_for("download_file", filename=output_filename)
    return {"message": "Image processed successfully", "download_url": download_url}


@app.post("/upload-video/")
async def upload_video(request: Request, file: UploadFile = File(...)):
    # Save uploaded video to disk
    video_filename = f"temp_{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(output_dir, video_filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load video
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_filename = f"output_{video_filename}"
    output_video_path = os.path.join(output_dir, output_filename)
    out = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo_model(frame)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cropped_plate = frame[y1:y2, x1:x2]
                if cropped_plate.size == 0:
                    continue

                # OCR
                ocr_result = ocr_model.ocr(cropped_plate, cls=True)
                text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""

                # Draw box and text
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if out is None:
            h, w, _ = frame.shape
            out = cv2.VideoWriter(output_video_path, fourcc, 20.0, (w, h))

        out.write(frame)

    cap.release()
    out.release()

    download_url = request.url_for("download_file", filename=output_filename)
    return {"message": "Video processed successfully", "download_url": download_url}


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(output_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="application/octet-stream")
    raise HTTPException(status_code=404, detail="File not found")
