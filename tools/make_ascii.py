"""
tools/make_ascii.py - Generates an ASCII-art hero portrait SVG and static high-res PNG
from assets/sujal.jpg.

Features:
- Full photo portrait with head, hair, face, neck, collar, broad shoulders, and chest
- Completely removes brick background cleanly using OpenCV GrabCut with corner priors
- Facial feature enhancement: CLAHE, gamma lift, unsharp mask, and DoG/Sobel edge blending
- Targeted micro-enhancements: teeth/smile luminance boost, eye & eyebrow contrast definition
- Balanced shirt tone mapping so the face remains the brightly lit focal center
- 28-character smooth tonal ramp with 100% solid subject fill (zero hollow gaps on cheeks)
- 4-tone cyan brightness coloring (#0e7490, #06b6d4, #22d3ee, #e0fbff)
- Grouped <tspan> elements keeping SVG under 250 KB
- Fixed textLength & lengthAdjust="spacing" with xml:space="preserve"
- OFL vector font outlines for "SUJAL KUMAR KANU" via fontTools
- SMIL line-by-line reveal animation (plays once, freezes)
- High-res 2400px wide PNG export for static fallbacks
- Tunable CLI flags: --cols, --gamma, --edge, --crop, --input, --output-svg, --output-png
"""

import os
import argparse
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen


# 28-character curated smooth ramp from sparse to dense
RAMP = " .'`^,:;~-_+<>i!*=?co1xS%#8&@W"

# 4 Cyan color shades by brightness
SHADE_SHADOW  = "#0e7490"  # deep shadows, hair texture, beard shadows
SHADE_MID_LOW = "#06b6d4"  # transitional midtones, shirt checks
SHADE_MID     = "#22d3ee"  # lit skin, facial features
SHADE_HIGH    = "#e0fbff"  # highlights, teeth, eye catchlights, hair reflections

RGB_SHADOW  = (14, 116, 144)
RGB_MID_LOW = (6, 182, 212)
RGB_MID     = (34, 211, 238)
RGB_HIGH    = (224, 251, 255)


def generate_vector_name(text="SUJAL KUMAR KANU", font_path="tools/fonts/Poppins-ExtraBold.ttf", font_size=52.0, target_width=1200.0, baseline_y=75.0):
    """Converts name text into vector <path> elements centered horizontally."""
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file {font_path} not found.")

    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    units_per_em = font["head"].unitsPerEm
    scale = font_size / units_per_em

    space_glyph_name = cmap.get(ord(" "))
    space_width = (glyph_set[space_glyph_name].width if space_glyph_name else 300) * scale

    glyphs = []
    total_width = 0.0

    for ch in text:
        if ch == " ":
            total_width += space_width
            continue
        code = ord(ch)
        glyph_name = cmap.get(code)
        if not glyph_name or glyph_name not in glyph_set:
            continue
        glyph = glyph_set[glyph_name]
        pen = SVGPathPen(glyph_set)
        glyph.draw(pen)
        d_cmd = pen.getCommands()
        adv = glyph.width * scale
        glyphs.append((total_width, d_cmd, adv))
        total_width += adv

    x_start = (target_width - total_width) / 2.0

    path_elements = []
    for x_off, d_cmd, _ in glyphs:
        # Font coordinates have Y inverted relative to SVG
        path_elements.append(
            f'      <g transform="translate({x_start + x_off:.2f}, {baseline_y:.2f}) scale({scale:.4f}, -{scale:.4f})">'
            f'<path d="{d_cmd}" fill="url(#hero-name-grad)" />'
            f'</g>'
        )

    return "\n".join(path_elements), x_start, baseline_y, total_width


def remove_background(img):
    """Removes brick background cleanly using GrabCut with corner background priors."""
    h, w, _ = img.shape
    mask = np.full((h, w), cv2.GC_PR_FGD, dtype=np.uint8)

    # Definite background priors: corners & top border where brick wall resides
    cv2.rectangle(mask, (0, 0), (int(w * 0.22), int(h * 0.62)), cv2.GC_BGD, -1)
    cv2.rectangle(mask, (int(w * 0.78), 0), (w, int(h * 0.62)), cv2.GC_BGD, -1)
    cv2.rectangle(mask, (0, 0), (w, int(h * 0.03)), cv2.GC_BGD, -1)

    # Definite foreground priors: center of face and center of chest/shirt
    cv2.rectangle(mask, (int(w * 0.38), int(h * 0.20)), (int(w * 0.64), int(h * 0.52)), cv2.GC_FGD, -1)
    cv2.rectangle(mask, (int(w * 0.20), int(h * 0.74)), (int(w * 0.82), int(h * 0.98)), cv2.GC_FGD, -1)

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(img, mask, None, bgdModel, fgdModel, 6, cv2.GC_INIT_WITH_MASK)
        fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(fg_mask)
        if num_labels > 1:
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            fg_mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)

        return fg_mask.astype(np.float32) / 255.0
    except Exception as e:
        print(f"GrabCut fallback due to: {e}")
        fall_mask = np.ones((h, w), dtype=np.float32)
        return fall_mask


def process_image(img, fg_mask, crop_str="35,1024,1.0", gamma=0.80, edge_weight=0.50):
    """Processes full image: CLAHE, gamma, unsharp mask, DoG/Sobel edge blending, teeth & eye boost."""
    h, w, _ = img.shape

    parts = [float(p.strip()) for p in crop_str.split(",")]
    top = int(parts[0])
    bottom = min(h, int(parts[1]))
    aspect_ratio = float(parts[2]) if len(parts) > 2 else 1.0

    crop_h = bottom - top
    crop_w = min(w, int(crop_h * aspect_ratio))
    cx = w // 2
    left = max(0, cx - crop_w // 2)
    right = min(w, cx + crop_w // 2)

    cropped_img = img[top:bottom, left:right]
    cropped_mask = fg_mask[top:bottom, left:right]
    ch, cw, _ = cropped_img.shape

    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    y_coords, x_coords = np.indices((ch, cw))
    y_norm = y_coords.astype(np.float32) / ch
    x_norm = x_coords.astype(np.float32) / cw

    # 1. CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # 2. Gamma lift to illuminate facial shadows
    inv_gamma = 1.0 / max(0.1, gamma)
    table = np.array([((i / 255.0) ** inv_gamma) * 255.0 for i in np.arange(0, 256)]).astype("uint8")
    lifted = cv2.LUT(contrast, table)

    # 3. Unsharp mask
    blur = cv2.GaussianBlur(lifted, (0, 0), 2.0)
    unsharp = cv2.addWeighted(lifted, 1.50, blur, -0.50, 0)

    # 4. Edge layer blending (Difference of Gaussians + Sobel)
    g1 = cv2.GaussianBlur(gray, (0, 0), 0.6)
    g2 = cv2.GaussianBlur(gray, (0, 0), 2.0)
    dog = np.clip(g1.astype(float) - g2.astype(float), 0, 255)
    dog_norm = cv2.normalize(dog, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    edge_mag = np.hypot(sobelx, sobely)
    edge_norm = cv2.normalize(edge_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    combined_edges = cv2.addWeighted(dog_norm, 0.65, edge_norm, 0.35, 0)
    blended = cv2.addWeighted(unsharp, 0.80, combined_edges, edge_weight, 0)

    # 5. Targeted Feature Enhancements:
    # A. Teeth / Smile brightness boost
    teeth_region = (y_norm > 0.40) & (y_norm < 0.48) & (x_norm > 0.41) & (x_norm < 0.59)
    teeth_pixels = teeth_region & (unsharp > 145)
    blended[teeth_pixels] = np.clip(blended[teeth_pixels].astype(float) * 1.35, 0, 255).astype(np.uint8)

    # B. Eyes & Eyebrows contrast definition
    eyes_region = (y_norm > 0.25) & (y_norm < 0.35) & (x_norm > 0.36) & (x_norm < 0.64)
    dark_eye_pixels = eyes_region & (gray < 80)
    blended[dark_eye_pixels] = np.clip(blended[dark_eye_pixels].astype(float) * 0.70, 0, 255).astype(np.uint8)
    light_eye_pixels = eyes_region & (gray > 130)
    blended[light_eye_pixels] = np.clip(blended[light_eye_pixels].astype(float) * 1.25, 0, 255).astype(np.uint8)

    # C. Shirt tone balancing (y_norm > 0.64)
    shirt_fade = np.clip((y_norm - 0.64) / 0.10, 0.0, 1.0)
    blended_float = blended.astype(float)
    shirt_adjusted = np.clip(blended_float * 0.88, 0, 215)
    blended = ((1.0 - shirt_fade) * blended_float + shirt_fade * shirt_adjusted).astype(np.uint8)

    # 6. Baseline tone normalization on subject pixels so full face/shirt has continuous coverage
    is_person = cropped_mask > 0.10
    person_vals = blended[is_person]
    p_min = np.percentile(person_vals, 1)
    p_max = np.percentile(person_vals, 99)
    norm_vals = np.clip((blended.astype(float) - p_min) / max(1.0, (p_max - p_min)), 0.0, 1.0)

    final_vals = np.zeros_like(blended, dtype=np.float32)
    # Baseline at 42 so face has full, continuous coverage
    final_vals[is_person] = (42.0 + norm_vals[is_person] * 213.0)
    processed_final = np.clip(final_vals, 0, 255).astype(np.uint8)

    return processed_final, cropped_mask, ch, cw


def build_ascii_matrix(processed_img, cropped_mask, ch, cw, cols=195, vertical_ratio=0.50):
    """Downsamples image and maps pixels to characters and shade categories."""
    rows = int(cols * (ch / cw) * vertical_ratio)
    resized_img = cv2.resize(processed_img, (cols, rows), interpolation=cv2.INTER_AREA)
    resized_mask = cv2.resize(cropped_mask, (cols, rows), interpolation=cv2.INTER_AREA)

    # Post-downsampling micro-sharpening
    res_float = resized_img.astype(np.float32)
    blurred_res = cv2.GaussianBlur(res_float, (0, 0), 0.7)
    sharp_grid = np.clip(res_float * 1.30 - blurred_res * 0.30, 0, 255).astype(np.uint8)

    n_ramp = len(RAMP)
    matrix = []

    for r in range(rows):
        row_entries = []
        for c in range(cols):
            m_val = resized_mask[r, c]
            val = float(sharp_grid[r, c])

            # Background pixel
            if m_val < 0.25:
                row_entries.append((" ", SHADE_SHADOW, 0))
                continue

            # Subject pixel: map between 35 and 255 to ramp
            norm = np.clip((val - 35.0) / (255.0 - 35.0), 0.0, 1.0)
            char_idx = 1 + int((norm ** 1.02) * (n_ramp - 2))
            char_idx = max(1, min(n_ramp - 1, char_idx))
            ch_char = RAMP[char_idx]

            if val < 75:
                shade = SHADE_SHADOW
            elif val < 130:
                shade = SHADE_MID_LOW
            elif val < 190:
                shade = SHADE_MID
            else:
                shade = SHADE_HIGH

            row_entries.append((ch_char, shade, int(val)))
        matrix.append(row_entries)

    return matrix, cols, rows


def generate_hero_svg(matrix, cols, rows, vector_name_svg=None, output_svg="assets/hero.svg", no_name=True):
    """Generates 1200px wide hero SVG with optional vector name and grouped-tspan animated portrait."""
    target_width = 1200.0

    # Layout metrics: portrait width 1080px centered in 1200px container
    portrait_width = 1080.0
    char_w = portrait_width / cols
    char_h = char_w / 0.50 # ~11.07px per row
    portrait_x_start = (target_width - portrait_width) / 2.0
    portrait_y_start = 0.0 if no_name else 110.0

    total_svg_height = int(portrait_y_start + rows * char_h + (30.0 if not no_name else 30.0))

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {total_svg_height}" width="100%" height="{total_svg_height}" preserveAspectRatio="xMidYMid meet">',
        '  <defs>',
    ]

    if not no_name and vector_name_svg:
        svg_lines.extend([
            '    <!-- Gradient for Name Header -->',
            '    <linearGradient id="hero-name-grad" x1="0%" y1="0%" x2="100%" y2="0%">',
            '      <stop offset="0%" stop-color="#22d3ee" />',
            '      <stop offset="100%" stop-color="#8b5cf6" />',
            '    </linearGradient>',
        ])

    svg_lines.extend([
        '    <style>',
        '      .hero-bg { fill: #0d1117; }',
        '      .ascii-row {',
        '        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;',
        '        font-size: 10.5px;',
        '        letter-spacing: 0px;',
        '      }',
        '      @media (prefers-reduced-motion: reduce) {',
        '        text, g { opacity: 1 !important; }',
        '      }',
        '    </style>',
        '  </defs>',
        '',
        '  <!-- Dark GitHub Profile Background -->',
        f'  <rect width="1200" height="{total_svg_height}" class="hero-bg" />',
        '',
    ])

    if not no_name and vector_name_svg:
        svg_lines.extend([
            '  <!-- Vector Name Outline: SUJAL KUMAR KANU (OFL Font) -->',
            '  <g id="hero-name">',
            vector_name_svg,
            '  </g>',
            '',
        ])

    svg_lines.append('  <!-- ASCII Portrait Rows (Grouped <tspan> runs with fixed textLength) -->')
    svg_lines.append('  <g id="portrait-rows" class="ascii-row">')

    # Animation timing: reveal rows line by line
    anim_start = 0.20
    step_delay = 0.016

    for r_idx, row in enumerate(matrix):
        y_pos = portrait_y_start + (r_idx + 1) * char_h
        anim_time = round(anim_start + r_idx * step_delay, 3)

        # Group consecutive characters by shade
        runs = []
        cur_shade = None
        cur_chars = []

        for ch_char, shade, _ in row:
            if shade != cur_shade:
                if cur_chars:
                    runs.append((cur_shade, "".join(cur_chars)))
                cur_shade = shade
                cur_chars = [ch_char]
            else:
                cur_chars.append(ch_char)
        if cur_chars:
            runs.append((cur_shade, "".join(cur_chars)))

        # Build tspans
        tspans = []
        for shade, text_chunk in runs:
            escaped = (
                text_chunk.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )
            tspans.append(f'<tspan fill="{shade}">{escaped}</tspan>')

        tspans_html = "".join(tspans)
        svg_lines.append(
            f'    <text x="{portrait_x_start:.1f}" y="{y_pos:.1f}" xml:space="preserve" '
            f'textLength="{portrait_width:.1f}" lengthAdjust="spacing">'
            f'<animate attributeName="opacity" from="0" to="1" dur="0.12s" begin="{anim_time}s" fill="freeze" />'
            f'{tspans_html}</text>'
        )

    svg_lines.append('  </g>')
    svg_lines.append('</svg>')

    full_svg = "\n".join(svg_lines)
    with open(output_svg, "w", encoding="utf-8") as f:
        f.write(full_svg)

    svg_kb = len(full_svg.encode("utf-8")) / 1024
    print(f"Generated {output_svg}: {svg_kb:.1f} KB (viewBox 0 0 1200 {total_svg_height})")
    return full_svg, total_svg_height


def generate_hero_png(matrix, cols, rows, font_path, output_png="assets/hero.png", total_h_svg=1104, no_name=True):
    """Renders a pristine 2400px wide static PNG fallback."""
    scale = 2.0
    png_w = int(1200 * scale)
    png_h = int(total_h_svg * scale)

    png_img = Image.new("RGB", (png_w, png_h), (13, 17, 23)) # #0d1117
    draw = ImageDraw.Draw(png_img)

    if not no_name:
        # Render Name Banner with gradient at top
        try:
            title_font = ImageFont.truetype(font_path, int(52 * scale))
        except Exception:
            title_font = ImageFont.load_default()

        name_text = "SUJAL KUMAR KANU"
        bbox = draw.textbbox((0, 0), name_text, font=title_font)
        name_w = bbox[2] - bbox[0]
        name_x = (png_w - name_w) / 2.0
        name_y = int(30 * scale)

        # Render gradient text onto mask
        mask_img = Image.new("L", (png_w, png_h), 0)
        mask_draw = ImageDraw.Draw(mask_img)
        mask_draw.text((name_x, name_y), name_text, fill=255, font=title_font)

        # Linear gradient #22d3ee to #8b5cf6
        grad_img = Image.new("RGB", (png_w, png_h))
        grad_draw = ImageDraw.Draw(grad_img)
        for x in range(int(name_x), int(name_x + name_w + 1)):
            t = (x - name_x) / max(1.0, name_w)
            r = int(34 + t * (139 - 34))
            g = int(211 + t * (92 - 211))
            b = int(238 + t * (246 - 238))
            grad_draw.line([(x, name_y), (x, name_y + int(70 * scale))], fill=(r, g, b))

        png_img.paste(grad_img, (0, 0), mask_img)

    # Render ASCII rows
    try:
        mono_font = ImageFont.truetype("consola.ttf", int(10.5 * scale * 1.7))
    except Exception:
        mono_font = ImageFont.load_default()

    portrait_width = 1080.0 * scale
    char_w = portrait_width / cols
    char_h = char_w / 0.50
    portrait_x_start = (png_w - portrait_width) / 2.0
    portrait_y_start = (0.0 if no_name else 110.0) * scale

    for r in range(rows):
        y_pos = portrait_y_start + r * char_h
        for c in range(cols):
            ch_char, shade, val = matrix[r][c]
            if ch_char == " ":
                continue
            x_pos = portrait_x_start + c * char_w

            if shade == SHADE_SHADOW:
                rgb = RGB_SHADOW
            elif shade == SHADE_MID_LOW:
                rgb = RGB_MID_LOW
            elif shade == SHADE_MID:
                rgb = RGB_MID
            else:
                rgb = RGB_HIGH

            draw.text((x_pos, y_pos), ch_char, fill=rgb, font=mono_font)

    png_img.save(output_png, "PNG")
    print(f"Generated {output_png} ({png_w}x{png_h})")


def main():
    parser = argparse.ArgumentParser(description="Generate ASCII Hero Banner & Portrait")
    parser.add_argument("--input", default="assets/sujal.jpg", help="Path to input photo")
    parser.add_argument("--cols", type=int, default=195, help="Number of ASCII columns (170-200)")
    parser.add_argument("--gamma", type=float, default=0.80, help="Gamma correction factor (~0.8)")
    parser.add_argument("--edge", type=float, default=0.50, help="Edge layer blend weight (0.2-0.6)")
    parser.add_argument("--crop", default="35,1024,1.0", help="Crop bounds: top,bottom,ratio")
    parser.add_argument("--output-svg", default="assets/hero.svg", help="Output hero SVG path")
    parser.add_argument("--output-png", default="assets/hero.png", help="Output hero PNG path")
    parser.add_argument("--font", default="tools/fonts/Poppins-ExtraBold.ttf", help="OFL Heavy font path")
    parser.add_argument("--no-name", dest="no_name", action="store_true", default=True, help="Omit gradient name text banner (default: True)")
    parser.add_argument("--with-name", dest="no_name", action="store_false", help="Include gradient name text banner")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input photo {args.input} does not exist.")
        return 1

    print(f"Loading {args.input}...")
    img = cv2.imread(args.input)

    print("Step 1: Segmenting background with GrabCut...")
    fg_mask = remove_background(img)

    print(f"Step 2: Processing image (crop={args.crop}, gamma={args.gamma}, edge={args.edge})...")
    processed_img, cropped_mask, ch, cw = process_image(
        img, fg_mask,
        crop_str=args.crop,
        gamma=args.gamma,
        edge_weight=args.edge
    )

    print(f"Step 3: Building ASCII matrix ({args.cols} columns)...")
    matrix, cols, rows = build_ascii_matrix(processed_img, cropped_mask, ch, cw, cols=args.cols)

    vector_name_svg = None
    if not args.no_name:
        print(f"Step 4: Extracting vector glyphs from {args.font}...")
        vector_name_svg, _, _, _ = generate_vector_name(
            text="SUJAL KUMAR KANU",
            font_path=args.font,
            font_size=52.0,
            target_width=1200.0,
            baseline_y=75.0
        )
    else:
        print("Step 4: Skipping name header (--no-name)...")

    print(f"Step 5: Writing hero SVG to {args.output_svg}...")
    _, total_h = generate_hero_svg(matrix, cols, rows, vector_name_svg, output_svg=args.output_svg, no_name=args.no_name)

    print(f"Step 6: Writing high-res fallback PNG to {args.output_png}...")
    generate_hero_png(matrix, cols, rows, args.font, output_png=args.output_png, total_h_svg=total_h, no_name=args.no_name)

    print("ASCII portrait generation complete!")
    return 0


if __name__ == "__main__":
    main()
