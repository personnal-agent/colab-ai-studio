/**
 * Client API HTTP & SSE unifié pour Colab AI Studio (frontend/src/services/apiClient.ts).
 */

import {
  BrandKit,
  ExecutionMode,
  Generation,
  HealthResponse,
  ModelDefinition,
  Project,
  StudioConfig,
  TaskProgressEvent,
} from '../types/studio';

class ApiClientError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Erreur HTTP ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      // Non-JSON error
    }
    throw new ApiClientError(errorDetail, response.status);
  }

  return response.json();
}

export const apiClient = {
  // Santé & Diagnostic
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch('/api/health');
    if (!res.ok) {
      throw new ApiClientError(`Erreur HTTP ${res.status}`, res.status);
    }
    return res.json();
  },

  // Configuration & Bascule à chaud Local / Colab
  async getConfig(): Promise<StudioConfig> {
    return request<StudioConfig>('/api/config');
  },

  async switchExecutionMode(
    mode: ExecutionMode
  ): Promise<{ switched: boolean; executionMode: ExecutionMode }> {
    return request<{ switched: boolean; executionMode: ExecutionMode }>(
      '/api/config/execution-mode',
      {
        method: 'POST',
        body: JSON.stringify({ executionMode: mode }),
      }
    );
  },

  // Modèles
  async listModels(): Promise<ModelDefinition[]> {
    return request<ModelDefinition[]>('/api/models');
  },

  async switchModel(modelId: string): Promise<{ switched: boolean; activeModel: string }> {
    return request<{ switched: boolean; activeModel: string }>('/api/models/switch', {
      method: 'POST',
      body: JSON.stringify({ modelId }),
    });
  },

  // Générations & Cycle de vie
  async listGenerations(filters?: {
    isFavorite?: boolean;
    mediaType?: string;
    q?: string;
  }): Promise<Generation[]> {
    const params = new URLSearchParams();
    if (filters?.isFavorite !== undefined) {
      params.set('isFavorite', String(filters.isFavorite));
    }
    if (filters?.mediaType) {
      params.set('mediaType', filters.mediaType);
    }
    if (filters?.q) {
      params.set('q', filters.q);
    }
    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`/api/generations${queryStr}`);
    if (!res.ok) {
      throw new ApiClientError(`Erreur HTTP ${res.status}`, res.status);
    }
    return res.json();
  },

  async getGeneration(id: string): Promise<Generation> {
    return request<Generation>(`/api/generations/${id}`);
  },

  async toggleFavorite(id: string): Promise<Generation> {
    return request<Generation>(`/api/generations/${id}/favorite`, {
      method: 'PATCH',
    });
  },

  async deleteGeneration(id: string): Promise<{ deleted: boolean; id: string }> {
    return request<{ deleted: boolean; id: string }>(`/api/generations/${id}`, {
      method: 'DELETE',
    });
  },

  async generateMedia(payload: unknown): Promise<Generation> {
    return request<Generation>('/api/generate/media', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async cancelTask(taskId: string): Promise<Generation> {
    return request<Generation>(`/api/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  },

  // Projets
  async listProjects(): Promise<Project[]> {
    return request<Project[]>('/api/projects');
  },

  async createProject(payload: Partial<Project>): Promise<Project> {
    return request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteProject(id: string): Promise<{ deleted: boolean; id: string }> {
    return request<{ deleted: boolean; id: string }>(`/api/projects/${id}`, {
      method: 'DELETE',
    });
  },

  // Brand Kits
  async listBrandKits(): Promise<BrandKit[]> {
    return request<BrandKit[]>('/api/brand-kits');
  },

  async createBrandKit(payload: Partial<BrandKit>): Promise<BrandKit> {
    return request<BrandKit>('/api/brand-kits', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteBrandKit(id: string): Promise<{ deleted: boolean; id: string }> {
    return request<{ deleted: boolean; id: string }>(`/api/brand-kits/${id}`, {
      method: 'DELETE',
    });
  },

  // Souscription SSE temps réel
  subscribeTaskStatus(
    taskId: string,
    onEvent: (event: TaskProgressEvent) => void,
    onError?: (err: Event) => void
  ): () => void {
    const eventSource = new EventSource(`/api/tasks/${taskId}/status`);

    eventSource.onmessage = (msg: MessageEvent) => {
      try {
        const data = JSON.parse(msg.data) as TaskProgressEvent;
        onEvent(data);
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
          eventSource.close();
        }
      } catch {
        // Ignorer les messages mal formés ou pings
      }
    };

    eventSource.onerror = (err: Event) => {
      if (onError) {
        onError(err);
      }
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  },
};
