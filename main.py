from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from ultralytics import YOLO
from paddleocr import PaddleOCR
import sqlite3, shutil, os, uuid, cv2, json, threading
from database import get_authorized_plates, get_plate_owner, log_detection  # Updated

app = FastAPI()

# Paths
model_path = "runs/detect/train2/weights/best.pt"
output_dir = "output"
live_log_file = "live_log.json"
db_file = "plates.db"

os.makedirs(output_dir, exist_ok=True)

# Load YOLO model
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model not found at {model_path}")
yolo_model = YOLO(model_path)

# Load OCR
ocr_model = PaddleOCR(use_angle_cls=True, lang='en')

def normalize_plate(text):
    return text.replace(" ", "").upper()

def init_db():
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorized_plates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT UNIQUE NOT NULL,
                owner TEXT
            )
        """)
init_db()

def is_authorized_plate(plate):
    plate = normalize_plate(plate)
    with sqlite3.connect(db_file) as conn:
        result = conn.execute("SELECT * FROM authorized_plates WHERE plate = ?", (plate,)).fetchone()
        return result is not None

def add_authorized_plate(plate, owner):
    plate = normalize_plate(plate)
    with sqlite3.connect(db_file) as conn:
        conn.execute("INSERT OR REPLACE INTO authorized_plates (plate, owner) VALUES (?, ?)", (plate, owner))

# 📸 Upload Image
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
            if cropped_plate.size == 0: continue
            ocr_result = ocr_model.ocr(cropped_plate, cls=True)
            text = normalize_plate(ocr_result[0][0][1][0]) if ocr_result and ocr_result[0] else ""
            status = "Authorized" if is_authorized_plate(text) else "Unauthorized"
            log_detection(text, status, source="image")  # ✅ Log detection
            color = (0, 255, 0) if status == "Authorized" else (0, 0, 255)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{text} - {status}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    output_filename = f"output_{image_filename}"
    output_path = os.path.join(output_dir, output_filename)
    cv2.imwrite(output_path, image)
    download_url = request.url_for("download_file", filename=output_filename)
    return {"message": "Image processed successfully", "download_url": download_url}

# 🎥 Upload Video
@app.post("/upload-video/")
async def upload_video(request: Request, file: UploadFile = File(...)):
    video_filename = f"temp_{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(output_dir, video_filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(video_path)
    output_filename = f"output_{video_filename}"
    output_video_path = os.path.join(output_dir, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        results = yolo_model(frame)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cropped_plate = frame[y1:y2, x1:x2]
                if cropped_plate.size == 0: continue
                ocr_result = ocr_model.ocr(cropped_plate, cls=True)
                text = normalize_plate(ocr_result[0][0][1][0]) if ocr_result and ocr_result[0] else ""
                status = "Authorized" if is_authorized_plate(text) else "Unauthorized"
                log_detection(text, status, source="video")  # ✅ Log detection
                color = (0, 255, 0) if status == "Authorized" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{text} - {status}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if out is None:
            h, w, _ = frame.shape
            out = cv2.VideoWriter(output_video_path, fourcc, 20.0, (w, h))

        out.write(frame)

    cap.release()
    out.release()
    download_url = request.url_for("download_file", filename=output_filename)
    return {"message": "Video processed successfully", "download_url": download_url}

# 📥 Download Endpoint
@app.get("/download/{filename}")
def download_file(filename: str):
    path = os.path.join(output_dir, filename)
    if os.path.exists(path):
        return FileResponse(path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

# 📡 Live CCTV Detection
@app.post("/start-cctv/")
def start_cctv():
    def run_detection():
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            results = yolo_model(frame)
            log = []

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cropped_plate = frame[y1:y2, x1:x2]
                    if cropped_plate.size == 0: continue
                    ocr_result = ocr_model.ocr(cropped_plate, cls=True)
                    text = normalize_plate(ocr_result[0][0][1][0]) if ocr_result and ocr_result[0] else ""
                    if text:
                        status = "Authorized" if is_authorized_plate(text) else "Unauthorized"
                        log_detection(text, status, source="live")  # ✅ Log detection
                        log.append({"plate": text, "status": status})
                        color = (0, 255, 0) if status == "Authorized" else (0, 0, 255)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{text} - {status}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if log:
                with open(live_log_file, "w") as f:
                    json.dump({"plates": log}, f)

            cv2.imshow("Live CCTV Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        cap.release()
        cv2.destroyAllWindows()

    threading.Thread(target=run_detection).start()
    return JSONResponse({"message": "Live CCTV detection started. Press 'q' to stop."})

# 📄 Get Live Log
@app.get("/live-log/")
def get_live_log():
    if os.path.exists(live_log_file):
        with open(live_log_file, "r") as f:
            return json.load(f)
    return {"plates": []}

# ➕ Add new authorized plate
@app.post("/add-authorized-plate/")
async def add_authorized_plate_endpoint(plate: str, owner: str):
    try:
        add_authorized_plate(plate, owner)
        return {"message": "Plate added to authorized list"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding plate: {e}")
