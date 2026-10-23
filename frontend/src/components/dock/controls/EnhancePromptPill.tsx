import React from 'react';

interface EnhancePromptPillProps {
  value: boolean;
  onChange: (value: boolean) => void;
}

export const EnhancePromptPill: React.FC<EnhancePromptPillProps> = ({
  value,
  onChange,
}) => {
  return (
    <button
      type="button"
      aria-label="Enhance prompt"
      title="Amélioration automatique du prompt"
      onClick={() => onChange(!value)}
      className={`h-8 px-3 rounded-pill border transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none ${
        value
          ? 'border-indigo-300 bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
          : 'border-studio-border bg-white text-studio-muted hover:bg-studio-subtle hover:text-studio-text'
      }`}
    >
      <span>🪄</span>
      <span> {value ? 'On' : 'Off'}</span>
    </button>
  );
};
