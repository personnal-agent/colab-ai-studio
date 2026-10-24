import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface UpscaleFrameRatePillProps {
  frameRate: string;
  onChange: (fps: string) => void;
}

const FPS_OPTIONS = ['Same as source', '24fps', '30fps', '60fps'];

export const UpscaleFrameRatePill: React.FC<UpscaleFrameRatePillProps> = ({
  frameRate,
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Cadence d'images ${frameRate}`}
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <span className="text-gray-400">🎞</span>
          <span>{frameRate || 'Same as source'}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="center"
          sideOffset={8}
          className="z-50 min-w-[130px] p-1.5 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-1 focus:outline-none"
        >
          <div className="px-2 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Cadence
          </div>
          {FPS_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => {
                onChange(opt);
                setOpen(false);
              }}
              className={`px-2.5 py-1.5 rounded-lg text-left text-xs font-medium transition-colors flex items-center justify-between ${
                frameRate === opt
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-700 hover:bg-studio-subtle'
              }`}
            >
              <span>{opt}</span>
              {frameRate === opt && <span className="text-[10px]">✓</span>}
            </button>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
