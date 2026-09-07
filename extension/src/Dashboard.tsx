import {
  Box,
  Typography,
  Button,
  CircularProgress,
} from "@mui/material";
import { useEffect, useState } from "react";
import { processYoutube } from "./services/api";
import { getCurrentTabInfo } from "./utils";

// TODO: Implement a persistent configuration system to manage server URLs and other settings.
const BASE_URL = "http://localhost:7749";

export function Dashboard() {
  const [tabInfo, setTabInfo] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      const info = await getCurrentTabInfo();
      setTabInfo(info);
			console.log(info);
    };
    init();
  }, []);

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
    </Box>
  );
}
