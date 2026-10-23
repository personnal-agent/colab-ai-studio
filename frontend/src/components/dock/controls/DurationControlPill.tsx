import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface DurationControlPillProps {
  mode?: 'discrete' | 'range';
  value: string;
  allowedDurations?: string[];
  range?: { min: number; max: number; step?: number };
  onChange: (value: string) => void;
}

const DEFAULT_DISCRETE = ['5s', '10s'];

export const DurationControlPill: React.FC<DurationControlPillProps> = ({
  mode = 'discrete',
  value,
  allowedDurations = DEFAULT_DISCRETE,
  range = { min: 4, max: 30, step: 1 },
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  // Extraire la valeur numérique pour le curseur
  const numericVal = parseInt(value.replace(/[^0-9]/g, ''), 10) || range.min;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Duration"
          title={`Durée de séquence : ${value}`}
          className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
        >
          <span className="text-studio-muted">⏱</span>
          <span> {value}</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="center"
          sideOffset={8}
          className="z-50 p-3 bg-white rounded-xl shadow-lg border border-studio-border text-xs focus:outline-none min-w-[160px]"
        >
          <div className="text-[11px] font-semibold text-studio-muted mb-2">
            Durée de génération
          </div>

          {mode === 'range' ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-studio-muted">{range.min}s</span>
                <span className="text-studio-text font-bold">{numericVal}s</span>
                <span className="text-studio-muted">{range.max}s</span>
              </div>
              <input
                type="range"
                role="slider"
                min={range.min}
                max={range.max}
                step={range.step || 1}
                value={numericVal}
                onChange={(e) => onChange(`${e.target.value}s`)}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-studio-text"
              />
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {allowedDurations.map((dur) => {
                const isSelected = dur === value;
                return (
                  <button
                    key={dur}
                    type="button"
                    aria-label={dur}
                    onClick={() => {
                      onChange(dur);
                      setOpen(false);
                    }}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors flex items-center justify-between ${
                      isSelected
                        ? 'bg-studio-text text-white'
                        : 'text-studio-text hover:bg-studio-subtle'
                    }`}
                  >
                    <span>{dur}</span>
                    {isSelected && <span className="text-[10px]">✓</span>}
                  </button>
                );
              })}
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
