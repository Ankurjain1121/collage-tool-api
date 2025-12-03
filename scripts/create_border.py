#!/usr/bin/env python3
"""
Generate a simple elegant border design.
This creates a PNG with transparent center for overlaying on collages.
"""

from PIL import Image, ImageDraw
import os


def create_gradient_border(
    width: int = 1920,
    height: int = 1080,
    border_width: int = 60,
    separator_width: int = 40,
    separator_x: int = 480,  # 25% of 1920
    colors: list = None,
    output_path: str = "default.png"
):
    """
    Create an elegant gradient border with transparent center.

    Args:
        width, height: Canvas dimensions
        border_width: Width of border on edges
        separator_width: Width of vertical separator
        separator_x: X position of separator
        colors: List of RGBA colors for gradient
        output_path: Output file path
    """
    if colors is None:
        # Soft pastel gradient: pink -> lavender -> light blue
        colors = [
            (255, 218, 233, 255),  # Soft pink
            (230, 210, 255, 255),  # Lavender
            (210, 230, 255, 255),  # Light blue
        ]

    # Create transparent canvas
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw border with gradient effect
    # Top border
    for i in range(border_width):
        alpha = int(255 * (1 - i / border_width))  # Fade out
        color_idx = int(i / border_width * (len(colors) - 1))
        color = colors[min(color_idx, len(colors) - 1)]
        color_with_alpha = color[:3] + (alpha,)
        draw.line([(0, i), (width, i)], fill=color_with_alpha)

    # Bottom border
    for i in range(border_width):
        alpha = int(255 * (1 - i / border_width))
        color_idx = int(i / border_width * (len(colors) - 1))
        color = colors[min(color_idx, len(colors) - 1)]
        color_with_alpha = color[:3] + (alpha,)
        draw.line([(0, height - 1 - i), (width, height - 1 - i)], fill=color_with_alpha)

    # Left border
    for i in range(border_width):
        alpha = int(255 * (1 - i / border_width))
        color_idx = int(i / border_width * (len(colors) - 1))
        color = colors[min(color_idx, len(colors) - 1)]
        color_with_alpha = color[:3] + (alpha,)
        draw.line([(i, 0), (i, height)], fill=color_with_alpha)

    # Right border
    for i in range(border_width):
        alpha = int(255 * (1 - i / border_width))
        color_idx = int(i / border_width * (len(colors) - 1))
        color = colors[min(color_idx, len(colors) - 1)]
        color_with_alpha = color[:3] + (alpha,)
        draw.line([(width - 1 - i, 0), (width - 1 - i, height)], fill=color_with_alpha)

    # Vertical separator between image1 and image2
    sep_start = separator_x - separator_width // 2
    for i in range(separator_width):
        # Soft gradient separator
        dist_from_center = abs(i - separator_width // 2)
        alpha = int(180 * (1 - dist_from_center / (separator_width // 2)))
        color = colors[1]  # Use middle color (lavender)
        color_with_alpha = color[:3] + (alpha,)
        draw.line(
            [(sep_start + i, border_width), (sep_start + i, height - border_width)],
            fill=color_with_alpha
        )

    # Add subtle corner decorations
    corner_size = border_width + 20
    corner_color = colors[0][:3] + (200,)

    # Top-left corner
    for i in range(corner_size):
        alpha = int(200 * (1 - i / corner_size))
        c = corner_color[:3] + (alpha,)
        draw.arc([0, 0, corner_size * 2, corner_size * 2], 180, 270, fill=c, width=2)

    # Top-right corner
    for i in range(corner_size):
        alpha = int(200 * (1 - i / corner_size))
        c = corner_color[:3] + (alpha,)
        draw.arc([width - corner_size * 2, 0, width, corner_size * 2], 270, 0, fill=c, width=2)

    # Bottom-left corner
    for i in range(corner_size):
        alpha = int(200 * (1 - i / corner_size))
        c = corner_color[:3] + (alpha,)
        draw.arc([0, height - corner_size * 2, corner_size * 2, height], 90, 180, fill=c, width=2)

    # Bottom-right corner
    for i in range(corner_size):
        alpha = int(200 * (1 - i / corner_size))
        c = corner_color[:3] + (alpha,)
        draw.arc([width - corner_size * 2, height - corner_size * 2, width, height], 0, 90, fill=c, width=2)

    # Save
    img.save(output_path, "PNG")
    print(f"Border saved to: {output_path}")


def main():
    # Create output directory if needed
    os.makedirs("assets/borders", exist_ok=True)

    # Create default border
    create_gradient_border(
        output_path="assets/borders/default.png"
    )

    # Create alternate color schemes
    # Warm pastel (peach/coral)
    create_gradient_border(
        colors=[
            (255, 218, 200, 255),  # Peach
            (255, 200, 180, 255),  # Coral
            (255, 220, 200, 255),  # Light peach
        ],
        output_path="assets/borders/warm.png"
    )

    # Cool pastel (mint/aqua)
    create_gradient_border(
        colors=[
            (200, 255, 230, 255),  # Mint
            (200, 240, 255, 255),  # Aqua
            (220, 255, 240, 255),  # Light mint
        ],
        output_path="assets/borders/cool.png"
    )

    # Neutral (cream/beige)
    create_gradient_border(
        colors=[
            (255, 250, 240, 255),  # Cream
            (245, 240, 230, 255),  # Beige
            (250, 245, 235, 255),  # Light cream
        ],
        output_path="assets/borders/neutral.png"
    )

    print("All borders created!")


if __name__ == "__main__":
    main()
