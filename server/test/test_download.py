import unittest
from unittest.mock import patch, MagicMock
from server.videos.download import download_video
from server.videos.video import VideoSource
from pathlib import Path
import os

class TestDownload(unittest.TestCase):
    def test_download_video_success(self):
        """Test that download_video constructs the correct path and calls yt_dlp."""
        video_id = "dQw4w9WgXcQ"
        # Mock the yt_dlp.YoutubeDL context manager and the download method
        with patch("yt_dlp.YoutubeDL") as MockYoutubeDL:
            instance = MockYoutubeDL.return_value

            # Ensure the mock doesn't actually try to download anything
            instance.download = MagicMock()

            result = download_video(video_id, VideoSource.YOUTUBE)

            # Verify result path
            self.assertIsInstance(result, Path)
            self.assertTrue(str(result).endswith(f"{video_id}-7.mp3"))

            # Verify yt-dlp was called with correct args
            MockYoutubeDL.assert_called_once()
            args, kwargs = MockYoutubeDL.call_args
            self.assertEqual(kwargs['extractor_args'], {'youtube:player_client': 'android'})
            self.assertEqual(kwargs['outtmpl'], str(result))
            instance.download.assert_called_once()

    def test_download_video_failure(self):
        """Test that download_video returns None and logs error on failure."""
        video_id = "failure_id"

        with patch("yt_dlp.YoutubeDL") as MockYoutubeDL:
            instance = MockYoutubeDL.return_value
            instance.download.side_effect = Exception("Download failed")

            result = download_video(video_id, VideoSource.YOUTUBE)

            self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
