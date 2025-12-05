# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
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
   - `BackgroundService.get_dominant_color()` → ColorThief extracts product color
   - `BackgroundService.get_contrast_background()` → HLS color space calculation
   - `CompositorService.create_collage()` → Final composition

### Canvas Layout

```
1920x1080 canvas with 80px border, 40px divider
+--------------------------------------------------+
|                    80px BORDER                    |
+------+------------+----+-------------------------+
|      |            |    |                         |
| 80px |  IMAGE 1   |40px|       IMAGE 2           |
|      |  430x920   |DIV |       1290x920          |
|      | (25% w/BG) |    |    (75% as-is)          |
+------+------------+----+-------------------------+
|                    80px BORDER                    |
+--------------------------------------------------+
```

- **Image 1**: Background removed, placed on contrast-colored solid background
- **Image 2**: Kept as-is, stretched to fill

### Key Services

| Service | File | Purpose |
|---------|------|---------|
| `BackgroundService` | `app/services/background.py` | BG removal (Replicate), color extraction, contrast calculation |
| `CompositorService` | `app/services/compositor.py` | Layout calculation, image compositing, border drawing |
| `StorageService` | `app/services/storage.py` | File I/O, path management, URL generation |

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
