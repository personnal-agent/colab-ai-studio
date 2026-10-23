import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';

interface FineSettingsPopoverProps {
  cfgScale?: number;
  steps?: number;
  motionBucket?: number;
  denoiseStrength?: number;
  onChangeCfgScale?: (val: number) => void;
  onChangeSteps?: (val: number) => void;
  onChangeMotionBucket?: (val: number) => void;
  onChangeDenoiseStrength?: (val: number) => void;
}

export const FineSettingsPopover: React.FC<FineSettingsPopoverProps> = ({
  cfgScale = 7.0,
  steps = 25,
  motionBucket,
  denoiseStrength,
  onChangeCfgScale,
  onChangeSteps,
  onChangeMotionBucket,
  onChangeDenoiseStrength,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Fine settings"
          title="Réglages fins avancés"
          className="h-8 px-2.5 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-medium inline-flex items-center gap-1 cursor-pointer select-none"
        >
          <span>🎛️</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-50 w-64 p-3.5 bg-white rounded-xl shadow-lg border border-studio-border text-xs focus:outline-none space-y-3"
        >
          <div className="font-semibold text-studio-text border-b border-studio-border pb-1.5 flex items-center justify-between">
            <span>Paramètres d'inférence avancés</span>
            <span className="text-[10px] text-studio-muted">Expert</span>
          </div>

          {onChangeSteps && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-studio-muted">Étapes d'échantillonnage</span>
                <span className="font-semibold">{steps}</span>
              </div>
              <input
                type="range"
                min={10}
                max={60}
                value={steps}
                onChange={(e) => onChangeSteps(parseInt(e.target.value, 10))}
                className="w-full h-1 bg-gray-200 rounded appearance-none cursor-pointer accent-studio-text"
              />
            </div>
          )}

          {onChangeCfgScale && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-studio-muted">Guidage CFG Scale</span>
                <span className="font-semibold">{cfgScale.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min={1.0}
                max={20.0}
                step={0.5}
                value={cfgScale}
                onChange={(e) => onChangeCfgScale(parseFloat(e.target.value))}
                className="w-full h-1 bg-gray-200 rounded appearance-none cursor-pointer accent-studio-text"
              />
            </div>
          )}

          {onChangeMotionBucket && motionBucket !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-studio-muted">Intensité mouvement (Motion Bucket)</span>
                <span className="font-semibold">{motionBucket}</span>
              </div>
              <input
                type="range"
                min={1}
                max={255}
                value={motionBucket}
                onChange={(e) => onChangeMotionBucket(parseInt(e.target.value, 10))}
                className="w-full h-1 bg-gray-200 rounded appearance-none cursor-pointer accent-studio-text"
              />
            </div>
          )}

          {onChangeDenoiseStrength && denoiseStrength !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-studio-muted">Force de débruitage</span>
                <span className="font-semibold">{denoiseStrength.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.1}
                max={1.0}
                step={0.05}
                value={denoiseStrength}
                onChange={(e) => onChangeDenoiseStrength(parseFloat(e.target.value))}
                className="w-full h-1 bg-gray-200 rounded appearance-none cursor-pointer accent-studio-text"
              />
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
