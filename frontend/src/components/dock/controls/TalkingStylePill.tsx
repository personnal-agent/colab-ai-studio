import React from 'react';

interface TalkingStylePillProps {
  value: string;
  onChange: (value: string) => void;
}

export const TalkingStylePill: React.FC<TalkingStylePillProps> = ({ value, onChange }) => {
  const isExpressive = value.toLowerCase() === 'expressive';

  const handleClick = () => {
    onChange(isExpressive ? 'Stable' : 'Expressive');
  };

  return (
    <button
      type="button"
      aria-label="Talking style"
      title={`Style d'élocution : ${value}`}
      onClick={handleClick}
      className={`h-8 px-3 rounded-pill border transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none ${
        isExpressive
          ? 'border-purple-300 bg-purple-50 text-purple-800 hover:bg-purple-100'
          : 'border-studio-border bg-white text-studio-text hover:bg-studio-subtle'
      }`}
    >
      <span className="text-studio-muted">🗣️</span>
      <span>{value}</span>
    </button>
  );
};
