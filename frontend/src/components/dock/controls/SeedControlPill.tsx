import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface SeedControlPillProps {
  value: number;
  onChange: (value: number) => void;
}

export const SeedControlPill: React.FC<SeedControlPillProps> = ({ value, onChange }) => {
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value >= 0 ? String(value) : '');

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (nextOpen) {
      setInputValue(value >= 0 ? String(value) : '');
    }
  };

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(inputValue, 10);
    if (!isNaN(parsed) && parsed >= 0) {
      onChange(parsed);
    } else {
      onChange(-1);
    }
    setOpen(false);
  };

  const handleReset = () => {
    onChange(-1);
    setInputValue('');
    setOpen(false);
  };

  const isRandom = value < 0;

  return (
    <Popover.Root open={open} onOpenChange={handleOpenChange}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Seed"
          title={`Graine aléatoire : ${isRandom ? 'Aléatoire (-1)' : value}`}
          className={`h-8 px-3 rounded-pill border transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none ${
            isRandom
              ? 'border-studio-border bg-white text-studio-text hover:bg-studio-subtle'
              : 'border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
          }`}
        >
          <span>🎲</span>
          <span> {isRandom ? 'Random' : value}</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="center"
          sideOffset={8}
          className="z-50 w-52 p-3 bg-white rounded-xl shadow-lg border border-studio-border text-xs focus:outline-none"
        >
          <form onSubmit={handleApply} className="space-y-2">
            <label htmlFor="dock-seed-input" className="block font-semibold text-studio-text">
              Graine (Seed)
            </label>
            <input
              id="dock-seed-input"
              type="number"
              placeholder="Seed (ex: 42)"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full px-2 py-1 border border-studio-border rounded-md text-xs focus:ring-1 focus:ring-studio-accent focus:outline-none"
              autoFocus
            />
            <div className="flex items-center justify-end gap-1.5 pt-1">
              <button
                type="button"
                onClick={handleReset}
                className="px-2 py-1 text-studio-muted hover:text-studio-text hover:bg-studio-subtle rounded transition-colors"
              >
                Aléatoire
              </button>
              <button
                type="submit"
                aria-label="Appliquer"
                className="px-2.5 py-1 bg-studio-text text-white rounded font-medium hover:bg-black transition-colors"
              >
                Appliquer
              </button>
            </div>
          </form>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
