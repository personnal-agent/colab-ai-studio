import React, { useState, useRef, useEffect } from 'react';
import { Cpu, Cloud, Shuffle, ChevronDown } from 'lucide-react';
import type { EnginePreference } from '../../types/studio';

export interface EngineSelectorPillProps {
  value: EnginePreference;
  onChange: (value: EnginePreference) => void;
  className?: string;
}

const ENGINE_OPTIONS: Array<{
  id: EnginePreference;
  label: string;
  badge: string;
  description: string;
  icon: React.FC<{ className?: string }>;
  colorClasses: string;
  activeColorClasses: string;
}> = [
  {
    id: 'local',
    label: 'Local RTX 5000 Ada',
    badge: '16GB VRAM • 0s Latence',
    description: 'Inférence locale directe sur ComfyUI GPU',
    icon: Cpu,
    colorClasses: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20',
    activeColorClasses: 'bg-emerald-500/20 text-emerald-300 border-emerald-400',
  },
  {
    id: 'cloud',
    label: 'Cloud API',
    badge: 'Colab / RunPod distant',
    description: 'Délégation vers GPU cloud distant',
    icon: Cloud,
    colorClasses: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10 hover:bg-indigo-500/20',
    activeColorClasses: 'bg-indigo-500/20 text-indigo-300 border-indigo-400',
  },
  {
    id: 'hybrid',
    label: 'Hybride',
    badge: 'Storyboard Cloud + GPU Local',
    description: 'Découpage LLM Cloud & rendu haute fidélité sur RTX 5000',
    icon: Shuffle,
    colorClasses: 'text-purple-400 border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20',
    activeColorClasses: 'bg-purple-500/20 text-purple-300 border-purple-400',
  },
];

export const EngineSelectorPill: React.FC<EngineSelectorPillProps> = ({
  value,
  onChange,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentOption = ENGINE_OPTIONS.find((o) => o.id === value) || ENGINE_OPTIONS[0];
  const Icon = currentOption.icon;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div ref={containerRef} className={`relative inline-block ${className}`}>
      <button
        type="button"
        role="button"
        aria-label={`Moteur: ${currentOption.label}`}
        onClick={() => setIsOpen((prev) => !prev)}
        className={`px-2.5 py-1 rounded-full text-[11px] font-medium border flex items-center space-x-1.5 transition-all shadow-xs ${currentOption.colorClasses}`}
      >
        <Icon className="w-3.5 h-3.5 flex-shrink-0" />
        <span className="font-semibold tracking-tight">{currentOption.label}</span>
        <ChevronDown className="w-3 h-3 opacity-70" />
      </button>

      {isOpen && (
        <div
          data-testid="engine-selector-menu"
          className="absolute bottom-full left-0 mb-2 w-64 bg-[#18191d] text-white border border-white/10 rounded-2xl shadow-xl p-1.5 z-50 flex flex-col gap-1 backdrop-blur-md animate-fade-in"
        >
          <div className="px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-400 border-b border-white/5">
            Moteur d'Exécution (Google Flow Pro)
          </div>
          {ENGINE_OPTIONS.map((opt) => {
            const OptIcon = opt.icon;
            const isSelected = opt.id === value;
            return (
              <button
                key={opt.id}
                type="button"
                role="button"
                aria-label={`Option ${opt.label}`}
                onClick={() => {
                  onChange(opt.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left p-2 rounded-xl border text-xs flex items-start gap-2.5 transition-colors ${
                  isSelected
                    ? opt.activeColorClasses
                    : 'border-transparent hover:bg-white/5 text-neutral-300'
                }`}
              >
                <div className="mt-0.5 p-1 rounded-lg bg-black/40 border border-white/5">
                  <OptIcon className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="flex-1">
                  <div className="font-bold flex items-center justify-between text-white">
                    <span>{opt.label}</span>
                    {isSelected && <span className="text-[10px] font-mono text-emerald-400">✓ Actif</span>}
                  </div>
                  <div className="text-[10px] text-neutral-400">{opt.description}</div>
                  <div className="text-[9px] font-mono text-neutral-500 mt-0.5">{opt.badge}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
