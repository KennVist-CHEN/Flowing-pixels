
import streamlit as st
from PIL import Image
import html
import math

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
    try:
        image = Image.open(uploaded_file).convert("RGB")

        st.subheader("Character Art Settings")

        col1, col2 = st.columns(2)

        with col1:
            density = st.slider(
                "Character density",
                min_value=60,
                max_value=240,
                value=140,
                step=10,
                help="Higher values create finer details.",
            )

        with col2:
            color_mode = st.selectbox(
                "Character color",
                ["Monochrome", "Original colors"],
            )

        # Preserve the original image aspect ratio.
        image_ratio = image.width / image.height

        # Density controls the number of character columns.
        grid_width = density
        grid_height = max(
            1, round(grid_width / image_ratio * 0.5)
        )

        # Resize using a high-quality resampling filter.
        small_image = image.resize(
            (grid_width, grid_height),
            Image.Resampling.LANCZOS,
        )

        pixels = list(small_image.getdata())

        # Darker pixels use denser characters.
        characters = "@%#*+=-:. "

        text_rows = []
        html_rows = []

        for y in range(grid_height):
            text_row = []
            html_row = []

            for x in range(grid_width):
                r, g, b = pixels[y * grid_width + x]

                brightness = (
                    0.299 * r + 0.587 * g + 0.114 * b
                )

                index = round(
                    brightness / 255 * (len(characters) - 1)
                )
                char = characters[index]

                text_row.append(char)

                if color_mode == "Original colors":
                    html_rows.append(
                        f'<span style="color:rgb({r},{g},{b})">'
                        f"{html.escape(char)}</span>"
                    )
                else:
                    html_rows.append(html.escape(char))

            text_rows.append("".join(text_row))

        art = "\n".join(text_rows)

        st.subheader("Your Character Art")

        # Scale the preview to fit the page while preserving
        # the original image proportions.
        preview_width = min(1100, max(320, grid_width * 6))
        font_size = preview_width / grid_width * 1.65
        line_height = font_size * 1.15

        preview_height = max(
            120,
            min(1000, int(grid_height * line_height + 30)),
        )

        # Build a centered, proportion-preserving preview.
        art_html = "\n".join(
            "".join(
                html_rows[y * grid_width:(y + 1) * grid_width]
            )
            for y in range(grid_height)
        )

        preview_html = f"""
        <div style="
            width: 100%;
            display: flex;
            justify-content: center;
            overflow-x: auto;
        ">
          <div style="
              width: {preview_width}px;
              max-width: 100%;
              margin: 0 auto;
              background: #ffffff;
              padding: 12px;
              box-sizing: border-box;
              overflow: hidden;
          ">
            <div style="
                font-family: monospace;
                font-size: {font_size}px;
                line-height: {line_height}px;
                letter-spacing: 0;
                white-space: pre;
                text-align: left;
            ">{art_html}</div>
          </div>
        </div>
        """

        st.components.v1.html(
            preview_html,
            height=preview_height,
            scrolling=True,
        )

        st.download_button(
            "Download character art",
            data=art,
            file_name="flowing_pixels.txt",
            mime="text/plain",
        )

    except Exception as error:
        st.error(
            "Sorry, this image could not be processed. "
            "Please try another image."
        )
        st.caption(f"Error details: {error}")

else:
    st.info("Upload an image to create your first character art.")
