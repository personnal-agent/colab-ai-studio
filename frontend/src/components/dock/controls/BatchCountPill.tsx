import React from 'react';

interface BatchCountPillProps {
  value: number;
  allowedValues?: number[];
  onChange: (value: number) => void;
}

export const BatchCountPill: React.FC<BatchCountPillProps> = ({
  value,
  allowedValues = [1, 2, 4],
  onChange,
}) => {
  const handleClick = () => {
    const currentIndex = allowedValues.indexOf(value);
    const nextIndex = (currentIndex + 1) % allowedValues.length;
    onChange(allowedValues[nextIndex]);
  };

  return (
    <button
      type="button"
      aria-label="Batch count"
      title={`Tirages parallèles : ${value}`}
      onClick={handleClick}
      className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
    >
      <span className="text-studio-muted">⚏</span>
      <span> {value}</span>
    </button>
  );
};
