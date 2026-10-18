# Project Context & Agent Instructions

## Project Overview
Sasayaku: Whisper-based subtitle generation tool/pipeline, that interacts with asbplayer.
- **Frontend**: React Chrome Extension (in `/extension`). Interacts with backend.
- **Backend**: Python / Flask, WhisperX for transcription, SQLite database (in `/server`)

## Modular Context Index (`.claude/`)
Read these files ONLY when working in their respective domain:
- `.claude/FRONTEND.md` — Chrome extension architecture and guidance
- `.claude/BACKEND.md` — Flask backend architecture and guidance

## Universal Code Rules
1. **No Speculative Rewrites**: Edit only the specific lines or functions requested or directly affected. Do not rewrite surrounding unchanged boilerplate.
2. **Keep Context Clean**: Do not read full log files or whole sqlite databases into context; tail logs or query specific schema tables.
3. **Imports & Types**: Maintain TypeScript types on the frontend and Python type hints on the backend.
4. **Doc Maintenance**: Update (with user approval) `.claude/FRONTEND.md` or `.claude/BACKEND.md` when adding new files or changing file path and project architecture.
