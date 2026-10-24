
import streamlit as st
from PIL import Image
import base64
import io
import json

st.set_page_config(
    page_title="Flowing Pixels",
    page_icon="〰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# Compact page styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 1600px;
    }

    h1 {
        margin-bottom: 0.2rem;
    }

    h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.35rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }

    div[data-testid="stSlider"] {
        padding-top: 0;
        padding-bottom: 0;
    }

    div[data-testid="stSelectbox"],
    div[data-testid="stTextInput"],
    div[data-testid="stFileUploader"] {
        margin-bottom: 0;
    }

    div[data-testid="stColorPicker"] {
        padding-bottom: 0;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
    }

    .section-caption {
        color: #777;
        font-size: 0.85rem;
        margin-top: -0.3rem;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("〰️ Flowing Pixels")
st.caption("Transform your image into living text art.")

# --------------------------------------------------
# 1. Main layout
# --------------------------------------------------

control_col, preview_col = st.columns(
    [0.85, 2.15],
    gap="medium"
)

# --------------------------------------------------
# 2. Controls
# --------------------------------------------------

with control_col:
    st.subheader("Image")

    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed"
    )

    st.divider()

    st.subheader("Character settings")

    pixel_content = st.text_input(
        "Pixel content",
        value="@%#*+=-:.",
        max_chars=100,
        help="Enter letters, words, punctuation, or emoticons."
    )

    density = st.slider(
        "Character density",
        min_value=30,
        max_value=240,
        value=100,
        step=10,
        help="Higher density preserves more image detail."
    )

    color_mode = st.selectbox(
        "Color mode",
        ["Monochrome", "Original colors"]
    )

    if color_mode == "Monochrome":
        with st.expander("Monochrome colors", expanded=True):
            pixel_color = st.color_picker(
                "Pixel color",
                value="#000000"
            )

            background_color = st.color_picker(
                "Background color",
                value="#FFFFFF"
            )
    else:
        pixel_color = "#000000"
        background_color = "#FFFFFF"

    st.divider()

    st.subheader("〰️ Wave animation")

    play_animation = st.toggle(
        "Play animation",
        value=True
    )

    with st.expander("Animation settings", expanded=True):
        wave_speed = st.slider(
            "Wave speed",
            min_value=0.5,
            max_value=3.0,
            value=1.0,
            step=0.5
        )

        wave_amplitude = st.slider(
            "Wave amplitude",
            min_value=0,
            max_value=16,
            value=5,
            step=1
        )


# --------------------------------------------------
# 3. Preview
# --------------------------------------------------

with preview_col:
    st.subheader("Character Art")

    if uploaded_file is None:
        st.info(
            "Upload an image from the panel on the left "
            "to see your character art here."
        )

    else:
        try:
            image = Image.open(uploaded_file).convert("RGB")

            content = "".join(pixel_content.split())

            if not content:
                st.warning("Please enter at least one character.")
            else:
                image_ratio = image.width / image.height
                grid_width = density

                # Match the grid ratio to the source image.
                # Character cells are proportioned at 2:3.
                grid_height = max(
                    1,
                    round(grid_width / image_ratio * 2 / 3)
                )

                small_image = image.resize(
                    (grid_width, grid_height),
                    Image.Resampling.LANCZOS
                )

                buffer = io.BytesIO()
                small_image.save(buffer, format="PNG")

                image_base64 = base64.b64encode(
                    buffer.getvalue()
                ).decode("ascii")

                config = {
                    "imageData": (
                        "data:image/png;base64,"
                        + image_base64
                    ),
                    "content": content,
                    "gridWidth": grid_width,
                    "gridHeight": grid_height,
                    "colorMode": color_mode,
                    "pixelColor": pixel_color,
                    "backgroundColor": background_color,
                    "playing": play_animation,
                    "speed": wave_speed,
                    "amplitude": wave_amplitude,
                }

                config_json = json.dumps(config).replace(
                    "</", "<\\/"
                )

                # ----------------------------------------
                # Canvas renderer
                # ----------------------------------------

                canvas_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        width: 100%;
        background: transparent;
        overflow: hidden;
    }}

    #viewport {{
        width: 100%;
        padding: 12px;
        overflow: hidden;
        border-radius: 8px;
        background: {background_color};
    }}

    #stage {{
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: flex-start;
    }}

    #artCanvas {{
        display: block;
        width: 100%;
        max-width: 1000px;
        height: auto;
    }}
</style>
</head>

<body>
<div id="viewport">
    <div id="stage">
        <canvas id="artCanvas"></canvas>
    </div>
</div>

<script>
(() => {{
    const cfg = {config_json};

    const canvas = document.getElementById("artCanvas");
    const ctx = canvas.getContext("2d", {{
        alpha: false
    }});

    const viewport = document.getElementById("viewport");
    const source = new Image();

    const cols = cfg.gridWidth;
    const rows = cfg.gridHeight;

    let pixels = [];
    let animationFrame = null;
    let lastTime = 0;
    let elapsed = 0;
    let isPlaying = cfg.playing;

    let cellWidth = 1;
    let cellHeight = 1;
    let fontSize = 1;

    const fontFamily = '"Courier New", monospace';

    function resizeCanvas() {{
        const availableWidth = Math.max(
            1,
            viewport.clientWidth - 24
        );

        const targetWidth = Math.min(
            1000,
            availableWidth
        );

        canvas.width = Math.max(
            1,
            Math.round(targetWidth)
        );

        cellWidth = canvas.width / cols;
        cellHeight = cellWidth * 1.5;
        fontSize = cellWidth * 1.25;

        canvas.height = Math.max(
            1,
            Math.round(rows * cellHeight)
        );

        canvas.style.width = "100%";
        canvas.style.maxWidth = "1000px";
        canvas.style.height = "auto";

        if (pixels.length) {{
            drawFrame();
        }}
    }}

    source.onload = () => {{
        const sourceCanvas = document.createElement("canvas");
        sourceCanvas.width = cols;
        sourceCanvas.height = rows;

        const sourceCtx = sourceCanvas.getContext("2d", {{
            willReadFrequently: true
        }});

        sourceCtx.drawImage(source, 0, 0, cols, rows);

        const imageData = sourceCtx.getImageData(
            0, 0, cols, rows
        ).data;

        pixels = [];

        for (let i = 0; i < cols * rows; i++) {{
            const r = imageData[i * 4];
            const g = imageData[i * 4 + 1];
            const b = imageData[i * 4 + 2];

            const brightness =
                0.299 * r + 0.587 * g + 0.114 * b;

            pixels.push({{
                r, g, b, brightness
            }});
        }}

        resizeCanvas();

        if (isPlaying) {{
            startAnimation();
        }}
    }};

    source.onerror = () => {{
        ctx.fillStyle = cfg.backgroundColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = cfg.pixelColor;
        ctx.font = "14px sans-serif";
        ctx.fillText(
            "Unable to load image preview.",
            10,
            25
        );
    }};

    source.src = cfg.imageData;

    function drawFrame() {{
        ctx.fillStyle = cfg.backgroundColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.font = "bold " + fontSize + "px " + fontFamily;
        ctx.textBaseline = "top";

        const chars = Array.from(cfg.content);

        if (!chars.length || !pixels.length) {{
            return;
        }}

        const phaseSpeed = cfg.speed * 0.0018;
        const spatialX = 0.045;
        const spatialY = 0.025;

        for (let y = 0; y < rows; y++) {{
            for (let x = 0; x < cols; x++) {{
                const index = y * cols + x;
                const p = pixels[index];
                const char = chars[index % chars.length];

                const phase =
                    elapsed * phaseSpeed
                    - x * spatialX
                    - y * spatialY;

                const offsetY = isPlaying
                    ? Math.sin(phase) * cfg.amplitude
                    : 0;

                if (cfg.colorMode === "Original colors") {{
                    ctx.fillStyle =
                        `rgb(${{p.r}},${{p.g}},${{p.b}})`;
                }} else {{
                    const opacity = Math.max(
                        0.08,
                        Math.min(1, 1 - p.brightness / 255)
                    );

                    ctx.fillStyle = hexToRgba(
                        cfg.pixelColor,
                        opacity
                    );
                }}

                ctx.fillText(
                    char,
                    x * cellWidth,
                    y * cellHeight + offsetY
                );
            }}
        }}
    }}

    function hexToRgba(hex, alpha) {{
        const normalized = hex.replace("#", "");

        const r = parseInt(normalized.slice(0, 2), 16);
        const g = parseInt(normalized.slice(2, 4), 16);
        const b = parseInt(normalized.slice(4, 6), 16);

        return `rgba(${{r}},${{g}},${{b}},${{alpha}})`;
    }}

    function animate(timestamp) {{
        if (!isPlaying) {{
            animationFrame = null;
            return;
        }}

        if (!lastTime) {{
            lastTime = timestamp;
        }}

        const delta = Math.min(timestamp - lastTime, 50);
        lastTime = timestamp;
        elapsed += delta;

        drawFrame();
        animationFrame = requestAnimationFrame(animate);
    }}

    function startAnimation() {{
        if (animationFrame !== null) {{
            return;
        }}

        lastTime = 0;
        animationFrame = requestAnimationFrame(animate);
    }}

    if (window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches) {{
        isPlaying = false;
    }}

    resizeCanvas();

    if ("ResizeObserver" in window) {{
        const observer = new ResizeObserver(() => {{
            resizeCanvas();
        }});

        observer.observe(viewport);
    }} else {{
        window.addEventListener("resize", resizeCanvas);
    }}
}})();
</script>
</body>
</html>
"""

                st.caption(
                    f"{image.width} × {image.height} px  ·  "
                    f"{grid_width} columns × {grid_height} rows"
                )

                # Keep the iframe tall enough for portrait images.
                preview_height = min(
                    1200,
                    max(220, round(1000 / image_ratio) + 50)
                )

                st.components.v1.html(
                    canvas_html,
                    height=preview_height,
                    scrolling=False
                )

                st.download_button(
                    label="Download character art (.txt)",
                    data="\n".join(
                        "".join(
                            content[
                                (y * grid_width + x) % len(content)
                            ]
                            for x in range(grid_width)
                        )
                        for y in range(grid_height)
                    ),
                    file_name="flowing_pixels.txt",
                    mime="text/plain"
                )

        except Exception as error:
            st.error(
                "Something went wrong while processing the image."
            )
            st.caption(f"Details: {error}")
