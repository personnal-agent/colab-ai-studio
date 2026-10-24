import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface AspectRatioPillProps {
  value: string;
  options?: string[];
  onChange: (ratio: string) => void;
}

const DEFAULT_RATIOS = ['16:9', '9:16', '1:1', '4:3', '21:9'];

export const AspectRatioPill: React.FC<AspectRatioPillProps> = ({
  value,
  options = DEFAULT_RATIOS,
  onChange,
}) => {
  const [open, setOpen] = useState(false);
  const items = options.length > 0 ? options : DEFAULT_RATIOS;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Format ${value}`}
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <span className="text-gray-400">▭</span>
          <span>{value || '16:9'}</span>
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
            Format & Ratio
          </div>
          {items.map((ratio) => (
            <button
              key={ratio}
              type="button"
              onClick={() => {
                onChange(ratio);
                setOpen(false);
              }}
              className={`px-2.5 py-1.5 rounded-lg text-left text-xs font-medium transition-colors flex items-center justify-between ${
                value === ratio
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-700 hover:bg-studio-subtle'
              }`}
            >
              <span>{ratio}</span>
              {value === ratio && <span className="text-[10px]">✓</span>}
            </button>
          ))}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
