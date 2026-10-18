import pytest
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from server.videos import (
    Video,
    VideoStatus,
    VideoSource,
    init_db,
    get_all_videos,
    get_non_fail_videos,
    get_videos_by_status,
    get_videos_by_id
)

# Monkeypatch the DB_PATH to a temporary file for testing
TEST_DB_PATH = Path("./test_videos.db")

@pytest.fixture(autouse=True)
def setup_test_db():
    # Remove test db if it exists
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)

    # Point the module's DB_PATH to the test one
    # This works because we want to override the module-level variable
    import server.videos
    server.videos.DB_PATH = TEST_DB_PATH

    # Initialize the database
    init_db()

    yield

    # Cleanup
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)

def test_get_all_videos_sorting_and_pagination():
    now = datetime.now()
    # We want to ensure specific order: pending_download_at DESC, id DESC
    # We'll insert them in order of time, but with different IDs
    with server.videos._get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("vid1", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now.replace(minute=0))
        )
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("vid2", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now.replace(minute=1))
        )
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("vid3", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now.replace(minute=2))
        )

    # Test sorting: should be vid3, vid2, vid1 (latest first)
    videos = get_all_videos(limit=5)
    assert len(videos) == 3
    assert videos[0].video_id == "vid3"
    assert videos[1].video_id == "vid2"
    assert videos[2].video_id == "vid1"

    # Test pagination
    videos_paged = get_all_videos(limit=2, offset=1)
    assert len(videos_paged) == 2
    assert videos_paged[0].video_id == "vid2"
    assert videos_paged[1].video_id == "vid1"

def test_get_non_fail_videos_filtering():
    now = datetime.now()
    with server.videos._get_cursor() as cursor:
        # Fail 1
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("fail1", VideoSource.YOUTUBE, 1, VideoStatus.DOWNLOAD_FAILED, now)
        )
        # Fail 2
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("fail2", VideoSource.YOUTUBE, 1, VideoStatus.PROCESSING_FAILED, now)
        )
        # Success
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("success", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now)
        )

    # Should only have 1 result
    videos = get_non_fail_videos()
    assert len(videos) == 1
    assert videos[0].video_id == "success"

def test_get_videos_by_status_sorting():
    now = datetime.now()
    with server.videos._get_cursor() as cursor:
        # id 1: 10:00
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("v1", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now.replace(minute=0))
        )
        # id 2: 10:01
        cursor.execute(
            "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
            ("v2", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now.replace(minute=1))
        )

    # Should be sorted by pending_download_at DESC, id DESC
    # So v2, then v1
    videos = get_videos_by_status(VideoStatus.PENDING_DOWNLOAD)
    assert len(videos) == 2
    assert videos[0].video_id == "v2"
    assert videos[1].video_id == "v1"

def test_get_videos_by_id_pagination():
    now = datetime.now()
    with server.videos._get_cursor() as cursor:
        # Use same video_id for multiple entries to test get_videos_by_id
        for i in range(5):
            cursor.execute(
                "INSERT INTO videos (video_id, video_source, tab_id, status, pending_download_at) VALUES (?, ?, ?, ?, ?)",
                ("group_vid", VideoSource.YOUTUBE, 1, VideoStatus.PENDING_DOWNLOAD, now)
            )

    # Since all have same pending_download_at, it sorts by id DESC.
    # IDs will be 1, 2, 3, 4, 5. So order is 5, 4, 3, 2, 1.
    videos = get_videos_by_id("group_vid", VideoSource.YOUTUBE, limit=2, offset=1)
    assert len(videos) == 2
    assert videos[0].id == 5
    assert videos[1].id == 4
