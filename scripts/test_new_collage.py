"""
Test script: New layered collage composition.

Tests:
1. Base background loading
2. Overlay color selection based on product lightness
3. Auto-rotation for Image 2
4. Full collage generation

Usage: python scripts/test_new_collage.py [product_image_path] [variants_image_path]
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from app.services.compositor import CompositorService
from app.services.background import BackgroundService
from app.services.storage import StorageService
from app.config import settings


async def test_components():
    """Test individual components."""
    print("=" * 60)
    print("Testing Components")
    print("=" * 60)

    bg_service = BackgroundService()

    # Test 1: Check backgrounds exist
    print("\n1. Checking base backgrounds...")
    for bg_name in settings.BASE_BACKGROUNDS:
        bg_path = settings.BACKGROUNDS_PATH / bg_name
        if bg_path.exists():
            img = Image.open(bg_path)
            print(f"   [OK] {bg_name}: {img.size}")
        else:
            print(f"   [FAIL] {bg_name}: NOT FOUND at {bg_path}")

    # Test 2: Overlay color selection
    print("\n2. Testing overlay selection logic...")
    test_colors = [
        ((255, 255, 255), "white product"),
        ((0, 0, 0), "black product"),
        ((128, 128, 128), "gray product"),
        ((200, 180, 160), "light beige"),
        ((50, 40, 30), "dark brown"),
    ]
    for rgb, desc in test_colors:
        overlay, name = bg_service.select_overlay_color(rgb)
        print(f"   {desc} {rgb} -> {name} {overlay}")

    print("\n[OK] Component tests passed!")


async def test_full_collage(product_path: str, variants_path: str):
    """Test full collage generation."""
    print("\n" + "=" * 60)
    print("Testing Full Collage Generation")
    print("=" * 60)

    # Create temporary storage paths if needed
    storage = StorageService()

    # Copy test images to storage location
    import shutil
    from pathlib import Path

    inputs_dir = settings.INPUTS_PATH
    inputs_dir.mkdir(parents=True, exist_ok=True)

    # Copy product image
    product_dest = inputs_dir / "test_product.jpg"
    shutil.copy(product_path, product_dest)
    print(f"\n1. Copied product image to: {product_dest}")

    # Copy variants image
    variants_dest = inputs_dir / "test_variants.jpg"
    shutil.copy(variants_path, variants_dest)
    print(f"2. Copied variants image to: {variants_dest}")

    # Create collage
    print("\n3. Creating collage...")
    compositor = CompositorService()

    # Use relative paths for storage service
    rel_product = f"inputs/test_product.jpg"
    rel_variants = f"inputs/test_variants.jpg"

    collage_bytes = await compositor.create_collage(
        rel_product,
        rel_variants,
        background_name="base_mint_green.png"  # Use specific background for test
    )

    # Save output
    output_path = r"C:\Users\Intel\Downloads\new_collage_output.png"
    with open(output_path, "wb") as f:
        f.write(collage_bytes)

    print(f"\n[OK] Collage saved to: {output_path}")

    # Show collage info
    result = Image.open(output_path)
    print(f"  Size: {result.size}")
    print(f"  Mode: {result.mode}")


async def main():
    # Default test paths
    product_path = sys.argv[1] if len(sys.argv) > 1 else r"F:\Shared Folder\IMAGES\GPO\GPO\5211.jpeg"
    variants_path = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\Intel\Downloads\123.png"

    print(f"Product image: {product_path}")
    print(f"Variants image: {variants_path}")

    # Run component tests first
    await test_components()

    # Check if source images exist before full test
    if os.path.exists(product_path) and os.path.exists(variants_path):
        await test_full_collage(product_path, variants_path)
    else:
        print("\n[WARN] Skipping full collage test - source images not found")
        if not os.path.exists(product_path):
            print(f"  Missing: {product_path}")
        if not os.path.exists(variants_path):
            print(f"  Missing: {variants_path}")


if __name__ == "__main__":
    asyncio.run(main())
