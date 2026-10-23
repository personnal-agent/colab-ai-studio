import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface ResolutionPillProps {
  value: string;
  allowedResolutions?: string[];
  onChange: (value: string) => void;
}

const DEFAULT_RESOLUTIONS = ['720p', '1080p', '4K'];

export const ResolutionPill: React.FC<ResolutionPillProps> = ({
  value,
  allowedResolutions = DEFAULT_RESOLUTIONS,
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Resolution"
          title={`Définition & Résolution : ${value}`}
          className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
        >
          <span className="text-studio-muted">⇅</span>
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
            Résolution
          </div>
          <div className="flex flex-col gap-1 min-w-[120px]">
            {allowedResolutions.map((res) => {
              const isSelected = res === value;
              return (
                <button
                  key={res}
                  type="button"
                  aria-label={res}
                  onClick={() => {
                    onChange(res);
                    setOpen(false);
                  }}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-studio-text text-white'
                      : 'text-studio-text hover:bg-studio-subtle'
                  }`}
                >
                  <span>{res}</span>
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
