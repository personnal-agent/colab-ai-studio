import { fireEvent, render, screen, waitFor, act } from '@testing-library/react';
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
});
