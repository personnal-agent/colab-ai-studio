import React, { useEffect, useRef, useState } from 'react';
import { Film, Layers, Mic, Sparkles, Star, Trash2, Volume2, AlertTriangle } from 'lucide-react';
import { apiClient, getMediaFileUrl, getMediaThumbnailUrl } from '../../services/apiClient';
import type { Generation } from '../../types/studio';

export interface MediaCardProps {
  generation: Generation;
  onSelect: (generation: Generation) => void;
  onFavoriteToggled?: (generation: Generation) => void;
  onDelete?: (generation: Generation) => void;
  onInjectToCanvas?: (generation: Generation) => void;
}

export const MediaCard: React.FC<MediaCardProps> = ({
  generation,
  onSelect,
  onFavoriteToggled,
  onDelete,
  onInjectToCanvas,
}) => {
  const [isFavorite, setIsFavorite] = useState(generation.isFavorite);
  const [isUpdatingFavorite, setIsUpdatingFavorite] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    setIsFavorite(generation.isFavorite);
  }, [generation.isFavorite]);

  const handleToggleFavorite = async (e: React.MouseEvent | React.KeyboardEvent) => {
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

  const handleDelete = async (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (!window.confirm('Supprimer définitivement cette création ?')) return;
    try {
      await apiClient.deleteGeneration(generation.id);
      onDelete?.(generation);
    } catch (err) { console.error('Failed to delete generation:', err); }
  };

  const isVideoMedia =
    generation.mediaType === 'video' ||
    generation.mediaType === 'lip_sync' ||
    (generation.mediaType === 'upscale' && (
      Boolean(generation.filePath?.endsWith('.mp4')) ||
      generation.references?.upscaleSourceType === 'video'
    ));

  const handleMouseEnter = () => { if (isVideoMedia && videoRef.current) videoRef.current.play().catch(() => {}); };
  const handleMouseLeave = () => { if (isVideoMedia && videoRef.current) { videoRef.current.pause(); videoRef.current.currentTime = 0; } };
  const is4K = generation.mediaType === 'upscale' || generation.parameters?.resolution?.toLowerCase().includes('4k');
  const fileUrl = getMediaFileUrl(generation);
  const thumbUrl = getMediaThumbnailUrl(generation);

  return (
    <div
      data-testid={`media-card-${generation.id}`}
      role="button"
      tabIndex={0}
      aria-label={`Inspecter ${generation.prompt}`}
      onClick={() => onSelect(generation)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(generation);
        }
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="group relative bg-white rounded-dock border border-studio-border hover:border-gray-300 shadow-sm hover:shadow-md transition-all cursor-pointer overflow-hidden flex flex-col focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
    >
      <div className="relative aspect-video w-full bg-studio-canvas overflow-hidden flex items-center justify-center">
        {generation.status === 'failed' ? (
          <div className="w-full h-full flex flex-col items-center justify-center bg-rose-50/90 dark:bg-rose-950/40 p-4 text-center">
            <AlertTriangle className="w-7 h-7 text-rose-500 mb-1" />
            <span className="text-xs font-bold text-rose-600 dark:text-rose-400">Échec du rendu</span>
            <span className="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-2 mt-1" title={generation.errorMessage || 'Erreur GPU'}>
              {generation.errorMessage ? generation.errorMessage.slice(0, 90) : 'Paramètre non supporté'}
            </span>
          </div>
        ) : (
          <>
            {!isVideoMedia && (
              <img src={thumbUrl} alt={generation.prompt} loading="lazy" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            )}
            {isVideoMedia && (
              <div className="relative w-full h-full">
                <video ref={videoRef} src={fileUrl} poster={thumbUrl} preload="none" muted loop playsInline className="w-full h-full object-cover" />
                {generation.mediaType === 'lip_sync' && (
                  <div className="absolute top-2 left-2 bg-purple-600/90 text-white text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm"><Mic className="w-3 h-3" /><span>Lip Sync</span></div>
                )}
              </div>
            )}
            {generation.mediaType === 'audio' && (
              <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 p-4">
                <Volume2 className="w-10 h-10 text-indigo-400 animate-pulse" /><span className="text-xs text-gray-500 mt-2 font-mono">{generation.parameters?.duration || 'Audio'}</span>
              </div>
            )}
          </>
        )}
        {generation.sequenceTotal && generation.sequenceTotal > 1 && (
          <div className="absolute bottom-2 left-2 bg-black/75 backdrop-blur-sm text-white text-[10px] font-mono font-medium px-2 py-0.5 rounded-md flex items-center gap-1 z-10">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            <span>Plan {generation.sequenceIndex}/{generation.sequenceTotal}</span>
          </div>
        )}
        {generation.cameraAngleLabel && (
          <div className="absolute bottom-2 left-2 bg-indigo-900/80 backdrop-blur-sm text-white text-[10px] font-medium px-2 py-0.5 rounded-md flex items-center gap-1 z-10">
            <span>🎥 {generation.cameraAngleLabel}</span>
          </div>
        )}
        <div className="absolute top-2 right-2 flex items-center gap-1.5 z-10">
          {generation.rating && generation.rating > 0 && (
            <span className="bg-black/60 backdrop-blur-sm text-amber-400 text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-0.5">
              <Star className="w-2.5 h-2.5 fill-amber-400 text-amber-400" />
              {generation.rating}
            </span>
          )}
          {is4K && <span className="bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-0.5"><Sparkles className="w-2.5 h-2.5" />4K</span>}
          {generation.mediaType === 'video' && <span className="bg-black/60 backdrop-blur-sm text-white text-[10px] font-medium px-1.5 py-0.5 rounded flex items-center gap-1"><Film className="w-2.5 h-2.5" />{generation.parameters?.duration || 'Video'}</span>}
          <button
            type="button"
            onClick={handleToggleFavorite}
            onKeyDown={(e) => { e.stopPropagation(); }}
            aria-label={isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
            className="w-7 h-7 rounded-full bg-white/80 hover:bg-white backdrop-blur-sm flex items-center justify-center transition-colors shadow-sm"
          >
            <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-amber-400 text-amber-400' : 'text-gray-400 hover:text-amber-400'}`} />
          </button>
          {onInjectToCanvas && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onInjectToCanvas(generation);
              }}
              onKeyDown={(e) => { e.stopPropagation(); }}
              aria-label="Injecter dans le canevas"
              title="Injecter dans le canevas"
              className="w-7 h-7 rounded-full bg-white/80 hover:bg-indigo-50 hover:text-indigo-600 text-gray-500 backdrop-blur-sm flex items-center justify-center transition-colors shadow-sm opacity-0 group-hover:opacity-100 focus:opacity-100"
            >
              <Layers className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={handleDelete}
            onKeyDown={(e) => { e.stopPropagation(); }}
            aria-label="Supprimer la génération"
            className="w-7 h-7 rounded-full bg-white/80 hover:bg-rose-50 hover:text-rose-600 text-gray-400 backdrop-blur-sm flex items-center justify-center transition-colors shadow-sm opacity-0 group-hover:opacity-100 focus:opacity-100"
          >
            <Trash2 className="w-3.5 h-3.5" />
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
