import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { apiClient } from '../services/apiClient';
import type { Generation, HealthResponse, StudioConfig } from '../types/studio';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    getConfig: vi.fn(), getHealth: vi.fn(), listProjects: vi.fn(),
    listGenerations: vi.fn(), toggleFavorite: vi.fn(), cancelTask: vi.fn(), subscribeTaskStatus: vi.fn(),
  },
  getMediaFileUrl: (g: { filePath?: string | null }) => g.filePath || '',
  getMediaThumbnailUrl: (g: { thumbnailPath?: string | null; filePath?: string | null }) => g.thumbnailPath || g.filePath || '',
}));

describe('App Integration', () => {
  const mockGen: Generation = {
    id: 'gen_app_1', status: 'completed', mediaType: 'image', prompt: 'Majestic mountain landscape at sunrise',
    filePath: '/outputs/mountain.png', thumbnailPath: '/outputs/mountain_thumb.png',
    modelId: 'flux-dev', modelName: 'FLUX.1 Dev', isFavorite: false,
    parameters: { seed: 1234, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
    references: {}, createdAt: '2026-10-24T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.getConfig).mockResolvedValue({
      executionMode: 'colab', defaultStoragePath: '/workspace/storage',
      colab: { tunnelUrl: 'https://colab-proxy-abc.ngrok.app', gpuName: 'NVIDIA A100-SXM4-40GB', vramTotalMb: 40960, vramUsedMb: 8200 },
    } as unknown as StudioConfig);
    vi.mocked(apiClient.getHealth).mockResolvedValue({
      status: 'ok', executionMode: 'colab', storage: { path: '/workspace/storage', reachable: true, availableBytes: 1000000 },
      worker: { reachable: true, executionMode: 'colab', gpuName: 'NVIDIA A100-SXM4-40GB', vramTotalMb: 40960, vramUsedMb: 8200, latencyMs: 42 },
    } as unknown as HealthResponse);
    vi.mocked(apiClient.listProjects).mockResolvedValue([]);
    vi.mocked(apiClient.listGenerations).mockResolvedValue([mockGen]);
  });

  it('renders app with TopNavBar, MediaGallery and opens MediaPlayerModal on card click', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /Colab AI Studio/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Image & Video')).toBeInTheDocument();
      expect(screen.getByText('Majestic mountain landscape at sunrise')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('media-card-gen_app_1'));
    await waitFor(() => { expect(screen.getByRole('button', { name: /remix/i })).toBeInTheDocument(); });

    fireEvent.click(screen.getByRole('button', { name: /remix/i }));
    await waitFor(() => { expect(screen.queryByRole('button', { name: /remix/i })).not.toBeInTheDocument(); });
  });
});
