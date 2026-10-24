import React from 'react';

interface NativeAudioPillProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

export const NativeAudioPill: React.FC<NativeAudioPillProps> = ({ enabled, onChange }) => {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      aria-label="Native audio"
      aria-pressed={enabled}
      className={`h-8 px-2.5 rounded-pill text-xs font-medium border transition-colors flex items-center gap-1.5 shadow-sm select-none ${
        enabled
          ? 'border-indigo-300 bg-indigo-50/70 text-indigo-700'
          : 'border-studio-border bg-white hover:bg-gray-50 text-gray-700'
      }`}
    >
      <span>🔊 </span>
      <span>{enabled ? 'On' : 'Off'}</span>
    </button>
  );
};
