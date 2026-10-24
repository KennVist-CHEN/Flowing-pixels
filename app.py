
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
    "Your input repeats across the image to create the pattern."
)

density = st.slider(
    "Character density",
    min_value=30,
    max_value=240,
    value=100,
    step=10,
    help="Lower values create a coarser image; higher values preserve more detail."
)

color_mode = st.selectbox(
    "Color mode",
    ["Monochrome", "Original colors"]
)

# Color controls only appear in Monochrome mode.
if color_mode == "Monochrome":
    st.subheader("Monochrome colors")

    col1, col2 = st.columns(2)

    with col1:
        pixel_color = st.color_picker(
            "Pixel color",
            value="#000000"
        )

    with col2:
        background_color = st.color_picker(
            "Background color",
            value="#FFFFFF"
        )

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")

        content = "".join(pixel_content.split())

        if not content:
            st.warning(
                "Please enter at least one character "
                "for your pixel content."
            )
            st.stop()

        # Preserve the source image proportions.
        image_ratio = image.width / image.height
        grid_width = density

        # Compensate for the shape of monospace character cells.
        grid_height = max(
            1,
            round(grid_width / image_ratio * 0.5)
        )

        small_image = image.resize(
            (grid_width, grid_height),
            Image.Resampling.LANCZOS
        )

        pixels = list(small_image.getdata())
        symbols = list(content)

        text_rows = []
        html_rows = []

        for y in range(grid_height):
            text_row = []
            html_row = []

            for x in range(grid_width):
                r, g, b = pixels[y * grid_width + x]

                brightness = (
                    0.299 * r
                    + 0.587 * g
                    + 0.114 * b
                )

                # Repeat the user's custom characters.
                symbol_index = (
                    y * grid_width + x
                ) % len(symbols)

                char = symbols[symbol_index]
                safe_char = html.escape(char)

                text_row.append(char)

                if color_mode == "Original colors":
                    # Keep original RGB coloring unchanged.
                    style = f"color: rgb({r},{g},{b});"
                else:
                    # Use the chosen pixel color.
                    # Image brightness controls character opacity.
                    opacity = 1.0 - brightness / 255.0
                    opacity = max(0.08, min(1.0, opacity))

                    style = (
                        f"color: {pixel_color};"
                        f"opacity: {opacity:.2f};"
                    )

                html_row.append(
                    f'<span style="{style}">'
                    f'{safe_char}</span>'
                )

            text_rows.append("".join(text_row))
            html_rows.append("".join(html_row))

        # Preview background.
        if color_mode == "Monochrome":
            preview_background = background_color
        else:
            preview_background = "#FFFFFF"

        # Keep preview width independent of density.
        preview_width = 1000

        font_size = preview_width / grid_width * 1.55
        line_height = font_size * 1.15

        preview_height = min(
            900,
            max(
                180,
                int(grid_height * line_height + 40)
            )
        )

        formatted_rows = "<br>".join(html_rows)

        # Center the character art horizontally in the preview.
        preview_html = f"""
        <div style="
            background: {preview_background};
            width: 100%;
            height: 100%;
            box-sizing: border-box;
            padding: 15px;
            border-radius: 8px;
            overflow: auto;
        ">
            <div style="
                width: fit-content;
                min-width: 0;
                margin-left: auto;
                margin-right: auto;
            ">
                <div style="
                    font-family: 'Courier New', monospace;
                    font-size: {font_size}px;
                    line-height: {line_height}px;
                    font-weight: bold;
                    letter-spacing: 0;
                    white-space: pre;
                    color: #000000;
                ">{formatted_rows}</div>
            </div>
        </div>
        """

        st.subheader("Character Art")

        st.caption(
            f"Grid: {grid_width} columns × {grid_height} rows"
        )

        st.components.v1.html(
            preview_html,
            height=preview_height,
            scrolling=True
        )

        # Download plain-text character art.
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
