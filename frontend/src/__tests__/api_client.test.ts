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

  it('updates colab url and secret via POST', async () => {
    const tunnelUrl = 'https://new-colab.ngrok-free.app';
    const secret = 'my-secret-token';
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ tunnelUrl, secretConfigured: true }) });
    const res = await apiClient.updateColabUrl(tunnelUrl, secret);
    expect(global.fetch).toHaveBeenCalledWith('/api/config/colab-url', {
      method: 'POST',
      body: JSON.stringify({ tunnelUrl, secret }),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.tunnelUrl).toBe(tunnelUrl);
    expect(res.secretConfigured).toBe(true);
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

  it('handles characters CRUD with archetypes and update', async () => {
    const mockChar = {
      id: 'char_1',
      name: 'Elena Vance',
      physicalPrompt: 'silver hair',
      archetype: 'The Wildcard',
      visualAnchors: ['neon jacket'],
      enginePreference: 'local',
      createdAt: '2026-10-29T12:00:00Z',
    };
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [mockChar] })
      .mockResolvedValueOnce({ ok: true, json: async () => mockChar })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockChar, name: 'Elena V2' }) });

    const filtered = await apiClient.listCharacters('The Wildcard');
    expect(global.fetch).toHaveBeenCalledWith('/api/characters?archetype=The%20Wildcard', expect.anything());
    expect(filtered).toHaveLength(1);

    const retrieved = await apiClient.getCharacter('char_1');
    expect(global.fetch).toHaveBeenCalledWith('/api/characters/char_1', expect.anything());
    expect(retrieved.name).toBe('Elena Vance');

    const updated = await apiClient.updateCharacter('char_1', { name: 'Elena V2' });
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/characters/char_1',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ name: 'Elena V2' }) }),
    );
    expect(updated.name).toBe('Elena V2');
  });

  it('handles agent instructions CRUD, toggle, and reorder', async () => {
    const mockInst = {
      id: 'inst_1',
      title: 'Cinematic Lighting',
      description: 'Use soft volumetric lighting',
      isActive: true,
      referenceAssetUrls: [],
      order: 0,
      createdAt: '2026-10-29T12:00:00Z',
      updatedAt: '2026-10-29T12:00:00Z',
    };
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [mockInst] })
      .mockResolvedValueOnce({ ok: true, json: async () => mockInst })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockInst, isActive: false }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', instructions: [mockInst] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'deleted', id: 'inst_1' }) });

    const instructions = await apiClient.listAgentInstructions();
    expect(instructions).toHaveLength(1);

    const created = await apiClient.createAgentInstruction({
      title: 'Cinematic Lighting',
      description: 'Use soft volumetric lighting',
    });
    expect(created.title).toBe('Cinematic Lighting');

    const toggled = await apiClient.toggleAgentInstruction('inst_1', false);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/agent-instructions/inst_1/toggle',
      expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ isActive: false }) }),
    );
    expect(toggled.isActive).toBe(false);

    const reordered = await apiClient.reorderAgentInstructions(['inst_1']);
    expect(reordered.status).toBe('ok');

    const deleted = await apiClient.deleteAgentInstruction('inst_1');
    expect(deleted.id).toBe('inst_1');
  });

  it('throws API error with response message on failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Custom error detail' }) });
    await expect(apiClient.getConfig()).rejects.toThrow('Custom error detail');
  });
});
