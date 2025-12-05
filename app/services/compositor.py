from PIL import Image
from io import BytesIO
from app.config import settings
from app.services.background import BackgroundService
from app.services.storage import StorageService


class CompositorService:
    """Create the final collage image."""

    def __init__(self):
        self.bg_service = BackgroundService()
        self.storage_service = StorageService()

    def _calculate_layout(self) -> dict:
        """
        Calculate inner box dimensions after borders/divider.

        Returns:
            dict with layout measurements:
            - canvas_w, canvas_h: Full canvas size (1920x1080)
            - border: Border thickness (80px)
            - divider: Divider thickness (40px)
            - img1_box: (width, height) for image 1 (430x920)
            - img2_box: (width, height) for image 2 (1290x920)
            - img1_pos: (x, y) position for image 1 (80, 80)
            - img2_pos: (x, y) position for image 2 (550, 80)
        """
        canvas_w = settings.CANVAS_WIDTH
        canvas_h = settings.CANVAS_HEIGHT
        border = settings.BORDER_THICKNESS
        divider = settings.DIVIDER_THICKNESS

        # Usable space after borders and divider
        usable_w = canvas_w - (border * 2) - divider
        usable_h = canvas_h - (border * 2)

        # Section widths based on ratio
        img1_w = int(usable_w * settings.IMAGE1_WIDTH_RATIO)
        img2_w = usable_w - img1_w

        return {
            "canvas_w": canvas_w,
            "canvas_h": canvas_h,
            "border": border,
            "divider": divider,
            "img1_box": (img1_w, usable_h),      # (430, 920)
            "img2_box": (img2_w, usable_h),      # (1290, 920)
            "img1_pos": (border, border),         # (80, 80)
            "img2_pos": (border + img1_w + divider, border),  # (550, 80)
        }

    async def create_collage(
        self,
        image1_path: str,
        image2_path: str
    ) -> bytes:
        """
        Create the final collage from two images.

        Layout (with 80px border, 40px divider):
        - Canvas: 1920x1080
        - Image 1: 430x920 @ position (80, 80) - product with contrast BG
        - Image 2: 1290x920 @ position (550, 80) - color variants as-is
        - Black border and divider drawn on top

        Args:
            image1_path: Relative path to product image
            image2_path: Relative path to color variants image

        Returns:
            PNG image bytes
        """
        # Calculate layout with borders
        layout = self._calculate_layout()

        # Load images
        img1_full_path = self.storage_service.get_full_path(image1_path)
        img2_full_path = self.storage_service.get_full_path(image2_path)

        # Process Image 1: Remove BG, add contrast background, stretch to fill
        with open(img1_full_path, "rb") as f:
            img1_bytes = f.read()

        # Remove background (async Replicate API call)
        img1_nobg = await self.bg_service.remove_background(img1_bytes)

        # Get dominant color and create contrast background
        dominant_color = self.bg_service.get_dominant_color(str(img1_full_path))
        bg_color = self.bg_service.get_contrast_background(dominant_color)

        # Stretch to fill image box exactly (430x920)
        img1_processed = self._stretch_to_fill(
            img1_nobg,
            layout["img1_box"],
            bg_color
        )

        # Process Image 2: Keep as-is, stretch to fill (1290x920)
        img2 = Image.open(img2_full_path).convert("RGB")
        img2_processed = self._stretch_to_fill(
            img2,
            layout["img2_box"]
        )

        # Create canvas with white background
        canvas = Image.new("RGB", (layout["canvas_w"], layout["canvas_h"]), (255, 255, 255))

        # Place images in their inner boxes
        canvas.paste(img1_processed, layout["img1_pos"])
        canvas.paste(img2_processed, layout["img2_pos"])

        # Draw black border and divider on top
        canvas = self._draw_border_and_divider(canvas, layout)

        # Export as PNG
        output = BytesIO()
        canvas.save(output, format="PNG", quality=95)
        output.seek(0)
        return output.read()

    def _stretch_to_fill(
        self,
        image: Image.Image,
        target_size: tuple[int, int],
        bg_color: tuple[int, int, int] = None
    ) -> Image.Image:
        """
        Stretch image to exactly fill target size.

        Args:
            image: PIL Image to resize
            target_size: (width, height) to fill exactly
            bg_color: Background color for RGBA images

        Returns:
            PIL Image stretched to exact target_size
        """
        # Handle transparent images (RGBA) - composite on background first
        if image.mode == "RGBA" and bg_color:
            background = Image.new("RGB", image.size, bg_color)
            background.paste(image, (0, 0), image)
            image = background

        # Convert to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Stretch to exact target size
        return image.resize(target_size, Image.Resampling.LANCZOS)

    def _fit_to_box(
        self,
        image: Image.Image,
        target_size: tuple[int, int],
        bg_color: tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        Fit image into target box maintaining aspect ratio, fill remaining space with bg_color.

        Args:
            image: PIL Image to resize
            target_size: (width, height) box to fit into
            bg_color: Background color to fill empty space

        Returns:
            PIL Image fitted to target_size with background color padding
        """
        target_w, target_h = target_size

        # Create background canvas at target size
        canvas = Image.new("RGB", target_size, bg_color)

        # Handle transparent images (RGBA) - resize first, then composite
        if image.mode == "RGBA":
            # Calculate size to fit while maintaining aspect ratio
            img_w, img_h = image.size
            ratio = min(target_w / img_w, target_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)

            # Resize with high quality
            resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Center on canvas
            x = (target_w - new_w) // 2
            y = (target_h - new_h) // 2

            # Paste with transparency mask
            canvas.paste(resized, (x, y), resized)
            return canvas

        # For RGB images
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Calculate size to fit while maintaining aspect ratio
        img_w, img_h = image.size
        ratio = min(target_w / img_w, target_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        # Resize with high quality
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Center on canvas
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        canvas.paste(resized, (x, y))

        return canvas

    def _draw_border_and_divider(self, canvas: Image.Image, layout: dict) -> Image.Image:
        """
        Draw solid black border and vertical divider on canvas.

        Args:
            canvas: Base canvas image
            layout: Layout measurements from _calculate_layout()

        Returns:
            Canvas with border and divider drawn
        """
        from PIL import ImageDraw

        draw = ImageDraw.Draw(canvas)
        color = settings.BORDER_COLOR
        b = layout["border"]
        w, h = layout["canvas_w"], layout["canvas_h"]

        # Draw outer borders (top, bottom, left, right)
        draw.rectangle([0, 0, w, b], fill=color)           # Top
        draw.rectangle([0, h - b, w, h], fill=color)       # Bottom
        draw.rectangle([0, 0, b, h], fill=color)           # Left
        draw.rectangle([w - b, 0, w, h], fill=color)       # Right

        # Draw vertical divider between image boxes
        div_x = b + layout["img1_box"][0]
        draw.rectangle([div_x, b, div_x + layout["divider"], h - b], fill=color)

        return canvas
