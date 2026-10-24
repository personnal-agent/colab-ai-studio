import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { SlidersHorizontal } from 'lucide-react';

interface FineSettingsPopoverProps {
  negativePrompt?: string;
  onNegativePromptChange?: (val: string) => void;
  steps?: number;
  onStepsChange?: (val: number) => void;
  guidanceScale?: number;
  onGuidanceScaleChange?: (val: number) => void;
}

export const FineSettingsPopover: React.FC<FineSettingsPopoverProps> = ({
  negativePrompt = '',
  onNegativePromptChange,
  steps = 20,
  onStepsChange,
  guidanceScale = 7.5,
  onGuidanceScaleChange,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Réglages fins"
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-gray-500" />
          <span className="hidden sm:inline">🎛️</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="end"
          sideOffset={8}
          className="z-50 w-72 p-3.5 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-3 focus:outline-none"
        >
          <div className="flex items-center justify-between pb-1 border-b border-gray-100">
            <span className="font-semibold text-gray-900">Paramètres experts</span>
            <span className="text-[10px] text-gray-400">Fine tuning</span>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium text-gray-600">Prompt négatif</label>
            <textarea
              rows={2}
              value={negativePrompt}
              onChange={(e) => onNegativePromptChange?.(e.target.value)}
              placeholder="Éléments indésirables (flou, déformation...)"
              className="w-full px-2 py-1.5 rounded-lg border border-gray-200 text-xs resize-none focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <span className="text-[11px] text-gray-600">Étapes (Steps : {steps})</span>
            <input
              type="range"
              min={10}
              max={50}
              value={steps}
              onChange={(e) => onStepsChange?.(Number(e.target.value))}
              className="w-32 accent-gray-900 cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <span className="text-[11px] text-gray-600">CFG Scale ({guidanceScale})</span>
            <input
              type="range"
              min={1}
              max={20}
              step={0.5}
              value={guidanceScale}
              onChange={(e) => onGuidanceScaleChange?.(Number(e.target.value))}
              className="w-32 accent-gray-900 cursor-pointer"
            />
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
