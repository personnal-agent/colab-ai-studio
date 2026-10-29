/**
 * @vitest-environment node
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import http from 'http';
import { ElectronProcessOrchestrator } from '../../../electron/orchestrator';

describe('ElectronProcessOrchestrator Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default and custom endpoints', () => {
    const orchestratorDefault = new ElectronProcessOrchestrator('/test/root');
    expect(orchestratorDefault.getEndpoints()).toEqual({
      fastapi: 'http://127.0.0.1:8000',
      gateway: 'http://127.0.0.1:51491',
      auth: 'http://127.0.0.1:45899',
      localService: 'http://127.0.0.1:8002',
    });

    const orchestratorCustom = new ElectronProcessOrchestrator('/test/root', {
      fastapi: 'http://127.0.0.1:9000',
    });
    expect(orchestratorCustom.getEndpoints().fastapi).toBe('http://127.0.0.1:9000');
  });

  it('probes health and returns true on HTTP 200', async () => {
    // Crée un serveur mock HTTP temporaire sur un port aléatoire
    const server = http.createServer((_req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'healthy' }));
    });

    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', () => resolve()));
    const port = (server.address() as import('net').AddressInfo).port;
    const testUrl = `http://127.0.0.1:${port}/api/health`;

    try {
      const orchestrator = new ElectronProcessOrchestrator('/test/root');
      const isHealthy = await orchestrator.probeHealth(testUrl);
      expect(isHealthy).toBe(true);

      const waitForResult = await orchestrator.waitForHealth(testUrl, 1000);
      expect(waitForResult).toBe(true);
    } finally {
      await new Promise<void>((resolve) => server.close(() => resolve()));
    }
  });

  it('returns false when probing an unreachable port', async () => {
    const orchestrator = new ElectronProcessOrchestrator('/test/root');
    // Port réservé / fermé
    const isHealthy = await orchestrator.probeHealth('http://127.0.0.1:59999/api/health');
    expect(isHealthy).toBe(false);

    const waitForResult = await orchestrator.waitForHealth('http://127.0.0.1:59999/api/health', 300);
    expect(waitForResult).toBe(false);
  });

  it('stops all child processes gracefully without error', async () => {
    const orchestrator = new ElectronProcessOrchestrator('/test/root');
    await expect(orchestrator.stopAll()).resolves.toBeUndefined();
  });
});
