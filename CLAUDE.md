# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference (Current Implementation)

### Canvas Layout (CURRENT)
```
1920x1080 canvas with 25px border, 10px gap
+--------------------------------------------------+
|                    25px BORDER                    |
+------+------------+----+-------------------------+
|      |            |    |                         |
| 25px |  IMAGE 1   |10px|       IMAGE 2           |
|      |  ~465x1030 |GAP |       ~1400x1030        |
|      | (25% crop) |    |    (75% STRETCHED)      |
+------+------------+----+-------------------------+
|                    25px BORDER                    |
+--------------------------------------------------+
```

### Image Fitting Behaviors (CRITICAL)
| Image | Method | Behavior | Rationale |
|-------|--------|----------|-----------|
| Image 1 (Product) | `_fit_and_center()` | **Crop-to-fill** - scales to COVER box, center crops | Product should fill box without padding |
| Image 2 (Variants) | `_fit_to_box()` | **Stretch-to-fill** - stretches to EXACT size | Variants should fill completely, user prefers stretch over crop |

### Overlay Color Logic (CURRENT)
1. Remove background from Image 1 (product) via Replicate API
2. Extract dominant color from **RGBA image** (ignores transparent pixels)
3. Calculate lightness using HLS color space
4. Select overlay based on contrast:
   - **Light product (L > 0.5)** → Dark overlay (Bottle Green `#006A4E`)
   - **Dark product (L ≤ 0.5)** → Light overlay (Sky Blue `#87CEEB`)

### Configuration Values (`app/config.py`)
```python
BORDER_THICKNESS: int = 25    # Border on all edges
GAP_THICKNESS: int = 10       # Gap between Image 1 and Image 2
IMAGE1_WIDTH_RATIO: float = 0.25   # 25% for product
IMAGE2_WIDTH_RATIO: float = 0.75   # 75% for variants
```

### Solid Overlay Colors (light → dark)
| Color | RGB | Hex | Usage |
|-------|-----|-----|-------|
| Sky Blue | (135, 206, 235) | #87CEEB | Dark products |
| Cream | (255, 248, 220) | #FFF8DC | - |
| Tan | (210, 180, 140) | #D2B48C | - |
| Olive | (128, 128, 0) | #808000 | - |
| Bottle Green | (0, 106, 78) | #006A4E | Light products |

---

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test collage generation (local script)
python scripts/test_new_collage.py
```

## Environment Variables

Create `.env` in project root:
```
DATABASE_URL=sqlite:///path/to/collage.db   # or postgresql://...
REPLICATE_API_TOKEN=your_token
STORAGE_PATH=/path/to/storage
BASE_URL=http://localhost:8000
```

## Architecture

### Collage Generation Pipeline

1. **Session Creation** → User creates session via `/api/collage/session`
2. **Image Upload** → Two images uploaded (any order) via `/api/collage/upload`
3. **Processing** → `/api/collage/process` triggers:
   - `BackgroundService.remove_background()` → Replicate API (`lucataco/remove-bg`)
   - `BackgroundService.get_dominant_color_from_rgba()` → Extracts color from product (ignores transparent)
   - `BackgroundService.select_overlay_color()` → Contrast-based overlay selection
   - `CompositorService.create_collage()` → Final composition with layered approach

### Layered Composition (Bottom to Top)
1. **Base background** - Pastel with geometric patterns (from `assets/backgrounds/`)
2. **Image 2** - Stretched to fill right section (75% width)
3. **Solid color box** - At Image 1 position with selected overlay color
4. **Product image** - Background removed, crop-to-fill on solid color

### Key Services

| Service | File | Purpose |
|---------|------|---------|
| `BackgroundService` | `app/services/background.py` | BG removal, RGBA color extraction, contrast-based overlay selection |
| `CompositorService` | `app/services/compositor.py` | Layout calculation, crop-to-fill/stretch-to-fill, image enhancement |
| `StorageService` | `app/services/storage.py` | File I/O, path management, URL generation |

### Key Methods

| Method | File | Purpose |
|--------|------|---------|
| `get_dominant_color_from_rgba()` | background.py | Extract color from RGBA (product only, ignores transparent) |
| `select_overlay_color()` | background.py | Returns overlay color based on product lightness |
| `_fit_and_center()` | compositor.py | Crop-to-fill for Image 1 |
| `_fit_to_box()` | compositor.py | Stretch-to-fill for Image 2 |
| `_enhance_image()` | compositor.py | Sharpening, contrast (+8%), saturation (+12%) |

### Data Flow

```
Request → Router (app/routers/collage.py)
       → Service Layer (app/services/)
       → Database (SQLAlchemy + SQLite/PostgreSQL)
       → Storage (filesystem via STORAGE_PATH)
```

### Session States

`awaiting_image1` → `awaiting_image2` → `processing` → `completed` | `failed`

## Database

- Uses SQLAlchemy with SQLite (local) or PostgreSQL (production)
- Session IDs are String(36) UUIDs for SQLite compatibility
- Tables auto-created on startup via `Base.metadata.create_all()`

## External API

Background removal uses Replicate API:
- Model: `lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1`
- Called async via `asyncio.run_in_executor()` since Replicate SDK is sync
- Token set via `REPLICATE_API_TOKEN` env var

## Assets

### Base Backgrounds (`assets/backgrounds/`)
- `base_light_pink.png` - Pink pastel with geometric patterns
- `base_mint_green.png` - Mint green pastel
- `base_powder_blue.png` - Light blue pastel
- `base_lavender.png` - Lavender pastel
- `base_cream.png` - Cream pastel

### Background Selection
- Random selection from available backgrounds
- Can specify via `background_name` parameter

---

## Troubleshooting

### Port Already in Use (WinError 10013)
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process by PID
Stop-Process -Id <PID> -Force
```

### Overlay Always Same Color
- Check if `get_dominant_color_from_rgba()` is being called (not `get_dominant_color_from_bytes()`)
- Verify color extraction happens AFTER background removal
- Check lightness calculation in `select_overlay_color()`

### Image Has Padding/Gaps
- Image 1: Uses crop-to-fill (max ratio) - should fill box
- Image 2: Uses stretch-to-fill (exact resize) - should fill box
- Check `BORDER_THICKNESS` and `GAP_THICKNESS` in config.py

### Image Enhancement
Applied in `_enhance_image()`:
- UnsharpMask: radius=1.5, percent=50, threshold=3
- Contrast: +8% (1.08)
- Saturation: +12% (1.12)
