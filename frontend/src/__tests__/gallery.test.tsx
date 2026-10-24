import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MediaCard } from '../components/gallery/MediaCard';
import { MediaGallery } from '../components/gallery/MediaGallery';
import { SearchAndFilterBar } from '../components/gallery/SearchAndFilterBar';
import { TaskProgressCard } from '../components/gallery/TaskProgressCard';
import { apiClient } from '../services/apiClient';
import type { Generation, TaskStatusEvent } from '../types/studio';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    listGenerations: vi.fn(), toggleFavorite: vi.fn(), cancelTask: vi.fn(), subscribeTaskStatus: vi.fn(),
  },
}));

describe('Gallery and Media Components', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  describe('SearchAndFilterBar', () => {
    it('renders input with WCAG placeholder and cumulative filter pills', () => {
      const onSearchChange = vi.fn();
      const onTogglePill = vi.fn();
      render(<SearchAndFilterBar searchValue="" onSearchChange={onSearchChange} activePills={['image']} onTogglePill={onTogglePill} />);

      const input = screen.getByPlaceholderText('Search images, videos, and lip syncs');
      expect(input).toBeInTheDocument();
      expect(input).toHaveClass('placeholder-[#4B5563]');

      fireEvent.change(input, { target: { value: 'cyberpunk' } });
      expect(onSearchChange).toHaveBeenCalledWith('cyberpunk');

      const videoPill = screen.getByRole('button', { name: /\+ Video/i });
      fireEvent.click(videoPill);
      expect(onTogglePill).toHaveBeenCalledWith('video');
    });
  });

  describe('TaskProgressCard', () => {
    it('renders progress, step and handles task cancellation', async () => {
      vi.mocked(apiClient.cancelTask).mockResolvedValue({ status: 'cancelled', taskId: 'task_99' });
      const onCancel = vi.fn();
      const event: TaskStatusEvent = { taskId: 'task_99', status: 'running', progress: 65, step: 'Denoising step 13/20' };

      render(<TaskProgressCard event={event} prompt="Futuristic city in rain" modelName="Wan 2.1 Video" onCancelled={onCancel} />);

      expect(screen.getByText('65%')).toBeInTheDocument();
      expect(screen.getByText('Denoising step 13/20')).toBeInTheDocument();
      expect(screen.getByText('Futuristic city in rain')).toBeInTheDocument();
      expect(screen.getByText('Wan 2.1 Video')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /annuler/i }));
      await waitFor(() => {
        expect(apiClient.cancelTask).toHaveBeenCalledWith('task_99');
        expect(onCancel).toHaveBeenCalledWith('task_99');
      });
    });
  });

  describe('MediaCard', () => {
    const baseGen: Generation = {
      id: 'gen_101', status: 'completed', mediaType: 'image', prompt: 'Neon cyber samurai',
      filePath: '/outputs/samurai.png', thumbnailPath: '/outputs/samurai_thumb.png',
      modelId: 'flux-dev', modelName: 'FLUX.1 Dev', isFavorite: false,
      parameters: { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
      references: {}, createdAt: '2026-10-24T12:00:00Z',
    };

    it('renders image card and toggles favorite', async () => {
      vi.mocked(apiClient.toggleFavorite).mockResolvedValue({ id: 'gen_101', isFavorite: true });
      const onSelect = vi.fn();
      render(<MediaCard generation={baseGen} onSelect={onSelect} />);

      expect(screen.getByText('Neon cyber samurai')).toBeInTheDocument();
      expect(screen.getByText('FLUX.1 Dev')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /favori/i }));
      await waitFor(() => { expect(apiClient.toggleFavorite).toHaveBeenCalledWith('gen_101'); });

      fireEvent.click(screen.getByTestId('media-card-gen_101'));
      expect(onSelect).toHaveBeenCalledWith(baseGen);
    });

    it('renders 4K badge on upscaled media cards', () => {
      const upscaledGen: Generation = {
        ...baseGen, id: 'gen_102', mediaType: 'upscale', parameters: { ...baseGen.parameters, resolution: '4K' },
      };
      render(<MediaCard generation={upscaledGen} onSelect={() => {}} />);
      expect(screen.getByText('4K')).toBeInTheDocument();
    });

    it('controls muted video playback on mouse enter and leave', () => {
      const videoGen: Generation = { ...baseGen, id: 'gen_103', mediaType: 'video', filePath: '/outputs/video.mp4' };
      const playSpy = vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockImplementation(() => Promise.resolve());
      const pauseSpy = vi.spyOn(window.HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});

      render(<MediaCard generation={videoGen} onSelect={() => {}} />);
      const card = screen.getByTestId('media-card-gen_103');
      fireEvent.mouseEnter(card);
      expect(playSpy).toHaveBeenCalled();
      fireEvent.mouseLeave(card);
      expect(pauseSpy).toHaveBeenCalled();
    });
  });

  describe('MediaGallery', () => {
    const mockGenerations: Generation[] = [
      {
        id: 'gen_1', status: 'completed', mediaType: 'image', prompt: 'Sunset on beach',
        filePath: '/outputs/beach.png', modelId: 'flux-dev', modelName: 'FLUX.1 Dev', isFavorite: false,
        parameters: { seed: 10, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
        references: {}, createdAt: '2026-10-24T12:00:00Z',
      },
      {
        id: 'gen_2', status: 'completed', mediaType: 'video', prompt: 'Drone shot over mountains',
        filePath: '/outputs/drone.mp4', modelId: 'wan-2.1', modelName: 'Wan 2.1 Video', isFavorite: true,
        parameters: { seed: 20, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
        references: {}, createdAt: '2026-10-24T12:10:00Z',
      },
    ];

    it('fetches generations and applies search and favorite filtering', async () => {
      vi.mocked(apiClient.listGenerations).mockResolvedValue(mockGenerations);
      render(<MediaGallery favoritesOnly={false} activeProjectId={null} onSelectGeneration={() => {}} />);

      await waitFor(() => {
        expect(screen.getByText('Sunset on beach')).toBeInTheDocument();
        expect(screen.getByText('Drone shot over mountains')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search images, videos, and lip syncs');
      fireEvent.change(searchInput, { target: { value: 'Drone' } });

      await waitFor(() => {
        expect(screen.queryByText('Sunset on beach')).not.toBeInTheDocument();
        expect(screen.getByText('Drone shot over mountains')).toBeInTheDocument();
      });
    });
  });
});
