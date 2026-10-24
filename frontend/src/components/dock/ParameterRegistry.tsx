import React from 'react';
import type { GenerationParameters, ModelDefinition } from '../../types/studio';
import { ModelSelectorPopover } from './controls/ModelSelectorPopover';
import { BatchCountPill } from './controls/BatchCountPill';
import { EnhancePromptPill } from './controls/EnhancePromptPill';
import { SeedControlPill } from './controls/SeedControlPill';
import { AspectRatioPill } from './controls/AspectRatioPill';
import { ResolutionPill } from './controls/ResolutionPill';
import { DurationControlPill } from './controls/DurationControlPill';
import { NativeAudioPill } from './controls/NativeAudioPill';
import { TalkingStylePill } from './controls/TalkingStylePill';
import { UpscaleScalePill } from './controls/UpscaleScalePill';
import { UpscaleQualityPill } from './controls/UpscaleQualityPill';
import { UpscaleFrameRatePill } from './controls/UpscaleFrameRatePill';
import { FineSettingsPopover } from './controls/FineSettingsPopover';

export interface ParameterRegistryProps {
  mode: string;
  model?: ModelDefinition | null;
  models: ModelDefinition[];
  onModelChange: (model: ModelDefinition) => void;
  parameters: GenerationParameters;
  onParametersChange: (params: Partial<GenerationParameters>) => void;
  batchCount?: number;
  onBatchCountChange?: (count: number) => void;
  talkingStyle?: string;
  onTalkingStyleChange?: (style: string) => void;
  upscaleScale?: string;
  onUpscaleScaleChange?: (scale: string) => void;
  upscaleQuality?: string;
  onUpscaleQualityChange?: (quality: string) => void;
  upscaleFrameRate?: string;
  onUpscaleFrameRateChange?: (fps: string) => void;
  negativePrompt?: string;
  onNegativePromptChange?: (val: string) => void;
  steps?: number;
  onStepsChange?: (val: number) => void;
  guidanceScale?: number;
  onGuidanceScaleChange?: (val: number) => void;
}

export const ParameterRegistry: React.FC<ParameterRegistryProps> = ({
  mode,
  model,
  models,
  onModelChange,
  parameters,
  onParametersChange,
  batchCount = 1,
  onBatchCountChange,
  talkingStyle = 'Stable',
  onTalkingStyleChange,
  upscaleScale = '2x',
  onUpscaleScaleChange,
  upscaleQuality = 'Fast',
  onUpscaleQualityChange,
  upscaleFrameRate = 'Same as source',
  onUpscaleFrameRateChange,
  negativePrompt,
  onNegativePromptChange,
  steps,
  onStepsChange,
  guidanceScale,
  onGuidanceScaleChange,
}) => {
  const caps = model?.capabilities;

  // Si mode LLM / text, aucun contrôle multimédia
  if (mode === 'llm' || mode === 'text') {
    return (
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
        <ModelSelectorPopover
          activeModel={model}
          models={models}
          mode="llm"
          onSelect={onModelChange}
        />
      </div>
    );
  }

  // Détection des capacités
  const showAspect =
    mode !== 'upscale' && Boolean(caps?.aspectRatios?.length);
  const showResolution =
    Boolean(caps?.resolutions?.length);
  const showDuration =
    mode === 'video' && caps?.durations !== undefined;
  const showAudio =
    mode === 'video' && caps?.supportsAudio === true;
  const showLipSync =
    mode === 'lip_sync';
  const showUpscale =
    mode === 'upscale';

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1 max-w-full">
      {/* 1. Sélecteur de modèle */}
      <ModelSelectorPopover
        activeModel={model}
        models={models}
        mode={mode}
        onSelect={onModelChange}
      />

      {/* 2. Format / Aspect Ratio */}
      {showAspect && (
        <AspectRatioPill
          value={parameters.aspectRatio}
          options={caps?.aspectRatios}
          onChange={(aspectRatio: string) => onParametersChange({ aspectRatio })}
        />
      )}

      {/* 3. Définition / Résolution */}
      {showResolution && (
        <ResolutionPill
          value={parameters.resolution}
          options={caps?.resolutions}
          onChange={(resolution: string) => onParametersChange({ resolution })}
        />
      )}

      {/* 4. Durée (range ou discrete) */}
      {showDuration && (
        <DurationControlPill
          value={parameters.duration}
          config={caps?.durations}
          onChange={(duration: string) => onParametersChange({ duration })}
        />
      )}

      {/* 5. Commutateur Audio / SFX Natif */}
      {showAudio && (
        <NativeAudioPill
          enabled={parameters.audio ?? true}
          onChange={(audio: boolean) => onParametersChange({ audio })}
        />
      )}

      {/* 6. Style d'élocution (Lip sync) */}
      {showLipSync && (
        <TalkingStylePill
          style={talkingStyle}
          onChange={(style: string) => onTalkingStyleChange?.(style)}
        />
      )}

      {/* 7. Rehaussement (Upscale) */}
      {showUpscale && (
        <>
          <UpscaleScalePill
            scale={upscaleScale}
            onChange={(s: string) => onUpscaleScaleChange?.(s)}
          />
          {(model?.type === 'video' || caps?.fps) && (
            <>
              <UpscaleQualityPill
                quality={upscaleQuality}
                onChange={(q: string) => onUpscaleQualityChange?.(q)}
              />
              <UpscaleFrameRatePill
                frameRate={upscaleFrameRate}
                options={caps?.fps}
                onChange={(fps: string) => onUpscaleFrameRateChange?.(fps)}
              />
            </>
          )}
        </>
      )}

      {/* 8. Tirages Parallèles Universels */}
      <BatchCountPill
        count={batchCount}
        onChange={(c: number) => onBatchCountChange?.(c)}
      />

      {/* 9. Amélioration de Prompt Universelle */}
      <EnhancePromptPill
        enabled={parameters.enhance ?? false}
        onChange={(enhance: boolean) => onParametersChange({ enhance })}
      />

      {/* 10. Graine (Seed) */}
      <SeedControlPill
        seed={parameters.seed}
        onChange={(seed: number) => onParametersChange({ seed })}
      />

      {/* 11. Paramètres fins / Experts */}
      <FineSettingsPopover
        negativePrompt={negativePrompt}
        onNegativePromptChange={onNegativePromptChange}
        steps={steps}
        onStepsChange={onStepsChange}
        guidanceScale={guidanceScale}
        onGuidanceScaleChange={onGuidanceScaleChange}
      />
    </div>
  );
};
