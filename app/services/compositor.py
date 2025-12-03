from PIL import Image
from pathlib import Path
from io import BytesIO
from app.config import settings
from app.services.background import BackgroundService
from app.services.storage import StorageService


class CompositorService:
    """Create the final collage image."""

    def __init__(self):
        self.bg_service = BackgroundService()
        self.storage_service = StorageService()

    def create_collage(
        self,
        image1_path: str,
        image2_path: str,
        border_name: str = None
    ) -> bytes:
        """
        Create the final collage from two images.

        Layout:
        - Canvas: 1920x1080
        - Left 25% (480px): Image 1 (product with new BG)
        - Right 75% (1440px): Image 2 (color variants as-is)
        - Border overlay if provided

        Args:
            image1_path: Relative path to product image
            image2_path: Relative path to color variants image
            border_name: Optional border design name

        Returns:
            PNG image bytes
        """
        canvas_w = settings.CANVAS_WIDTH
        canvas_h = settings.CANVAS_HEIGHT

        # Calculate section widths
        img1_w = int(canvas_w * settings.IMAGE1_WIDTH_RATIO)  # 480px
        img2_w = canvas_w - img1_w  # 1440px

        # Load images
        img1_full_path = self.storage_service.get_full_path(image1_path)
        img2_full_path = self.storage_service.get_full_path(image2_path)

        # Process Image 1: Remove BG and add solid color
        with open(img1_full_path, "rb") as f:
            img1_bytes = f.read()

        # Remove background
        img1_nobg = self.bg_service.remove_background(img1_bytes)

        # Get dominant color and create background
        dominant_color = self.bg_service.get_dominant_color(str(img1_full_path))
        bg_color = self.bg_service.get_pastel_background(dominant_color)

        # Apply background and resize to fit section
        img1_processed = self._fit_image_to_section(
            img1_nobg,
            (img1_w, canvas_h),
            bg_color
        )

        # Process Image 2: Keep as-is, just resize to fit
        img2 = Image.open(img2_full_path).convert("RGB")
        img2_processed = self._fit_image_to_section(
            img2,
            (img2_w, canvas_h),
            fill_color=(255, 255, 255)  # White fill for any gaps
        )

        # Create canvas
        canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        # Place images
        canvas.paste(img1_processed, (0, 0))
        canvas.paste(img2_processed, (img1_w, 0))

        # Apply border if available
        if border_name:
            border_path = self.storage_service.get_border_path(border_name)
            if border_path.exists():
                canvas = self._apply_border(canvas, border_path)
        else:
            # Try default border
            default_border = self.storage_service.get_border_path("default.png")
            if default_border.exists():
                canvas = self._apply_border(canvas, default_border)

        # Export as PNG
        output = BytesIO()
        canvas.save(output, format="PNG", quality=95)
        output.seek(0)
        return output.read()

    def _fit_image_to_section(
        self,
        image: Image.Image,
        section_size: tuple[int, int],
        bg_color: tuple[int, int, int] = None,
        fill_color: tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        Fit an image into a section, maintaining aspect ratio.

        Args:
            image: PIL Image to fit
            section_size: (width, height) of target section
            bg_color: Background color for transparent images
            fill_color: Fill color for any gaps

        Returns:
            PIL Image sized exactly to section_size
        """
        section_w, section_h = section_size

        # Handle transparent images
        if image.mode == "RGBA" and bg_color:
            # Create background and composite
            background = Image.new("RGB", image.size, bg_color)
            background.paste(image, (0, 0), image)
            image = background

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Calculate aspect ratios
        img_ratio = image.width / image.height
        section_ratio = section_w / section_h

        if img_ratio > section_ratio:
            # Image is wider - fit to width
            new_w = section_w
            new_h = int(section_w / img_ratio)
        else:
            # Image is taller - fit to height
            new_h = section_h
            new_w = int(section_h * img_ratio)

        # Resize image
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Create section canvas and center image
        section = Image.new("RGB", (section_w, section_h), fill_color)
        offset_x = (section_w - new_w) // 2
        offset_y = (section_h - new_h) // 2
        section.paste(resized, (offset_x, offset_y))

        return section

    def _apply_border(self, canvas: Image.Image, border_path: Path) -> Image.Image:
        """
        Apply a border overlay to the canvas.

        Args:
            canvas: Base canvas image
            border_path: Path to border PNG with transparency

        Returns:
            Canvas with border applied
        """
        border = Image.open(border_path).convert("RGBA")

        # Resize border to match canvas if needed
        if border.size != canvas.size:
            border = border.resize(canvas.size, Image.Resampling.LANCZOS)

        # Convert canvas to RGBA for compositing
        canvas_rgba = canvas.convert("RGBA")

        # Composite border on top
        canvas_rgba.paste(border, (0, 0), border)

        # Convert back to RGB
        return canvas_rgba.convert("RGB")
