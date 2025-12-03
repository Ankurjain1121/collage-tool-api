# Collage Tool API

Product collage generator with automatic background removal. Built with FastAPI.

## Features

- **Background Removal**: Automatically removes product backgrounds using rembg
- **Color Extraction**: Extracts dominant colors using ColorThief
- **Smart Backgrounds**: Creates pastel backgrounds based on product colors
- **Collage Generation**: Creates 1920x1080 collages with 25%/75% split layout
- **Session Management**: Tracks collage creation sessions per user
- **Border Overlays**: Supports custom border designs

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database for session tracking
- **rembg** - AI-powered background removal
- **Pillow** - Image processing
- **Docker** - Containerized deployment

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/info` | GET | API configuration |
| `/api/collage/session` | POST | Create new session |
| `/api/collage/session/{user_id}` | GET | Get active session |
| `/api/collage/upload` | POST | Upload image |
| `/api/collage/process` | POST | Generate collage |
| `/api/collage/borders` | GET | List available borders |

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL
- Docker (optional)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/collage_db"
export STORAGE_PATH="/var/www/collage"
export BASE_URL="http://localhost:8000"

# Run server
uvicorn app.main:app --reload
```

### Docker Deployment

```bash
docker-compose up --build -d
```

## Database Setup

```sql
CREATE DATABASE collage_db;
CREATE USER collage_user WITH PASSWORD 'your_password';
GRANT ALL ON DATABASE collage_db TO collage_user;

-- Create table
CREATE TABLE collage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slack_user_id TEXT NOT NULL,
    slack_channel_id TEXT NOT NULL,
    slack_thread_ts TEXT,
    status TEXT NOT NULL DEFAULT 'awaiting_image1',
    image1_path TEXT,
    image2_path TEXT,
    output_path TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `STORAGE_PATH` | `/var/www/collage` | File storage path |
| `BASE_URL` | `https://collage.paraslace.in` | Public URL |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |

## Workflow

1. Create session with Slack user/channel info
2. Upload product closeup image (image 1)
3. Upload color variants image (image 2)
4. Call process endpoint to generate collage
5. Get output URL from response

## License

MIT
