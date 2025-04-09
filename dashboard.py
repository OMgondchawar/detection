import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json

# 🌐 Set page config
st.set_page_config(page_title="AI-powered Secure Parking System", layout="wide")

# 🎨 Custom CSS Styling
st.markdown("""
    <style>
        .main {
            background-color: #f5f7fa;
        }
        .block-container {
            padding: 0rem 2rem 2rem 2rem;
        }
        header, footer {visibility: hidden;}
        .css-1rs6os.edgvbvh3 {
            background: linear-gradient(180deg, #9C27B0 0%, #E91E63 100%);
            padding: 2rem 1rem 2rem 1rem;
            border-radius: 0 20px 20px 0;
        }
        .stButton>button {
            background-color: #1f4e79;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
        }
        .stat-card {
            background-color: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #1f4e79;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
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

# 🚀 Sidebar with Logo and Gradient
with st.sidebar:
    st.image("C:/Users/omgon/detection/logo.png.png", width=150)
    st.markdown("## **Secure Parking**")
    st.markdown("AI-powered License Plate Detection & Recognition")

# 🧠 Title and Intro
st.title("🚗 AI-powered Secure Parking System")
st.write("Upload an image or video for license plate detection and recognition.")

# 📊 Stat Cards (dummy placeholders — you can replace these later with actual backend stats)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="stat-card"><div class="stat-number">186</div><div class="stat-label">Plates Processed</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stat-card"><div class="stat-number">172</div><div class="stat-label">Authorized Vehicles</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-card"><div class="stat-number">14</div><div class="stat-label">Unauthorized Alerts</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-card"><div class="stat-number">98%</div><div class="stat-label">Recognition Accuracy</div></div>', unsafe_allow_html=True)

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
