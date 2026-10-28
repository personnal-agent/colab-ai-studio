import React from 'react';
import { Sparkles, Bot } from 'lucide-react';

export type AppMode = 'Studio' | 'Agents';

export interface AppModeSwitchProps {
  mode: AppMode;
  onChange: (mode: AppMode) => void;
  className?: string;
}

export const AppModeSwitch: React.FC<AppModeSwitchProps> = ({
  mode,
  onChange,
  className = '',
}) => {
  const handleSelectMode = (newMode: AppMode) => {
    if (newMode === mode) return;
    onChange(newMode);
    if (typeof window !== 'undefined' && window.electron?.switchMode) {
      window.electron.switchMode(newMode).catch((err: unknown) => {
        console.warn('[AppModeSwitch] Erreur lors du basculement Electron:', err);
      });
    }
  };

  return (
    <div
      data-testid="app-mode-switch"
      role="tablist"
      aria-label="Mode de l'application"
      className={`inline-flex items-center bg-[#EFEFEF] dark:bg-gray-800 p-0.5 rounded-full border border-gray-200 dark:border-gray-700 select-none ${className}`}
    >
      <button
        type="button"
        role="tab"
        id="mode-studio-tab"
        aria-selected={mode === 'Studio'}
        data-testid="app-mode-studio"
        onClick={() => handleSelectMode('Studio')}
        className={`flex items-center space-x-1.5 px-3 py-1 text-xs rounded-full transition-all duration-150 ${
          mode === 'Studio'
            ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-semibold shadow-sm'
            : 'text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 font-medium'
        }`}
      >
        <Sparkles className="w-3.5 h-3.5" strokeWidth={1.75} />
        <span>Studio</span>
      </button>

      <button
        type="button"
        role="tab"
        id="mode-agents-tab"
        aria-selected={mode === 'Agents'}
        data-testid="app-mode-agents"
        onClick={() => handleSelectMode('Agents')}
        className={`flex items-center space-x-1.5 px-3 py-1 text-xs rounded-full transition-all duration-150 ${
          mode === 'Agents'
            ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-semibold shadow-sm'
            : 'text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 font-medium'
        }`}
      >
        <Bot className="w-3.5 h-3.5" strokeWidth={1.75} />
        <span>Agents</span>
      </button>
    </div>
  );
};
