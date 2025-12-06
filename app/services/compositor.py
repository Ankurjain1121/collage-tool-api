import random
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from app.config import settings
from app.services.background import BackgroundService
from app.services.storage import StorageService


class CompositorService:
    """Create the final collage image with layered composition."""

    def __init__(self):
        self.bg_service = BackgroundService()
        self.storage_service = StorageService()

    def _calculate_layout(self) -> dict:
        """
        Calculate box dimensions and positions for the new layered layout.

        Layout:
        - Canvas: 1920x1080
        - Border: 50px all edges (base background visible)
        - Gap: 15px between boxes (base background visible)
        - Image 1 box: ~25% width (solid color overlay)
        - Image 2 area: ~75% width (directly on base background)

        Returns:
            dict with layout measurements
        """
        canvas_w = settings.CANVAS_WIDTH
        canvas_h = settings.CANVAS_HEIGHT
        border = settings.BORDER_THICKNESS
        gap = settings.GAP_THICKNESS

        # Usable space after borders
        usable_w = canvas_w - (border * 2) - gap
        usable_h = canvas_h - (border * 2)

        # Section widths based on ratio
        img1_w = int(usable_w * settings.IMAGE1_WIDTH_RATIO)
        img2_w = usable_w - img1_w

        return {
            "canvas_w": canvas_w,
            "canvas_h": canvas_h,
            "border": border,
            "gap": gap,
            "img1_box": (img1_w, usable_h),      # ~430x920
            "img2_box": (img2_w, usable_h),      # ~1290x920
            "img1_pos": (border, border),         # (80, 80)
            "img2_pos": (border + img1_w + gap, border),  # (80 + 430 + 30, 80)
        }

    def _load_base_background(self, background_name: str = None) -> Image.Image:
        """
        Load a base background from assets.

        Args:
            background_name: Specific background filename, or None for random

        Returns:
            PIL Image of base background (1920x1080)
        """
        if background_name is None:
            background_name = random.choice(settings.BASE_BACKGROUNDS)

        bg_path = settings.BACKGROUNDS_PATH / background_name
        return Image.open(bg_path).convert("RGB")

    def _should_rotate(self, image: Image.Image, target_box: tuple[int, int]) -> bool:
        """
        Check if rotating the image 90° would better fit the target box.

        Args:
            image: PIL Image to check
            target_box: (width, height) of target area

        Returns:
            True if rotation would improve fit
        """
        img_aspect = image.width / image.height
        box_aspect = target_box[0] / target_box[1]
        rotated_aspect = image.height / image.width

        # Check which orientation matches better
        current_diff = abs(img_aspect - box_aspect)
        rotated_diff = abs(rotated_aspect - box_aspect)

        return rotated_diff < current_diff

    def _fit_and_center(
        self,
        image: Image.Image,
        target_size: tuple[int, int],
        bg_color: tuple[int, int, int]
    ) -> Image.Image:
        """
        Crop image to fill target box completely (no padding).

        Uses crop-to-fill approach: scales to cover the box completely,
        then center-crops to exact dimensions.

        Args:
            image: PIL Image to resize (can be RGBA with transparency)
            target_size: (width, height) box to fill
            bg_color: Background color for the box

        Returns:
            PIL Image cropped to fill, composited on solid color background
        """
        target_w, target_h = target_size
        img_w, img_h = image.size

        # Create background canvas at target size
        canvas = Image.new("RGB", target_size, bg_color)

        # Use MAX ratio to COVER the box (crop-to-fill)
        ratio = max(target_w / img_w, target_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        # Resize with high quality
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Center crop coordinates
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        cropped = resized.crop((left, top, left + target_w, top + target_h))

        # Paste with transparency mask if RGBA
        if cropped.mode == "RGBA":
            canvas.paste(cropped, (0, 0), cropped)
        else:
            canvas.paste(cropped, (0, 0))

        return canvas

    def _fit_to_box(
        self,
        image: Image.Image,
        target_size: tuple[int, int]
    ) -> Image.Image:
        """
        Stretch image to exactly fill target box (no gaps, no cropping).

        Stretches Image 2 (variants) to fill the box completely.
        Returns RGB image stretched to exact target_size.

        Args:
            image: PIL Image to resize
            target_size: (width, height) box to fill

        Returns:
            PIL Image (RGB) stretched to exact target_size
        """
        # Convert to RGB
        if image.mode == "RGBA":
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, (0, 0), image)
            image = bg
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Stretch to exact target size
        return image.resize(target_size, Image.Resampling.LANCZOS)

    async def create_collage(
        self,
        image1_path: str,
        image2_path: str,
        background_name: str = None
    ) -> bytes:
        """
        Create the final collage with layered composition.

        Layers (bottom to top):
        1. Base background (pastel + geometric patterns)
        2. Solid color box at Image 1 position
        3. Product image (bg removed, fit & centered)
        4. Image 2 (auto-rotated if needed, fit to box, directly on base)

        Args:
            image1_path: Relative path to product image
            image2_path: Relative path to color variants image
            background_name: Optional specific background filename

        Returns:
            PNG image bytes
        """
        # Calculate layout
        layout = self._calculate_layout()

        # Layer 1: Load base background
        canvas = self._load_base_background(background_name)

        # Load images
        img1_full_path = self.storage_service.get_full_path(image1_path)
        img2_full_path = self.storage_service.get_full_path(image2_path)

        # Process Image 1: Remove BG, select overlay color, fit & center
        with open(img1_full_path, "rb") as f:
            img1_bytes = f.read()

        # Remove background (async Replicate API call)
        img1_nobg = await self.bg_service.remove_background(img1_bytes)

        # Get dominant color from background-removed image (product pixels only)
        dominant_color = self.bg_service.get_dominant_color_from_rgba(img1_nobg)
        overlay_color, overlay_name = self.bg_service.select_overlay_color(dominant_color)

        # Layer 2 & 3: Create solid color box with product centered
        img1_processed = self._fit_and_center(
            img1_nobg,
            layout["img1_box"],
            overlay_color
        )

        # Process Image 2: Auto-rotate if better fit, then fit to box
        img2 = Image.open(img2_full_path).convert("RGBA")

        # Check if rotation would improve fit
        if self._should_rotate(img2, layout["img2_box"]):
            img2 = img2.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)

        # Fit to box (crop-to-fill, returns RGB)
        img2_fitted = self._fit_to_box(img2, layout["img2_box"])

        # Layer 4: Place Image 2 on base background (crop-to-fill, no transparency)
        canvas.paste(img2_fitted, layout["img2_pos"])

        # Place Image 1 solid box (overwrites base background in that area)
        canvas.paste(img1_processed, layout["img1_pos"])

        # Apply final enhancement (sharpening, contrast, saturation)
        canvas = self._enhance_image(canvas)

        # Export as PNG (lossless format, optimize=False for speed)
        output = BytesIO()
        canvas.save(output, format="PNG", optimize=False)
        output.seek(0)
        return output.read()

    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """
        Apply subtle enhancements to restore clarity after resize operations.

        Enhancements:
        1. Slight sharpening (UnsharpMask) - restores detail lost during resize
        2. Subtle contrast boost - makes colors pop
        3. Light saturation increase - more vibrant appearance

        Args:
            image: PIL Image to enhance

        Returns:
            Enhanced PIL Image
        """
        # 1. Sharpening - subtle unsharp mask to restore detail
        sharpened = image.filter(
            ImageFilter.UnsharpMask(radius=1.5, percent=50, threshold=3)
        )

        # 2. Contrast boost (1.0 = original, 1.08 = 8% increase)
        contrast_enhancer = ImageEnhance.Contrast(sharpened)
        contrasted = contrast_enhancer.enhance(1.08)

        # 3. Saturation boost (1.0 = original, 1.12 = 12% increase)
        color_enhancer = ImageEnhance.Color(contrasted)
        enhanced = color_enhancer.enhance(1.12)

        return enhanced

    def _stretch_to_fill(
        self,
        image: Image.Image,
        target_size: tuple[int, int],
        bg_color: tuple[int, int, int] = None
    ) -> Image.Image:
        """
        Stretch image to exactly fill target size (legacy method).

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
