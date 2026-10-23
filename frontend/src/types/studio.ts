/**
 * Contrats TypeScript du domaine Colab AI Studio (frontend/src/types/studio.ts).
 * Miroir exact des schémas Pydantic du backend (app/models/domain.py).
 */

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type ExecutionMode = 'colab' | 'local';

export type MediaType = 'image' | 'video' | 'audio' | 'lip_sync' | 'upscale';

export interface GenerationParameters {
  seed: number;
  aspectRatio: string;
  resolution: string;
  duration: string;
  frameRate?: string | null;
  audio?: boolean | null;
  enhance?: boolean | null;
}

export interface GenerationReferences {
  startFrame?: string | null;
  endFrame?: string | null;
  imageRefs?: string[];
  videoRefs?: string[];
  audioRef?: string | null;
  brandKitId?: string | null;
}

export interface BrandColor {
  hex: string;
  name: string;
  role?: string | null;
}

export interface BrandKitSnapshot {
  id: string;
  name: string;
  logoUrl?: string | null;
  primaryColor?: string | null;
}

export interface BrandKit {
  id: string;
  name: string;
  overview: string;
  palette: BrandColor[];
  fonts: string[];
  dos: string[];
  donts: string[];
  logoPath?: string | null;
  referenceImages: string[];
  updatedAt: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  colorTag?: string | null;
  storagePath?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Generation {
  id: string;
  status: TaskStatus;
  mediaType: string;
  prompt: string;
  negativePrompt?: string | null;
  compiledPrompt?: string | null;
  modelId: string;
  modelName: string;
  parameters: GenerationParameters;
  references: GenerationReferences;
  brandKitSnapshot?: BrandKitSnapshot | null;
  filePath?: string | null;
  thumbnailPath?: string | null;
  isFavorite: boolean;
  progress: number;
  errorMessage?: string | null;
  projectId?: string | null;
  createdAt: string;
  completedAt?: string | null;
}

export interface ModelCapabilities {
  aspectRatios?: string[];
  resolutions?: string[];
  durations?: string[];
  fpsOptions?: string[];
  supportsAudio?: boolean;
  supportsNegativePrompt?: boolean;
  supportsStartEndFrames?: boolean;
  maxImageRefs?: number;
}

export interface ModelDefinition {
  id: string;
  name: string;
  mediaType: string;
  description?: string;
  capabilities?: ModelCapabilities;
}

export interface ColabConfig {
  tunnelUrl: string;
  accountEmail?: string | null;
  lastPing?: string | null;
}

export interface LocalConfig {
  device: string;
  threads: number;
  workerUrl: string;
}

export interface CompilerLlmConfig {
  provider: string;
  model: string;
  apiKeyEnv: string;
  apiKey?: string | null;
}

export interface LlmProxyConfig {
  enabled: boolean;
  host: string;
  port: number;
  timeout: number;
}

export interface StudioConfig {
  executionMode: ExecutionMode;
  colab: ColabConfig;
  local: LocalConfig;
  compilerLlm: CompilerLlmConfig;
  defaultStoragePath: string;
  llmProxy: LlmProxyConfig;
}

export interface WorkerDiagnostic {
  reachable: boolean;
  executionMode: string;
  latencyMs?: number;
  gpu?: string | null;
  vramFreeMb?: number | null;
  workerStatus?: string;
  error?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  executionMode: ExecutionMode;
  activeWorkerReachable: boolean;
  worker?: WorkerDiagnostic;
}

export interface TaskProgressEvent {
  taskId: string;
  status: TaskStatus;
  progress: number;
  filePath?: string | null;
  error?: string | null;
}
