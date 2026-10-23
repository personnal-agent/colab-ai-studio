import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MediaPlayerModal } from '../components/gallery/MediaPlayerModal';
import { Generation } from '../types/studio';

describe('MediaPlayerModal & Remix Action', () => {
  const mockGeneration: Generation = {
    id: 'gen_modal_1',
    status: 'completed',
    mediaType: 'video',
    prompt: 'A majestic eagle soaring over foggy pine canyons',
    compiledPrompt:
      'A majestic eagle soaring over foggy pine canyons, cinematic lighting, photorealistic, brand coherent.',
    modelId: 'seedance-2.5-pro',
    modelName: 'Seedance 2.5 Pro',
    parameters: {
      seed: 8888,
      aspectRatio: '16:9',
      resolution: '1080p',
      duration: '10s',
    },
    references: {},
    brandKitSnapshot: {
      id: 'kit_nature',
      name: 'Wild Nature Brand',
      primaryColor: '#2D5A27',
    },
    filePath: '/outputs/eagle.mp4',
    isFavorite: false,
    progress: 100,
    createdAt: '2026-10-23T14:00:00Z',
  };

  it('renders technical metadata, prompt and brand snapshot', () => {
    render(
      <MediaPlayerModal
        generation={mockGeneration}
        isOpen={true}
        onClose={vi.fn()}
        onToggleFavorite={vi.fn()}
        onRemix={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(
      screen.getByText('A majestic eagle soaring over foggy pine canyons')
    ).toBeInTheDocument();
    expect(screen.getAllByText('Seedance 2.5 Pro')[0]).toBeInTheDocument();
    expect(screen.getByText('8888')).toBeInTheDocument();
    expect(screen.getByText('16:9')).toBeInTheDocument();
    expect(screen.getByText('10s')).toBeInTheDocument();
    expect(screen.getByText('Wild Nature Brand')).toBeInTheDocument();
  });

  it('calls onRemix with generation context when clicking Remix button', () => {
    const onRemix = vi.fn();
    const onClose = vi.fn();

    render(
      <MediaPlayerModal
        generation={mockGeneration}
        isOpen={true}
        onClose={onClose}
        onToggleFavorite={vi.fn()}
        onRemix={onRemix}
        onDelete={vi.fn()}
      />
    );

    const remixBtn = screen.getByRole('button', { name: /remix/i });
    expect(remixBtn).toBeInTheDocument();

    fireEvent.click(remixBtn);
    expect(onRemix).toHaveBeenCalledWith(mockGeneration);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onToggleFavorite and onDelete handlers', () => {
    const onToggleFavorite = vi.fn();
    const onDelete = vi.fn();

    render(
      <MediaPlayerModal
        generation={mockGeneration}
        isOpen={true}
        onClose={vi.fn()}
        onToggleFavorite={onToggleFavorite}
        onRemix={vi.fn()}
        onDelete={onDelete}
      />
    );

    const favBtn = screen.getByRole('button', { name: /favori/i });
    fireEvent.click(favBtn);
    expect(onToggleFavorite).toHaveBeenCalledWith('gen_modal_1');

    const deleteBtn = screen.getByRole('button', { name: /supprimer/i });
    fireEvent.click(deleteBtn);
    expect(onDelete).toHaveBeenCalledWith('gen_modal_1');
  });
});
