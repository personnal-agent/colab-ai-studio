export type AppMode = 'Studio' | 'Agents';

export interface ElectronAPI {
  switchMode: (mode: AppMode) => Promise<void>;
  getAppMode: () => Promise<AppMode>;
  onModeChanged: (callback: (mode: AppMode) => void) => () => void;
  getSystemStatus: () => Promise<{ fastapi: boolean; port: number }>;
  platform: string;
}

declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}
