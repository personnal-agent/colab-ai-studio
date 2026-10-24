import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface ResolutionPillProps {
  value: string;
  options?: string[];
  onChange: (resolution: string) => void;
}

const DEFAULT_RESOLUTIONS = ['720p', '1080p', '4K'];

export const ResolutionPill: React.FC<ResolutionPillProps> = ({
  value,
  options = DEFAULT_RESOLUTIONS,
  onChange,
}) => {
  const [open, setOpen] = useState(false);
  const items = options.length > 0 ? options : DEFAULT_RESOLUTIONS;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Résolution ${value}`}
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <span className="text-gray-400">⇅</span>
          <span>{value || '720p'}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="center"
          sideOffset={8}
          className="z-50 min-w-[120px] p-1.5 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-1 focus:outline-none"
        >
          <div className="px-2 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Définition
          </div>
          {items.map((res) => (
            <button
              key={res}
              type="button"
              onClick={() => {
                onChange(res);
                setOpen(false);
              }}
              className={`px-2.5 py-1.5 rounded-lg text-left text-xs font-medium transition-colors flex items-center justify-between ${
                value === res
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-700 hover:bg-studio-subtle'
              }`}
            >
              <span>{res}</span>
              {value === res && <span className="text-[10px]">✓</span>}
            </button>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
