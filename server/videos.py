import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from server.utils.config import CONFIG
import utils


diag = utils.gen_diag("videos")
DB_PATH = Path(CONFIG("downloads.downloads_path")) / "sasayaku.db"


class VideoStatus(str, Enum):
    PENDING_DOWNLOAD = 'pending_download'
    DOWNLOAD_FAILED = 'download_failed'
    PENDING_PROCESSING = 'pending_processing'
    PROCESSING = 'processing'
    PROCESSING_FAILED = 'processing_failed'
    FINISHED = 'finished'
    CANCELLED = 'cancelled'


class VideoSource(str, Enum):
    YOUTUBE = 'youtube'


@dataclass
class Video:
    video_id: str
    video_source: VideoSource
    tab_id: int
    status: VideoStatus
    pending_download_at: datetime
    id: Optional[int] = None
    pending_processing_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    processing_time: Optional[int] = None

    def __post_init__(self):
        """Coerce strings to Enums if passed directly."""
        if isinstance(self.status, str):
            self.status = VideoStatus(self.status)
        if isinstance(self.video_source, str):
            self.video_source = VideoSource(self.video_source)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Video":
        """Constructs a Video instance directly from a sqlite3.Row object."""
        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(val) if val else None

        return cls(
            id=row["id"],
            video_id=row["video_id"],
            video_source=VideoSource(row["video_source"]),
            tab_id=row["tab_id"],
            status=VideoStatus(row["status"]),
            pending_download_at=datetime.fromisoformat(row["pending_download_at"]),
            pending_processing_at=parse_dt(row["pending_processing_at"]),
            finished_at=parse_dt(row["finished_at"]),
            processing_time=row["processing_time"],
        )

    def to_dict(self) -> dict:
        """Serializes the model for JSON responses or logging."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "video_source": self.video_source.value,
            "tab_id": self.tab_id,
            "status": self.status.value,
            "pending_download_at": self.pending_download_at.isoformat(),
            "pending_processing_at": (
                self.pending_processing_at.isoformat()
                if self.pending_processing_at
                else None
            ),
            "finished_at": (
                self.finished_at.isoformat() if self.finished_at else None
            ),
            "processing_time": self.processing_time,
        }


@contextmanager
def _get_cursor():
    """Context manager that handles connection, transaction commit/rollback, and closing."""
    conn = sqlite3.connect(str(DB_PATH))
    # Return queries as sqlite3.Row object instead of a tuple.
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # Automatically commits on success or rolls back on exception
            yield conn.cursor()
    finally:
        conn.close()  # Guarantees the connection closes


def init_db():
    """Initializes the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    def table_schema(table_name: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT(11) NOT NULL,
            video_source TEXT NOT NULL,
            tab_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            pending_download_at TIMESTAMP NOT NULL,
            pending_processing_at TIMESTAMP,
            finished_at TIMESTAMP,
            processing_time INTEGER,
            CHECK (status IN ('pending_download', 'download_failed', 'pending_processing', 'processing', 'processing_failed', 'finished', 'cancelled'))
            CHECK (video_source IN ('youtube'))
        )
        """
        # TODO also store video transcription options and metadata 
        # this might get hectic, we'll also want to support translations.

    def create_indexes(cursor, table_name: str):
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_video_id ON {table_name}(video_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)")

    try:
        with _get_cursor() as cursor:
            cursor.execute(table_schema("videos"))
            create_indexes(cursor, "videos")
        diag.info(f"init_db: database initialized at {DB_PATH}.")
    except (sqlite3.Error, OSError) as e:
        diag.error(f"init_db: Failed to initialize database: {e}")
        raise


# TODO: multiple video_id entries can exist!!!
# - within sasayaku/videos/<video_id> should contain 1 audio file
#  - audio file gets replaced with every request
#  - subtitles are identified by BOTH video_id and id
#  - we do not allow 2 downloads of the same video_id at the same time; you can cancel
#    and redo a video download

# - if a video was cancelled during subtitle generation, any generated file should be
#   discarded
def register_video(video_id: str, video_source: VideoSource, tab_id: int) -> int:
    """Registers a new video for processing and returns its new internal ID."""
    video_source = utils.enforce_enum(VideoSource, video_source, "register_video")

    now = utils.get_now_iso()
    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    video_id,
                    video_source.value,
                    tab_id,
                    VideoStatus.PENDING_DOWNLOAD.value,
                    now,
                )
            )
            created_id = cursor.lastrowid

        diag.info(
            f"register_video: Successfully registered '{video_id}' with ID"
            f" {created_id}."
        )
        return created_id
    except Exception as e:
        diag.error(f"register_video: Failed to register video {video_id}: {e}")
        raise


def update_status(id: int, new_status: VideoStatus,
                  processing_time: Optional[int] = None) -> bool:
    """Updates the status (and relevant timestamps) of a video by its database ID."""
    new_status = utils.enforce_enum(VideoStatus, new_status, "update_status")

    now = utils.get_now_iso()
    timestamp_col_map = {
        VideoStatus.PENDING_DOWNLOAD: 'pending_download_at',
        VideoStatus.DOWNLOAD_FAILED: 'finished_at',
        VideoStatus.PENDING_PROCESSING: 'pending_processing_at',
        VideoStatus.PROCESSING: None,
        VideoStatus.PROCESSING_FAILED: 'finished_at',
        VideoStatus.FINISHED: 'finished_at',
        VideoStatus.CANCELLED: 'finished_at'
    }
    timestamp_col = timestamp_col_map[new_status]

    # Build query:
    set_clauses = ["status = ?"]
    params = [new_status.value]

    if timestamp_col:
        set_clauses.append(f"{timestamp_col} = ?")
        params.append(now)
    if processing_time:
        set_clauses.append("processing_time = ?")
        params.append(processing_time)

    params.append(id)
    query = f"UPDATE videos SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        with _get_cursor() as cursor:
            cursor.execute(query, params)
            if cursor.rowcount == 0:
                diag.warning(f"update_status: No record found for id {id}")
                return False
        diag.info(f"update_status: Video ID {id} status updated to '{new_status.value}'.")
        return True
    except Exception as e:
        diag.error(f"update_status: Failed to update status of video {id}: {e}")
        raise


def get_video(id: int) -> Optional[Video]:
    """Fetch a video by its database primary key ID."""
    try:
        with _get_cursor() as cursor:
            cursor.execute("SELECT * FROM videos WHERE id = ?", (id,))
            row = cursor.fetchone()
            return Video.from_row(row) if row else None
    except Exception as e:
        diag.error(f"get_video: Failed to fetch video with id {id}: {e}")
        raise


def get_videos_by_id(video_id: str, video_source: VideoSource) -> list[Video]:
    """Fetches all video records for a given video_id and video_source, sorted newest first."""
    video_source = utils.enforce_enum(VideoSource, video_source, "get_videos_by_id")

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM videos
                WHERE video_id = ? AND video_source = ?
                ORDER BY pending_download_at DESC, id DESC
                """,
                (video_id, video_source.value)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(f"get_videos_by_id: Failed to fetch videos for {video_id} ({video_source.value}): {e}")
        raise


def get_videos_by_status(status: VideoStatus) -> list[Video]:
    """Fetches all videos matching a specific status."""
    status = utils.enforce_enum(VideoStatus, status, "get_videos_by_status")

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM videos WHERE status = ? ORDER BY id ASC",
                (status.value,)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(f"get_videos_by_status: Failed to fetch videos with status '{status.value}': {e}")
        raise

