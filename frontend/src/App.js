import React, { useEffect, useState } from "react";
import VideoSourceList from "./components/VideoSourceList";
import VideoPlayer from "./components/VideoPlayer";

const App = () => {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);

  useEffect(() => {
    // Fetch from your Django API
    fetch("/api/videos/") // adjust URL as needed
      .then((res) => res.json())
      .then((data) => setVideos(data));
  }, []);

  const grouped = videos.reduce((acc, video) => {
    acc[video.source] = acc[video.source] || [];
    acc[video.source].push(video);
    return acc;
  }, {});

  return (
    <div className="flex flex-row h-screen">
      <aside className="overflow-y-auto basis-1/3">
        {Object.entries(grouped).map(([source, vids]) => (
          <VideoSourceList
            key={source}
            source={source}
            videos={vids}
            onSelect={setSelectedVideo}
          />
        ))}
      </aside>
      <main className="basis-2/3 flex-1 p-4 flex items-center justify-center">
        <VideoPlayer video={selectedVideo} />
      </main>
    </div>
  );
};

export default App;
