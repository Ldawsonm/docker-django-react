import React from "react";
import ReactPlayer from "react-player";

const VideoPlayer = ({ video }) => {
  if (!video) {
    return <div className="p-4">Select a video to play</div>;
  }

  return (
    <div className="flex flex-col w-full">
      <div className="aspect-video mb-4">
        <ReactPlayer
          url={video.player_url}
          controls
          width="100%"
          height="100%"
        />
      </div>
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-bold mb-2">Transcript</h2>
        <p className="whitespace-pre-wrap">{video.transcript_text || "No transcript available."}</p>
      </div>
    </div>
  );
};

export default VideoPlayer;
