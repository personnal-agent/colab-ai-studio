import { Loader2, StopCircle } from 'lucide-react';
import { Generation } from '../../types/studio';

interface TaskProgressCardProps {
  task: Generation;
  onCancel: (taskId: string) => void;
}

export function TaskProgressCard({ task, onCancel }: TaskProgressCardProps) {
  const isRunning = task.status === 'running';

  return (
    <div className="relative overflow-hidden rounded-slot bg-studio-card border border-indigo-200 shadow-card p-4 flex flex-col justify-between aspect-video transition-all animate-pulse-glow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
          <span className="text-xs font-semibold text-indigo-900 truncate max-w-[140px]">
            {task.modelName || task.modelId}
          </span>
        </div>
        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-pill bg-indigo-50 text-indigo-700 border border-indigo-200">
          {isRunning ? 'Calcul en cours' : 'En attente'}
        </span>
      </div>

      <div className="my-2">
        <p className="text-xs text-gray-700 line-clamp-2 italic font-normal">
          &ldquo;{task.prompt}&rdquo;
        </p>
      </div>

      <div className="space-y-2">
        {/* Jauge de progression */}
        <div className="flex items-center justify-between text-[11px] font-medium text-gray-600">
          <span>Progression</span>
          <span className="text-indigo-600 font-semibold">{task.progress}%</span>
        </div>
        <div className="w-full bg-studio-subtle rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-indigo-600 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.max(5, task.progress)}%` }}
          />
        </div>

        {/* Bouton d'annulation */}
        <div className="pt-1 flex justify-end">
          <button
            type="button"
            aria-label="Annuler la tâche"
            onClick={(e) => {
              e.stopPropagation();
              onCancel(task.id);
            }}
            className="text-[11px] text-red-600 hover:text-red-700 hover:bg-red-50 font-medium py-1 px-2.5 rounded-slot flex items-center gap-1 transition-colors border border-transparent hover:border-red-200"
          >
            <StopCircle className="w-3.5 h-3.5" />
            <span>Annuler</span>
          </button>
        </div>
      </div>
    </div>
  );
}
