import { Film, Image as ImageIcon, Sparkles, Star, Volume2 } from 'lucide-react';
import React, { useRef } from 'react';
import { Generation } from '../../types/studio';

interface MediaCardProps {
  generation: Generation;
  onSelect: (gen: Generation) => void;
  onToggleFavorite: (id: string) => void;
}

export function MediaCard({ generation, onSelect, onToggleFavorite }: MediaCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const isVideo = generation.mediaType === 'video';
  const isAudio = generation.mediaType === 'audio';
  const isLipSync = generation.mediaType === 'lip_sync';
  const is4K = generation.parameters.resolution === '4k';

  const handleMouseEnter = () => {
    if (isVideo && videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    if (isVideo && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  const getBadgeIcon = () => {
    if (isVideo) return <Film className="w-3 h-3" />;
    if (isAudio) return <Volume2 className="w-3 h-3" />;
    if (isLipSync) return <Sparkles className="w-3 h-3" />;
    return <ImageIcon className="w-3 h-3" />;
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(generation)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(generation);
        }
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="group relative overflow-hidden rounded-slot bg-studio-card border border-studio-border shadow-card hover:shadow-dropdown transition-all duration-200 cursor-pointer flex flex-col justify-between aspect-video"
    >
      {/* Média Preview */}
      <div className="absolute inset-0 bg-gray-900 flex items-center justify-center overflow-hidden">
        {isVideo && generation.filePath ? (
          <video
            ref={videoRef}
            src={generation.filePath}
            poster={generation.thumbnailPath || undefined}
            muted
            loop
            preload="none"
            playsInline
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : generation.filePath || generation.thumbnailPath ? (
          <img
            src={generation.filePath || generation.thumbnailPath || undefined}
            alt={generation.prompt}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="text-gray-500 text-xs flex flex-col items-center gap-1">
            {getBadgeIcon()}
            <span className="capitalize">{generation.mediaType}</span>
          </div>
        )}
      </div>

      {/* Badges supérieurs (Type, 4K & Favori) */}
      <div className="relative z-10 p-2.5 flex items-start justify-between bg-gradient-to-b from-black/60 via-black/20 to-transparent">
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded-pill bg-black/50 backdrop-blur-md text-[10px] font-medium text-white flex items-center gap-1">
            {getBadgeIcon()}
            <span className="capitalize">{generation.mediaType}</span>
          </span>
          {is4K && (
            <span className="px-1.5 py-0.5 rounded-pill bg-indigo-600/90 backdrop-blur-md text-[9px] font-bold text-white tracking-wider">
              4K
            </span>
          )}
        </div>

        <button
          type="button"
          aria-label={
            generation.isFavorite
              ? 'Retirer des favoris'
              : 'Marquer comme favori'
          }
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            onToggleFavorite(generation.id);
          }}
          className={`p-1.5 rounded-full backdrop-blur-md transition-colors ${
            generation.isFavorite
              ? 'bg-amber-400 text-black shadow-sm'
              : 'bg-black/40 text-white/80 hover:text-white hover:bg-black/60'
          }`}
        >
          <Star
            className={`w-3.5 h-3.5 ${
              generation.isFavorite ? 'fill-black stroke-black' : 'stroke-current'
            }`}
          />
        </button>
      </div>

      {/* Métadonnées & Prompt en pied de carte au survol */}
      <div className="relative z-10 p-2.5 bg-gradient-to-t from-black/80 via-black/40 to-transparent text-white opacity-95 group-hover:opacity-100 transition-opacity">
        <p className="text-xs font-normal line-clamp-1 drop-shadow-sm">
          {generation.prompt}
        </p>
        <div className="flex items-center justify-between text-[10px] text-white/70 mt-1">
          <span>{generation.modelName || generation.modelId}</span>
          <span>{generation.parameters.aspectRatio}</span>
        </div>
      </div>
    </div>
  );
}
