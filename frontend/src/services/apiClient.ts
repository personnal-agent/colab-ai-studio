/**
 * Client API & SSE pour Colab AI Studio (frontend/src/services/apiClient.ts).
 */
import type {
  BrandKit, ExecutionMode, Generation, GenerationSubmitRequest,
  GenerationSubmitResponse, HealthResponse, ModelDefinition,
  Project, StudioConfig, TaskStatusEvent,
} from '../types/studio';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (!headers['Content-Type'] && options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(endpoint, { ...options, headers });
  if (!response.ok) {
    let detail = `Erreur HTTP ${response.status}`;
    try {
      const errJson = (await response.json()) as { detail?: string };
      if (errJson?.detail) detail = errJson.detail;
    } catch { /* ignore non-json errors */ }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export function getMediaFileUrl(generation: { id: string; filePath?: string | null }): string {
  const path = generation.filePath;
  if (path && (/^(https?:|\/\/|data:|blob:)/i.test(path))) return path;
  return `/api/generations/${generation.id}/file`;
}

export function getMediaThumbnailUrl(generation: { id: string; filePath?: string | null; thumbnailPath?: string | null }): string {
  const thumb = generation.thumbnailPath;
  if (thumb && (/^(https?:|\/\/|data:|blob:)/i.test(thumb))) return thumb;
  if (thumb) return `/api/generations/${generation.id}/thumbnail`;
  return getMediaFileUrl(generation);
}

export const apiClient = {
  getConfig: () => request<StudioConfig>('/api/config'),
  switchExecutionMode: (executionMode: ExecutionMode) =>
    request<{ executionMode: ExecutionMode }>('/api/config/execution-mode', {
      method: 'POST', body: JSON.stringify({ executionMode }),
    }),
  updateColabUrl: (tunnelUrl: string) =>
    request<{ tunnelUrl: string }>('/api/config/colab-url', {
      method: 'POST', body: JSON.stringify({ tunnelUrl }),
    }),
  getHealth: () => request<HealthResponse>('/api/health'),
  listModels: () => request<ModelDefinition[]>('/api/models'),
  switchModel: (modelId: string) =>
    request<Record<string, unknown>>('/api/models/switch', {
      method: 'POST', body: JSON.stringify({ modelId }),
    }),
  listGenerations: (filters?: { projectId?: string; favorite?: boolean; isFavorite?: boolean; mediaType?: string; q?: string; search?: string }) => {
    const params = new URLSearchParams();
    if (filters?.projectId) params.set('projectId', filters.projectId);
    const fav = filters?.favorite !== undefined ? filters.favorite : filters?.isFavorite;
    if (fav !== undefined) params.set('favorite', String(fav));
    if (filters?.mediaType) params.set('mediaType', filters.mediaType);
    const queryStr = filters?.q || filters?.search;
    if (queryStr) params.set('q', queryStr);
    const query = params.toString();
    return request<Generation[]>(query ? `/api/generations?${query}` : '/api/generations');
  },
  getGeneration: (id: string) => request<Generation>(`/api/generations/${id}`),
  submitGeneration: (req: GenerationSubmitRequest) =>
    request<GenerationSubmitResponse>('/api/generate/media', { method: 'POST', body: JSON.stringify(req) }),
  toggleFavorite: (id: string) =>
    request<{ id: string; isFavorite: boolean }>(`/api/generations/${id}/favorite`, { method: 'PATCH' }),
  deleteGeneration: (id: string) =>
    request<{ status: string; id: string }>(`/api/generations/${id}`, { method: 'DELETE' }),
  cancelTask: (taskId: string) =>
    request<{ status: string; taskId: string }>(`/api/tasks/${taskId}/cancel`, { method: 'POST' }),
  subscribeTaskStatus(taskId: string, onEvent: (event: TaskStatusEvent) => void, onError?: (err: unknown) => void): () => void {
    const es = new EventSource(`/api/tasks/${taskId}/status`);
    const handleEvent = (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data) as Record<string, unknown>;
        onEvent({ taskId: (data.taskId as string) || taskId, ...data } as TaskStatusEvent);
      } catch (err) { onError?.(err); }
    };
    ['pending', 'running', 'completed', 'failed', 'cancelled'].forEach((name) => {
      es.addEventListener(name, handleEvent as EventListener);
    });
    es.onmessage = handleEvent as (e: MessageEvent) => void;
    if (onError) es.onerror = (err) => onError(err);
    return () => es.close();
  },
  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (p: { name: string; description?: string; colorTag?: string; storagePath?: string }) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(p) }),
  deleteProject: (id: string) => request<{ status: string; id: string }>(`/api/projects/${id}`, { method: 'DELETE' }),
  listBrandKits: () => request<BrandKit[]>('/api/brand-kits'),
  createBrandKit: async (data: {
    source: 'blank' | 'website' | 'files';
    name: string;
    overview?: string;
    url?: string;
    files?: File[];
  }): Promise<BrandKit> => {
    const formData = new FormData();
    formData.append('source', data.source);
    formData.append('name', data.name);
    if (data.overview) formData.append('overview', data.overview);
    if (data.url) {
      formData.append('url', data.url);
      formData.append('websiteUrl', data.url);
    }
    if (data.files) {
      data.files.forEach((f) => formData.append('files', f));
    }
    const response = await fetch('/api/brand-kits', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      let detail = `Erreur HTTP ${response.status}`;
      try {
        const errJson = (await response.json()) as { detail?: string };
        if (errJson?.detail) detail = errJson.detail;
      } catch { /* ignore non-json error */ }
      throw new ApiError(detail, response.status);
    }
    return (await response.json()) as BrandKit;
  },
  streamChatCompletion: async (
    requestData: {
      model: string;
      messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>;
      temperature?: number;
      stream?: boolean;
    },
    onChunk: (chunk: string) => void,
    signal?: AbortSignal
  ): Promise<string> => {
    const response = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...requestData, stream: true }),
      signal,
    });
    if (!response.ok) {
      let detail = `Erreur HTTP ${response.status}`;
      try {
        const errJson = (await response.json()) as { detail?: string };
        if (errJson?.detail) detail = errJson.detail;
      } catch { /* ignore non-json error */ }
      throw new ApiError(detail, response.status);
    }
    const reader = response.body?.getReader();
    if (!reader) throw new ApiError('No response body available to stream', 500);
    const decoder = new TextDecoder();
    let fullText = '';
    let buffer = '';

    let isDone = false;
    while (!isDone) {
      const { done, value } = await reader.read();
      if (done) {
        isDone = true;
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue;
        if (trimmed === 'data: [DONE]') continue;
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            const delta = data.choices?.[0]?.delta?.content || '';
            if (delta) {
              fullText += delta;
              onChunk(delta);
            }
          } catch {
            // Ignore non-json or malformed SSE line
          }
        }
      }
    }
    return fullText;
  },
};
