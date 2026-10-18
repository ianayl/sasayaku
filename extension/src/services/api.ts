import { Video } from "../types";

/**
 * Pings the server to verify connection / server health.
 * @param baseUrl Server URL
 * * @returns A promise that resolves to true if the server responds correctly
 */
export async function ping(baseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}/api/ping`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.status === 'pong';
  } catch (error) {
    return false;
  }
}

/**
 * Sends a YouTube URL to the server for processing.
 * @param baseUrl Server URL
 * @param youtubeUrl The URL of the YouTube video
 * @returns A promise that resolves to true if the server accepts the URL
 */
export async function processYoutube(baseUrl: string, youtubeUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}/api/process-youtube`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.status === 'success';
  } catch (error) {
    return false;
  }
}

/**
 * Fetches the total count of videos from the server.
 * @param baseUrl Server URL
 * @returns A promise that resolves to the count or null if the request fails
 */
export async function getVideoCount(baseUrl: string): Promise<number | null> {
  try {
    const response = await fetch(`${baseUrl}/api/get-video-count`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.count ?? null;
  } catch (error) {
    return null;
  }
}

/**
 * Fetches a list of videos from the server with pagination.
 * @param baseUrl Server URL
 * @param limit Number of videos to return per page
 * @param offset Number of videos to skip
 * * @returns A promise that resolves to an array of Video objects or null if the request fails
 * */
export async function getAllVideos(baseUrl: string, limit: number = 20, offset: number = 0): Promise<Video[] | null> {
  try {
    const response = await fetch(`${baseUrl}/api/get-all-videos?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    // Map snake_case keys from API to camelCase for our Video type
    return (data.videos || []).map((v: any) => ({
      id: v.id,
      videoId: v.video_id,
      videoSource: v.video_source,
      tabId: v.tab_id,
      status: v.status,
      pendingDownloadAt: v.pending_download_at,
      pendingProcessingAt: v.pending_processing_at,
      finishedAt: v.finished_at,
      processingTime: v.processing_time
    }));
  } catch (error) {
    return null;
  }
}
