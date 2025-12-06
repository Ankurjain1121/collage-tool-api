"""
Generate 5 pastel backgrounds with mixed geometric patterns.
Patterns include: circles, triangles, lines
"""
import random
from PIL import Image, ImageDraw
from pathlib import Path

# Canvas size
WIDTH = 1920
HEIGHT = 1080

# 5 Pastel base colors (confirmed)
PASTEL_COLORS = [
    ("#FFB6C1", "light_pink"),     # Light Pink
    ("#98FF98", "mint_green"),     # Mint Green
    ("#B0E0E6", "powder_blue"),    # Powder Blue
    ("#E6E6FA", "lavender"),       # Lavender
    ("#FFFDD0", "cream"),          # Cream
]


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def darken_color(rgb: tuple, factor: float = 0.15) -> tuple:
    """Darken a color slightly for geometric shapes."""
    return tuple(max(0, int(c * (1 - factor))) for c in rgb)


def lighten_color(rgb: tuple, factor: float = 0.15) -> tuple:
    """Lighten a color slightly for geometric shapes."""
    return tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)


def draw_circles(draw: ImageDraw, base_rgb: tuple, count: int = 30):
    """Draw scattered circles."""
    shape_color = darken_color(base_rgb, 0.1)
    for _ in range(count):
        x = random.randint(-50, WIDTH + 50)
        y = random.randint(-50, HEIGHT + 50)
        radius = random.randint(10, 60)
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=shape_color,
            outline=None
        )


def draw_triangles(draw: ImageDraw, base_rgb: tuple, count: int = 20):
    """Draw scattered triangles."""
    shape_color = lighten_color(base_rgb, 0.1)
    for _ in range(count):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(20, 80)
        # Random rotation by varying triangle points
        angle_offset = random.uniform(0, 360)
        import math
        points = []
        for i in range(3):
            angle = math.radians(angle_offset + i * 120)
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=shape_color, outline=None)


def draw_lines(draw: ImageDraw, base_rgb: tuple, count: int = 15):
    """Draw scattered thin lines."""
    shape_color = darken_color(base_rgb, 0.08)
    for _ in range(count):
        x1 = random.randint(-100, WIDTH + 100)
        y1 = random.randint(-100, HEIGHT + 100)
        length = random.randint(100, 300)
        angle = random.uniform(0, 360)
        import math
        x2 = x1 + length * math.cos(math.radians(angle))
        y2 = y1 + length * math.sin(math.radians(angle))
        width = random.randint(2, 6)
        draw.line([(x1, y1), (x2, y2)], fill=shape_color, width=width)


def generate_background(hex_color: str, name: str, output_dir: Path) -> Path:
    """Generate a single pastel background with mixed geometric patterns."""
    base_rgb = hex_to_rgb(hex_color)

    # Create base image
    img = Image.new("RGB", (WIDTH, HEIGHT), base_rgb)
    draw = ImageDraw.Draw(img)

    # Add mixed geometric shapes
    random.seed(hash(name))  # Consistent patterns per color
    draw_circles(draw, base_rgb, count=25)
    draw_triangles(draw, base_rgb, count=15)
    draw_lines(draw, base_rgb, count=12)

    # Save
    output_path = output_dir / f"base_{name}.png"
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")
    return output_path


def main():
    """Generate all 5 pastel backgrounds."""
    # Determine output directory
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "assets" / "backgrounds"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating backgrounds to: {output_dir}")
    print("-" * 50)

    generated = []
    for hex_color, name in PASTEL_COLORS:
        path = generate_background(hex_color, name, output_dir)
        generated.append(path)

    print("-" * 50)
    print(f"Generated {len(generated)} backgrounds:")
    for p in generated:
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
