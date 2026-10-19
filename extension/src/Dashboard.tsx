import {
  Box,
  Typography,
  Button,
  CircularProgress,
} from "@mui/material";
import { useEffect, useState } from "react";
import { processYoutube, getVideoCount, getAllVideos } from "./services/api";
import { getCurrentTabInfo } from "./utils";
import { VideoList } from "./components/VideoList";
import type { Video } from "./types";

// TODO: Add a system that automatically checks the database for a video_id,
// and a card popup if we already have the subtitles generated.

// TODO: Implement a persistent configuration system to manage server URLs and other settings.
const BASE_URL = "http://localhost:7749";

export function Dashboard() {
  const [tabInfo, setTabInfo] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [videoCount, setVideoCount] = useState<number | null>(null);

  // Video List State
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  const LIMIT = 20;

  useEffect(() => {
    const init = async () => {
      const info = await getCurrentTabInfo();
      setTabInfo(info);
      console.log(info);
    };
    init();
  }, []);

  // Fetch videos when page changes
  useEffect(() => {
    const fetchVideos = async () => {
      setIsLoadingVideos(true);
      const data = await getAllVideos(BASE_URL, LIMIT, currentPage * LIMIT);
      if (data !== null) {
        setVideos(data);
      } else {
				// TODO: it doesnt actually make sense that setStatus is used for "failed to
				// fetch videos" since it's affixed currently to "process video" button.
				// REFACTOR setStatus to something else!
        setStatus("Failed to fetch videos.");
        setTimeout(() => setStatus(null), 3000);
      }
      setIsLoadingVideos(false);
    };

    fetchVideos();
  }, [currentPage]);

  const handleProcess = async () => {
    if (!tabInfo || !tabInfo.isYouTube) return;

    setIsProcessing(true);
    const success = await processYoutube(BASE_URL, tabInfo.url);
    setIsProcessing(false);

    if (success) {
      setStatus("Success! Video queued for processing.");
    } else {
      setStatus("Error processing video.");
    }
    setTimeout(() => setStatus(null), 3000);
  };

  const handleFetchVideoCount = async () => {
    const count = await getVideoCount(BASE_URL);
    setVideoCount(count);
    if (count === null) {
      setStatus("Failed to fetch video count.");
      setTimeout(() => setStatus(null), 3000);
    }
  };

  const handlePageChange = (page: number) => {
		// TODO Check page count first; we might want the api to return total page
		// count too. Don't change the page and request pages that don't exist.
    setCurrentPage(page);
  };
	// TODO maybe add a refresh button for the VideoList to refresh from db at
	// page 0.

  return (
    <Box sx={{ p: 1, width: 400 }}>
      {tabInfo?.isYouTube ? (
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            fullWidth
            disabled={isProcessing}
            onClick={handleProcess}
            startIcon={isProcessing ? <CircularProgress size={20} /> : null}
          >
            {isProcessing ? "Processing..." : "Process YouTube Video"}
          </Button>
          {status && <Typography variant="caption" sx={{ mt: 1, textAlign: 'center' }}>
            {status}
          </Typography>}
        </Box>
      ) : (
        <Typography variant="body1">
          Not on a YouTube video page.
        </Typography>
      )}

      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #eee' }}>
        <Button
          variant="outlined"
          fullWidth
          onClick={handleFetchVideoCount}
        >
          Show Video Count
        </Button>
        {videoCount !== null && (
          <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
            Total Videos: {videoCount}
          </Typography>
        )}
      </Box>

      <VideoList
        videos={videos}
        isLoading={isLoadingVideos}
        currentPage={currentPage}
        onPageChange={handlePageChange}
      />
    </Box>
  );
}
