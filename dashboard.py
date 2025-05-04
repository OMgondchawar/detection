import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
import datetime
import re  # For license plate validation

# 🌐 Set page config
st.set_page_config(page_title="AI-powered Secure Parking System", layout="wide")

# 🎨 Custom CSS Styling
st.markdown("""
    <style>
        .main {
            background-color: #F4F6F8; /* Soft Grey Background */
        }
        .block-container {
            padding: 2rem 2rem 2rem 2rem;
        }
        header, footer {visibility: hidden;}
        .css-1rs6os.edgvbvh3 {
            background: linear-gradient(180deg, #4A00E0 0%, #8E2DE2 100%);
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
            background: linear-gradient(145deg, #ffffff, #f1f1f1);
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin: 1rem;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #4A00E0; /* Primary Color */
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        .authorized {
            color: #00C9A7; /* Teal */
            font-weight: bold;
        }
        .unauthorized {
            color: #E91E63; /* Red */
            font-weight: bold;
        }
        .stSidebar .sidebar-content {
            background: #4A00E0;
            color: white;
        }
        .stSidebar .sidebar-header {
            background: #8E2DE2; /* Secondary Color */
        }
        .sidebar .stButton>button:hover {
            background-color: #8E2DE2;
        }
        .tab-content {
            background: #F4F6F8;
            padding: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# 🌐 Sidebar with Logo and Gradient (Removed Secure Parking Text)
with st.sidebar:
    st.image("Untitled design.png", width=150)
    
# 📊 Navigation Tabs
tabs = st.tabs(["Image Upload", "Video Upload", "Live Detection", "Vehicle Management"])

with tabs[0]:
    st.header("📷 Upload Image")
    image_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key="image")

    if image_file and st.button("Process Image"):
        if image_file.size > 10 * 1024 * 1024:  # 10MB size check
            st.warning("The image is too large. Please upload an image smaller than 10MB.")
        else:
            with st.spinner("Processing Image..."):
                try:
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
                        st.error("❌ Failed to process image. Try again.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

with tabs[1]:
    st.header("🎥 Upload Video")
    video_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi"], key="video")

    if video_file and st.button("Process Video"):
        if video_file.size > 50 * 1024 * 1024:  # 50MB size check
            st.warning("The video is too large. Please upload a video smaller than 50MB.")
        else:
            with st.spinner("Processing Video..."):
                try:
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
                        st.error("❌ Failed to process video. Try again.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

with tabs[2]:
    st.header("📡 Live Feed Detection")
    st.write("Start the live detection from your webcam. Detected license plates will be shown below in real time.")

    if st.button("Start Live Detection"):
        with st.spinner("Starting live detection..."):
            try:
                live_feed_url = "http://127.0.0.1:8000/live-feed/"  # FastAPI live feed endpoint
                st.image(live_feed_url, caption="Live CCTV Feed", use_column_width=True)

                response = requests.post("http://127.0.0.1:8000/start-cctv/")
                if response.status_code == 200:
                    st.success("Live detection started. Close the video window or press 'q' to stop.")
                else:
                    st.error("Failed to start live detection. Try again.")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")

with tabs[3]:
    st.subheader("✅ Manage Authorized Vehicles")

    from database import get_authorized_plates, add_authorized_plate, delete_authorized_plate

    # Display authorized plates
    authorized_list = get_authorized_plates()

    if authorized_list:
        st.markdown("### 📋 Current Authorized Plates")
        for item in authorized_list:
            st.markdown(f"• **{item['plate']}** - {item['owner']}")
    else:
        st.info("No authorized plates found.")

    # Add new authorized plate
    with st.expander("➕ Add New Authorized Vehicle"):
        new_plate = st.text_input("License Plate Number", key="new_plate").upper()
        new_owner = st.text_input("Owner Name", key="new_owner")

        # Validate license plate format (supporting Indian-style formats like MH12AB1234)
        plate_regex = "^[A-Z0-9]{4,10}$"

        if st.button("Add Vehicle"):
            if new_plate and new_owner and re.match(plate_regex, new_plate):
                add_authorized_plate(new_plate, new_owner)
                st.success(f"✅ {new_plate} added for {new_owner}")
            elif not new_plate or not new_owner:
                st.warning("Please fill in both fields.")
            else:
                st.warning("Please enter a valid license plate number.")
    
    # Delete authorized plate
    with st.expander("🗑️ Delete Authorized Vehicle"):
        if authorized_list:
            delete_choice = st.selectbox(
                "Select a plate to remove:",
                [f"{item['plate']} - {item['owner']}" for item in authorized_list]
            )
            if st.button("Delete Vehicle"):
                plate_to_delete = delete_choice.split(" - ")[0]
                delete_authorized_plate(plate_to_delete)
                st.success(f"✅ {plate_to_delete} removed.")
        else:
            st.info("No authorized vehicles to delete.")

