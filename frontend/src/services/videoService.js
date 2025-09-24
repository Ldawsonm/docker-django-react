export async function fetchVideos() {
  const response = await fetch("/api/videos/");
  if (!response.ok) throw new Error("Failed to fetch videos: " + response.Error);
  return response.json();
}