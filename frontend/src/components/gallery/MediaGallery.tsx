import { FolderOpen } from 'lucide-react';
import { Generation } from '../../types/studio';
import { MediaCard } from './MediaCard';
import { TaskProgressCard } from './TaskProgressCard';

interface MediaGalleryProps {
  activeTasks: Generation[];
  generations: Generation[];
  onSelectGeneration: (gen: Generation) => void;
  onToggleFavorite: (id: string) => void;
  onCancelTask: (taskId: string) => void;
}

export function MediaGallery({
  activeTasks,
  generations,
  onSelectGeneration,
  onToggleFavorite,
  onCancelTask,
}: MediaGalleryProps) {
  const totalCount = activeTasks.length + generations.length;

  if (totalCount === 0) {
    return (
      <div className="w-full py-20 flex flex-col items-center justify-center text-center">
        <div className="p-4 rounded-full bg-studio-subtle text-gray-400 mb-3">
          <FolderOpen className="w-8 h-8" />
        </div>
        <h3 className="text-base font-semibold text-gray-800">Aucun média trouvé</h3>
        <p className="text-sm text-gray-500 max-w-sm mt-1">
          Lancez une génération depuis le poste de commande flottant ou modifiez vos filtres de recherche.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full pb-32">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* Tâches actives en vol (en tête de grille) */}
        {activeTasks.map((task) => (
          <TaskProgressCard key={task.id} task={task} onCancel={onCancelTask} />
        ))}

        {/* Créations terminées */}
        {generations.map((gen) => (
          <MediaCard
            key={gen.id}
            generation={gen}
            onSelect={onSelectGeneration}
            onToggleFavorite={onToggleFavorite}
          />
        ))}
      </div>
    </div>
  );
}
