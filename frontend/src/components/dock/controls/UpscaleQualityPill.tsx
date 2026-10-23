import React from 'react';

interface UpscaleQualityPillProps {
  value: string;
  allowedQualities?: string[];
  onChange: (value: string) => void;
}

const DEFAULT_QUALITIES = ['Fast', 'Precise'];

export const UpscaleQualityPill: React.FC<UpscaleQualityPillProps> = ({
  value,
  allowedQualities = DEFAULT_QUALITIES,
  onChange,
}) => {
  const handleClick = () => {
    const currentIndex = allowedQualities.indexOf(value);
    const nextIndex = (currentIndex + 1) % allowedQualities.length;
    onChange(allowedQualities[nextIndex]);
  };

  return (
    <button
      type="button"
      aria-label="Quality"
      title={`Qualité de suréchantillon : ${value}`}
      onClick={handleClick}
      className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
    >
      <span className="text-studio-muted">💎</span>
      <span>{value}</span>
    </button>
  );
};
