import React from 'react';
import type { ModelDefinition, GenerationParameters } from '../../../types/studio';
import { ModelSelectorPopover } from './ModelSelectorPopover';
import { AspectRatioPill } from './AspectRatioPill';
import { ResolutionPill } from './ResolutionPill';
import { DurationControlPill } from './DurationControlPill';
import { NativeAudioPill } from './NativeAudioPill';
import { TalkingStylePill } from './TalkingStylePill';
import { UpscaleScalePill } from './UpscaleScalePill';
import { UpscaleQualityPill } from './UpscaleQualityPill';
import { UpscaleFrameRatePill } from './UpscaleFrameRatePill';
import { BatchCountPill } from './BatchCountPill';
import { EnhancePromptPill } from './EnhancePromptPill';
import { SeedControlPill } from './SeedControlPill';
import { FineSettingsPopover } from './FineSettingsPopover';

interface ParameterRegistryProps {
  activeModel: ModelDefinition;
  models: ModelDefinition[];
  parameters: GenerationParameters;
  onParametersChange: (newParams: GenerationParameters) => void;
  onModelChange: (modelId: string) => void;
}

export const ParameterRegistry: React.FC<ParameterRegistryProps> = ({
  activeModel,
  models,
  parameters,
  onParametersChange,
  onModelChange,
}) => {
  const caps = activeModel.capabilities || {};
  const mediaType = activeModel.mediaType.toLowerCase();

  const updateParam = <K extends keyof GenerationParameters>(
    key: K,
    val: GenerationParameters[K]
  ) => {
    onParametersChange({
      ...parameters,
      [key]: val,
    });
  };

  const isUpscale = mediaType === 'upscale';
  const isLipSync = mediaType === 'lip_sync';
  const isVideo = mediaType === 'video';
  const isImage = mediaType === 'image';

  return (
    <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto py-1">
      {/* 1. Sélecteur de modèle universel */}
      <ModelSelectorPopover
        activeModelId={activeModel.id}
        mediaType={activeModel.mediaType}
        models={models}
        onSelectModel={onModelChange}
      />

      {/* 2. Format & Ratio (Image, Vidéo, Lip Sync) */}
      {(isVideo || isImage || isLipSync) && caps.aspectRatios && caps.aspectRatios.length > 0 && (
        <AspectRatioPill
          value={parameters.aspectRatio}
          allowedRatios={caps.aspectRatios}
          onChange={(r) => updateParam('aspectRatio', r)}
        />
      )}

      {/* 3. Définition & Résolution (Image, Vidéo, Lip Sync) */}
      {(isVideo || isImage || isLipSync) && caps.resolutions && caps.resolutions.length > 0 && (
        <ResolutionPill
          value={parameters.resolution}
          allowedResolutions={caps.resolutions}
          onChange={(res) => updateParam('resolution', res)}
        />
      )}

      {/* 4. Durée (Vidéo) */}
      {isVideo && (caps.durations || caps.durationRange || caps.durationMode) && (
        <DurationControlPill
          mode={caps.durationMode || 'discrete'}
          value={parameters.duration}
          allowedDurations={caps.durations}
          range={caps.durationRange}
          onChange={(d) => updateParam('duration', d)}
        />
      )}

      {/* 5. Commutateur audio / SFX natif (Vidéo) */}
      {isVideo && (caps.supportsNativeAudio || caps.supportsAudio) && (
        <NativeAudioPill
          enabled={parameters.audio ?? true}
          onChange={(a) => updateParam('audio', a)}
        />
      )}

      {/* 6. Style d'élocution (Lip Sync) */}
      {isLipSync && (
        <TalkingStylePill
          value={parameters.talkingStyle || 'Stable'}
          onChange={(ts) => updateParam('talkingStyle', ts)}
        />
      )}

      {/* 7. Contrôles spécifiques Upscaling */}
      {isUpscale && caps.upscaleScales && (
        <UpscaleScalePill
          value={parameters.scaleFactor || '2x'}
          allowedScales={caps.upscaleScales}
          onChange={(s) => updateParam('scaleFactor', s)}
        />
      )}
      {isUpscale && caps.upscaleQualities && (
        <UpscaleQualityPill
          value={parameters.upscaleQuality || 'Fast'}
          allowedQualities={caps.upscaleQualities}
          onChange={(q) => updateParam('upscaleQuality', q)}
        />
      )}
      {isUpscale && caps.fpsOptions && (
        <UpscaleFrameRatePill
          value={parameters.frameRate || 'Same as source'}
          allowedFps={caps.fpsOptions}
          onChange={(f) => updateParam('frameRate', f)}
        />
      )}

      {/* 8. Contrôles universels passe-partout */}
      <BatchCountPill
        value={parameters.batchCount || 1}
        allowedValues={caps.batchSize || [1, 2, 4]}
        onChange={(bc) => updateParam('batchCount', bc)}
      />

      {!isUpscale && (
        <EnhancePromptPill
          value={parameters.enhance ?? true}
          onChange={(enh) => updateParam('enhance', enh)}
        />
      )}

      <SeedControlPill
        value={parameters.seed}
        onChange={(s) => updateParam('seed', s)}
      />

      <FineSettingsPopover
        cfgScale={parameters.cfgScale}
        steps={parameters.steps}
        motionBucket={parameters.motionBucket}
        denoiseStrength={parameters.denoiseStrength}
        onChangeCfgScale={(cfg) => updateParam('cfgScale', cfg)}
        onChangeSteps={(st) => updateParam('steps', st)}
        onChangeMotionBucket={(mb) => updateParam('motionBucket', mb)}
        onChangeDenoiseStrength={(ds) => updateParam('denoiseStrength', ds)}
      />
    </div>
  );
};
