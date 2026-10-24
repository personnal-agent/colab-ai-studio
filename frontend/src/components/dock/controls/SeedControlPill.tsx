import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Dices } from 'lucide-react';

interface SeedControlPillProps {
  seed: number;
  onChange: (seed: number) => void;
}

export const SeedControlPill: React.FC<SeedControlPillProps> = ({ seed, onChange }) => {
  const [open, setOpen] = useState(false);
  const isRandom = seed === -1 || seed === undefined;

  const handleRandomToggle = () => {
    if (isRandom) onChange(Math.floor(Math.random() * 1000000));
    else onChange(-1);
  };

  const handleGenerateRandom = () => {
    onChange(Math.floor(Math.random() * 1000000));
  };

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Seed"
          className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
        >
          <Dices className="w-3.5 h-3.5 text-gray-400" />
          <span>{isRandom ? 'Aléatoire' : String(seed)}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="center"
          sideOffset={8}
          className="z-50 w-56 p-3 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-2.5 focus:outline-none"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-gray-900">Graine (Seed)</span>
            <button
              type="button"
              onClick={handleGenerateRandom}
              className="text-[11px] text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
            >
              🎲 Tirer
            </button>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              aria-label="Graine (seed)"
              disabled={isRandom}
              value={isRandom ? '' : seed}
              onChange={(e) => onChange(Number(e.target.value) || 0)}
              placeholder="Ex: 42"
              className="w-full px-2.5 py-1.5 rounded-lg border border-gray-200 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900 disabled:bg-gray-50 disabled:text-gray-400"
            />
          </div>
          <label className="flex items-center gap-2 cursor-pointer select-none text-[11px] text-gray-600">
            <input
              type="checkbox"
              checked={isRandom}
              onChange={handleRandomToggle}
              className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
            />
            <span>Graine aléatoire (-1)</span>
          </label>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
