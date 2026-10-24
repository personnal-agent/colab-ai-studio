import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MediaPlayerModal } from '../components/gallery/MediaPlayerModal';
import { apiClient } from '../services/apiClient';
import type { Generation } from '../types/studio';

vi.mock('../services/apiClient', () => ({
  apiClient: { toggleFavorite: vi.fn() },
  getMediaFileUrl: (g: { filePath?: string | null }) => g.filePath || '',
  getMediaThumbnailUrl: (g: { thumbnailPath?: string | null; filePath?: string | null }) => g.thumbnailPath || g.filePath || '',
}));

describe('MediaPlayerModal', () => {
  const mockGen: Generation = {
    id: 'gen_modal_1', status: 'completed', mediaType: 'video', prompt: 'Cinematic drone shot over misty cyberpunk neon metropolis',
    compiledPrompt: 'RAW photo, cinematic drone shot over misty cyberpunk neon metropolis, 8k uhd, dslr, soft lighting, high quality, film grain',
    filePath: '/outputs/cyberpunk.mp4', thumbnailPath: '/outputs/cyberpunk_thumb.jpg', modelId: 'wan-2.1', modelName: 'Wan 2.1 Video', isFavorite: false,
    parameters: { seed: 98765, aspectRatio: '16:9', resolution: '1080p', duration: '5s' }, references: {},
    brandKitSnapshot: { id: 'brand_1', name: 'Cyberpunk Neon Brand', overview: 'High contrast dark neon cyberpunk aesthetic', colors: ['#00ffcc', '#ff007f'], logos: [], fonts: ['Orbitron'], guidelines: ['Use neon glow on dark backgrounds'] },
    createdAt: '2026-10-24T12:30:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockImplementation(() => Promise.resolve()) } });
  });

  it('renders modal with video player, metadata, prompt and brandkit snapshot', () => {
    render(<MediaPlayerModal generation={mockGen} isOpen={true} onClose={() => {}} onRemix={() => {}} />);
    expect(screen.getByText('Wan 2.1 Video')).toBeInTheDocument();
    expect(screen.getByText('Cinematic drone shot over misty cyberpunk neon metropolis')).toBeInTheDocument();
    expect(screen.getByText(/RAW photo, cinematic drone shot/)).toBeInTheDocument();
    expect(screen.getByText('98765')).toBeInTheDocument();
    expect(screen.getByText('16:9')).toBeInTheDocument();
    expect(screen.getByText('1080p')).toBeInTheDocument();
    expect(screen.getByText('Cyberpunk Neon Brand')).toBeInTheDocument();
  });

  it('copies prompt and file path to clipboard', async () => {
    render(<MediaPlayerModal generation={mockGen} isOpen={true} onClose={() => {}} onRemix={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: /copier le prompt/i }));
    await waitFor(() => { expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockGen.prompt); });
    fireEvent.click(screen.getByRole('button', { name: /copier le chemin/i }));
    await waitFor(() => { expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockGen.filePath); });
  });

  it('toggles favorite inside modal', async () => {
    vi.mocked(apiClient.toggleFavorite).mockResolvedValue({ id: 'gen_modal_1', isFavorite: true });
    const onFavoriteToggled = vi.fn();
    render(<MediaPlayerModal generation={mockGen} isOpen={true} onClose={() => {}} onRemix={() => {}} onFavoriteToggled={onFavoriteToggled} />);

    fireEvent.click(screen.getByRole('button', { name: /favori/i }));
    await waitFor(() => {
      expect(apiClient.toggleFavorite).toHaveBeenCalledWith('gen_modal_1');
      expect(onFavoriteToggled).toHaveBeenCalledWith(expect.objectContaining({ isFavorite: true }));
    });
  });

  it('triggers onRemix callback when remix button is clicked', () => {
    const onRemix = vi.fn();
    render(<MediaPlayerModal generation={mockGen} isOpen={true} onClose={() => {}} onRemix={onRemix} />);
    fireEvent.click(screen.getByRole('button', { name: /remix/i }));
    expect(onRemix).toHaveBeenCalledWith(mockGen);
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<MediaPlayerModal generation={mockGen} isOpen={true} onClose={onClose} onRemix={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: /fermer/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
