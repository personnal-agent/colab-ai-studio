import React from 'react';

interface TalkingStylePillProps {
  style: string;
  onChange: (style: string) => void;
}

export const TalkingStylePill: React.FC<TalkingStylePillProps> = ({ style, onChange }) => {
  const handleClick = () => {
    onChange(style === 'Stable' ? 'Expressive' : 'Stable');
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`Talking style: ${style || 'Stable'}`}
      className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
    >
      <span className="text-gray-400">🗣</span>
      <span>{style || 'Stable'}</span>
    </button>
  );
};
