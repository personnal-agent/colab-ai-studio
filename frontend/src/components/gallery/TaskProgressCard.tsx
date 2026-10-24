import React, { useState } from 'react';
import { Loader2, XCircle } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { TaskStatusEvent } from '../../types/studio';

export interface TaskProgressCardProps {
  event: TaskStatusEvent; prompt: string; modelName: string; onCancelled: (taskId: string) => void;
}

export const TaskProgressCard: React.FC<TaskProgressCardProps> = ({ event, prompt, modelName, onCancelled }) => {
  const [cancelling, setCancelling] = useState(false);
  const handleCancel = async () => {
    setCancelling(true);
    try { await apiClient.cancelTask(event.taskId); onCancelled(event.taskId); }
    catch (err) { console.error('Failed to cancel task:', err); }
    finally { setCancelling(false); }
  };
  const progressPercent = Math.min(100, Math.max(0, event.progress || 0));

  return (
    <div data-testid={`task-progress-${event.taskId}`} className="bg-white rounded-dock border border-indigo-200 p-4 shadow-sm animate-pulse-glow flex flex-col justify-between transition-all">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2"><Loader2 className="w-4 h-4 text-indigo-600 animate-spin" /><span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Génération en cours</span></div>
        <span className="text-xs font-mono font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{modelName}</span>
      </div>
      <div className="my-3 space-y-2">
        <p className="text-xs text-gray-900 font-medium line-clamp-2" title={prompt}>{prompt}</p>
        {event.step && <p className="text-[11px] text-gray-500 font-mono truncate">{event.step}</p>}
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
          <div className="bg-indigo-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs font-mono font-bold text-indigo-600">{progressPercent}%</span>
        <button type="button" onClick={handleCancel} disabled={cancelling} aria-label="Annuler la tâche" className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded transition-colors flex items-center gap-1 disabled:opacity-50">
          <XCircle className="w-3.5 h-3.5" /><span>Annuler</span>
        </button>
      </div>
    </div>
  );
};
