import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BatchCountPill } from '../components/dock/controls/BatchCountPill';
import { EnhancePromptPill } from '../components/dock/controls/EnhancePromptPill';
import { SeedControlPill } from '../components/dock/controls/SeedControlPill';
import { AspectRatioPill } from '../components/dock/controls/AspectRatioPill';
import { ResolutionPill } from '../components/dock/controls/ResolutionPill';
import { DurationControlPill } from '../components/dock/controls/DurationControlPill';
import { NativeAudioPill } from '../components/dock/controls/NativeAudioPill';
import { TalkingStylePill } from '../components/dock/controls/TalkingStylePill';
import { UpscaleScalePill } from '../components/dock/controls/UpscaleScalePill';
import { UpscaleQualityPill } from '../components/dock/controls/UpscaleQualityPill';
import { UpscaleFrameRatePill } from '../components/dock/controls/UpscaleFrameRatePill';
import { ModelSelectorPopover } from '../components/dock/controls/ModelSelectorPopover';
import { ParameterRegistry } from '../components/dock/controls/ParameterRegistry';
import type { ModelDefinition, GenerationParameters } from '../types/studio';

const mockVideoModel: ModelDefinition = {
  id: 'minimax-h3',
  name: 'MiniMax-H3 Heretic',
  mediaType: 'video',
  description: 'Génération vidéo haute fidélité',
  capabilities: {
    aspectRatios: ['16:9', '9:16', '1:1'],
    resolutions: ['720p', '1080p'],
    durations: ['5s', '10s', '15s'],
    durationMode: 'discrete',
    supportsNativeAudio: true,
    maxImageRefs: 9,
    supportsStartFrame: true,
    supportsEndFrame: true,
  },
};

const mockImageModel: ModelDefinition = {
  id: 'noctq-v4',
  name: 'NoctQ V4 Photo',
  mediaType: 'image',
  description: 'Modèle photo ultra-réaliste',
  capabilities: {
    aspectRatios: ['16:9', '9:16', '1:1', '4:5'],
    resolutions: ['1K', '2K'],
    batchSize: [1, 2, 4],
    maxImageRefs: 4,
  },
};

const mockUpscaleModel: ModelDefinition = {
  id: 'topaz-video-upscale',
  name: 'Topaz Video Upscale',
  mediaType: 'upscale',
  description: 'Super-résolution vidéo avec interpolation temporelle',
  capabilities: {
    upscaleScales: ['1.25x', '2x', '4x'],
    upscaleQualities: ['Fast', 'Precise'],
    fpsOptions: ['Same as source', '24fps', '60fps'],
  },
};

const defaultParams: GenerationParameters = {
  seed: -1,
  aspectRatio: '16:9',
  resolution: '720p',
  duration: '5s',
  audio: true,
  enhance: true,
  batchCount: 1,
};

describe('Contrôles atomiques de paramètres du Dock', () => {
  it('BatchCountPill incrémente ou cycle entre 1 et 4', () => {
    const onChange = vi.fn();
    render(<BatchCountPill value={1} onChange={onChange} />);

    const button = screen.getByRole('button', { name: /batch count/i });
    expect(button).toHaveTextContent('⚏ 1');

    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it('EnhancePromptPill bascule entre On et Off', () => {
    const onChange = vi.fn();
    const { rerender } = render(<EnhancePromptPill value={true} onChange={onChange} />);

    const button = screen.getByRole('button', { name: /enhance prompt/i });
    expect(button).toHaveTextContent('🪄 On');

    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith(false);

    rerender(<EnhancePromptPill value={false} onChange={onChange} />);
    expect(button).toHaveTextContent('🪄 Off');
  });

  it('SeedControlPill permet de saisir une seed ou de revenir à aléatoire', () => {
    const onChange = vi.fn();
    render(<SeedControlPill value={-1} onChange={onChange} />);

    const trigger = screen.getByRole('button', { name: /seed/i });
    expect(trigger).toHaveTextContent('🎲 Random');

    fireEvent.click(trigger);
    const input = screen.getByPlaceholderText(/seed/i);
    fireEvent.change(input, { target: { value: '42' } });

    const applyBtn = screen.getByRole('button', { name: /ok|appliquer/i });
    fireEvent.click(applyBtn);

    expect(onChange).toHaveBeenCalledWith(42);
  });

  it('AspectRatioPill propose uniquement les ratios autorisés par le modèle', () => {
    const onChange = vi.fn();
    render(
      <AspectRatioPill
        value="16:9"
        allowedRatios={['16:9', '9:16', '1:1']}
        onChange={onChange}
      />
    );

    const trigger = screen.getByRole('button', { name: /aspect ratio/i });
    expect(trigger).toHaveTextContent('▭ 16:9');

    fireEvent.click(trigger);
    expect(screen.getByRole('button', { name: '9:16' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '1:1' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '21:9' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '9:16' }));
    expect(onChange).toHaveBeenCalledWith('9:16');
  });

  it('ResolutionPill affiche et permet de sélectionner la résolution', () => {
    const onChange = vi.fn();
    render(
      <ResolutionPill
        value="720p"
        allowedResolutions={['720p', '1080p']}
        onChange={onChange}
      />
    );

    const trigger = screen.getByRole('button', { name: /resolution/i });
    expect(trigger).toHaveTextContent('⇅ 720p');

    fireEvent.click(trigger);
    fireEvent.click(screen.getByRole('button', { name: '1080p' }));
    expect(onChange).toHaveBeenCalledWith('1080p');
  });

  it('DurationControlPill affiche des pilules en mode discrete et un slider en mode range', () => {
    const onChangeDiscrete = vi.fn();
    const { rerender } = render(
      <DurationControlPill
        mode="discrete"
        value="5s"
        allowedDurations={['5s', '10s', '15s']}
        onChange={onChangeDiscrete}
      />
    );

    const trigger = screen.getByRole('button', { name: /duration/i });
    expect(trigger).toHaveTextContent('⏱ 5s');

    fireEvent.click(trigger);
    fireEvent.click(screen.getByRole('button', { name: '10s' }));
    expect(onChangeDiscrete).toHaveBeenCalledWith('10s');

    const onChangeRange = vi.fn();
    rerender(
      <DurationControlPill
        mode="range"
        value="8s"
        range={{ min: 4, max: 30 }}
        onChange={onChangeRange}
      />
    );

    const triggerRange = screen.getByRole('button', { name: /duration/i });
    expect(triggerRange).toHaveTextContent('⏱ 8s');
    fireEvent.click(triggerRange);

    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('min', '4');
    expect(slider).toHaveAttribute('max', '30');
    fireEvent.change(slider, { target: { value: '12' } });
    expect(onChangeRange).toHaveBeenCalledWith('12s');
  });

  it('NativeAudioPill bascule le son physique pour les modèles le supportant', () => {
    const onChange = vi.fn();
    render(<NativeAudioPill enabled={true} onChange={onChange} />);

    const button = screen.getByRole('button', { name: /audio/i });
    expect(button).toHaveTextContent('🔊 On');

    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('TalkingStylePill bascule entre Stable et Expressive', () => {
    const onChange = vi.fn();
    render(<TalkingStylePill value="Stable" onChange={onChange} />);

    const button = screen.getByRole('button', { name: /talking style/i });
    expect(button).toHaveTextContent('Stable');

    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith('Expressive');
  });

  it('UpscaleScalePill et UpscaleQualityPill permettent de configurer la super-résolution', () => {
    const onScale = vi.fn();
    const onQuality = vi.fn();
    const onFps = vi.fn();

    render(
      <div>
        <UpscaleScalePill value="2x" allowedScales={['1.25x', '2x', '4x']} onChange={onScale} />
        <UpscaleQualityPill value="Fast" allowedQualities={['Fast', 'Precise']} onChange={onQuality} />
        <UpscaleFrameRatePill value="Same as source" allowedFps={['Same as source', '24fps', '60fps']} onChange={onFps} />
      </div>
    );

    const scaleTrigger = screen.getByRole('button', { name: /scale/i });
    expect(scaleTrigger).toHaveTextContent('⊕ 2x');
    fireEvent.click(scaleTrigger);
    fireEvent.click(screen.getByRole('button', { name: '4x' }));
    expect(onScale).toHaveBeenCalledWith('4x');

    const qualTrigger = screen.getByRole('button', { name: /quality/i });
    expect(qualTrigger).toHaveTextContent('Fast');
    fireEvent.click(qualTrigger);
    expect(onQuality).toHaveBeenCalledWith('Precise');

    const fpsTrigger = screen.getByRole('button', { name: /framerate/i });
    expect(fpsTrigger).toHaveTextContent('Same as source');
    fireEvent.click(fpsTrigger);
    fireEvent.click(screen.getByRole('button', { name: '60fps' }));
    expect(onFps).toHaveBeenCalledWith('60fps');
  });

  it('ModelSelectorPopover filtre et affiche les badges Beta / New / Slow', () => {
    const onSelect = vi.fn();
    const models: ModelDefinition[] = [
      {
        id: 'm1',
        name: 'Model Normal',
        mediaType: 'video',
        description: 'Standard model',
      },
      {
        id: 'm2',
        name: 'Model Beta',
        mediaType: 'video',
        description: 'New feature preview',
        capabilities: { badge: 'Beta' },
      },
      {
        id: 'm3',
        name: 'Model Slow',
        mediaType: 'video',
        description: 'Heavy quality',
        capabilities: { badge: 'Slow' },
      },
    ];

    render(
      <ModelSelectorPopover
        activeModelId="m1"
        mediaType="video"
        models={models}
        onSelectModel={onSelect}
      />
    );

    const trigger = screen.getByRole('button', { name: /select model/i });
    expect(trigger).toHaveTextContent('Model Normal');

    fireEvent.click(trigger);
    expect(screen.getByText('Model Beta')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('! Slower than usual')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/search model/i);
    fireEvent.change(searchInput, { target: { value: 'Beta' } });
    const modelList = screen.getByTestId('model-list');
    expect(modelList).not.toHaveTextContent('Model Normal');
    expect(modelList).toHaveTextContent('Model Beta');

    fireEvent.click(screen.getByText('Model Beta'));
    expect(onSelect).toHaveBeenCalledWith('m2');
  });

  it('ParameterRegistry monte dynamiquement les contrôles selon le modèle actif', () => {
    const onParamsChange = vi.fn();
    const onModelChange = vi.fn();

    const { rerender } = render(
      <ParameterRegistry
        activeModel={mockVideoModel}
        models={[mockVideoModel, mockImageModel, mockUpscaleModel]}
        parameters={defaultParams}
        onParametersChange={onParamsChange}
        onModelChange={onModelChange}
      />
    );

    // En mode Video: Ratio, Resolution, Duration, NativeAudio, BatchCount, Enhance, Seed, FineSettings
    expect(screen.getByRole('button', { name: /aspect ratio/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /resolution/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /duration/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /audio/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /batch count/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enhance prompt/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /scale/i })).not.toBeInTheDocument();

    // Rerender avec modèle Upscale:
    rerender(
      <ParameterRegistry
        activeModel={mockUpscaleModel}
        models={[mockVideoModel, mockImageModel, mockUpscaleModel]}
        parameters={defaultParams}
        onParametersChange={onParamsChange}
        onModelChange={onModelChange}
      />
    );

    // Upscale controls mounted, Video specific unmounted
    expect(screen.getByRole('button', { name: /scale/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /quality/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /framerate/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /duration/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /aspect ratio/i })).not.toBeInTheDocument();
  });
});
