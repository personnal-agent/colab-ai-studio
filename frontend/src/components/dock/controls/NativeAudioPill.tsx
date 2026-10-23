import React from 'react';

interface NativeAudioPillProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

export const NativeAudioPill: React.FC<NativeAudioPillProps> = ({ enabled, onChange }) => {
  return (
    <button
      type="button"
      aria-label="Audio"
      title="Audio & effets sonores natifs"
      onClick={() => onChange(!enabled)}
      className={`h-8 px-3 rounded-pill border transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none ${
        enabled
          ? 'border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
          : 'border-studio-border bg-white text-studio-muted hover:bg-studio-subtle hover:text-studio-text'
      }`}
    >
      <span>🔊</span>
      <span> {enabled ? 'On' : 'Off'}</span>
    </button>
  );
};
