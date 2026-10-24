import React, { useEffect, useState } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Cpu, Globe, HardDrive, RefreshCw, Server, User } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { ExecutionMode, HealthResponse, StudioConfig } from '../../types/studio';

export const WorkerStatusAvatar: React.FC = () => {
  const [config, setConfig] = useState<StudioConfig | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true); setError(null);
      const [cfg, h] = await Promise.all([apiClient.getConfig(), apiClient.getHealth()]);
      setConfig(cfg); setHealth(h);
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur télémétrie'); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    void fetchStatus();
    const interval = setInterval(() => { void fetchStatus(); }, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSwitchMode = async (targetMode: ExecutionMode) => {
    try {
      setSwitching(true); setError(null);
      await apiClient.switchExecutionMode(targetMode);
      await fetchStatus();
    } catch (err) { setError(err instanceof Error ? err.message : 'Échec bascule'); }
    finally { setSwitching(false); }
  };

  const isColab = config?.executionMode === 'colab';
  const reachable = health?.worker?.reachable ?? false;

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" aria-label="Statut worker et compte" className="relative p-1.5 rounded-full border border-studio-border bg-white hover:bg-studio-subtle transition-colors shadow-sm flex items-center justify-center">
          {isColab ? (
            <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-semibold text-xs"><User className="w-4 h-4" /></div>
          ) : (
            <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: '#9CA3AF' }}><Cpu className="w-3.5 h-3.5 text-white" /></div>
          )}
          <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${!reachable ? 'bg-rose-500' : isColab ? 'bg-emerald-500' : 'bg-emerald-400'}`} />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={8} className="w-80 bg-white rounded-2xl shadow-dropdown border border-studio-border p-4 z-50 animate-in fade-in zoom-in-95 space-y-3">
          <div className="flex items-center justify-between border-b border-studio-border pb-2.5">
            <div className="flex items-center gap-2"><Server className="w-4 h-4 text-indigo-600" /><h3 className="text-xs font-semibold text-gray-900">{isColab ? 'Mode Google Colab' : 'Mode Local'}</h3></div>
            <button type="button" onClick={fetchStatus} disabled={loading} className="p-1 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-studio-subtle transition-colors"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /></button>
          </div>
          {error && <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">{error}</div>}
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-studio-divider"><span className="text-gray-500">Statut du worker :</span><span className={`font-medium ${reachable ? 'text-emerald-600' : 'text-rose-600'}`}>{reachable ? 'En ligne' : 'Inaccessible'}</span></div>
            {health?.worker?.gpu && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider"><span className="text-gray-500 flex items-center gap-1"><Cpu className="w-3.5 h-3.5 text-gray-400" />GPU :</span><span className="font-mono text-gray-900">{health.worker.gpu}</span></div>
            )}
            {health?.worker?.vramFreeMb !== undefined && health.worker.vramFreeMb !== null && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider"><span className="text-gray-500 flex items-center gap-1"><HardDrive className="w-3.5 h-3.5 text-gray-400" />VRAM :</span><span className="font-mono text-gray-900">{health.worker.vramFreeMb} Mo libre</span></div>
            )}
            {health?.worker?.latencyMs !== undefined && health.worker.latencyMs !== null && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider"><span className="text-gray-500">Latence réseau :</span><span className="font-mono text-gray-900">{health.worker.latencyMs} ms</span></div>
            )}
            {isColab && config?.colab?.tunnelUrl && (
              <div className="flex flex-col gap-1 py-1"><span className="text-gray-500 flex items-center gap-1"><Globe className="w-3.5 h-3.5 text-gray-400" />Tunnel Colab :</span><span className="font-mono text-[11px] text-gray-700 truncate bg-studio-canvas p-1.5 rounded border border-studio-border">{config.colab.tunnelUrl}</span></div>
            )}
          </div>
          <div className="pt-2 border-t border-studio-border">
            <button type="button" disabled={switching} onClick={() => handleSwitchMode(isColab ? 'local' : 'colab')} className="w-full h-8 text-xs font-medium rounded-lg border border-studio-border bg-studio-canvas hover:bg-studio-subtle text-gray-800 transition-colors flex items-center justify-center gap-1.5">
              <RefreshCw className={`w-3.5 h-3.5 ${switching ? 'animate-spin' : ''}`} /><span>Basculer vers {isColab ? 'Mode Local' : 'Google Colab'}</span>
            </button>
          </div>
          <Popover.Arrow className="fill-white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
