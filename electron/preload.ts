import { contextBridge, ipcRenderer } from 'electron';

export type AppMode = 'Studio' | 'Agents';

export interface ElectronAPI {
  switchMode: (mode: AppMode) => Promise<void>;
  getAppMode: () => Promise<AppMode>;
  onModeChanged: (callback: (mode: AppMode) => void) => () => void;
  getSystemStatus: () => Promise<{ fastapi: boolean; port: number }>;
  platform: string;
}

const electronAPI: ElectronAPI = {
  switchMode: (mode: AppMode) => ipcRenderer.invoke('switch-mode', mode),
  getAppMode: () => ipcRenderer.invoke('get-app-mode'),
  onModeChanged: (callback: (mode: AppMode) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, mode: AppMode) => callback(mode);
    ipcRenderer.on('mode-changed', handler);
    return () => {
      ipcRenderer.removeListener('mode-changed', handler);
    };
  },
  getSystemStatus: () => ipcRenderer.invoke('get-system-status'),
  platform: process.platform,
};

contextBridge.exposeInMainWorld('electron', electronAPI);
