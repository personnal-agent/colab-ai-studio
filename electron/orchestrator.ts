import { ChildProcess, spawn } from 'child_process';
import http from 'http';
import path from 'path';
import fs from 'fs';

export interface RuntimeEndpoints {
  fastapi: string;
  gateway: string;
  auth: string;
  localService: string;
}

export class ElectronProcessOrchestrator {
  private repoRoot: string;
  private fastapiProcess: ChildProcess | null = null;
  private endpoints: RuntimeEndpoints;
  private isShuttingDown = false;

  constructor(repoRoot: string, endpoints?: Partial<RuntimeEndpoints>) {
    this.repoRoot = repoRoot;
    this.endpoints = {
      fastapi: endpoints?.fastapi || 'http://127.0.0.1:8000',
      gateway: endpoints?.gateway || 'http://127.0.0.1:51491',
      auth: endpoints?.auth || 'http://127.0.0.1:45899',
      localService: endpoints?.localService || 'http://127.0.0.1:8002',
    };
  }

  public getEndpoints(): RuntimeEndpoints {
    return { ...this.endpoints };
  }

  private resolvePythonBin(): string {
    const venvBin = '/home/instructeur/.venvs/colab-ai-studio/bin/python';
    if (fs.existsSync(venvBin)) {
      return venvBin;
    }
    const localVenv = path.join(this.repoRoot, '.venv', 'bin', 'python');
    if (fs.existsSync(localVenv)) {
      return localVenv;
    }
    return process.platform === 'win32' ? 'python' : 'python3';
  }

  public async startFastAPI(): Promise<void> {
    if (this.fastapiProcess) {
      return;
    }

    const url = new URL(this.endpoints.fastapi);
    const port = url.port || '8000';
    const host = url.hostname || '127.0.0.1';

    // Vérifie si l'API est déjà active (ex: dev server pré-existant)
    const alreadyUp = await this.probeHealth(this.endpoints.fastapi + '/api/health');
    if (alreadyUp) {
      console.log(`[Orchestrator] FastAPI déjà actif sur ${this.endpoints.fastapi}`);
      return;
    }

    const pythonBin = this.resolvePythonBin();
    console.log(`[Orchestrator] Démarrage FastAPI via ${pythonBin} sur ${host}:${port}...`);

    this.fastapiProcess = spawn(
      pythonBin,
      ['-m', 'uvicorn', 'app.main:app', '--host', host, '--port', port],
      {
        cwd: this.repoRoot,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
          ALLOW_CONFIG_EDIT: '1',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      }
    );

    this.fastapiProcess.stdout?.on('data', (chunk: Buffer) => {
      process.stdout.write(`[FastAPI] ${chunk}`);
    });

    this.fastapiProcess.stderr?.on('data', (chunk: Buffer) => {
      process.stderr.write(`[FastAPI] ${chunk}`);
    });

    this.fastapiProcess.on('exit', (code, signal) => {
      console.log(`[Orchestrator] FastAPI terminé avec code ${code}, signal ${signal}`);
      this.fastapiProcess = null;
      if (!this.isShuttingDown) {
        console.warn('[Orchestrator] Arrêt inattendu de FastAPI !');
      }
    });

    // Attente active de la sonde de santé
    const ready = await this.waitForHealth(this.endpoints.fastapi + '/api/health', 15000);
    if (!ready) {
      await this.stopAll();
      throw new Error(`[Orchestrator] Échec de la sonde de santé FastAPI sur ${this.endpoints.fastapi}`);
    }
    console.log(`[Orchestrator] FastAPI est prêt et opérationnel sur ${this.endpoints.fastapi}`);
  }

  public async probeHealth(healthUrl: string): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        const req = http.get(healthUrl, { timeout: 1500 }, (res) => {
          resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.on('timeout', () => {
          req.destroy();
          resolve(false);
        });
      } catch {
        resolve(false);
      }
    });
  }

  public async waitForHealth(healthUrl: string, timeoutMs: number = 10000): Promise<boolean> {
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      if (this.isShuttingDown) return false;
      const ok = await this.probeHealth(healthUrl);
      if (ok) return true;
      await new Promise((r) => setTimeout(r, 400));
    }
    return false;
  }

  public async stopAll(): Promise<void> {
    this.isShuttingDown = true;
    console.log('[Orchestrator] Arrêt des processus fils...');

    if (this.fastapiProcess && this.fastapiProcess.pid) {
      const pid = this.fastapiProcess.pid;
      try {
        this.fastapiProcess.kill('SIGTERM');
      } catch {
        // Déjà arrêté
      }

      // Période de grâce de 2,5s avant SIGKILL
      const waitGrace = new Promise<void>((resolve) => {
        const interval = setInterval(() => {
          if (!this.fastapiProcess) {
            clearInterval(interval);
            resolve();
          }
        }, 100);
        setTimeout(() => {
          clearInterval(interval);
          resolve();
        }, 2500);
      });

      await waitGrace;

      if (this.fastapiProcess) {
        console.warn(`[Orchestrator] Processus ${pid} toujours actif, émission SIGKILL...`);
        try {
          this.fastapiProcess.kill('SIGKILL');
        } catch {
          // Ignorer
        }
        this.fastapiProcess = null;
      }
    }
    console.log('[Orchestrator] Tous les sous-processus sont arrêtés.');
  }
}
