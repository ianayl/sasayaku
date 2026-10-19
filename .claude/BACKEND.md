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
- `server/videos/download.py` — `yt-dlp` audio extraction (`download_audio` returns the real output path, raises on failure)
- `server/videos/storage.py` — `JobPaths`: **single source of truth** for on-disk layout. Never build artifact paths elsewhere.
- `server/videos/whisper.py` — WhisperX model loading (`load_model`) & transcription/SRT generation (`generate_subtitles`, raises on failure)
- `server/workers/job.py` — `Job`: unit of work flowing through the pipeline; carries `JobPaths` and produced artifacts (`audio_path`, `srt_path`)
- `server/workers/stage_worker.py` — `StageWorker` base thread: queue loop, status transitions, failure handling. Subclasses implement `handle(job)`.
- `server/workers/download_worker.py`, `server/workers/transcribe_worker.py` — concrete pipeline stages
- `server/workers/taskmaster.py` — `Taskmaster`: owns per-stage queues, wires each stage's output into the next stage (`DEFAULT_PIPELINE`)
- `server/asbplayer/` — `asbplayer` upload integration
- `utils/config.py` — Configuration definitions (`whisper`, `downloads`, `asbplayer`)

## On-disk Layout (see `JobPaths`)
- `<downloads_path>/<source>/<video_id>/audio.mp3` — shared per `video_id`, replaced on each request
- `<downloads_path>/<source>/<video_id>/<db_id>.srt` — per job

## Pipeline
`routes` → `taskmaster.submit()` → `DownloadWorker` → `TranscribeWorker`. Stages never reference each other; the
Taskmaster routes the `Job` between queues. To add a stage, subclass `StageWorker` (set `stage_name`,
`running_status`, `done_status`, `failed_status`) and append it to `DEFAULT_PIPELINE`.

## Database Schema
- Database schema for `Video` is stored in `server/videos/video.py`

## Data Flow
1. **Registration**: YouTube URL -> `Video` object -> SQLite (`status: pending_download`).
2. **Download**: Fetch audio -> Save to local path -> Update DB.
3. **Transcription**: WhisperX processes audio -> Save resulting `.srt` -> Update DB (`status: finished`).
4. **Delivery**: Push `.srt` to `asbplayer` (Not yet implemented).

## Logging Rules
- **Logging**: Use `diag = utils.gen_diag("component_name")` from `server/utils/utils.py` for all server-side logging. `component_name` should represent the specific subsystem or worker being updated (e.g., "routes", "taskmaster", "download").
