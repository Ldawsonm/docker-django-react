import React from "react";
import VideoCard from "./VideoCard";

const VideoSourceList = ({ source, videos, onSelect }) => {
  return (
    <div className="mb-6">
      <h2 className="text-lg font-bold mb-2">{source} Videos</h2>
      {videos.map((video) => (
        <VideoCard key={video.id} video={video} onSelect={onSelect} />
      ))}
    </div>
  );
};

export default VideoSourceList;
