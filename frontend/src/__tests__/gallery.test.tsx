import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MediaCard } from '../components/gallery/MediaCard';
import { MediaGallery } from '../components/gallery/MediaGallery';
import { SearchAndFilterBar } from '../components/gallery/SearchAndFilterBar';
import { TaskProgressCard } from '../components/gallery/TaskProgressCard';
import { Generation } from '../types/studio';

describe('Gallery & Search Components', () => {
  describe('SearchAndFilterBar', () => {
    it('handles search input and toggles filter chips cumulatively', () => {
      const onSearchChange = vi.fn();
      const onFilterChange = vi.fn();

      render(
        <SearchAndFilterBar
          searchQuery=""
          selectedTypes={[]}
          onSearchChange={onSearchChange}
          onFilterChange={onFilterChange}
        />
      );

      const input = screen.getByPlaceholderText(/search images, videos, and lip syncs/i);
      expect(input).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'mountain' } });
      expect(onSearchChange).toHaveBeenCalledWith('mountain');

      const videoChip = screen.getByRole('button', { name: /\+ Video/i });
      fireEvent.click(videoChip);
      expect(onFilterChange).toHaveBeenCalledWith(['video']);
    });
  });

  describe('TaskProgressCard', () => {
    it('displays task progress and cancels task on button click', () => {
      const onCancel = vi.fn();
      const task: Generation = {
        id: 'task_active_1',
        status: 'running',
        mediaType: 'video',
        prompt: 'A misty mountain range at sunrise',
        modelId: 'seedance-2.5',
        modelName: 'Seedance 2.5',
        parameters: { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
        references: {},
        isFavorite: false,
        progress: 65,
        createdAt: '2026-10-23T12:00:00Z',
      };

      render(<TaskProgressCard task={task} onCancel={onCancel} />);

      expect(screen.getByText('Seedance 2.5')).toBeInTheDocument();
      expect(screen.getByText(/65%/)).toBeInTheDocument();

      const cancelBtn = screen.getByRole('button', { name: /annuler/i });
      fireEvent.click(cancelBtn);
      expect(onCancel).toHaveBeenCalledWith('task_active_1');
    });
  });

  describe('MediaCard', () => {
    const mockImageGen: Generation = {
      id: 'gen_img_1',
      status: 'completed',
      mediaType: 'image',
      prompt: 'Cyberpunk neon street at dusk',
      modelId: 'noctq-v4',
      modelName: 'NoctQ V4',
      parameters: { seed: 1234, aspectRatio: '16:9', resolution: '1080p', duration: '0s' },
      references: {},
      filePath: '/outputs/img_1.png',
      thumbnailPath: '/outputs/img_1_thumb.jpg',
      isFavorite: false,
      progress: 100,
      createdAt: '2026-10-23T10:00:00Z',
    };

    const mockVideoGen: Generation = {
      ...mockImageGen,
      id: 'gen_vid_1',
      mediaType: 'video',
      filePath: '/outputs/vid_1.mp4',
    };

    it('renders image card and toggles favorite without selecting card', () => {
      const onSelect = vi.fn();
      const onToggleFavorite = vi.fn();

      render(
        <MediaCard
          generation={mockImageGen}
          onSelect={onSelect}
          onToggleFavorite={onToggleFavorite}
        />
      );

      expect(screen.getByText('Cyberpunk neon street at dusk')).toBeInTheDocument();

      const favBtn = screen.getByRole('button', { name: /marquer comme favori/i });
      fireEvent.click(favBtn);
      expect(onToggleFavorite).toHaveBeenCalledWith('gen_img_1');
      expect(onSelect).not.toHaveBeenCalled();

      // Click sur la carte
      fireEvent.click(screen.getByText('Cyberpunk neon street at dusk'));
      expect(onSelect).toHaveBeenCalledWith(mockImageGen);
    });

    it('renders video card with 4K badge when upscaled', () => {
      const upscaledVid: Generation = {
        ...mockVideoGen,
        id: 'gen_up_vid',
        parameters: { ...mockVideoGen.parameters, resolution: '4k' },
      };

      render(
        <MediaCard
          generation={upscaledVid}
          onSelect={vi.fn()}
          onToggleFavorite={vi.fn()}
        />
      );

      expect(screen.getByText('4K')).toBeInTheDocument();
    });
  });

  describe('MediaGallery', () => {
    it('renders active tasks at the top and completed cards in grid', () => {
      const activeTask: Generation = {
        id: 'task_running',
        status: 'running',
        mediaType: 'image',
        prompt: 'Generating futuristic city...',
        modelId: 'noctq',
        modelName: 'NoctQ',
        parameters: { seed: 1, aspectRatio: '1:1', resolution: '1080p', duration: '0s' },
        references: {},
        isFavorite: false,
        progress: 30,
        createdAt: '2026-10-23T12:00:00Z',
      };

      const completedGen: Generation = {
        id: 'gen_done',
        status: 'completed',
        mediaType: 'video',
        prompt: 'Forest drone view',
        modelId: 'seedance',
        modelName: 'Seedance',
        parameters: { seed: 2, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
        references: {},
        filePath: '/outputs/forest.mp4',
        isFavorite: true,
        progress: 100,
        createdAt: '2026-10-23T11:00:00Z',
      };

      render(
        <MediaGallery
          activeTasks={[activeTask]}
          generations={[completedGen]}
          onSelectGeneration={vi.fn()}
          onToggleFavorite={vi.fn()}
          onCancelTask={vi.fn()}
        />
      );

      expect(screen.getByText(/Generating futuristic city/i)).toBeInTheDocument();
      expect(screen.getByText('Forest drone view')).toBeInTheDocument();
    });

    it('renders empty message when no generations exist', () => {
      render(
        <MediaGallery
          activeTasks={[]}
          generations={[]}
          onSelectGeneration={vi.fn()}
          onToggleFavorite={vi.fn()}
          onCancelTask={vi.fn()}
        />
      );

      expect(screen.getByText(/aucun média trouvé/i)).toBeInTheDocument();
    });
  });
});
