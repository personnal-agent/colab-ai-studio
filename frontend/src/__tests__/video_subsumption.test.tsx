import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReferenceSlot } from '../components/dock/conditioning/ReferenceSlot';
import { ConditioningTray } from '../components/dock/conditioning/ConditioningTray';
import type { ModelDefinition, GenerationReferences } from '../types/studio';

describe('ReferenceSlot Component', () => {
  it('renders empty slot with label and file input trigger', () => {
    const onSelect = vi.fn();
    render(<ReferenceSlot label="Start frame" onFileSelected={onSelect} />);
    expect(screen.getByText('Start frame')).toBeInTheDocument();

    const file = new File(['fake'], 'start.png', { type: 'image/png' });
    const input = screen.getByTestId('reference-slot-input');
    fireEvent.change(input, { target: { files: [file] } });
    expect(onSelect).toHaveBeenCalledWith(file);
  });

  it('renders filled slot with preview and clear button', () => {
    const onClear = vi.fn();
    render(
      <ReferenceSlot
        label="Start frame"
        fileUrl="blob:http://localhost/start.png"
        onClear={onClear}
      />
    );
    expect(screen.getByRole('button', { name: /supprimer la référence start frame/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /supprimer la référence start frame/i }));
    expect(onClear).toHaveBeenCalled();
  });
});

describe('ConditioningTray & Video Subsumption', () => {
  const completeVideoModel: ModelDefinition = {
    id: 'wan-2.1',
    name: 'Wan 2.1 Video',
    type: 'video',
    capabilities: {
      supportsFirstFrame: true,
      supportsLastFrame: true,
      supportsImageRef: true,
      maxImageRefs: 9,
      supportsVideoRef: true,
      maxVideoRefs: 1,
    },
  };

  it('renders complete video slots: Start frame, End frame and Ingredients', () => {
    const refs: GenerationReferences = {
      startFrame: null, endFrame: null, imageRefs: [], videoRefs: [],
    };
    render(
      <ConditioningTray
        mode="video"
        model={completeVideoModel}
        references={refs}
        onReferencesChange={() => {}}
      />
    );

    expect(screen.getByText('Start frame')).toBeInTheDocument();
    expect(screen.getByText('End frame')).toBeInTheDocument();
    expect(screen.getByText('+ Ingrédient')).toBeInTheDocument();
  });

  it('supports single ingredient mode without start or end frame', () => {
    const onRefChange = vi.fn();
    const refs: GenerationReferences = {
      imageRefs: ['blob:http://localhost/char_bible.png'],
    };
    render(
      <ConditioningTray
        mode="video"
        model={completeVideoModel}
        references={refs}
        onReferencesChange={onRefChange}
      />
    );

    // Only ingredient is populated
    expect(screen.getByText('Start frame')).toBeInTheDocument();
    expect(screen.getByText('End frame')).toBeInTheDocument();
    expect(screen.getByText('Réf 1')).toBeInTheDocument();
  });

  it('shows warning when exceeding maxImageRefs', () => {
    const overLimitRefs: GenerationReferences = {
      imageRefs: Array.from({ length: 10 }, (_, i) => `blob:ref_${i}.png`),
    };
    render(
      <ConditioningTray
        mode="video"
        model={completeVideoModel}
        references={overLimitRefs}
        onReferencesChange={() => {}}
      />
    );

    expect(screen.getByText(/limite de références dépassée/i)).toBeInTheDocument();
  });

  it('renders Lip Sync mode with portrait image and vocal audio slots', () => {
    const refs: GenerationReferences = {};
    render(
      <ConditioningTray
        mode="lip_sync"
        model={{ id: 'sad-talker', name: 'SadTalker', type: 'lip_sync' }}
        references={refs}
        onReferencesChange={() => {}}
      />
    );

    expect(screen.getByText(/portrait/i)).toBeInTheDocument();
    expect(screen.getByText(/voix/i)).toBeInTheDocument();
  });

  it('renders Upscale mode with media source slot', () => {
    const refs: GenerationReferences = {};
    render(
      <ConditioningTray
        mode="upscale"
        model={{ id: 'topaz', name: 'Topaz Upscale', type: 'upscale' }}
        references={refs}
        onReferencesChange={() => {}}
      />
    );

    expect(screen.getByText(/source/i)).toBeInTheDocument();
  });

  it('hides conditioning tray in LLM mode', () => {
    const { container } = render(
      <ConditioningTray
        mode="llm"
        model={{ id: 'llama', name: 'Llama 3', type: 'text' }}
        references={{}}
        onReferencesChange={() => {}}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});
