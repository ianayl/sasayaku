export interface Video {
  id: number;
  videoId: string;
  videoSource: string;
  tabId: number;
  status: string;
  pendingDownloadAt: string;
  pendingProcessingAt: string | null;
  finishedAt: string | null;
  processingTime: number | null;
}

export interface YouTubeVideoInfo {
  videoId: string | null;
  url: string;
  title: string | null;
  isYouTube: boolean;
}

// export interface ServerResponse {
//   success: boolean;
//   message: string;
//   data?: unknown;
// }
// 
// export interface ServerConfig {
//   url: string;
//   apiKey?: string;
// }
