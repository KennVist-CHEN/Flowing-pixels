
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

    animation_mode = st.selectbox(
        "Motion style",
        ["Wave", "Pixel Build", "Outline → Fill"],
        help=(
            "Wave: continuous vertical movement. "
            "Pixel Build: reveal characters from the center outward. "
            "Outline → Fill: reveal image edges first, "
            "then fill in the remaining characters."
        ),
    )

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

    if animation_mode == "Wave":
        st.caption("Characters move in continuous waves.")
    elif animation_mode == "Pixel Build":
        st.caption(
            "Characters appear from the center outward, "
            "then the process repeats."
        )
    else:
        st.caption(
            "Image edges appear first, followed by the "
            "remaining characters."
        )

    st.caption(
        "Animation is limited to 30 FPS. "
        "Build animations draw new characters incrementally."
    )


# --------------------------------------------------
# Preview
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

            # Preserve the image aspect ratio.
            grid_width = density
            grid_height = max(
                1,
                round(grid_width / image_ratio * 2 / 3),
            )

            small_image = image.resize(
                (grid_width, grid_height),
                Image.Resampling.LANCZOS,
            )

            pixel_data = []

            for red, green, blue in small_image.getdata():
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

            # Downloadable text artwork.
            characters = list(pixel_content)
            text_rows = []

            for y in range(grid_height):
                row_chars = []

                for x in range(grid_width):
                    index = y * grid_width + x
                    row_chars.append(
                        characters[index % len(characters)]
                    )

                text_rows.append("".join(row_chars))

            text_art = "\n".join(text_rows)

            config = {
                "cols": grid_width,
                "rows": grid_height,
                "pixels": pixel_data,
                "content": pixel_content,
                "colorMode": color_mode,
                "pixelColor": pixel_color,
                "backgroundColor": background_color,
                "playing": play_animation,
                "mode": animation_mode,
                "speed": animation_speed,
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
    const totalCells = cols * rows;

    const MAX_WIDTH = 1000;
    const FRAME_INTERVAL = 1000 / 30;

    // At speed 1, build approximately 1,200 cells per second.
    const BUILD_CELLS_PER_SECOND = 1200;
    const COMPLETE_PAUSE_MS = 1000;

    let cellWidth = 1;
    let cellHeight = 1;
    let fontSize = 1;

    let elapsed = 0;
    let lastTimestamp = 0;
    let lastDrawTimestamp = 0;
    let animationFrame = null;

    let isPlaying = cfg.playing;
    let pageIsVisible = !document.hidden;

    // Incremental build state.
    let buildOrder = [];
    let buildCursor = 0;
    let buildElapsed = 0;
    let completedAt = null;
    let buildInitialized = false;

    const fontFamily =
        "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

    function hexToRgba(hex, alpha) {
        const cleanHex = hex.replace("#", "");

        const r = parseInt(cleanHex.slice(0, 2), 16);
        const g = parseInt(cleanHex.slice(2, 4), 16);
        const b = parseInt(cleanHex.slice(4, 6), 16);

        return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
    }

    function clearCanvas() {
        const cssWidth = parseFloat(canvas.style.width) || 1;
        const cssHeight = parseFloat(canvas.style.height) || 1;

        ctx.fillStyle = cfg.backgroundColor;
        ctx.fillRect(0, 0, cssWidth, cssHeight);
    }

    function setupCanvas() {
        const availableWidth = Math.max(
            1,
            container.clientWidth
        );

        const cssWidth = Math.min(
            availableWidth,
            MAX_WIDTH
        );

        const cssHeight = cssWidth / cfg.imageRatio;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);

        canvas.style.width = cssWidth + "px";
        canvas.style.height = cssHeight + "px";

        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        cellWidth = cssWidth / cols;
        cellHeight = cssHeight / rows;
        fontSize = cellWidth * 1.25;

        ctx.font = "bold " + fontSize + "px " + fontFamily;
        ctx.textBaseline = "top";

        clearCanvas();
    }

    // Draw exactly one character cell.
    // Build animations use this without redrawing previous cells.
    function drawCharacter(index) {
        const p = pixels[index];
        const chars = Array.from(cfg.content);
        const char = chars[index % chars.length];

        const x = index % cols;
        const y = Math.floor(index / cols);

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
            y * cellHeight
        );
    }

    // Build a center-out order using squared distance.
    // Avoids repeated square roots when sorting.
    function getCenterOutOrder(indices) {
        const centerX = (cols - 1) / 2;
        const centerY = (rows - 1) / 2;

        return indices.sort(function (a, b) {
            const ax = a % cols;
            const ay = Math.floor(a / cols);
            const bx = b % cols;
            const by = Math.floor(b / cols);

            const distanceA =
                Math.pow(ax - centerX, 2)
                + Math.pow(ay - centerY, 2);

            const distanceB =
                Math.pow(bx - centerX, 2)
                + Math.pow(by - centerY, 2);

            return distanceA - distanceB;
        });
    }

    // Estimate image edges from neighboring brightness values.
    // Strong local brightness changes are likely to be outlines.
    function calculateEdgeScores() {
        const scores = new Array(totalCells).fill(0);

        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const index = y * cols + x;
                const current = pixels[index].brightness;

                const rightIndex = Math.min(
                    x + 1,
                    cols - 1
                ) + y * cols;

                const downIndex =
                    Math.min(y + 1, rows - 1) * cols + x;

                const rightBrightness =
                    pixels[rightIndex].brightness;

                const downBrightness =
                    pixels[downIndex].brightness;

                const horizontalDifference =
                    Math.abs(current - rightBrightness);

                const verticalDifference =
                    Math.abs(current - downBrightness);

                scores[index] =
                    horizontalDifference + verticalDifference;
            }
        }

        return scores;
    }

    function createBuildOrder() {
        const allIndices = Array.from(
            { length: totalCells },
            function (_, index) {
                return index;
            }
        );

        if (cfg.mode === "Pixel Build") {
            // Simple deterministic center-out build.
            buildOrder = getCenterOutOrder(allIndices);
        } else {
            // Outline → Fill:
            // 1. Select the strongest local brightness changes.
            // 2. Draw these edge characters first.
            // 3. Fill all remaining cells center outward.
            const edgeScores = calculateEdgeScores();

            const ranked = allIndices.slice().sort(
                function (a, b) {
                    return edgeScores[b] - edgeScores[a];
                }
            );

            // Use approximately the strongest 18% of edge scores
            // to create a visible outline phase.
            const outlineCount = Math.max(
                1,
                Math.floor(totalCells * 0.18)
            );

            const outlineIndices = ranked
                .slice(0, outlineCount)
                .sort(function (a, b) {
                    return a - b;
                });

            const outlineSet = new Set(outlineIndices);

            const remainingIndices = allIndices.filter(
                function (index) {
                    return !outlineSet.has(index);
                }
            );

            const fillOrder = getCenterOutOrder(
                remainingIndices
            );

            buildOrder = outlineIndices.concat(fillOrder);
        }

        buildCursor = 0;
        buildElapsed = 0;
        completedAt = null;
        buildInitialized = true;
    }

    function drawCompleteImage() {
        clearCanvas();

        for (let i = 0; i < totalCells; i++) {
            drawCharacter(i);
        }
    }

    function resetBuild() {
        clearCanvas();
        buildCursor = 0;
        buildElapsed = 0;
        completedAt = null;
        createBuildOrder();
    }

    // Wave is the only continuously moving full-image animation.
    function drawWave() {
        clearCanvas();

        const phaseSpeed = cfg.speed * 0.0018;
        const spatialX = 0.045;
        const spatialY = 0.025;
        const amplitude = 5;

        const chars = Array.from(cfg.content);

        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                const index = y * cols + x;
                const p = pixels[index];
                const char = chars[index % chars.length];

                const phase =
                    elapsed * phaseSpeed
                    - x * spatialX
                    - y * spatialY;

                const offsetY =
                    Math.sin(phase) * amplitude;

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

    function updateBuild(delta) {
        if (completedAt !== null) {
            if (performance.now() - completedAt >= COMPLETE_PAUSE_MS) {
                resetBuild();
            }

            return;
        }

        buildElapsed += delta;

        const targetCount = Math.min(
            totalCells,
            Math.floor(
                buildElapsed / 1000
                * BUILD_CELLS_PER_SECOND
                * cfg.speed
            )
        );

        // Draw only newly revealed characters.
        // Already visible cells remain on the canvas.
        const end = Math.min(
            targetCount,
            totalCells
        );

        while (buildCursor < end) {
            drawCharacter(buildOrder[buildCursor]);
            buildCursor++;
        }

        if (buildCursor >= totalCells) {
            completedAt = performance.now();
        }
    }

    function drawFrame(delta) {
        if (cfg.mode === "Wave") {
            elapsed += delta;
            drawWave();
        } else {
            updateBuild(delta);
        }
    }

    function animate(timestamp) {
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

        if (timestamp - lastDrawTimestamp >= FRAME_INTERVAL) {
            lastDrawTimestamp = timestamp;
            drawFrame(delta);
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

        if (cfg.mode === "Wave") {
            drawWave();
        } else {
            drawCompleteImage();
        }
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
                drawCompleteImage();
            }
        }
    );

    // Initial state.
    setupCanvas();

    if (cfg.mode !== "Wave") {
        createBuildOrder();
    }

    if (isPlaying) {
        if (cfg.mode === "Wave") {
            drawWave();
        } else {
            resetBuild();
        }

        startAnimation();
    } else {
        drawCompleteImage();
    }

    if ("ResizeObserver" in window) {
        const observer = new ResizeObserver(function () {
            setupCanvas();

            if (isPlaying && cfg.mode !== "Wave") {
                // Restart build after resizing so its positions
                // remain consistent with the new canvas size.
                resetBuild();
            } else if (isPlaying) {
                drawWave();
            } else {
                drawCompleteImage();
            }
        });

        observer.observe(container);
    } else {
        window.addEventListener("resize", function () {
            setupCanvas();

            if (isPlaying && cfg.mode !== "Wave") {
                resetBuild();
            } else if (isPlaying) {
                drawWave();
            } else {
                drawCompleteImage();
            }
        });
    }
})();
</script>
</body>
</html>
"""

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

