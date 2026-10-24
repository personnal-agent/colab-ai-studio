import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../services/apiClient';
import type { TaskStatusEvent } from '../types/studio';

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches studio config', async () => {
    const mockConfig = { executionMode: 'colab', defaultStoragePath: '/data' };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => mockConfig });
    const config = await apiClient.getConfig();
    expect(global.fetch).toHaveBeenCalledWith('/api/config', expect.anything());
    expect(config).toEqual(mockConfig);
  });

  it('switches execution mode via POST', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ executionMode: 'local' }) });
    const res = await apiClient.switchExecutionMode('local');
    expect(global.fetch).toHaveBeenCalledWith('/api/config/execution-mode', { method: 'POST', body: JSON.stringify({ executionMode: 'local' }), headers: { 'Content-Type': 'application/json' } });
    expect(res.executionMode).toBe('local');
  });

  it('updates colab url via POST', async () => {
    const tunnelUrl = 'https://new-colab.ngrok-free.app';
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ tunnelUrl }) });
    const res = await apiClient.updateColabUrl(tunnelUrl);
    expect(global.fetch).toHaveBeenCalledWith('/api/config/colab-url', { method: 'POST', body: JSON.stringify({ tunnelUrl }), headers: { 'Content-Type': 'application/json' } });
    expect(res.tunnelUrl).toBe(tunnelUrl);
  });

  it('fetches health status', async () => {
    const mockHealth = { status: 'healthy', worker: { reachable: true } };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => mockHealth });
    const health = await apiClient.getHealth();
    expect(global.fetch).toHaveBeenCalledWith('/api/health', expect.anything());
    expect(health.status).toBe('healthy');
  });

  it('lists models and switches active model', async () => {
    const mockModels = [{ id: 'wan-2.1', name: 'Wan 2.1 Video', type: 'video' }];
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => mockModels })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ currentModel: 'wan-2.1' }) });
    const models = await apiClient.listModels();
    expect(models).toHaveLength(1);
    const switchRes = await apiClient.switchModel('wan-2.1');
    expect(switchRes.currentModel).toBe('wan-2.1');
  });

  it('lists generations with query parameters', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    await apiClient.listGenerations({ projectId: 'proj_1', favorite: true, mediaType: 'image', q: 'sunset' });
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/generations?projectId=proj_1&favorite=true&mediaType=image&q=sunset', expect.anything(),
    );
  });

  it('submits generation request', async () => {
    const submitReq = { modelId: 'wan-2.1', prompt: 'Sunset over ocean' };
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ taskId: 'task_1', status: 'pending' }) });
    const res = await apiClient.submitGeneration(submitReq);
    expect(global.fetch).toHaveBeenCalledWith('/api/generate/media', expect.anything());
    expect(res.taskId).toBe('task_1');
  });

  it('toggles favorite on generation via PATCH', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 'gen_1', isFavorite: true }) });
    const res = await apiClient.toggleFavorite('gen_1');
    expect(global.fetch).toHaveBeenCalledWith('/api/generations/gen_1/favorite', expect.objectContaining({ method: 'PATCH' }));
    expect(res.isFavorite).toBe(true);
  });

  it('cancels active task', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'cancelled', taskId: 'task_1' }) });
    const res = await apiClient.cancelTask('task_1');
    expect(res.status).toBe('cancelled');
  });

  it('subscribes to task status SSE events', () => {
    const events: TaskStatusEvent[] = [];
    const eventSourceMockInstances: MockEventSource[] = [];

    class MockEventSource {
      url: string;
      listeners: Record<string, ((evt: { data: string }) => void)[]> = {};
      close = vi.fn();
      constructor(url: string) {
        this.url = url;
        eventSourceMockInstances.push(this);
      }
      addEventListener(event: string, cb: (evt: { data: string }) => void) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(cb);
      }
      dispatchEvent(event: string, data: unknown) {
        for (const cb of this.listeners[event] || []) {
          cb({ data: JSON.stringify(data) });
        }
      }
    }

    const origES = (global as unknown as { EventSource: unknown }).EventSource;
    (global as unknown as { EventSource: unknown }).EventSource = MockEventSource;

    const unsubscribe = apiClient.subscribeTaskStatus('task_123', (evt) => { events.push(evt); });
    expect(eventSourceMockInstances).toHaveLength(1);
    expect(eventSourceMockInstances[0].url).toBe('/api/tasks/task_123/status');

    eventSourceMockInstances[0].dispatchEvent('running', {
      status: 'running', progress: 50, step: 'Sampling step 10/20',
    });
    expect(events).toHaveLength(1);
    expect(events[0].taskId).toBe('task_123');
    expect(events[0].progress).toBe(50);
    unsubscribe();
    expect(eventSourceMockInstances[0].close).toHaveBeenCalled();
    (global as unknown as { EventSource: unknown }).EventSource = origES;
  });

  it('throws API error with response message on failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Custom error detail' }) });
    await expect(apiClient.getConfig()).rejects.toThrow('Custom error detail');
  });
});
