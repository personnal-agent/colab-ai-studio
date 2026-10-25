import React, { useCallback, useEffect, useState } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Check, Cpu, Globe, HardDrive, Key, RefreshCw, Server, Settings, User } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { ExecutionMode, HealthResponse, StudioConfig } from '../../types/studio';

export const WorkerStatusAvatar: React.FC = () => {
  const [config, setConfig] = useState<StudioConfig | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Édition de la configuration Colab (Tunnel URL et Secret partagé)
  const [isEditingConfig, setIsEditingConfig] = useState(false);
  const [tunnelInput, setTunnelInput] = useState('');
  const [secretInput, setSecretInput] = useState('');
  const [savingConfig, setSavingConfig] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [cfg, h] = await Promise.all([apiClient.getConfig(), apiClient.getHealth()]);
      setConfig(cfg);
      setHealth(h);
      if (!isEditingConfig && cfg.colab?.tunnelUrl) {
        setTunnelInput(cfg.colab.tunnelUrl);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur télémétrie');
    } finally {
      setLoading(false);
    }
  }, [isEditingConfig]);

  useEffect(() => {
    void fetchStatus();
    const interval = setInterval(() => {
      void fetchStatus();
    }, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleSwitchMode = async (targetMode: ExecutionMode) => {
    try {
      setSwitching(true);
      setError(null);
      await apiClient.switchExecutionMode(targetMode);
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec bascule');
    } finally {
      setSwitching(false);
    }
  };

  const handleSaveColabConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tunnelInput.trim()) return;
    try {
      setSavingConfig(true);
      setError(null);
      await apiClient.updateColabUrl(tunnelInput.trim(), secretInput.trim() || undefined);
      setIsEditingConfig(false);
      setSecretInput('');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec mise à jour configuration Colab');
    } finally {
      setSavingConfig(false);
    }
  };

  const isColab = config?.executionMode === 'colab';
  const reachable = health?.worker?.reachable ?? false;

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Statut worker et compte"
          className="relative p-1.5 rounded-full border border-studio-border bg-white hover:bg-studio-subtle transition-colors shadow-sm flex items-center justify-center"
        >
          {isColab ? (
            <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-semibold text-xs">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div
              className="w-6 h-6 rounded-full flex items-center justify-center"
              style={{ backgroundColor: '#9CA3AF' }}
            >
              <Cpu className="w-3.5 h-3.5 text-white" />
            </div>
          )}
          <span
            className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${
              !reachable ? 'bg-rose-500' : isColab ? 'bg-emerald-500' : 'bg-emerald-400'
            }`}
          />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="w-84 bg-white rounded-2xl shadow-dropdown border border-studio-border p-4 z-50 animate-in fade-in zoom-in-95 space-y-3"
        >
          <div className="flex items-center justify-between border-b border-studio-border pb-2.5">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-indigo-600" />
              <h3 className="text-xs font-semibold text-gray-900">
                {isColab ? 'Mode Google Colab' : 'Mode Local'}
              </h3>
            </div>
            <div className="flex items-center gap-1">
              {isColab && (
                <button
                  type="button"
                  aria-label="Configurer la liaison Colab"
                  onClick={() => setIsEditingConfig(!isEditingConfig)}
                  className={`p-1 rounded-lg transition-colors ${
                    isEditingConfig
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-400 hover:text-gray-700 hover:bg-studio-subtle'
                  }`}
                >
                  <Settings className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                type="button"
                aria-label="Rafraîchir le statut du worker"
                onClick={fetchStatus}
                disabled={loading}
                className="p-1 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-studio-subtle transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
          {error && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
              {error}
            </div>
          )}
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-studio-divider">
              <span className="text-gray-500">Statut du worker :</span>
              <span className={`font-medium ${reachable ? 'text-emerald-600' : 'text-rose-600'}`}>
                {reachable ? 'En ligne' : 'Inaccessible'}
              </span>
            </div>
            {health?.worker?.gpu && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider">
                <span className="text-gray-500 flex items-center gap-1"><Cpu className="w-3.5 h-3.5 text-gray-400" /> GPU :</span>
                <span className="font-mono text-gray-900">{health.worker.gpu}</span>
              </div>
            )}
            {health?.worker?.vramFreeMb != null && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider">
                <span className="text-gray-500 flex items-center gap-1"><HardDrive className="w-3.5 h-3.5 text-gray-400" /> VRAM :</span>
                <span className="font-mono text-gray-900">{health.worker.vramFreeMb} Mo libre</span>
              </div>
            )}
            {health?.worker?.latencyMs != null && (
              <div className="flex items-center justify-between py-1 border-b border-studio-divider">
                <span className="text-gray-500">Latence réseau :</span>
                <span className="font-mono text-gray-900">{health.worker.latencyMs} ms</span>
              </div>
            )}

            {isColab && !isEditingConfig && config?.colab?.tunnelUrl && (
              <div className="flex flex-col gap-1 py-1">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 flex items-center gap-1"><Globe className="w-3.5 h-3.5 text-gray-400" /> Tunnel Colab :</span>
                  <button type="button" onClick={() => setIsEditingConfig(true)} className="text-[11px] text-indigo-600 hover:underline">Modifier</button>
                </div>
                <span className="font-mono text-[11px] text-gray-700 truncate bg-studio-canvas p-1.5 rounded border border-studio-border">
                  {config.colab.tunnelUrl}
                </span>
                {config.colab.secret && (
                  <span className="text-[11px] text-emerald-600 flex items-center gap-1 mt-0.5">
                    <Key className="w-3 h-3" /> Secret partagé configuré
                  </span>
                )}
              </div>
            )}

            {isColab && isEditingConfig && (
              <form onSubmit={handleSaveColabConfig} className="p-2.5 bg-gray-50 rounded-xl border border-studio-border space-y-2 mt-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-gray-700 flex items-center gap-1"><Globe className="w-3 h-3 text-gray-400" /> URL du tunnel :</label>
                  <input type="url" required value={tunnelInput} onChange={(e) => setTunnelInput(e.target.value)} placeholder="https://xxxx.trycloudflare.com" className="w-full h-7 px-2 text-xs font-mono border border-studio-border rounded bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-gray-700 flex items-center gap-1"><Key className="w-3 h-3 text-gray-400" /> Secret du worker :</label>
                  <input type="password" value={secretInput} onChange={(e) => setSecretInput(e.target.value)} placeholder={config?.colab?.secret ? '••••••••' : 'Jeton affiché dans le notebook'} className="w-full h-7 px-2 text-xs font-mono border border-studio-border rounded bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                </div>
                <div className="flex items-center justify-end gap-1.5 pt-1">
                  <button type="button" onClick={() => setIsEditingConfig(false)} className="px-2 h-6 text-[11px] text-gray-600 hover:text-gray-800 rounded">Annuler</button>
                  <button type="submit" disabled={savingConfig} className="px-2.5 h-6 text-[11px] font-medium bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors flex items-center gap-1">
                    <Check className="w-3 h-3" /><span>Enregistrer</span>
                  </button>
                </div>
              </form>
            )}
          </div>
          <div className="pt-2 border-t border-studio-border">
            <button
              type="button"
              disabled={switching}
              onClick={() => handleSwitchMode(isColab ? 'local' : 'colab')}
              className="w-full h-8 text-xs font-medium rounded-lg border border-studio-border bg-studio-canvas hover:bg-studio-subtle text-gray-800 transition-colors flex items-center justify-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${switching ? 'animate-spin' : ''}`} />
              <span>Basculer vers {isColab ? 'Mode Local' : 'Google Colab'}</span>
            </button>
          </div>
          <Popover.Arrow className="fill-white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
