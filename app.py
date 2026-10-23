
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Flowing Pixels",
    page_icon="〰️",
    layout="wide",
)

st.title("〰️ Flowing Pixels")
st.write(
    "Transform your images into character art "
    "and bring them to life with flowing motion."
)

uploaded_file = st.file_uploader(
    "Upload an image to get started",
    type=["png", "jpg", "jpeg", "webp"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.subheader("Your Original Image")
    st.image(image, caption="Uploaded image", use_container_width=True)

    st.info(
        "Your image is ready! Character art conversion "
        "and animation controls will be added next."
    )
else:
    st.caption("Upload an image to begin your pixel journey.")
