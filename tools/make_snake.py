"""
tools/make_snake.py - Generates self-contained, auto-playing SVG snake animations
for GitHub contribution grids (dark and light modes) without external services.
"""
import os

def generate_snake_svg(
    output_path="assets/snake.svg",
    is_dark=True,
    step_duration=0.08,
    snake_length=6
):
    cols = 52
    rows = 7
    cell_size = 11
    cell_gap = 3
    step_size = cell_size + cell_gap  # 14px
    grid_x = 18
    grid_y = 18
    
    # Dimensions
    grid_width = cols * step_size - cell_gap   # 725px
    grid_height = rows * step_size - cell_gap  # 95px
    svg_width = grid_width + grid_x * 2        # 761px
    svg_height = grid_height + grid_y * 2      # 131px

    # Color Palette
    if is_dark:
        bg_color = "#0d1117"
        border_color = "#30363d"
        empty_cell = "#161b22"
        palette = {
            1: "#0e4429",
            2: "#006d32",
            3: "#26a641",
            4: "#39d353"
        }
        # Cyan glowing snake gradient
        snake_colors = [
            "#ffffff",  # Head (bright white/cyan)
            "#67e8f9",  # Neck (cyan-300)
            "#22d3ee",  # Body 1 (cyan-400)
            "#06b6d4",  # Body 2 (cyan-500)
            "#0891b2",  # Body 3 (cyan-600)
            "#0e7490",  # Tail (cyan-700)
        ]
    else:
        bg_color = "#ffffff"
        border_color = "#d0d7de"
        empty_cell = "#ebedf0"
        palette = {
            1: "#9be9a8",
            2: "#40c463",
            3: "#30a14e",
            4: "#216e39"
        }
        # Cyan-teal snake on light
        snake_colors = [
            "#0f172a",  # Head (dark slate)
            "#0284c7",  # Neck (sky-600)
            "#06b6d4",  # Body 1 (cyan-500)
            "#0891b2",  # Body 2 (cyan-600)
            "#0d9488",  # Body 3 (teal-600)
            "#14b8a6",  # Tail (teal-500)
        ]

    # Sample Contribution Pattern (around 47 total commits distributed realistically)
    # Labeled as sample placeholder data matching user's profile activity
    # Map of (col, row) -> level (1..4)
    sample_contributions = {
        # October - November
        (3, 2): 1, (3, 4): 2, (4, 1): 1, (4, 3): 1,
        # December - January
        (9, 2): 1, (10, 5): 1, (12, 1): 2, (13, 3): 1,
        # February - March
        (17, 0): 1, (18, 4): 2, (20, 2): 1, (21, 5): 3,
        # April (Hackathon period - CODE RED)
        (25, 1): 2, (25, 2): 3, (26, 0): 1, (26, 3): 4, (26, 4): 2,
        # May
        (29, 2): 2, (30, 4): 1, (31, 1): 1,
        # June - July
        (35, 3): 2, (36, 1): 1, (38, 5): 1, (39, 2): 2,
        # August - September
        (43, 0): 1, (44, 4): 2, (45, 2): 1, (46, 3): 3,
        # October (Recent portfolio & research collab commits)
        (49, 1): 3, (49, 2): 4, (49, 3): 2, (50, 0): 2, (50, 1): 4, (50, 4): 3,
        (51, 1): 3, (51, 2): 4, (51, 3): 3, (51, 5): 2
    }

    # Generate zigzag path through all 52 columns x 7 rows
    # Col 0: down (r=0..6)
    # Col 1: up (r=6..0)
    # ...
    # Lead-in (snake starts off-grid above col 0)
    lead_in = [(0, -snake_length + i) for i in range(snake_length)]
    
    grid_path = []
    cell_visit_step = {}

    for c in range(cols):
        if c % 2 == 0:
            row_order = list(range(rows))  # down: 0 -> 6
        else:
            row_order = list(range(rows - 1, -1, -1))  # up: 6 -> 0
        
        for r in row_order:
            step_idx = len(lead_in) + len(grid_path)
            cell_visit_step[(c, r)] = step_idx
            grid_path.append((c, r))

    # Lead-out (snake exits off-grid above col 51)
    lead_out = [(cols - 1, -1 - i) for i in range(snake_length)]
    
    full_path = lead_in + grid_path + lead_out
    total_steps = len(full_path)
    total_duration = round(total_steps * step_duration, 2)

    # KeyTimes computation
    key_times_list = [f"{i / total_steps:.5f}" for i in range(total_steps)]
    key_times_list.append("1.00000")
    key_times_str = ";".join(key_times_list)

    # Pixel coordinate mapper
    def to_pixel(c, r):
        px = grid_x + c * step_size
        py = grid_y + r * step_size
        return px, py

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%">',
        f'  <!-- Auto-Playing Contribution Snake Animation ({cols} cols x {rows} rows) -->',
        f'  <!-- Loop Duration: {total_duration}s @ {step_duration}s/step ({total_steps} steps) -->',
        f'  <!-- Sample contribution pattern generated locally for preview -->',
        f'  <rect width="{svg_width}" height="{svg_height}" rx="6" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>',
        '  <g id="grid">'
    ]

    # Render Grid Cells
    for c in range(cols):
        for r in range(rows):
            px, py = to_pixel(c, r)
            if (c, r) in sample_contributions:
                lvl = sample_contributions[(c, r)]
                active_color = palette[lvl]
                visit_step = cell_visit_step[(c, r)]
                # Fraction of time when head eats the cell
                t_eat = visit_step / total_steps
                
                # Discrete cell eaten animation:
                # Active level color until t_eat, then changes to empty_cell color
                svg_lines.append(
                    f'    <rect x="{px}" y="{py}" width="{cell_size}" height="{cell_size}" rx="2" fill="{active_color}">'
                    f'<animate attributeName="fill" values="{active_color};{empty_cell};{empty_cell}" '
                    f'keyTimes="0;{t_eat:.5f};1" dur="{total_duration}s" calcMode="discrete" repeatCount="indefinite"/>'
                    f'</rect>'
                )
            else:
                # Static empty cell
                svg_lines.append(
                    f'    <rect x="{px}" y="{py}" width="{cell_size}" height="{cell_size}" rx="2" fill="{empty_cell}"/>'
                )

    svg_lines.append('  </g>')
    svg_lines.append('  <g id="snake">')

    # Render Snake Segments (Tail to Head so head is rendered on top)
    for seg_idx in range(snake_length - 1, -1, -1):
        color = snake_colors[seg_idx]
        
        # Build x and y values for this segment across all total_steps
        x_vals = []
        y_vals = []
        for s in range(total_steps):
            head_step = s - seg_idx
            if head_step < 0:
                c, r = lead_in[0]
            elif head_step >= len(full_path):
                c, r = lead_out[-1]
            else:
                c, r = full_path[head_step]
            
            px, py = to_pixel(c, r)
            x_vals.append(str(px))
            y_vals.append(str(py))

        # Add wrap-around value matching end
        x_vals.append(x_vals[-1])
        y_vals.append(y_vals[-1])

        x_str = ";".join(x_vals)
        y_str = ";".join(y_vals)

        # Head styling: slightly rounded or accent dot
        rx = 3 if seg_idx == 0 else 2

        svg_lines.append(f'    <!-- Snake Segment {seg_idx} {"(Head)" if seg_idx == 0 else ""} -->')
        svg_lines.append(
            f'    <rect width="{cell_size}" height="{cell_size}" rx="{rx}" fill="{color}">'
            f'<animate attributeName="x" values="{x_str}" keyTimes="{key_times_str}" dur="{total_duration}s" calcMode="discrete" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{y_str}" keyTimes="{key_times_str}" dur="{total_duration}s" calcMode="discrete" repeatCount="indefinite"/>'
            f'</rect>'
        )

    svg_lines.append('  </g>')
    svg_lines.append('</svg>')

    content = "\n".join(svg_lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    kb_size = len(content.encode("utf-8")) / 1024
    print(f"Generated {output_path} ({kb_size:.1f} KB, is_dark={is_dark})")
    return True

def main():
    os.makedirs("assets", exist_ok=True)
    # 1. Dark mode animated snake
    generate_snake_svg("assets/snake.svg", is_dark=True)
    # 2. Also keep snake-placeholder.svg in sync
    generate_snake_svg("assets/snake-placeholder.svg", is_dark=True)
    # 3. Light mode animated snake
    generate_snake_svg("assets/snake-light.svg", is_dark=False)

if __name__ == "__main__":
    main()
