import { YouTubeVideoInfo, ServerConfig } from "./types";

const DEFAULT_SERVER_URL = "http://localhost:8000";

export const SERVER_CONFIG_KEY = "server_config";

export function getStoredServerConfig(): Promise<ServerConfig> {
  return new Promise((resolve) => {
    chrome.storage.sync.get<{ [SERVER_CONFIG_KEY]: ServerConfig }>([SERVER_CONFIG_KEY]).then((result) => {
      resolve(
        result[SERVER_CONFIG_KEY] ?? { url: DEFAULT_SERVER_URL }
      );
    });
  });
}

export function saveServerConfig(config: ServerConfig): Promise<void> {
  return new Promise((resolve) => {
    chrome.storage.sync.set({ [SERVER_CONFIG_KEY]: config }).then(resolve);
  });
}

export async function getCurrentTabInfo(): Promise<YouTubeVideoInfo> {
  let tab: any = null;

  // Try primary method: query
  const tabs = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });

  if (tabs && tabs.length > 0) {
    tab = tabs[0];
  }

  // Fallback: If the tab exists but lacks a URL, try getting the current tab directly.
  if (tab && !tab.url) {
    tab = await chrome.tabs.getCurrent();
  }

  console.log("Debug Tab Object:", tab);

  if (!tab || !tab.url) {
    return {
      videoId: null,
      url: "",
      title: tab?.title ?? null,
      isYouTube: false,
    };
  }

  const isYouTube = tab.url.includes("youtube.com/watch") || tab.url.includes("youtu.be/");
  let videoId: string | null = null;

  if (isYouTube) {
    try {
      const urlObj = new URL(tab.url);
      videoId = urlObj.searchParams.get("v");
      if (!videoId && tab.url.includes("youtu.be/")) {
        videoId = tab.url.split("youtu.be/")[1].split(/[?&#]/)[0];
      }
    } catch (e) {
      console.error("Failed to parse YouTube URL", e);
    }
  }

  return {
    videoId,
    url: tab.url,
    title: tab.title ?? null,
    isYouTube,
  };
}

export async function sendVideoToBackend(
  config: ServerConfig,
  video: YouTubeVideoInfo
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (config.apiKey) {
    headers["Authorization"] = `Bearer ${config.apiKey}`;
  }

  return fetch(`${config.url}/api/video`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      url: video.url,
      videoId: video.videoId,
      title: video.title,
    }),
  });
}