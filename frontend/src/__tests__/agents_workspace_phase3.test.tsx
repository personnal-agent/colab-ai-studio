import { fireEvent, render, screen, waitFor, act, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AgentsWorkspaceView } from '../components/agents/AgentsWorkspaceView';
import { apiClient } from '../services/apiClient';
import type { HealthResponse } from '../types/studio';

describe('AgentsWorkspaceView Phase 3 Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the multi-agent workspace with toolbar and dialogue panels', () => {
    render(<AgentsWorkspaceView />);

    expect(screen.getByTestId('agents-workspace-view')).toBeInTheDocument();
    expect(screen.getByText('Hilo Swarm Dialogue')).toBeInTheDocument();
    expect(screen.getByText('leader active')).toBeInTheDocument();
    expect(screen.getByText(/CanvasAreaV3/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Injecter maillage 3D/i })).toBeInTheDocument();
  });

  it('renders dynamic hardware telemetry chips including CPU, RAM, and GPU/VRAM', async () => {
    const mockHealth: HealthResponse = {
      status: 'healthy',
      executionMode: 'local',
      worker: { reachable: true },
      host: {
        cpu: 'Intel Core i9-13950HX',
        threads: 32,
        ram: '63.6 Go',
        gpu: {
          name: 'NVIDIA RTX 5000 Ada Generation Laptop GPU',
          shortName: 'RTX 5000 Ada',
          vramTotalMb: 15352,
          vramUsedMb: 300,
          vramFreeMb: 15052,
          vramTotalGb: 15.0,
          vramUsedGb: 0.3,
          vramFreeGb: 14.7,
          temperatureC: 52,
          utilizationPct: 1,
          label: 'RTX 5000 Ada · 14.7 Go VRAM',
        },
      },
    };

    vi.spyOn(apiClient, 'getHealth').mockResolvedValue(mockHealth);

    render(<AgentsWorkspaceView />);

    await waitFor(() => {
      const cpuChip = screen.getByTestId('telemetry-cpu-chip');
      const ramChip = screen.getByTestId('telemetry-ram-chip');
      const gpuChip = screen.getByTestId('telemetry-gpu-chip');

      expect(cpuChip).toHaveTextContent(/Intel Core i9-13950HX/i);
      expect(ramChip).toHaveTextContent(/63.6 Go/i);
      expect(gpuChip).toHaveTextContent(/RTX 5000 Ada · 14.7 Go VRAM/i);
      expect(gpuChip).toHaveAttribute('title', expect.stringContaining('14.7 Go libres'));
    });
  });

  it('switches between active agents (leader, planner, coder)', () => {
    render(<AgentsWorkspaceView />);

    const plannerBtn = screen.getByRole('button', { name: 'planner' });
    fireEvent.click(plannerBtn);

    expect(screen.getByText('planner active')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Demander à planner...')).toBeInTheDocument();
  });

  it('streams responses from /v1/chat/completions via SSE reader', async () => {
    const sseChunks = [
      'data: {"choices":[{"delta":{"content":"Composition "}}]}\n\n',
      'data: {"choices":[{"delta":{"content":"WebGPU initiée."}}]}\n\n',
      'data: [DONE]\n\n',
    ];

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        for (const chunk of sseChunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<AgentsWorkspaceView />);

    const input = screen.getByPlaceholderText('Demander à leader...');
    fireEvent.change(input, { target: { value: 'Créer calque 3D' } });

    const submitBtn = screen.getByRole('button', { name: /Envoyer instruction agent/i });
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/v1/chat/completions',
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(screen.getByText(/Composition WebGPU initiée\./i)).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it('triggers 3D mesh generation on /api/generate/media and updates canvas', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        taskId: 'task-mesh-xyz-789',
        generationId: 'gen-mesh-xyz-789',
        status: 'pending',
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<AgentsWorkspaceView />);

    const btn3D = screen.getByRole('button', { name: /Injecter maillage 3D/i });
    await act(async () => {
      fireEvent.click(btn3D);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/generate/media',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"type":"3d"'),
        })
      );
      expect(screen.getByTestId('canvas-3d-layer')).toBeInTheDocument();
      expect(screen.getByText('Calque 3D #1')).toBeInTheDocument();
      expect(screen.getByText(/\[task-mes\]/i)).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it('detects image intent from prompt and triggers NoctQ V4 inference with canvas injection', async () => {
    const submitSpy = vi.spyOn(apiClient, 'submitGeneration').mockResolvedValue({
      taskId: 'task-noctq-12345',
      status: 'pending',
      generationId: 'gen-noctq-12345',
    });

    let sseCallback: ((event: import('../types/studio').TaskStatusEvent) => void) | null = null;
    vi.spyOn(apiClient, 'subscribeTaskStatus').mockImplementation((_taskId, onEvent) => {
      sseCallback = onEvent;
      return () => {};
    });

    const onLayerInjectedMock = vi.fn();

    render(<AgentsWorkspaceView onLayerInjected={onLayerInjectedMock} />);

    const input = screen.getByPlaceholderText('Demander à leader...');
    fireEvent.change(input, { target: { value: 'Génère une image cinématique de métropole cyberpunk' } });

    const submitBtn = screen.getByRole('button', { name: /Envoyer instruction agent/i });
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          modelId: 'noctq-v4',
          prompt: 'Génère une image cinématique de métropole cyberpunk',
          type: 'image',
        })
      );
      const card = screen.getByTestId('gpu-task-card-task-noctq-12345');
      expect(card).toBeInTheDocument();
      expect(within(card).getByText(/NoctQ V4/i)).toBeInTheDocument();
    });

    // Simule la progression SSE puis la complétion
    await act(async () => {
      sseCallback?.({
        taskId: 'task-noctq-12345',
        status: 'running',
        progress: 60,
        step: 'Denoising pass 12/20 on RTX 5000 Ada...',
      });
    });

    expect(screen.getByText(/60%/i)).toBeInTheDocument();

    await act(async () => {
      sseCallback?.({
        taskId: 'task-noctq-12345',
        status: 'completed',
        progress: 100,
        outputUrl: '/outputs/cyberpunk_metropolis.png',
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('canvas-asset-layer')).toBeInTheDocument();
      expect(onLayerInjectedMock).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'image',
          taskId: 'task-noctq-12345',
        })
      );
    });
  });

  it('detects video intent from prompt and triggers MiniMax H3 inference', async () => {
    const submitSpy = vi.spyOn(apiClient, 'submitGeneration').mockResolvedValue({
      taskId: 'task-minimax-777',
      status: 'pending',
      generationId: 'gen-minimax-777',
    });

    vi.spyOn(apiClient, 'subscribeTaskStatus').mockImplementation(() => () => {});

    render(<AgentsWorkspaceView />);

    const input = screen.getByPlaceholderText('Demander à leader...');
    fireEvent.change(input, { target: { value: 'Génère une vidéo haute vitesse avec travelling caméra' } });

    const submitBtn = screen.getByRole('button', { name: /Envoyer instruction agent/i });
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          modelId: 'minimax-h3',
          prompt: 'Génère une vidéo haute vitesse avec travelling caméra',
          type: 'video',
        })
      );
      const card = screen.getByTestId('gpu-task-card-task-minimax-777');
      expect(card).toBeInTheDocument();
      expect(within(card).getByText(/MiniMax H3/i)).toBeInTheDocument();
    });
  });

  it('provides quick toolbar buttons for direct NoctQ V4 and MiniMax H3 generation', async () => {
    const submitSpy = vi.spyOn(apiClient, 'submitGeneration').mockResolvedValue({
      taskId: 'task-quick-image-1',
      status: 'pending',
    });

    vi.spyOn(apiClient, 'subscribeTaskStatus').mockImplementation(() => () => {});

    render(<AgentsWorkspaceView />);

    const quickImageBtn = screen.getByTestId('quick-generate-image-btn');
    const quickVideoBtn = screen.getByTestId('quick-generate-video-btn');

    expect(quickImageBtn).toBeInTheDocument();
    expect(quickVideoBtn).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(quickImageBtn);
    });

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          modelId: 'noctq-v4',
          type: 'image',
        })
      );
    });
  });

  it('does not trigger media generation for purely conversational questions mentioning image or video', async () => {
    const submitSpy = vi.spyOn(apiClient, 'submitGeneration');

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"choices":[{"delta":{"content":"La résolution est 1920x1080."}}]}\n\n'));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<AgentsWorkspaceView />);

    const input = screen.getByPlaceholderText('Demander à leader...');
    fireEvent.change(input, { target: { value: 'Quelle est la résolution de cette image ?' } });

    const submitBtn = screen.getByRole('button', { name: /Envoyer instruction agent/i });
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/v1/chat/completions',
        expect.objectContaining({ method: 'POST' })
      );
      expect(submitSpy).not.toHaveBeenCalled();
    });

    vi.unstubAllGlobals();
  });

  it('correctly extracts real taskId and subscribes when onSubmitGeneration prop is passed', async () => {
    const mockSubmitProp = vi.fn().mockResolvedValue({
      taskId: 'task-real-from-app-999',
      status: 'pending',
      generationId: 'gen-real-999',
    });

    const subscribeSpy = vi.spyOn(apiClient, 'subscribeTaskStatus').mockImplementation(() => () => {});

    render(<AgentsWorkspaceView onSubmitGeneration={mockSubmitProp} />);

    const quickVideoBtn = screen.getByTestId('quick-generate-video-btn');
    await act(async () => {
      fireEvent.click(quickVideoBtn);
    });

    await waitFor(() => {
      expect(mockSubmitProp).toHaveBeenCalledWith(
        expect.objectContaining({
          modelId: 'minimax-h3',
          type: 'video',
        })
      );
      expect(subscribeSpy).toHaveBeenCalledWith(
        'task-real-from-app-999',
        expect.any(Function),
        expect.any(Function)
      );
      expect(screen.getByTestId('gpu-task-card-task-real-from-app-999')).toBeInTheDocument();
    });
  });

  it('cleans up active SSE subscriptions on unmount', async () => {
    const unsubMock = vi.fn();
    vi.spyOn(apiClient, 'submitGeneration').mockResolvedValue({
      taskId: 'task-unmount-test',
      status: 'pending',
    });
    vi.spyOn(apiClient, 'subscribeTaskStatus').mockImplementation(() => unsubMock);

    const { unmount } = render(<AgentsWorkspaceView />);

    const quickImageBtn = screen.getByTestId('quick-generate-image-btn');
    await act(async () => {
      fireEvent.click(quickImageBtn);
    });

    await waitFor(() => {
      expect(screen.getByTestId('gpu-task-card-task-unmount-test')).toBeInTheDocument();
    });

    unmount();

    expect(unsubMock).toHaveBeenCalled();
  });
});
