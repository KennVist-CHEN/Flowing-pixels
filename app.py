
import base64
import io
import json

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Flowing Pixels",
    page_icon="〰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1600px;
        padding-top: 1.4rem;
        padding-bottom: 1rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.65rem;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 1.5rem;
    }

    .app-subtitle {
        color: #777;
        font-size: 0.95rem;
        margin-top: -0.5rem;
        margin-bottom: 1.2rem;
    }

    .preview-heading {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .preview-description {
        color: #777;
        font-size: 0.85rem;
        margin-bottom: 0.6rem;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("Flowing Pixels")

st.markdown(
    '<div class="app-subtitle">'
    "Transform images into character art and bring them to life."
    "</div>",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Layout
# --------------------------------------------------

control_col, preview_col = st.columns(
    [0.85, 2.15],
    gap="medium",
)


# --------------------------------------------------
# Controls
# --------------------------------------------------

with control_col:
    st.subheader("Settings")

    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"],
    )

    pixel_content = st.text_input(
        "Characters",
        value="FLOWINGPIXELS",
        help="Characters are repeated across the image.",
    )

    density = st.slider(
        "Density",
        min_value=30,
        max_value=240,
        value=100,
        step=10,
        help="Higher density creates more character cells.",
    )

    color_mode = st.selectbox(
        "Color mode",
        ["Monochrome", "Original colors"],
    )

    if color_mode == "Monochrome":
        pixel_color = st.color_picker(
            "Character color",
            value="#000000",
        )
    else:
        pixel_color = "#000000"

    background_color = st.color_picker(
        "Background color",
        value="#FFFFFF",
    )

    st.divider()

    st.subheader("Animation")

    # Explicitly default to False.
    play_animation = st.checkbox(
        "Play animation",
        value=False,
        help="Animation is off when the app first opens.",
    )

    animation_speed = st.slider(
        "Animation speed",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.5,
        disabled=not play_animation,
    )

    animation_amplitude = st.slider(
        "Wave amplitude",
        min_value=0,
        max_value=16,
        value=5,
        step=1,
        disabled=not play_animation,
    )

    st.caption(
        "Animation is limited to 30 FPS. "
        "It pauses when this browser tab is hidden."
    )


# --------------------------------------------------
# Image processing and preview
# --------------------------------------------------

with preview_col:
    st.markdown(
        '<div class="preview-heading">Preview</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="preview-description">'
        "Your character artwork will appear here."
        "</div>",
        unsafe_allow_html=True,
    )

    if uploaded_file is None:
        st.info("Upload an image to get started.")

    elif not pixel_content.strip():
        st.warning("Please enter at least one character.")

    else:
        try:
            image = Image.open(uploaded_file).convert("RGB")

            image_width, image_height = image.size
            image_ratio = image_width / image_height

            # Number of character columns.
            grid_width = density

            # Keep the character grid proportional to the image.
            # Each character cell is approximately 2:3 (width:height).
            grid_height = max(
                1,
                round(grid_width / image_ratio * 2 / 3),
            )

            # Resize the source image to match the character grid.
            small_image = image.resize(
                (grid_width, grid_height),
                Image.Resampling.LANCZOS,
            )

            rgb_pixels = list(small_image.getdata())

            pixel_data = []

            for red, green, blue in rgb_pixels:
                brightness = (
                    0.299 * red
                    + 0.587 * green
                    + 0.114 * blue
                )

                pixel_data.append(
                    {
                        "r": red,
                        "g": green,
                        "b": blue,
                        "brightness": brightness,
                    }
                )

            # Text export: one character per grid cell.
            characters = list(pixel_content)

            text_rows = []

            for y in range(grid_height):
                row_chars = []

                for x in range(grid_width):
                    index = y * grid_width + x
                    char = characters[index % len(characters)]
                    row_chars.append(char)

                text_rows.append("".join(row_chars))

            text_art = "\n".join(text_rows)

            # Pass data safely into the browser-side Canvas.
            config = {
                "cols": grid_width,
                "rows": grid_height,
                "pixels": pixel_data,
                "content": pixel_content,
                "colorMode": color_mode,
                "pixelColor": pixel_color,
                "backgroundColor": background_color,
                "playing": play_animation,
                "speed": animation_speed,
                "amplitude": animation_amplitude,
                "imageRatio": image_ratio,
            }

            config_json = json.dumps(
                config,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            canvas_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
    * {
        box-sizing: border-box;
    }

    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        overflow: hidden;
        background: transparent;
    }

    #canvas-container {
        width: 100%;
        overflow: hidden;
        line-height: 0;
    }

    canvas {
        display: block;
        width: 100%;
        height: auto;
    }
</style>
</head>

<body>
<div id="canvas-container">
    <canvas id="artCanvas"></canvas>
</div>

<script>
(function () {
    const cfg = __CONFIG_JSON__;

    const canvas = document.getElementById("artCanvas");
    const container = document.getElementById("canvas-container");
    const ctx = canvas.getContext("2d", {
        alpha: false
    });

    const cols = cfg.cols;
    const rows = cfg.rows;
    const pixels = cfg.pixels;

    // Fixed preview width keeps the artwork display size stable
    // while density changes the number of character cells.
    const MAX_WIDTH = 1000;

    // 30 FPS = approximately one frame every 33.33 ms.
    const FRAME_INTERVAL = 1000 / 30;

    let cellWidth = 1;
    let cellHeight = 1;
    let fontSize = 1;

    let elapsed = 0;
    let lastTimestamp = 0;
    let lastDrawTimestamp = 0;
    let animationFrame = null;

    let isPlaying = cfg.playing;
    let pageIsVisible = !document.hidden;

    const fontFamily =
        "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

    function hexToRgba(hex, alpha) {
        const cleanHex = hex.replace("#", "");

        const r = parseInt(cleanHex.slice(0, 2), 16);
        const g = parseInt(cleanHex.slice(2, 4), 16);
        const b = parseInt(cleanHex.slice(4, 6), 16);

        return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
    }

    function resizeCanvas() {
        const availableWidth = Math.max(
            1,
            container.clientWidth
        );

        const cssWidth = Math.min(
            availableWidth,
            MAX_WIDTH
        );

        const cssHeight = cssWidth / cfg.imageRatio;

        const dpr = Math.min(
            window.devicePixelRatio || 1,
            2
        );

        canvas.style.width = cssWidth + "px";
        canvas.style.height = cssHeight + "px";

        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        // Draw in CSS-pixel coordinates for consistent sizing.
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        cellWidth = cssWidth / cols;
        cellHeight = cssHeight / rows;

        fontSize = cellWidth * 1.25;

        drawFrame();

        // Resizing should not start animation by itself.
        if (isPlaying && pageIsVisible) {
            startAnimation();
        }
    }

    function drawFrame() {
        const cssWidth = parseFloat(canvas.style.width) || 1;
        const cssHeight = parseFloat(canvas.style.height) || 1;

        ctx.fillStyle = cfg.backgroundColor;
        ctx.fillRect(0, 0, cssWidth, cssHeight);

        ctx.font = "bold " + fontSize + "px " + fontFamily;
        ctx.textBaseline = "top";

        const chars = Array.from(cfg.content);

        if (chars.length === 0 || pixels.length === 0) {
            return;
        }

        const phaseSpeed = cfg.speed * 0.0018;
        const spatialX = 0.045;
        const spatialY = 0.025;

        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const index = y * cols + x;
                const p = pixels[index];
                const char = chars[index % chars.length];

                let offsetY = 0;

                if (isPlaying) {
                    const phase =
                        elapsed * phaseSpeed
                        - x * spatialX
                        - y * spatialY;

                    offsetY =
                        Math.sin(phase) * cfg.amplitude;
                }

                if (cfg.colorMode === "Original colors") {
                    ctx.fillStyle =
                        "rgb(" + p.r + "," + p.g + "," + p.b + ")";
                } else {
                    const opacity = Math.max(
                        0.08,
                        Math.min(
                            1,
                            1 - p.brightness / 255
                        )
                    );

                    ctx.fillStyle = hexToRgba(
                        cfg.pixelColor,
                        opacity
                    );
                }

                ctx.fillText(
                    char,
                    x * cellWidth,
                    y * cellHeight + offsetY
                );
            }
        }
    }

    function animate(timestamp) {
        // The loop exits immediately if animation is turned off
        // or the browser tab is no longer visible.
        if (!isPlaying || !pageIsVisible) {
            animationFrame = null;
            lastTimestamp = 0;
            lastDrawTimestamp = 0;
            return;
        }

        if (lastTimestamp === 0) {
            lastTimestamp = timestamp;
            lastDrawTimestamp = timestamp;
        }

        const delta = Math.min(
            timestamp - lastTimestamp,
            100
        );

        lastTimestamp = timestamp;

        // Only draw when the 30 FPS interval has elapsed.
        if (timestamp - lastDrawTimestamp >= FRAME_INTERVAL) {
            elapsed += delta;
            lastDrawTimestamp = timestamp;
            drawFrame();
        }

        animationFrame = requestAnimationFrame(animate);
    }

    function startAnimation() {
        if (
            !isPlaying
            || !pageIsVisible
            || animationFrame !== null
        ) {
            return;
        }

        lastTimestamp = 0;
        lastDrawTimestamp = 0;

        animationFrame = requestAnimationFrame(animate);
    }

    function stopAnimation() {
        if (animationFrame !== null) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }

        lastTimestamp = 0;
        lastDrawTimestamp = 0;

        // Keep the last elapsed time so restarting continues
        // smoothly rather than resetting the wave.
        drawFrame();
    }

    document.addEventListener(
        "visibilitychange",
        function () {
            pageIsVisible = !document.hidden;

            if (!pageIsVisible) {
                stopAnimation();
            } else if (isPlaying) {
                startAnimation();
            } else {
                drawFrame();
            }
        }
    );

    // The checkbox state comes from Streamlit on each rerun.
    // When false, draw once and do not start a frame loop.
    if (isPlaying) {
        resizeCanvas();
        startAnimation();
    } else {
        resizeCanvas();
    }

    if ("ResizeObserver" in window) {
        const observer = new ResizeObserver(function () {
            resizeCanvas();
        });

        observer.observe(container);
    } else {
        window.addEventListener("resize", resizeCanvas);
    }
})();
</script>
</body>
</html>
"""

            # Replace the placeholder instead of using an f-string,
            # so JavaScript braces do not need escaping.
            canvas_html = canvas_html.replace(
                "__CONFIG_JSON__",
                config_json,
            )

            preview_height = min(
                1200,
                max(
                    220,
                    round(1000 / image_ratio) + 50,
                ),
            )

            components.html(
                canvas_html,
                height=preview_height,
                scrolling=False,
            )

            st.download_button(
                label="Download TXT",
                data=text_art,
                file_name="flowing_pixels.txt",
                mime="text/plain",
                use_container_width=True,
            )

            st.caption(
                f"Grid: {grid_width} × {grid_height} characters"
            )

        except Exception as error:
            st.error(
                "Unable to process this image. "
                "Please try another image file."
            )
            st.exception(error)
