import React from 'react';

interface UpscaleQualityPillProps {
  quality: string;
  onChange: (quality: string) => void;
}

export const UpscaleQualityPill: React.FC<UpscaleQualityPillProps> = ({ quality, onChange }) => {
  const handleClick = () => {
    onChange(quality === 'Fast' ? 'Precise' : 'Fast');
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label="Upscale quality"
      className="h-8 px-2.5 rounded-pill text-xs font-medium border border-studio-border bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1.5 transition-colors shadow-sm select-none"
    >
      <span className="text-gray-400">✨</span>
      <span>{quality || 'Fast'}</span>
    </button>
  );
};
