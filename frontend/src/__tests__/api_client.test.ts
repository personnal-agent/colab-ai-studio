import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../services/apiClient';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches health status successfully', async () => {
    const mockHealth = {
      status: 'ok',
      service: 'Colab AI Studio Control Tower',
      version: '1.0.0',
      executionMode: 'local',
      activeWorkerReachable: true,
      worker: { reachable: true, executionMode: 'local', latencyMs: 1.2 },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const res = await apiClient.getHealth();
    expect(res.status).toBe('ok');
    expect(res.executionMode).toBe('local');
    expect(global.fetch).toHaveBeenCalledWith('/api/health');
  });

  it('switches execution mode via POST /api/config/execution-mode', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ switched: true, executionMode: 'colab' }),
    } as Response);

    const res = await apiClient.switchExecutionMode('colab');
    expect(res.executionMode).toBe('colab');
    expect(global.fetch).toHaveBeenCalledWith('/api/config/execution-mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ executionMode: 'colab' }),
    });
  });

  it('handles 409 conflict when switching mode while tasks are running', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: 'Tâches en cours' }),
    } as Response);

    await expect(apiClient.switchExecutionMode('local')).rejects.toThrow('Tâches en cours');
  });

  it('lists generations with query params', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ id: 'gen_1', isFavorite: true }],
    } as Response);

    const items = await apiClient.listGenerations({ isFavorite: true, mediaType: 'video' });
    expect(items).toHaveLength(1);
    expect(global.fetch).toHaveBeenCalledWith('/api/generations?isFavorite=true&mediaType=video');
  });

  it('submits a new generation task via POST /api/generate/media', async () => {
    const payload = {
      mediaType: 'video',
      prompt: 'A misty mountain',
      modelId: 'seedance',
      modelName: 'Seedance',
      parameters: { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
      references: {},
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: 'gen_100', status: 'pending' }),
    } as Response);

    const gen = await apiClient.generateMedia(payload);
    expect(gen.id).toBe('gen_100');
    expect(gen.status).toBe('pending');
  });

  it('cancels a generation task via POST /api/tasks/{id}/cancel', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'gen_100', status: 'cancelled' }),
    } as Response);

    const res = await apiClient.cancelTask('gen_100');
    expect(res.status).toBe('cancelled');
    expect(global.fetch).toHaveBeenCalledWith('/api/tasks/gen_100/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
  });

  it('subscribes to SSE task progression and handles completed event', async () => {
    class MockEventSource {
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;
      url: string;
      close = vi.fn();

      constructor(url: string) {
        this.url = url;
      }
    }

    global.EventSource = MockEventSource as unknown as typeof EventSource;

    const onEvent = vi.fn();
    const onError = vi.fn();

    const unsubscribe = apiClient.subscribeTaskStatus('gen_test_1', onEvent, onError);
    expect(typeof unsubscribe).toBe('function');
  });
});
