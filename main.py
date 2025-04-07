from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import uuid
import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import threading
import json

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
    image_filename = f"temp_{uuid.uuid4().hex}.jpg"
    image_path = os.path.join(output_dir, image_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = cv2.imread(image_path)
    results = yolo_model(image)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_plate = image[y1:y2, x1:x2]
            if cropped_plate.size == 0:
                continue
            ocr_result = ocr_model.ocr(cropped_plate, cls=True)
            text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""
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
    video_filename = f"temp_{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(output_dir, video_filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
                ocr_result = ocr_model.ocr(cropped_plate, cls=True)
                text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""
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


@app.post("/start-cctv/")
def start_cctv():
    def run_detection():
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = yolo_model(frame)
            detected_plates = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cropped_plate = frame[y1:y2, x1:x2]
                    if cropped_plate.size == 0:
                        continue
                    ocr_result = ocr_model.ocr(cropped_plate, cls=True)
                    text = ocr_result[0][0][1][0] if ocr_result and ocr_result[0] else ""
                    if text:
                        detected_plates.append(text)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            if detected_plates:
                with open("live_log.json", "w") as f:
                    json.dump({"plates": detected_plates}, f)
            cv2.imshow("Live CCTV Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    threading.Thread(target=run_detection).start()
    return JSONResponse({"message": "Live CCTV detection started. Close the video window or press 'q' to stop."})


@app.get("/live-log/")
def get_live_log():
    if os.path.exists("live_log.json"):
        with open("live_log.json", "r") as f:
            data = json.load(f)
        return data
    return {"plates": []}
