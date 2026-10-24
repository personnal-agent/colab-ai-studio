import React, { useEffect, useMemo, useState } from 'react';
import { Layers } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { Generation, TaskStatusEvent } from '../../types/studio';
import { MediaCard } from './MediaCard';
import { SearchAndFilterBar } from './SearchAndFilterBar';
import { TaskProgressCard } from './TaskProgressCard';

export interface ActiveTaskState {
  event: TaskStatusEvent; prompt: string; modelName: string;
}

export interface MediaGalleryProps {
  favoritesOnly: boolean; activeProjectId: string | null;
  onSelectGeneration: (generation: Generation) => void;
  activeTask?: ActiveTaskState | null; onTaskCancelled?: (taskId: string) => void;
}

export const MediaGallery: React.FC<MediaGalleryProps> = ({
  favoritesOnly, activeProjectId, onSelectGeneration, activeTask, onTaskCancelled,
}) => {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState('');
  const [activePills, setActivePills] = useState<string[]>([]);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    apiClient.listGenerations(activeProjectId ? { projectId: activeProjectId } : undefined)
      .then((data) => { if (isMounted) { setGenerations(data); setLoading(false); } })
      .catch((err) => { console.error(err); if (isMounted) setLoading(false); });
    return () => { isMounted = false; };
  }, [activeProjectId]);

  const handleTogglePill = (pill: string) => {
    setActivePills((prev) => prev.includes(pill) ? prev.filter((p) => p !== pill) : [...prev, pill]);
  };

  const filteredGenerations = useMemo(() => {
    return generations.filter((gen) => {
      if (favoritesOnly && !gen.isFavorite) return false;
      if (searchValue.trim()) {
        const query = searchValue.toLowerCase().trim();
        if (!gen.prompt?.toLowerCase().includes(query) && !gen.modelName?.toLowerCase().includes(query)) return false;
      }
      if (activePills.length > 0) {
        const match = activePills.some((p) => (p === 'image' ? (gen.mediaType === 'image' || gen.mediaType === 'upscale') : gen.mediaType === p));
        if (!match) return false;
      }
      return true;
    });
  }, [generations, favoritesOnly, searchValue, activePills]);

  const handleFavoriteToggled = (updated: Generation) => {
    setGenerations((prev) => prev.map((g) => (g.id === updated.id ? { ...g, isFavorite: updated.isFavorite } : g)));
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <SearchAndFilterBar searchValue={searchValue} onSearchChange={setSearchValue} activePills={activePills} onTogglePill={handleTogglePill} />
      <div className="w-full min-h-[300px]">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="aspect-video bg-gray-100 rounded-dock animate-pulse border border-studio-border" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {activeTask && (
              <TaskProgressCard event={activeTask.event} prompt={activeTask.prompt} modelName={activeTask.modelName} onCancelled={(id) => onTaskCancelled?.(id)} />
            )}
            {filteredGenerations.map((gen) => (
              <MediaCard key={gen.id} generation={gen} onSelect={onSelectGeneration} onFavoriteToggled={handleFavoriteToggled} />
            ))}
          </div>
        )}
        {!loading && !activeTask && filteredGenerations.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center text-gray-500">
            <Layers className="w-12 h-12 text-gray-300 mb-3 stroke-[1.5]" />
            <h3 className="text-sm font-semibold text-gray-700">Aucune création</h3>
            <p className="text-xs text-gray-400 mt-1 max-w-sm">Aucun média ne correspond à vos critères de recherche ou de filtre.</p>
          </div>
        )}
      </div>
    </div>
  );
};
