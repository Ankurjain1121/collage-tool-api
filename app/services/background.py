import replicate
import httpx
import base64
import os
from PIL import Image
from colorthief import ColorThief
from io import BytesIO
import colorsys
import asyncio
from app.config import settings

# Set the Replicate API token from our config
os.environ["REPLICATE_API_TOKEN"] = settings.REPLICATE_API_TOKEN


class BackgroundService:
    """Handle background removal and color operations."""

    async def remove_background(self, image_bytes: bytes) -> Image.Image:
        """
        Remove background from image using Replicate lucataco/remove-bg.

        Args:
            image_bytes: Input image bytes

        Returns:
            PIL Image with transparent background (RGBA)
        """
        # Convert to base64 data URI
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"

        # Run Replicate model (sync API, run in thread pool)
        loop = asyncio.get_event_loop()
        output_url = await loop.run_in_executor(
            None,
            lambda: replicate.run(
                "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
                input={"image": data_uri}
            )
        )

        # Download result
        async with httpx.AsyncClient() as client:
            response = await client.get(output_url)
            response.raise_for_status()

        return Image.open(BytesIO(response.content)).convert("RGBA")

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
    def get_contrast_background(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Calculate a high-contrast background color for the product.

        Strategy: Create a light, desaturated version that contrasts
        with the product while not being distracting.

        - Dark products get light backgrounds
        - Light products get slightly darker backgrounds
        - Low saturation for non-distracting effect

        Args:
            rgb: RGB tuple of dominant color

        Returns:
            RGB tuple for contrast background
        """
        r, g, b = [x / 255.0 for x in rgb]
        h, l, s = colorsys.rgb_to_hls(r, g, b)

        # If product is dark, use light background
        # If product is light, use slightly darker background
        if l < 0.5:
            new_l = 0.92  # Light background for dark products
        else:
            new_l = 0.85  # Slightly less light for light products

        # Reduce saturation for softer, non-distracting background
        new_s = min(0.15, s * 0.3)

        r, g, b = colorsys.hls_to_rgb(h, new_l, new_s)
        return (int(r * 255), int(g * 255), int(b * 255))

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

    @staticmethod
    def get_dominant_color_from_bytes(image_bytes: bytes) -> tuple[int, int, int]:
        """
        Get the dominant color from image bytes.

        Args:
            image_bytes: Image file bytes

        Returns:
            RGB tuple of dominant color
        """
        color_thief = ColorThief(BytesIO(image_bytes))
        return color_thief.get_color(quality=1)

    @staticmethod
    def get_dominant_color_from_rgba(
        image: Image.Image,
        alpha_threshold: int = 128
    ) -> tuple[int, int, int]:
        """
        Extract dominant color from RGBA image, ignoring transparent pixels.

        This method analyzes only the non-transparent (product) pixels,
        giving accurate color extraction after background removal.

        Args:
            image: PIL RGBA Image (background removed)
            alpha_threshold: Minimum alpha value to consider pixel (0-255)

        Returns:
            RGB tuple of dominant color from non-transparent pixels
        """
        # Ensure RGBA mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Get all pixel data
        pixels = list(image.getdata())

        # Filter to only non-transparent pixels
        opaque_pixels = [
            (r, g, b) for r, g, b, a in pixels
            if a >= alpha_threshold
        ]

        if not opaque_pixels:
            # Fallback if no opaque pixels found
            return (128, 128, 128)  # Neutral gray

        # Create a temporary image from opaque pixels for quantization
        temp_size = int(len(opaque_pixels) ** 0.5) + 1
        temp_img = Image.new("RGB", (temp_size, temp_size), (255, 255, 255))
        temp_pixels = temp_img.load()

        # Fill temporary image with opaque pixels
        for i, (r, g, b) in enumerate(opaque_pixels):
            if i >= temp_size * temp_size:
                break
            x = i % temp_size
            y = i // temp_size
            temp_pixels[x, y] = (r, g, b)

        # Quantize to reduce to dominant colors
        quantized = temp_img.quantize(colors=5, method=Image.Quantize.MEDIANCUT)

        # Get the palette and find most common color
        palette = quantized.getpalette()
        color_counts = {}

        for pixel in quantized.getdata():
            idx = pixel * 3
            color = (palette[idx], palette[idx + 1], palette[idx + 2])
            color_counts[color] = color_counts.get(color, 0) + 1

        # Return most frequent color
        dominant = max(color_counts.items(), key=lambda x: x[1])[0]
        return dominant

    @staticmethod
    def select_overlay_color(product_rgb: tuple[int, int, int]) -> tuple[tuple[int, int, int], str]:
        """
        Select a solid overlay color based on product lightness (contrast logic).

        Light product → Dark overlay (Bottle Green)
        Dark product → Light overlay (Sky Blue)

        Args:
            product_rgb: RGB tuple of product's dominant color

        Returns:
            Tuple of (RGB color tuple, color name)
        """
        # Calculate lightness using HLS
        r, g, b = [x / 255.0 for x in product_rgb]
        _, lightness, _ = colorsys.rgb_to_hls(r, g, b)

        # Get overlay options from settings
        overlays = settings.SOLID_OVERLAYS

        if lightness > 0.5:
            # Light product → Dark overlay (last in list)
            return overlays[-1]
        else:
            # Dark product → Light overlay (first in list)
            return overlays[0]
