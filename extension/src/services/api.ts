
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
