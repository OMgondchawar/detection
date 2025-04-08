import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json

st.set_page_config(page_title="AI Parking System", layout="centered")

# 🔵 Custom Style
st.markdown("""
    <style>
        .main { background-color: #f0f2f6; }
        h1, h2, h3 { color: #1f4e79; }
        .stButton > button {
            background-color: #1f4e79;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
        }
        .authorized {
            color: green;
            font-weight: bold;
        }
        .unauthorized {
            color: red;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 AI-powered Secure Parking System")
st.write("Upload an image or video for license plate detection and recognition.")

# 📷 Upload Image Section
st.header("📷 Upload Image")
image_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key="image")

if image_file and st.button("Process Image"):
    with st.spinner("Processing Image..."):
        response = requests.post(
            "http://127.0.0.1:8000/upload-image/",
            files={"file": image_file}
        )
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Image processed!")

            download_url = data.get('download_url')
            if isinstance(download_url, dict) and "_url" in download_url:
                download_url = download_url["_url"]

            image_response = requests.get(download_url)
            if image_response.status_code == 200:
                st.image(Image.open(BytesIO(image_response.content)), caption="Detected License Plate", use_column_width=True)
                st.markdown(f"[⬇️ Download Image]({download_url})")
            else:
                st.warning("Couldn't load processed image.")
        else:
            st.error("❌ Failed to process image.")

# 🎥 Upload Video Section
st.header("🎥 Upload Video")
video_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi"], key="video")

if video_file and st.button("Process Video"):
    with st.spinner("Processing Video..."):
        response = requests.post(
            "http://127.0.0.1:8000/upload-video/",
            files={"file": video_file}
        )
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Video processed!")
            download_url = data.get('download_url')
            if isinstance(download_url, dict) and "_url" in download_url:
                download_url = download_url["_url"]
            st.markdown(f"[⬇️ Download Video]({download_url})")
        else:
            st.error("❌ Failed to process video.")

# 📡 Start Live Detection
st.header("📡 Live Feed Detection")
st.write("Start the live detection from your webcam. Detected license plates will be shown below in real time.")

if st.button("Start Live Detection"):
    response = requests.post("http://127.0.0.1:8000/start-cctv/")
    if response.status_code == 200:
        st.success("Live detection started. Close the video window or press 'q' to stop.")
    else:
        st.error("Failed to start live detection.")

# 🧾 Show Detected Plates from /live-log/
st.subheader("🧾 Live Detected License Plates")
if st.button("🔁 Refresh Live Results"):
    try:
        response = requests.get("http://127.0.0.1:8000/live-log/")
        if response.status_code == 200:
            log_data = response.json()
            if log_data["plates"]:
                for item in reversed(log_data["plates"]):
                    plate = item.get("plate", "")
                    status = item.get("status", "").lower()
                    if status == "authorized":
                        st.markdown(f'<span class="authorized">✅ {plate} — Authorized</span>', unsafe_allow_html=True)
                    elif status == "unauthorized":
                        st.markdown(f'<span class="unauthorized">❌ {plate} — Unauthorized</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"`{plate}`")
            else:
                st.info("No plates detected yet.")
        else:
            st.warning("Failed to fetch live data from server.")
    except Exception as e:
        st.warning("Error connecting to FastAPI backend.")
