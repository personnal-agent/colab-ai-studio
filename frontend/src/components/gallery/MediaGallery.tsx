import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Layers, RefreshCw } from 'lucide-react';
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
  generations?: Generation[];
  onGenerationsChange?: (updater: (prev: Generation[]) => Generation[]) => void;
  onFavoriteToggled?: (updated: Generation) => void;
}

export const MediaGallery: React.FC<MediaGalleryProps> = ({
  favoritesOnly, activeProjectId, onSelectGeneration, activeTask, onTaskCancelled,
  generations: propGenerations, onGenerationsChange, onFavoriteToggled,
}) => {
  const [localGenerations, setLocalGenerations] = useState<Generation[]>([]);
  const generations = propGenerations !== undefined ? propGenerations : localGenerations;
  const updateGenerations = useCallback((updater: (prev: Generation[]) => Generation[]) => {
    if (onGenerationsChange) onGenerationsChange(updater);
    else setLocalGenerations(updater);
  }, [onGenerationsChange]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchValue, setSearchValue] = useState('');
  const [activePills, setActivePills] = useState<string[]>([]);

  const fetchGenerations = useCallback(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    apiClient.listGenerations(activeProjectId ? { projectId: activeProjectId } : undefined)
      .then((data) => {
        if (!isMounted) return;
        updateGenerations(() => data);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error(err);
        updateGenerations(() => []);
        setError('Impossible de charger les créations.');
        setLoading(false);
      });
    return () => { isMounted = false; };
  }, [activeProjectId, updateGenerations]);

  useEffect(() => {
    const cleanup = fetchGenerations();
    return cleanup;
  }, [fetchGenerations]);

  // Écoute automatique des tâches actives dans la liste
  useEffect(() => {
    const activeItems = generations.filter((g) => g.status === 'pending' || g.status === 'running');
    if (activeItems.length === 0) return;
    const unsubscribers = activeItems.map((item) =>
      apiClient.subscribeTaskStatus(item.id, (ev) => {
        updateGenerations((prev) => prev.map((g) => {
          if (g.id !== item.id) return g;
          return {
            ...g,
            status: ev.status,
            progress: ev.progress ?? g.progress,
            filePath: ev.filePath || g.filePath,
          };
        }));
      })
    );
    return () => { unsubscribers.forEach((unsub) => unsub()); };
  }, [generations, updateGenerations]);

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

  const handleLocalFavorite = (updated: Generation) => {
    updateGenerations((prev) => prev.map((g) => (g.id === updated.id ? { ...g, isFavorite: updated.isFavorite } : g)));
    onFavoriteToggled?.(updated);
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <SearchAndFilterBar searchValue={searchValue} onSearchChange={setSearchValue} activePills={activePills} onTogglePill={handleTogglePill} />
      <div className="w-full min-h-[300px]">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="aspect-video bg-gray-100 rounded-dock animate-pulse border border-studio-border" />)}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="w-10 h-10 text-rose-500 mb-3" />
            <h3 className="text-sm font-semibold text-gray-800">{error}</h3>
            <button type="button" onClick={fetchGenerations} className="mt-4 px-4 py-2 text-xs font-medium rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-colors flex items-center gap-1.5 shadow-sm">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Réessayer</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {activeTask && (
              <TaskProgressCard event={activeTask.event} prompt={activeTask.prompt} modelName={activeTask.modelName} onCancelled={(id) => onTaskCancelled?.(id)} />
            )}
            {filteredGenerations.map((gen) => (
              <MediaCard key={gen.id} generation={gen} onSelect={onSelectGeneration} onFavoriteToggled={handleLocalFavorite} />
            ))}
          </div>
        )}
        {!loading && !error && !activeTask && filteredGenerations.length === 0 && (
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
