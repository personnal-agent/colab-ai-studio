import { fireEvent, render, screen, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MediaCard } from '../components/gallery/MediaCard';
import { MediaPlayerModal } from '../components/gallery/MediaPlayerModal';
import { AgentsWorkspaceView } from '../components/agents/AgentsWorkspaceView';
import type { CanvasAssetLayer, Generation } from '../types/studio';

describe('Canvas Injection Workflow (Phase 4 Task 3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockGeneration: Generation = {
    id: 'gen_inject_101',
    status: 'completed',
    mediaType: 'video',
    prompt: 'Cinematic robot walking on Mars',
    filePath: '/outputs/robot_mars.mp4',
    thumbnailPath: '/outputs/robot_mars_thumb.png',
    modelId: 'wan-2.1',
    modelName: 'Wan 2.1 Video',
    isFavorite: false,
    parameters: { seed: 1234, aspectRatio: '16:9', resolution: '1080p', duration: '5s' },
    references: {},
    createdAt: '2026-10-29T12:00:00Z',
  };

  it('renders "Injecter dans le canevas" button on MediaCard and fires callback', () => {
    const onInjectToCanvas = vi.fn();
    render(
      <MediaCard
        generation={mockGeneration}
        onSelect={() => {}}
        onInjectToCanvas={onInjectToCanvas}
      />
    );

    const injectBtn = screen.getByRole('button', { name: /injecter dans le canevas/i });
    expect(injectBtn).toBeInTheDocument();

    fireEvent.click(injectBtn);
    expect(onInjectToCanvas).toHaveBeenCalledTimes(1);
    expect(onInjectToCanvas).toHaveBeenCalledWith(mockGeneration);
  });

  it('renders "Injecter dans le Canevas Agents" button in MediaPlayerModal and handles injection', () => {
    const onInjectToCanvas = vi.fn();
    const onClose = vi.fn();
    render(
      <MediaPlayerModal
        generation={mockGeneration}
        isOpen={true}
        onClose={onClose}
        onRemix={() => {}}
        onInjectToCanvas={onInjectToCanvas}
      />
    );

    const injectModalBtn = screen.getByRole('button', { name: /injecter dans le canevas/i });
    expect(injectModalBtn).toBeInTheDocument();

    fireEvent.click(injectModalBtn);
    expect(onInjectToCanvas).toHaveBeenCalledTimes(1);
    expect(onInjectToCanvas).toHaveBeenCalledWith(mockGeneration);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders initial layers passed via injectedLayers prop in AgentsWorkspaceView', () => {
    const initialLayers: CanvasAssetLayer[] = [
      {
        id: 'layer-gen_inject_101',
        name: 'Cinematic robot walking on Mars',
        type: 'video',
        taskId: 'gen_inject_101',
        status: 'ready',
      },
    ];

    render(<AgentsWorkspaceView injectedLayers={initialLayers} />);

    expect(screen.getByText(/1 Calque\(s\) actif\(s\) sur le canevas/i)).toBeInTheDocument();
    expect(screen.getByText('Cinematic robot walking on Mars')).toBeInTheDocument();
    expect(screen.getByTestId('canvas-asset-layer')).toBeInTheDocument();
  });

  it('dynamically receives layer via window "omniforge:inject-canvas-asset" event', () => {
    render(<AgentsWorkspaceView />);

    expect(screen.getByText(/Prêt pour le montage des calques WebGPU/i)).toBeInTheDocument();

    const layerToInject: CanvasAssetLayer = {
      id: 'layer-dynamic-001',
      name: 'Dynamic 3D Mesh asset',
      type: 'mesh_3d',
      taskId: 'task-dyn-001',
      status: 'ready',
    };

    act(() => {
      window.dispatchEvent(
        new CustomEvent('omniforge:inject-canvas-asset', {
          detail: layerToInject,
        })
      );
    });

    expect(screen.getByText('Dynamic 3D Mesh asset')).toBeInTheDocument();
    expect(screen.getByText(/Calque\(s\) actif\(s\) sur le canevas/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Média "Dynamic 3D Mesh asset" \(mesh_3d\) injecté avec succès/i)
    ).toBeInTheDocument();
  });
});
