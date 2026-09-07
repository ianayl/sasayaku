export interface RecentVideo {
  videoId: string;
  title: string;
  url: string;
  timestamp: number;
}

export interface YouTubeVideoInfo {
  videoId: string | null;
  url: string;
  title: string | null;
  isYouTube: boolean;
}

export interface ServerResponse {
  success: boolean;
  message: string;
  data?: unknown;
}

export interface ServerConfig {
  url: string;
  apiKey?: string;
}
