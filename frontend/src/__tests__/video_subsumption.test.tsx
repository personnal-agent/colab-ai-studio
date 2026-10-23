import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReferenceSlot } from '../components/dock/slots/ReferenceSlot';
import { ConditioningTray } from '../components/dock/slots/ConditioningTray';
import type { ModelDefinition, GenerationReferences } from '../types/studio';

const fullVideoModel: ModelDefinition = {
  id: 'minimax-h3',
  name: 'MiniMax-H3',
  mediaType: 'video',
  capabilities: {
    supportsStartFrame: true,
    supportsEndFrame: true,
    maxImageRefs: 9,
    supportsNativeAudio: true,
  },
};

const imageModel: ModelDefinition = {
  id: 'noctq-v4',
  name: 'NoctQ V4',
  mediaType: 'image',
  capabilities: {
    maxImageRefs: 4,
  },
};

const lipSyncModel: ModelDefinition = {
  id: 'live-portrait',
  name: 'Live Portrait',
  mediaType: 'lip_sync',
  capabilities: {},
};

const upscaleModel: ModelDefinition = {
  id: 'topaz-upscale',
  name: 'Topaz Upscale',
  mediaType: 'upscale',
  capabilities: {},
};

describe('Fentes de conditionnement et règle de subsomption vidéo', () => {
  it('ReferenceSlot affiche son libellé et permet dajouter/supprimer un média', () => {
    const onSelect = vi.fn();
    const onRemove = vi.fn();

    const { rerender } = render(
      <ReferenceSlot
        label="Start frame"
        accept="image/*"
        onSelectFile={onSelect}
      />
    );

    const slot = screen.getByRole('button', { name: /start frame/i });
    expect(slot).toBeInTheDocument();
    expect(slot).toHaveTextContent('Start frame');

    // Rerender avec valeur renseignée
    rerender(
      <ReferenceSlot
        label="Start frame"
        previewUrl="https://example.com/start.jpg"
        onSelectFile={onSelect}
        onRemove={onRemove}
      />
    );

    const img = screen.getByRole('img', { name: /preview start frame/i });
    expect(img).toHaveAttribute('src', 'https://example.com/start.jpg');

    const removeBtn = screen.getByRole('button', { name: /remove start frame/i });
    fireEvent.click(removeBtn);
    expect(onRemove).toHaveBeenCalled();
  });

  it('Règle de subsomption : le modèle vidéo complet autorise toutes les combinaisons unitaires et partielles', () => {
    const onChange = vi.fn();
    let currentRefs: GenerationReferences = {};

    const { rerender } = render(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={(refs) => {
          currentRefs = refs;
          onChange(refs);
        }}
      />
    );

    // Vérification de la présence des 5 fentes du mode vidéo
    expect(screen.getByRole('button', { name: /start frame/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /end frame/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /image refs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /video refs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /audio refs/i })).toBeInTheDocument();

    // Combinaison 1 : Ingrédients seuls
    currentRefs = { imageRefs: ['https://example.com/ref1.jpg'] };
    rerender(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={onChange}
      />
    );
    expect(screen.getByText('1/9')).toBeInTheDocument();

    // Combinaison 2 : Start frame seul (First Frame)
    currentRefs = { startFrame: 'https://example.com/start.jpg' };
    rerender(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={onChange}
      />
    );
    expect(screen.getByRole('img', { name: /preview start frame/i })).toBeInTheDocument();

    // Combinaison 3 : End frame seul (Last Frame)
    currentRefs = { endFrame: 'https://example.com/end.jpg' };
    rerender(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={onChange}
      />
    );
    expect(screen.getByRole('img', { name: /preview end frame/i })).toBeInTheDocument();

    // Combinaison 4 : Start + End frame (Frame Chaining pur)
    currentRefs = {
      startFrame: 'https://example.com/start.jpg',
      endFrame: 'https://example.com/end.jpg',
    };
    rerender(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={onChange}
      />
    );
    expect(screen.getByRole('img', { name: /preview start frame/i })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /preview end frame/i })).toBeInTheDocument();

    // Combinaison 5 : Mode complet (Start + End + Ingrédients)
    currentRefs = {
      startFrame: 'https://example.com/start.jpg',
      endFrame: 'https://example.com/end.jpg',
      imageRefs: ['https://example.com/ref1.jpg', 'https://example.com/ref2.jpg'],
      videoRefs: ['https://example.com/prev_scene.mp4'],
    };
    rerender(
      <ConditioningTray
        model={fullVideoModel}
        references={currentRefs}
        onChange={onChange}
      />
    );
    expect(screen.getByText('2/9')).toBeInTheDocument();
  });

  it('Avertissement visuel quand le nombre dingrédients atteint la limite maxImageRefs', () => {
    const nineRefs = Array.from({ length: 9 }, (_, i) => `https://example.com/ref${i}.jpg`);
    render(
      <ConditioningTray
        model={fullVideoModel}
        references={{ imageRefs: nineRefs }}
        onChange={vi.fn()}
      />
    );

    const badge = screen.getByText('9/9');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('text-amber-600');
  });

  it('ConditioningTray adapte les fentes pour les pôles Image, Lip sync et Upscaling', () => {
    // Mode Image
    const { rerender } = render(
      <ConditioningTray
        model={imageModel}
        references={{}}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: /image refs/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /start frame/i })).not.toBeInTheDocument();

    // Mode Lip sync
    rerender(
      <ConditioningTray
        model={lipSyncModel}
        references={{}}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: /face reference/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /voice track/i })).toBeInTheDocument();

    // Mode Upscaling
    rerender(
      <ConditioningTray
        model={upscaleModel}
        references={{}}
        onChange={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: /source media/i })).toBeInTheDocument();
  });
});
