# Backend Architecture (`/server`)

Flask-based Python backend that manages a pipeline to fetch YouTube videos, transcribe them into subtitles using WhisperX, and upload the results to an `asbplayer` instance.

## Tech Stack
- Framework: Flask, Flask-CORS, SQLite
- Transcription: WhisperX, Torch (CUDA)
- Downloader: `yt-dlp`

## Core Directory Map
- `server/main.py` — Entry point & DB initialization
- `server/backend.py` — App factory & blueprint registration
- `server/routes.py` — API routes (`/api/...`)
- `server/videos/video.py` — `Video` dataclass and **database schema**, status Enums, SQLite video operations.
- `server/videos/download.py` — `yt-dlp` audio extraction
- `server/videos/whisper.py` — WhisperX transcription & SRT generation
- `server/asbplayer/` — `asbplayer` upload integration
- `utils/config.py` — Configuration definitions (`whisper`, `downloads`, `asbplayer`)

## Database Schema
- Database schema for `Video` is stored in `server/videos/video.py`

## Data Flow
1. **Registration**: YouTube URL -> `Video` object -> SQLite (`status: pending_download`).
2. **Download**: Fetch audio -> Save to local path -> Update DB.
3. **Transcription**: WhisperX processes audio -> Save resulting `.srt` -> Update DB (`status: finished`).
4. **Delivery**: Push `.srt` to `asbplayer` (Not yet implemented).

## Logging Rules
- **Logging**: Use `diag = utils.gen_diag("component_name")` from `server/utils/utils.py` for all server-side logging. `component_name` should represent the specific subsystem or worker being updated (e.g., "routes", "taskmaster", "download").
