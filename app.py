
import streamlit as st
from PIL import Image
import html

st.set_page_config(
    page_title="Flowing Pixels",
    page_icon="〰️",
    layout="wide",
)

st.title("〰️ Flowing Pixels")
st.write(
    "Transform an image into character art "
    "and explore its visual patterns."
)

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["png", "jpg", "jpeg", "webp"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.subheader("Character Art Settings")

    col1, col2 = st.columns(2)

    with col1:
        width = st.slider(
            "Character density",
            min_value=40,
            max_value=160,
            value=90,
            step=10,
        )

    with col2:
        color_mode = st.selectbox(
            "Character color",
            ["Monochrome", "Original colors"],
        )

    # Resize the image while preserving its aspect ratio.
    aspect_ratio = image.height / image.width
    height = max(1, int(width * aspect_ratio * 0.5))

    small_image = image.resize((width, height))
    pixels = list(small_image.getdata())

    characters = "@%#*+=-:. "
    output = []

    for y in range(height):
        row = []

        for x in range(width):
            r, g, b = pixels[y * width + x]
            brightness = (r * 0.299 + g * 0.587 + b * 0.114)

            index = int((brightness / 255) * (len(characters) - 1))
            char = characters[index]

            if color_mode == "Original colors":
                style = f"color:rgb({r},{g},{b})"
                row.append(
                    f'<span style="{style}">{html.escape(char)}</span>'
                )
            else:
                row.append(html.escape(char))

        output.append("".join(row))

    art = "\n".join(output)

    st.subheader("Your Character Art")

    st.code(art, language=None)

    if color_mode == "Original colors":
        colored_art = (
            '<div style="font-family:monospace;'
            'font-size:8px;line-height:1;'
            'white-space:pre;overflow-x:auto;">'
            + "\n".join(output)
            + "</div>"
        )
        st.markdown(colored_art, unsafe_allow_html=True)

    st.download_button(
        "Download character art",
        data=art,
        file_name="flowing_pixels.txt",
        mime="text/plain",
    )

else:
    st.info("Upload an image to create your first character art.")
