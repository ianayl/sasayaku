import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from utils.config import CONFIG
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
    metadata: Optional["VideoMetadata"] = None
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

        metadata = None
        if "metadata_video_id" in row.keys() and row["metadata_video_id"] is not None:
            metadata = VideoMetadata.from_joined_row(row)

        return cls(
            id=row["id"],
            video_id=row["video_id"],
            video_source=VideoSource(row["video_source"]),
            tab_id=row["tab_id"],
            status=VideoStatus(row["status"]),
            pending_download_at=datetime.fromisoformat(row["pending_download_at"]),
            metadata=metadata,
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
            "metadata": self.metadata.to_dict() if self.metadata else None,
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


@dataclass
class VideoMetadata:
    video_id: str
    video_source: VideoSource
    title: Optional[str]
    author: Optional[str]
    metadata_date: Optional[datetime]
    thumbnail_url: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.video_source, str):
            self.video_source = VideoSource(self.video_source)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "VideoMetadata":
        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(val) if val else None

        return cls(
            video_id=row["video_id"],
            video_source=VideoSource(row["video_source"]),
            title=row["title"],
            author=row["author"],
            metadata_date=parse_dt(row["metadata_date"]),
        )

    @classmethod
    def from_joined_row(cls, row: sqlite3.Row) -> "VideoMetadata":
        def parse_dt(val: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(val) if val else None

        return cls(
            video_id=row["metadata_video_id"],
            video_source=VideoSource(row["metadata_video_source"]),
            title=row["metadata_title"],
            author=row["metadata_author"],
            metadata_date=parse_dt(row["metadata_date"]),
        )

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "video_source": self.video_source.value,
            "title": self.title,
            "author": self.author,
            "metadata_date": (
                self.metadata_date.isoformat() if self.metadata_date else None
            ),
            "thumbnail_url": self.thumbnail_url,
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

    def videos_table_schema(table_name: str) -> str:
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

    def video_metadata_table_schema(table_name: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            video_id TEXT(11) NOT NULL,
            video_source TEXT NOT NULL,
            title TEXT,
            author TEXT,
            metadata_date TIMESTAMP,
            PRIMARY KEY (video_source, video_id),
            CHECK (video_source IN ('youtube'))
        )
        """

    def create_indexes(cursor, table_name: str):
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_video_id ON {table_name}(video_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)")

    try:
        with _get_cursor() as cursor:
            cursor.execute(videos_table_schema("videos"))
            cursor.execute(video_metadata_table_schema("video_metadata"))
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


def get_videos_by_id(video_id: str, video_source: VideoSource, limit: int = 50,
                     offset: int = 0) -> list[Video]:
    """Fetches all video records for a given video_id and video_source."""
    video_source = utils.enforce_enum(VideoSource, video_source,
                                      "get_videos_by_id")

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM videos
                WHERE video_id = ? AND video_source = ?
                ORDER BY pending_download_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (video_id, video_source.value, limit, offset)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(
            f"get_videos_by_id: Failed to fetch videos for {video_id} ({video_source.value}): {e}"
        )
        raise


def get_videos_by_status(status: VideoStatus, limit: int = 50, offset: int = 0) -> list[Video]:
    """Fetches all videos matching a specific status."""
    status = utils.enforce_enum(VideoStatus, status, "get_videos_by_status")

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM videos WHERE status = ? ORDER BY pending_download_at DESC, id DESC LIMIT ? OFFSET ?",
                (status.value, limit, offset)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(
            f"get_videos_by_status: Failed to fetch videos with status '{status.value}': {e}"
        )
        raise


def get_all_videos(limit: int = 20, offset: int = 0) -> list[Video]:
    """Fetches all videos, sorted newest first."""
    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    v.id AS id,
                    v.video_id AS video_id,
                    v.video_source AS video_source,
                    v.tab_id AS tab_id,
                    v.status AS status,
                    v.pending_download_at AS pending_download_at,
                    v.pending_processing_at AS pending_processing_at,
                    v.finished_at AS finished_at,
                    v.processing_time AS processing_time,
                    m.video_id AS metadata_video_id,
                    m.video_source AS metadata_video_source,
                    m.title AS metadata_title,
                    m.author AS metadata_author,
                    m.metadata_date AS metadata_date
                FROM videos v
                LEFT JOIN video_metadata m
                    ON m.video_source = v.video_source
                   AND m.video_id = v.video_id
                ORDER BY pending_download_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(f"get_all_videos: Failed to fetch all videos: {e}")
        raise


# TODO: I may not need this
def get_non_fail_videos(limit: int = 50, offset: int = 0) -> list[Video]:
    """Fetches all videos that have not failed downloading or processing."""
    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM videos
                WHERE status NOT IN ('download_failed', 'processing_failed')
                ORDER BY pending_download_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [Video.from_row(row) for row in rows]
    except Exception as e:
        diag.error(f"get_non_fail_videos: Failed to fetch non-fail videos: {e}")
        raise


def get_video_count() -> int:
    """Get number of videos."""
    try:
        with _get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM videos")
            res = cursor.fetchone()
            return res[0] if res else 0
    except Exception as e:
        diag.error(f"get_video_count: Failed to fetch video count: {e}")
        raise


def upsert_video_metadata(
    video_id: str,
    video_source: VideoSource,
    title: Optional[str],
    author: Optional[str],
    metadata_date: Optional[datetime],
) -> None:
    """Stores the latest metadata snapshot for a video."""
    video_source = utils.enforce_enum(VideoSource, video_source, "upsert_video_metadata")
    metadata_date_value = metadata_date.isoformat() if metadata_date else None

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO video_metadata (
                    video_id, video_source, title, author, metadata_date
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(video_source, video_id) DO UPDATE SET
                    title = excluded.title,
                    author = excluded.author,
                    metadata_date = excluded.metadata_date
                """,
                (
                    video_id,
                    video_source.value,
                    title,
                    author,
                    metadata_date_value,
                ),
            )
    except Exception as e:
        diag.error(
            f"upsert_video_metadata: Failed to store metadata for {video_source.value}:{video_id}: {e}"
        )
        raise


def get_video_metadata(
    video_id: str, video_source: VideoSource
) -> Optional[VideoMetadata]:
    """Fetches the latest metadata snapshot for a video."""
    video_source = utils.enforce_enum(VideoSource, video_source, "get_video_metadata")

    try:
        with _get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM video_metadata
                WHERE video_id = ? AND video_source = ?
                """,
                (video_id, video_source.value),
            )
            row = cursor.fetchone()
            return VideoMetadata.from_row(row) if row else None
    except Exception as e:
        diag.error(
            f"get_video_metadata: Failed to fetch metadata for {video_source.value}:{video_id}: {e}"
        )
        raise
