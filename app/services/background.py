from PIL import Image
from rembg import remove
from colorthief import ColorThief
from io import BytesIO
import colorsys


class BackgroundService:
    """Handle background removal and color operations."""

    @staticmethod
    def remove_background(image_bytes: bytes) -> Image.Image:
        """
        Remove background from image using rembg.

        Args:
            image_bytes: Input image bytes

        Returns:
            PIL Image with transparent background (RGBA)
        """
        output_bytes = remove(image_bytes)
        return Image.open(BytesIO(output_bytes)).convert("RGBA")

    @staticmethod
    def get_dominant_color(image_path: str) -> tuple[int, int, int]:
        """
        Get the dominant color from an image.

        Args:
            image_path: Path to image file

        Returns:
            RGB tuple of dominant color
        """
        color_thief = ColorThief(image_path)
        return color_thief.get_color(quality=1)

    @staticmethod
    def get_complementary_color(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Get a complementary/harmonious background color.

        For product photos, we want a soft, non-distracting background.
        We'll create a lighter, desaturated version of the dominant color.

        Args:
            rgb: RGB tuple of dominant color

        Returns:
            RGB tuple for background
        """
        r, g, b = [x / 255.0 for x in rgb]

        # Convert to HLS
        h, l, s = colorsys.rgb_to_hls(r, g, b)

        # Make it lighter and less saturated for a soft background
        l = min(0.92, l + 0.3)  # Lighter
        s = max(0.1, s * 0.3)   # Less saturated

        # Convert back to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def get_pastel_background(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Create a pastel background color based on the product color.

        Args:
            rgb: RGB tuple of dominant color

        Returns:
            RGB tuple for pastel background
        """
        # Mix with white to create pastel effect
        white_ratio = 0.7
        r = int(rgb[0] * (1 - white_ratio) + 255 * white_ratio)
        g = int(rgb[1] * (1 - white_ratio) + 255 * white_ratio)
        b = int(rgb[2] * (1 - white_ratio) + 255 * white_ratio)
        return (r, g, b)

    @staticmethod
    def apply_solid_background(
        fg_image: Image.Image,
        bg_color: tuple[int, int, int],
        size: tuple[int, int] = None
    ) -> Image.Image:
        """
        Apply a solid color background to a transparent image.

        Args:
            fg_image: Foreground image with transparency (RGBA)
            bg_color: RGB tuple for background color
            size: Optional output size (width, height)

        Returns:
            PIL Image with solid background (RGB)
        """
        if size is None:
            size = fg_image.size

        # Create background
        background = Image.new("RGB", size, bg_color)

        # Resize foreground to fit if needed
        if fg_image.size != size:
            fg_image = fg_image.copy()
            fg_image.thumbnail(size, Image.Resampling.LANCZOS)

            # Center the image
            offset = (
                (size[0] - fg_image.width) // 2,
                (size[1] - fg_image.height) // 2
            )
        else:
            offset = (0, 0)

        # Composite
        background.paste(fg_image, offset, fg_image if fg_image.mode == "RGBA" else None)

        return background
