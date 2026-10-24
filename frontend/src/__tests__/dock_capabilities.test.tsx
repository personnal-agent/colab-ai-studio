import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BatchCountPill } from '../components/dock/controls/BatchCountPill';
import { EnhancePromptPill } from '../components/dock/controls/EnhancePromptPill';
import { SeedControlPill } from '../components/dock/controls/SeedControlPill';
import { DurationControlPill } from '../components/dock/controls/DurationControlPill';
import { NativeAudioPill } from '../components/dock/controls/NativeAudioPill';
import { TalkingStylePill } from '../components/dock/controls/TalkingStylePill';
import { UpscaleScalePill } from '../components/dock/controls/UpscaleScalePill';
import { UpscaleQualityPill } from '../components/dock/controls/UpscaleQualityPill';
import { UpscaleFrameRatePill } from '../components/dock/controls/UpscaleFrameRatePill';
import { FineSettingsPopover } from '../components/dock/controls/FineSettingsPopover';
import { ModelSelectorPopover } from '../components/dock/controls/ModelSelectorPopover';
import { ParameterRegistry } from '../components/dock/ParameterRegistry';
import type { ModelDefinition, GenerationParameters } from '../types/studio';

describe('Atomic Dock Controls', () => {
  it('BatchCountPill cycles or selects batch 1 to 4', () => {
    const onChange = vi.fn();
    render(<BatchCountPill count={1} onChange={onChange} />);
    const btn = screen.getByRole('button', { name: /batch/i });
    expect(btn).toHaveTextContent('⚏ 1');
    fireEvent.click(btn);
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it('EnhancePromptPill toggles on/off state', () => {
    const onChange = vi.fn();
    const { rerender } = render(<EnhancePromptPill enabled={false} onChange={onChange} />);
    const btn = screen.getByRole('button', { name: /enhance/i });
    expect(btn).toHaveTextContent('🪄 Off');
    fireEvent.click(btn);
    expect(onChange).toHaveBeenCalledWith(true);
    rerender(<EnhancePromptPill enabled={true} onChange={onChange} />);
    expect(screen.getByRole('button', { name: /enhance/i })).toHaveTextContent('🪄 On');
  });

  it('SeedControlPill displays seed and random state', () => {
    const onChange = vi.fn();
    const { rerender } = render(<SeedControlPill seed={42} onChange={onChange} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    rerender(<SeedControlPill seed={-1} onChange={onChange} />);
    expect(screen.getByText(/aléatoire|random|🎲/i)).toBeInTheDocument();
  });

  it('DurationControlPill renders discrete pills when type is discrete or string array', async () => {
    const onChange = vi.fn();
    render(<DurationControlPill value="5s" config={['5s', '10s', '15s']} onChange={onChange} />);
    expect(screen.getByRole('button', { name: /5s/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /5s/i }));
    await waitFor(() => expect(screen.getByText('10s')).toBeInTheDocument());
    fireEvent.click(screen.getByText('10s'));
    expect(onChange).toHaveBeenCalledWith('10s');
  });

  it('DurationControlPill renders slider when type is range', async () => {
    const onChange = vi.fn();
    render(<DurationControlPill value="8s" config={{ min: 4, max: 30, type: 'range' }} onChange={onChange} />);
    expect(screen.getByRole('button', { name: /8s/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /8s/i }));
    await waitFor(() => expect(screen.getByRole('slider')).toBeInTheDocument());
    fireEvent.change(screen.getByRole('slider'), { target: { value: '12' } });
    expect(onChange).toHaveBeenCalledWith('12s');
  });

  it('NativeAudioPill toggles audio when supported', () => {
    const onChange = vi.fn();
    render(<NativeAudioPill enabled={true} onChange={onChange} />);
    const btn = screen.getByRole('button', { name: /audio/i });
    expect(btn).toHaveTextContent('🔊 On');
    fireEvent.click(btn);
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('TalkingStylePill switches between Stable and Expressive', () => {
    const onChange = vi.fn();
    render(<TalkingStylePill style="Stable" onChange={onChange} />);
    const btn = screen.getByRole('button', { name: /talking style|style/i });
    expect(btn).toHaveTextContent('Stable');
    fireEvent.click(btn);
    expect(onChange).toHaveBeenCalledWith('Expressive');
  });

  it('Upscale pills allow choosing scale and quality', () => {
    const onScale = vi.fn(), onQuality = vi.fn();
    render(<div><UpscaleScalePill scale="2x" onChange={onScale} /><UpscaleQualityPill quality="Fast" onChange={onQuality} /></div>);
    expect(screen.getByText(/2x/)).toBeInTheDocument();
    expect(screen.getByText('Fast')).toBeInTheDocument();
  });
});

describe('ModelSelectorPopover & ParameterRegistry', () => {
  const mockModels: ModelDefinition[] = [
    { id: 'flux-dev', name: 'FLUX.1 Dev', type: 'image', badge: 'New', capabilities: { aspectRatios: ['16:9', '1:1'], resolutions: ['1080p', '4K'], supportsEnhance: true } },
    { id: 'wan-2.1', name: 'Wan 2.1 Video', type: 'video', badge: 'Beta', capabilities: { aspectRatios: ['16:9'], resolutions: ['720p', '1080p'], durations: ['5s', '10s'], supportsAudio: true } },
    { id: 'topaz-upscale', name: 'Topaz Video Upscale', type: 'upscale', capabilities: { resolutions: ['4K'], fps: ['30fps', '60fps'] } },
    { id: 'llama-3', name: 'Llama 3.3 70B', type: 'text', badge: 'New' },
  ];

  it('ModelSelectorPopover filters models by search and mode', async () => {
    const onSelect = vi.fn();
    render(<ModelSelectorPopover activeModel={mockModels[0]} models={mockModels} mode="image" onSelect={onSelect} />);
    const trigger = screen.getByRole('button', { name: /FLUX\.1 Dev/i });
    expect(trigger).toBeInTheDocument();
    fireEvent.click(trigger);
    await waitFor(() => expect(screen.getByPlaceholderText(/rechercher un modèle/i)).toBeInTheDocument());
    const searchInput = screen.getByPlaceholderText(/rechercher un modèle/i);
    fireEvent.change(searchInput, { target: { value: 'Wan' } });
    await waitFor(() => expect(screen.getByText('Wan 2.1 Video')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Wan 2.1 Video'));
    expect(onSelect).toHaveBeenCalledWith(mockModels[1]);
  });

  it('ParameterRegistry adapts controls based on model capabilities', () => {
    const params: GenerationParameters = { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s', audio: true, enhance: true };
    const onParamChange = vi.fn(), onModelChange = vi.fn();
    const { rerender } = render(
      <ParameterRegistry mode="video" model={mockModels[1]} models={mockModels} parameters={params} onParametersChange={onParamChange} onModelChange={onModelChange} />
    );
    expect(screen.getByRole('button', { name: /5s/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /audio/i })).toBeInTheDocument();

    rerender(
      <ParameterRegistry mode="image" model={mockModels[0]} models={mockModels} parameters={params} onParametersChange={onParamChange} onModelChange={onModelChange} />
    );
    expect(screen.queryByRole('button', { name: /5s/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /audio/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /batch/i })).toBeInTheDocument();
  });

  it('DurationControlPill generates discrete steps bounded between min and max', async () => {
    const onChange = vi.fn();
    render(<DurationControlPill value="20s" config={{ min: 20, max: 30, type: 'discrete' }} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /20s/i }));
    await waitFor(() => {
      expect(screen.getByText('25s')).toBeInTheDocument();
      expect(screen.getByText('30s')).toBeInTheDocument();
    });
    expect(screen.queryByText('5s')).not.toBeInTheDocument();
  });

  it('UpscaleFrameRatePill respects model caps fps options', async () => {
    const onChange = vi.fn();
    render(<UpscaleFrameRatePill frameRate="30fps" options={['30fps', '60fps']} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /30fps/i }));
    await waitFor(() => expect(screen.getByText('60fps')).toBeInTheDocument());
    expect(screen.queryByText('24fps')).not.toBeInTheDocument();
  });

  it('ParameterRegistry displays resolution in lip_sync mode when declared in caps', () => {
    const params: GenerationParameters = { seed: 42, aspectRatio: '1:1', resolution: '1080p', duration: '5s' };
    const lipSyncModel: ModelDefinition = { id: 'sad-talker-hd', name: 'SadTalker HD', type: 'lip_sync', capabilities: { resolutions: ['720p', '1080p'] } };
    render(<ParameterRegistry mode="lip_sync" model={lipSyncModel} models={[lipSyncModel]} parameters={params} onParametersChange={() => {}} onModelChange={() => {}} />);
    expect(screen.getByRole('button', { name: /1080p/i })).toBeInTheDocument();
  });

  it('ParameterRegistry hides duration in video mode if caps.durations is undefined', () => {
    const params: GenerationParameters = { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s' };
    const videoModel: ModelDefinition = { id: 'no-durations-video', name: 'Fixed Video', type: 'video', capabilities: { aspectRatios: ['16:9'] } };
    render(<ParameterRegistry mode="video" model={videoModel} models={[videoModel]} parameters={params} onParametersChange={() => {}} onModelChange={() => {}} />);
    expect(screen.queryByRole('button', { name: /5s/i })).not.toBeInTheDocument();
  });

  it('FineSettingsPopover only renders controls when their respective callbacks exist', () => {
    const { rerender } = render(<FineSettingsPopover negativePrompt="bad quality" onNegativePromptChange={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /réglages fins/i }));
    expect(screen.getByLabelText(/prompt négatif/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/étapes/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/cfg scale/i)).not.toBeInTheDocument();

    rerender(<FineSettingsPopover negativePrompt="bad quality" onNegativePromptChange={vi.fn()} steps={25} onStepsChange={vi.fn()} guidanceScale={8} onGuidanceScaleChange={vi.fn()} />);
    expect(screen.getByLabelText(/étapes/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cfg scale/i)).toBeInTheDocument();
  });
});
