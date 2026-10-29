import { fireEvent, render, screen, waitFor, act, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { detectGraphicsCapability } from '../services/graphicsCapability';
import { Canvas2DFallback } from '../components/canvas/Canvas2DFallback';
import { AgentsWorkspaceView } from '../components/agents/AgentsWorkspaceView';
import type { CanvasAssetLayer } from '../types/studio';

describe('WebGPU Detection and Canvas2D Fallback (Phase 5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('detectGraphicsCapability', () => {
    it('returns "webgpu" when navigator.gpu and requestAdapter succeed', async () => {
      const mockAdapter = {
        info: { vendor: 'intel', architecture: 'gen9' },
      };
      const mockGpu = {
        requestAdapter: vi.fn().mockResolvedValue(mockAdapter),
      };
      vi.stubGlobal('navigator', { gpu: mockGpu });

      const res = await detectGraphicsCapability();
      expect(res.supported).toBe(true);
      expect(res.renderer).toBe('webgpu');
      expect(res.adapterInfo).toBeDefined();

      vi.unstubAllGlobals();
    });

    it('returns "canvas2d" fallback when navigator.gpu is undefined', async () => {
      vi.stubGlobal('navigator', {});

      const res = await detectGraphicsCapability();
      expect(res.supported).toBe(false);
      expect(res.renderer).toBe('canvas2d');
      expect(res.reason).toMatch(/non supporté/i);

      vi.unstubAllGlobals();
    });

    it('returns "canvas2d" fallback when requestAdapter returns null', async () => {
      const mockGpu = {
        requestAdapter: vi.fn().mockResolvedValue(null),
      };
      vi.stubGlobal('navigator', { gpu: mockGpu });

      const res = await detectGraphicsCapability();
      expect(res.supported).toBe(false);
      expect(res.renderer).toBe('canvas2d');
      expect(res.reason).toMatch(/aucun adaptateur/i);

      vi.unstubAllGlobals();
    });

    it('returns "canvas2d" fallback when requestAdapter throws an error', async () => {
      const mockGpu = {
        requestAdapter: vi.fn().mockRejectedValue(new Error('GPU device lost')),
      };
      vi.stubGlobal('navigator', { gpu: mockGpu });

      const res = await detectGraphicsCapability();
      expect(res.supported).toBe(false);
      expect(res.renderer).toBe('canvas2d');
      expect(res.reason).toMatch(/GPU device lost/i);

      vi.unstubAllGlobals();
    });
  });

  describe('Canvas2DFallback component', () => {
    const mockLayers: CanvasAssetLayer[] = [
      {
        id: 'layer-1',
        name: 'Mesh 3D Layer',
        type: 'mesh_3d',
        taskId: 't1',
        status: 'ready',
      },
      {
        id: 'layer-2',
        name: 'Video Background',
        type: 'video',
        taskId: 't2',
        status: 'ready',
      },
    ];

    it('renders HTML5 canvas element and maintains 60 fps render loop', () => {
      const getContextSpy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
        clearRect: vi.fn(),
        fillRect: vi.fn(),
        strokeRect: vi.fn(),
        fillText: vi.fn(),
        save: vi.fn(),
        restore: vi.fn(),
        scale: vi.fn(),
        translate: vi.fn(),
        beginPath: vi.fn(),
        stroke: vi.fn(),
        fill: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        measureText: vi.fn().mockReturnValue({ width: 50 }),
      } as unknown as CanvasRenderingContext2D);

      render(<Canvas2DFallback layers={mockLayers} zoomLevel={100} />);

      expect(screen.getByTestId('canvas-2d-surface')).toBeInTheDocument();
      expect(getContextSpy).toHaveBeenCalledWith('2d');
      expect(screen.getByText(/Canvas2D/i)).toBeInTheDocument();

      getContextSpy.mockRestore();
    });
  });

  describe('AgentsWorkspaceView Graphics Mode Integration', () => {
    it('detects capability and renders graphics status badge in toolbar', async () => {
      vi.stubGlobal('navigator', {}); // triggers canvas2d fallback

      render(<AgentsWorkspaceView />);

      await waitFor(() => {
        const badge = screen.getByTestId('graphics-mode-badge');
        expect(badge).toBeInTheDocument();
        expect(within(badge).getByText(/Canvas2D/i)).toBeInTheDocument();
      });

      vi.unstubAllGlobals();
    });

    it('allows toggling between WebGPU and Canvas2D renderers manually', async () => {
      render(<AgentsWorkspaceView />);

      await waitFor(() => {
        expect(screen.getByTestId('graphics-mode-badge')).toBeInTheDocument();
      });

      const toggleBtn = screen.getByTestId('toggle-renderer-btn');
      act(() => {
        fireEvent.click(toggleBtn);
      });

      await waitFor(() => {
        expect(screen.getByTestId('graphics-mode-badge')).toBeInTheDocument();
      });
    });
  });
});
