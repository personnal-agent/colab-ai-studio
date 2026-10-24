import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

export type DurationConfig =
  | string[]
  | { min: number; max: number; type: 'range' | 'discrete'; options?: string[] };

interface DurationControlPillProps {
  value: string;
  config?: DurationConfig;
  onChange: (duration: string) => void;
}

export const DurationControlPill: React.FC<DurationControlPillProps> = ({
  value,
  config = ['5s', '10s'],
  onChange,
}) => {
  const [open, setOpen] = useState(false);

  const isRange =
    typeof config === 'object' && !Array.isArray(config) && config.type === 'range';

  const rangeMin = isRange ? config.min : 4;
  const rangeMax = isRange ? config.max : 30;

  let discreteOptions: string[];
  if (Array.isArray(config)) {
    discreteOptions = config;
  } else if (config.options && config.options.length > 0) {
    discreteOptions = config.options;
  } else if (config.min !== undefined && config.max !== undefined) {
    const step = config.max - config.min >= 10 ? 5 : 1;
    const opts: string[] = [];
    for (let s = config.min; s <= config.max; s += step) {
      opts.push(`${s}s`);
    }
    if (!opts.includes(`${config.max}s`)) {
      opts.push(`${config.max}s`);
    }
    discreteOptions = opts;
  } else {
    discreteOptions = ['5s', '10s', '15s'];
  }

  const numericValue = parseInt(value, 10) || rangeMin;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Durée ${value}`}
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <span className="text-gray-400">⏱ </span>
          <span>{value || '5s'}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="center"
          sideOffset={8}
          className="z-50 min-w-[150px] p-2.5 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-2 focus:outline-none"
        >
          <div className="flex items-center justify-between text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            <span>Durée</span>
            <span className="text-gray-700">{value}</span>
          </div>

          {isRange ? (
            <div className="flex flex-col gap-1.5 pt-1">
              <input
                type="range"
                role="slider"
                aria-label="Durée en secondes"
                min={rangeMin}
                max={rangeMax}
                value={numericValue}
                onChange={(e) => onChange(`${e.target.value}s`)}
                className="w-full accent-gray-900 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-gray-400">
                <span>{rangeMin}s</span>
                <span>{rangeMax}s</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {discreteOptions.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                  }}
                  className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${
                    value === opt
                      ? 'bg-gray-900 text-white'
                      : 'bg-studio-subtle text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
