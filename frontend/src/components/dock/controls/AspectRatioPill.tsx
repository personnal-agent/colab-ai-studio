import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface AspectRatioPillProps {
  value: string;
  allowedRatios?: string[];
  onChange: (value: string) => void;
}

const DEFAULT_RATIOS = ['16:9', '9:16', '1:1', '4:5', '3:4', '21:9', '4:3'];

export const AspectRatioPill: React.FC<AspectRatioPillProps> = ({
  value,
  allowedRatios = DEFAULT_RATIOS,
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Aspect ratio"
          title={`Format & Ratio : ${value}`}
          className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
        >
          <span className="text-studio-muted">▭</span>
          <span> {value}</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="center"
          sideOffset={8}
          className="z-50 p-2 bg-white rounded-xl shadow-lg border border-studio-border text-xs focus:outline-none"
        >
          <div className="text-[11px] font-semibold text-studio-muted px-2 py-1">
            Format d'image
          </div>
          <div className="grid grid-cols-2 gap-1 min-w-[140px]">
            {allowedRatios.map((ratio) => {
              const isSelected = ratio === value;
              return (
                <button
                  key={ratio}
                  type="button"
                  aria-label={ratio}
                  onClick={() => {
                    onChange(ratio);
                    setOpen(false);
                  }}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-studio-text text-white'
                      : 'text-studio-text hover:bg-studio-subtle'
                  }`}
                >
                  <span>{ratio}</span>
                  {isSelected && <span className="text-[10px]">✓</span>}
                </button>
              );
            })}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
