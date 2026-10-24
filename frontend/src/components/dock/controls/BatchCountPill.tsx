import React from 'react';

interface BatchCountPillProps {
  count: number;
  onChange: (count: number) => void;
}

export const BatchCountPill: React.FC<BatchCountPillProps> = ({ count, onChange }) => {
  const handleClick = () => {
    const next = count >= 4 ? 1 : count + 1;
    onChange(next);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`Batch count: ${count}`}
      className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
    >
      <span className="text-gray-400">⚏ </span>
      <span>{count}</span>
    </button>
  );
};
