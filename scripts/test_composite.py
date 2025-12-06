"""
Test script: Remove background from product image and place on custom background.

Usage: python test_composite.py <product_image_path>
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from io import BytesIO
from app.services.background import BackgroundService
from app.config import settings

async def main():
    # Paths
    # Default paths
    product_image_path = sys.argv[1] if len(sys.argv) > 1 else r"F:\Shared Folder\IMAGES\GPO\GPO\5211.jpeg"
    background_path = r"C:\Users\Intel\Downloads\123.png"
    output_path = r"C:\Users\Intel\Downloads\composite_output.png"

    print(f"Loading product image from: {product_image_path}")
    with open(product_image_path, "rb") as f:
        product_bytes = f.read()

    print("Removing background using Replicate API...")
    bg_service = BackgroundService()
    product_nobg = await bg_service.remove_background(product_bytes)
    print(f"Background removed. Image size: {product_nobg.size}, mode: {product_nobg.mode}")

    print(f"Loading background image from: {background_path}")
    background = Image.open(background_path).convert("RGBA")
    print(f"Background size: {background.size}")

    # Resize product to fit nicely on background (e.g., 70% of background height)
    target_height = int(background.height * 0.7)
    aspect_ratio = product_nobg.width / product_nobg.height
    target_width = int(target_height * aspect_ratio)

    product_resized = product_nobg.resize((target_width, target_height), Image.Resampling.LANCZOS)
    print(f"Resized product to: {product_resized.size}")

    # Center the product on the background
    x = (background.width - product_resized.width) // 2
    y = (background.height - product_resized.height) // 2

    # Save the background-removed image first
    nobg_output_path = r"C:\Users\Intel\Downloads\nobg_output.png"
    product_nobg.save(nobg_output_path, "PNG")
    print(f"Saved background-removed image to: {nobg_output_path}")

    # Composite
    result = background.copy()
    result.paste(product_resized, (x, y), product_resized)

    # Save as RGB (PNG)
    result_rgb = result.convert("RGB")
    result_rgb.save(output_path, "PNG")
    print(f"\nSuccess! Saved composite to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
