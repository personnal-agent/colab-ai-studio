import React, { useRef, useState } from 'react';
import { Film, Mic, Sparkles, Star, Volume2 } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { Generation } from '../../types/studio';

export interface MediaCardProps {
  generation: Generation;
  onSelect: (generation: Generation) => void;
  onFavoriteToggled?: (generation: Generation) => void;
}

export const MediaCard: React.FC<MediaCardProps> = ({ generation, onSelect, onFavoriteToggled }) => {
  const [isFavorite, setIsFavorite] = useState(generation.isFavorite);
  const [isUpdatingFavorite, setIsUpdatingFavorite] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isUpdatingFavorite) return;
    setIsUpdatingFavorite(true);
    try {
      const res = await apiClient.toggleFavorite(generation.id);
      setIsFavorite(res.isFavorite);
      onFavoriteToggled?.({ ...generation, isFavorite: res.isFavorite });
    } catch (err) { console.error('Failed to toggle favorite:', err); }
    finally { setIsUpdatingFavorite(false); }
  };

  const handleMouseEnter = () => { if (generation.mediaType === 'video' && videoRef.current) videoRef.current.play().catch(() => {}); };
  const handleMouseLeave = () => { if (generation.mediaType === 'video' && videoRef.current) { videoRef.current.pause(); videoRef.current.currentTime = 0; } };
  const is4K = generation.mediaType === 'upscale' || generation.parameters?.resolution?.toLowerCase().includes('4k');

  return (
    <div data-testid={`media-card-${generation.id}`} onClick={() => onSelect(generation)} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} className="group relative bg-white rounded-dock border border-studio-border hover:border-gray-300 shadow-sm hover:shadow-md transition-all cursor-pointer overflow-hidden flex flex-col">
      <div className="relative aspect-video w-full bg-studio-canvas overflow-hidden flex items-center justify-center">
        {(generation.mediaType === 'image' || generation.mediaType === 'upscale') && (
          <img src={generation.thumbnailPath || generation.filePath || undefined} alt={generation.prompt} loading="lazy" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        )}
        {generation.mediaType === 'video' && (
          <video ref={videoRef} src={generation.filePath || undefined} poster={generation.thumbnailPath || undefined} preload="none" muted loop playsInline className="w-full h-full object-cover" />
        )}
        {generation.mediaType === 'lip_sync' && (
          <div className="relative w-full h-full">
            <video ref={videoRef} src={generation.filePath || undefined} poster={generation.thumbnailPath || undefined} preload="none" muted loop playsInline className="w-full h-full object-cover" />
            <div className="absolute top-2 left-2 bg-purple-600/90 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm"><Mic className="w-3 h-3" /><span>Lip Sync</span></div>
          </div>
        )}
        {generation.mediaType === 'audio' && (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 p-4">
            <Volume2 className="w-10 h-10 text-indigo-400 animate-pulse" /><span className="text-xs text-gray-500 mt-2 font-mono">{generation.parameters?.duration || 'Audio'}</span>
          </div>
        )}
        <div className="absolute top-2 right-2 flex items-center gap-1.5 z-10">
          {is4K && <span className="bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-0.5"><Sparkles className="w-2.5 h-2.5" />4K</span>}
          {generation.mediaType === 'video' && <span className="bg-black/60 backdrop-blur-sm text-white text-[10px] font-medium px-1.5 py-0.5 rounded flex items-center gap-1"><Film className="w-2.5 h-2.5" />{generation.parameters?.duration || 'Video'}</span>}
          <button type="button" onClick={handleToggleFavorite} aria-label={isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'} className="w-7 h-7 rounded-full bg-white/80 hover:bg-white backdrop-blur-sm flex items-center justify-center transition-colors shadow-sm">
            <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-amber-400 text-amber-400' : 'text-gray-400 hover:text-amber-400'}`} />
          </button>
        </div>
      </div>
      <div className="p-3 flex-1 flex flex-col justify-between">
        <p className="text-xs text-gray-900 font-medium line-clamp-2 leading-relaxed" title={generation.prompt}>{generation.prompt}</p>
        <div className="mt-2.5 pt-2 border-t border-studio-divider flex items-center justify-between text-[11px] text-gray-500">
          <span className="font-medium text-gray-700 truncate max-w-[130px]">{generation.modelName}</span>
          <span className="font-mono text-gray-400">{generation.parameters?.aspectRatio || '16:9'}</span>
        </div>
      </div>
    </div>
  );
};
