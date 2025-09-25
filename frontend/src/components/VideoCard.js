import React from "react";

const VideoCard = ({ video, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(video)}
      className="cursor-pointer border p-2 mb-2 rounded hover:bg-gray-50"
    >
      <h3 className="font-medium">{video.title}</h3>
      <p className="text-sm text-gray-600">
        {new Date(video.published_at).toLocaleDateString()}
      </p>

      <a
        href={video.player_url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 text-sm underline"
        onClick={(e) => e.stopPropagation()} // don't trigger select
      >
        Video Link
      </a>

      <button
        className="mt-1 px-2 py-1 bg-blue-500 text-white text-sm rounded"
        onClick={(e) => {
          e.stopPropagation(); // prevent parent click
          onSelect(video);
        }}
      >
        View Transcription
      </button>
    </div>
  );
};

export default VideoCard;
