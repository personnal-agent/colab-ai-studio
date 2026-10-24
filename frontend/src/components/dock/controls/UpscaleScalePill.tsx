import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface UpscaleScalePillProps {
  scale: string;
  onChange: (scale: string) => void;
}

const SCALE_OPTIONS = ['1.25x', '2x', '4x'];

export const UpscaleScalePill: React.FC<UpscaleScalePillProps> = ({ scale, onChange }) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Échelle d'agrandissement ${scale}`}
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <span>⊕ </span>
          <span>{scale || '2x'}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="center"
          sideOffset={8}
          className="z-50 min-w-[100px] p-1.5 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-1 focus:outline-none"
        >
          <div className="px-2 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Échelle
          </div>
          {SCALE_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => {
                onChange(opt);
                setOpen(false);
              }}
              className={`px-2.5 py-1.5 rounded-lg text-left text-xs font-medium transition-colors flex items-center justify-between ${
                scale === opt ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-studio-subtle'
              }`}
            >
              <span>{opt}</span>
              {scale === opt && <span className="text-[10px]">✓</span>}
            </button>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
