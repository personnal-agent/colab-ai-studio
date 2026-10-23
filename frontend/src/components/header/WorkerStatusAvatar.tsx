import * as Popover from '@radix-ui/react-popover';
import { Activity, AlertCircle, Cpu, HardDrive, RefreshCw, Server, User } from 'lucide-react';
import { useState } from 'react';
import { apiClient } from '../../services/apiClient';
import { ExecutionMode, HealthResponse } from '../../types/studio';

interface WorkerStatusAvatarProps {
  health: HealthResponse | null;
  executionMode: ExecutionMode;
  onModeChange: (newMode: ExecutionMode) => void;
}

export function WorkerStatusAvatar({
  health,
  executionMode,
  onModeChange,
}: WorkerStatusAvatarProps) {
  const [isSwitching, setIsSwitching] = useState(false);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const isColab = executionMode === 'colab';
  const isReachable = health?.activeWorkerReachable ?? false;

  const handleSwitchMode = async () => {
    const targetMode: ExecutionMode = isColab ? 'local' : 'colab';
    setIsSwitching(true);
    setSwitchError(null);
    try {
      const res = await apiClient.switchExecutionMode(targetMode);
      onModeChange(res.executionMode);
    } catch (err) {
      setSwitchError(
        err instanceof Error ? err.message : 'Erreur lors du changement de mode de calcul'
      );
    } finally {
      setIsSwitching(false);
    }
  };

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Statut du worker d'exécution"
          className="relative p-2 rounded-slot text-gray-700 hover:bg-studio-subtle transition-colors flex items-center justify-center border border-studio-border bg-white shadow-card"
          title={`Mode actif : ${isColab ? 'Google Colab' : 'Local Host'}`}
        >
          <User className="w-5 h-5" />
          {/* Pastille indicatrice */}
          <span
            className={`absolute bottom-1 right-1 w-2.5 h-2.5 rounded-full ring-2 ring-white ${
              !isColab
                ? 'bg-[#9CA3AF]' // Mode Local : gris neutre #9CA3AF
                : isReachable
                  ? 'bg-emerald-500' // Colab connecté : vert
                  : 'bg-amber-500' // Colab injoignable : ambre
            }`}
          />
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="w-80 bg-white rounded-menu shadow-dropdown border border-studio-border p-4 z-50 animate-in fade-in zoom-in-95"
        >
          <div className="flex items-center justify-between pb-3 border-b border-studio-border mb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-gray-700" />
              <span className="text-sm font-semibold text-gray-900">
                Mode d&apos;exécution : {isColab ? 'Google Colab' : 'Local'}
              </span>
            </div>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-pill ${
                isColab
                  ? isReachable
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-gray-100 text-gray-600 border border-gray-200'
              }`}
            >
              {isColab ? (isReachable ? 'En ligne' : 'Injoignable') : 'Machine Hôte'}
            </span>
          </div>

          {/* Diagnostic GPU / Latence */}
          <div className="space-y-2 text-xs text-gray-600 mb-4">
            <div className="flex items-center justify-between p-2 rounded-slot bg-studio-canvas">
              <div className="flex items-center gap-1.5 text-gray-500">
                <Cpu className="w-3.5 h-3.5" />
                <span>GPU / Périphérique</span>
              </div>
              <span className="font-medium text-gray-800 truncate max-w-[150px]">
                {health?.worker?.gpu || (isColab ? 'GPU Colab' : 'CPU Local')}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded-slot bg-studio-canvas">
              <div className="flex items-center gap-1.5 text-gray-500">
                <HardDrive className="w-3.5 h-3.5" />
                <span>VRAM disponible</span>
              </div>
              <span className="font-medium text-gray-800">
                {health?.worker?.vramFreeMb ? `${health.worker.vramFreeMb} Mo` : 'N/A'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded-slot bg-studio-canvas">
              <div className="flex items-center gap-1.5 text-gray-500">
                <Activity className="w-3.5 h-3.5" />
                <span>Latence</span>
              </div>
              <span className="font-medium text-gray-800">
                {health?.worker?.latencyMs ? `${health.worker.latencyMs} ms` : 'N/A'}
              </span>
            </div>
          </div>

          {switchError && (
            <div className="text-xs text-red-600 bg-red-50 p-2.5 rounded-slot mb-3 flex items-start gap-1.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>{switchError}</span>
            </div>
          )}

          {/* Commutateur à chaud Local / Colab */}
          <div className="pt-2 border-t border-studio-border">
            <button
              type="button"
              disabled={isSwitching}
              onClick={handleSwitchMode}
              className="w-full py-2 px-3 bg-gray-900 text-white rounded-slot text-xs font-medium hover:bg-black transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSwitching ? 'animate-spin' : ''}`} />
              <span>
                {isSwitching
                  ? 'Commutation en cours...'
                  : isColab
                    ? 'Basculer vers Local'
                    : 'Basculer vers Colab'}
              </span>
            </button>
            <p className="text-[10px] text-gray-400 mt-2 text-center">
              Bascule à chaud instantanée (Issue #2). Aucune perte de données.
            </p>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
