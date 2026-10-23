
import streamlit as st
from PIL import Image
import html

st.set_page_config(
    page_title="Flowing Pixels",
    page_icon="〰️",
    layout="wide"
)

st.title("〰️ Flowing Pixels")
st.write("Transform your image into customizable text art.")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["png", "jpg", "jpeg", "webp"]
)

st.subheader("Customize your pixels")

pixel_content = st.text_input(
    "Pixel content",
    value="@%#*+=-:.",
    max_chars=100,
    help="Enter letters, words, punctuation, or emoticons."
)

st.caption(
    "Your input will repeat across the image. "
    "Spaces are removed so the pattern stays continuous."
)

density = st.slider(
    "Character density",
    min_value=60,
    max_value=240,
    value=140,
    step=10
)

color_mode = st.selectbox(
    "Color mode",
    ["Monochrome", "Original colors"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")

        # Remove whitespace so the pattern tiles continuously.
        content = "".join(pixel_content.split())

        if not content:
            st.warning(
                "Please enter at least one character "
                "for your pixel content."
            )
            st.stop()

        # Preserve the original image proportions.
        image_ratio = image.width / image.height
        grid_width = density
        grid_height = max(
            1,
            round(grid_width / image_ratio * 0.5)
        )

        # Resize the source image to the character grid.
        small_image = image.resize(
            (grid_width, grid_height),
            Image.Resampling.LANCZOS
        )

        pixels = list(small_image.getdata())

        # Split the custom content into individual characters.
        symbols = list(content)

        text_rows = []
        html_rows = []

        for y in range(grid_height):
            text_row = []
            html_row = []

            for x in range(grid_width):
                r, g, b = pixels[y * grid_width + x]

                # Calculate perceived brightness.
                brightness = (
                    0.299 * r
                    + 0.587 * g
                    + 0.114 * b
                )

                # Cycle through the custom content.
                symbol_index = (
                    y * grid_width + x
                ) % len(symbols)

                char = symbols[symbol_index]
                safe_char = html.escape(char)

                text_row.append(char)

                if color_mode == "Original colors":
                    # Preserve the source image's pixel colors.
                    style = (
                        f"color: rgb({r},{g},{b});"
                    )
                else:
                    # Dark image areas use opaque black text;
                    # bright areas use lighter, more transparent text.
                    opacity = 1.0 - brightness / 255.0
                    opacity = max(0.08, min(1.0, opacity))

                    style = (
                        f"color: rgba(0,0,0,{opacity:.2f});"
                    )

                html_row.append(
                    f'<span style="{style}">'
                    f'{safe_char}</span>'
                )

            text_rows.append("".join(text_row))
            html_rows.append("".join(html_row))

        # Preview sizing.
        preview_width = min(
            1100,
            max(320, grid_width * 6)
        )

        font_size = preview_width / grid_width * 1.65
        line_height = font_size * 1.15

        preview_height = max(
            120,
            min(
                1000,
                int(grid_height * line_height + 40)
            )
        )

        formatted_rows = "<br>".join(html_rows)

        preview_html = f"""
        <div style="
            background: #ffffff;
            width: 100%;
            box-sizing: border-box;
            padding: 15px;
            overflow: auto;
            border-radius: 8px;
        ">
            <div style="
                font-family: 'Courier New', monospace;
                font-size: {font_size}px;
                line-height: {line_height}px;
                font-weight: bold;
                letter-spacing: 0;
                white-space: pre;
            ">{formatted_rows}</div>
        </div>
        """

        st.subheader("Character Art")

        st.components.v1.html(
            preview_html,
            height=preview_height,
            scrolling=True
        )

        # Download plain-text art.
        st.download_button(
            label="Download character art (.txt)",
            data="\n".join(text_rows),
            file_name="flowing_pixels.txt",
            mime="text/plain"
        )

    except Exception as error:
        st.error(
            "Something went wrong while processing the image."
        )
        st.caption(f"Details: {error}")

else:
    st.info(
        "Upload an image to get started. "
        "You can customize the pixel content, density, "
        "and color mode."
    )
