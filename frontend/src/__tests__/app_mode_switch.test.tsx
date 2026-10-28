import { fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { AppModeSwitch } from '../components/header/AppModeSwitch';
import { TopNavBar } from '../components/header/TopNavBar';
import { apiClient } from '../services/apiClient';
import type { Generation, HealthResponse, StudioConfig } from '../types/studio';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    getConfig: vi.fn(),
    getHealth: vi.fn(),
    listProjects: vi.fn(),
    listGenerations: vi.fn(),
    toggleFavorite: vi.fn(),
    cancelTask: vi.fn(),
    subscribeTaskStatus: vi.fn(),
    listModels: vi.fn(),
    listBrandKits: vi.fn(),
    submitGeneration: vi.fn(),
  },
  getMediaFileUrl: (g: { filePath?: string | null }) => g.filePath || '',
  getMediaThumbnailUrl: (g: { thumbnailPath?: string | null; filePath?: string | null }) =>
    g.thumbnailPath || g.filePath || '',
}));

describe('AppModeSwitch Component', () => {
  it('renders Studio and Agents buttons with correct accessible roles', () => {
    const handleChange = vi.fn();
    render(<AppModeSwitch mode="Studio" onChange={handleChange} />);

    const switchContainer = screen.getByTestId('app-mode-switch');
    expect(switchContainer).toBeInTheDocument();
    expect(switchContainer).toHaveAttribute('role', 'tablist');

    const studioTab = screen.getByTestId('app-mode-studio');
    const agentsTab = screen.getByTestId('app-mode-agents');

    expect(studioTab).toHaveAttribute('aria-selected', 'true');
    expect(agentsTab).toHaveAttribute('aria-selected', 'false');
  });

  it('triggers onChange when clicking on a different mode', () => {
    const handleChange = vi.fn();
    render(<AppModeSwitch mode="Studio" onChange={handleChange} />);

    const agentsTab = screen.getByTestId('app-mode-agents');
    fireEvent.click(agentsTab);

    expect(handleChange).toHaveBeenCalledWith('Agents');
  });

  it('does not trigger onChange when clicking the currently active mode', () => {
    const handleChange = vi.fn();
    render(<AppModeSwitch mode="Studio" onChange={handleChange} />);

    const studioTab = screen.getByTestId('app-mode-studio');
    fireEvent.click(studioTab);

    expect(handleChange).not.toHaveBeenCalled();
  });

  it('calls window.electron.switchMode if available in the Electron environment', () => {
    const mockSwitchMode = vi.fn().mockResolvedValue(undefined);
    window.electron = {
      switchMode: mockSwitchMode,
      getAppMode: vi.fn().mockResolvedValue('Studio'),
      onModeChanged: vi.fn().mockReturnValue(() => {}),
      getSystemStatus: vi.fn().mockResolvedValue({ fastapi: true, port: 8000 }),
      platform: 'linux',
    };

    const handleChange = vi.fn();
    render(<AppModeSwitch mode="Studio" onChange={handleChange} />);

    const agentsTab = screen.getByTestId('app-mode-agents');
    fireEvent.click(agentsTab);

    expect(handleChange).toHaveBeenCalledWith('Agents');
    expect(mockSwitchMode).toHaveBeenCalledWith('Agents');

    delete window.electron;
  });
});

describe('TopNavBar with AppModeSwitch Integration', () => {
  it('renders the mode switcher when onAppModeChange prop is provided', async () => {
    const handleModeChange = vi.fn();
    render(
      <TopNavBar
        favoritesOnly={false}
        onToggleFavorites={vi.fn()}
        appMode="Studio"
        onAppModeChange={handleModeChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('app-mode-switch')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('app-mode-agents'));
    expect(handleModeChange).toHaveBeenCalledWith('Agents');
  });
});

describe('App Multi-View Integration [ Studio | Agents ]', () => {
  const mockGen: Generation = {
    id: 'gen_mode_1',
    status: 'completed',
    mediaType: 'image',
    prompt: 'Concept art of an autonomous agent swarm',
    filePath: '/outputs/agent_swarm.png',
    thumbnailPath: '/outputs/agent_swarm_thumb.png',
    modelId: 'flux-dev',
    modelName: 'FLUX.1 Dev',
    isFavorite: false,
    parameters: { seed: 42, aspectRatio: '16:9', resolution: '720p', duration: '5s' },
    references: {},
    createdAt: '2026-10-28T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    delete window.electron;

    vi.mocked(apiClient.getConfig).mockResolvedValue({
      executionMode: 'colab',
      defaultStoragePath: '/workspace/storage',
      colab: {
        tunnelUrl: 'https://colab-proxy-abc.ngrok.app',
        gpuName: 'NVIDIA A100-SXM4-40GB',
        vramTotalMb: 40960,
        vramUsedMb: 8200,
      },
    } as unknown as StudioConfig);

    vi.mocked(apiClient.getHealth).mockResolvedValue({
      status: 'ok',
      executionMode: 'colab',
      storage: { path: '/workspace/storage', reachable: true, availableBytes: 1000000 },
      worker: {
        reachable: true,
        executionMode: 'colab',
        gpuName: 'NVIDIA A100-SXM4-40GB',
        vramTotalMb: 40960,
        vramUsedMb: 8200,
        latencyMs: 42,
      },
    } as unknown as HealthResponse);

    vi.mocked(apiClient.listProjects).mockResolvedValue([]);
    vi.mocked(apiClient.listModels).mockResolvedValue([]);
    vi.mocked(apiClient.listBrandKits).mockResolvedValue([]);
    vi.mocked(apiClient.listGenerations).mockResolvedValue([mockGen]);
  });

  it('renders Studio view by default and switches to Agents view on click', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Concept art of an autonomous agent swarm')).toBeInTheDocument();
    });

    // En mode Studio, le canevas Agents n'est pas affiché
    expect(screen.queryByTestId('agents-workspace-view')).not.toBeInTheDocument();

    // Clic sur l'onglet Agents
    const agentsTab = screen.getByTestId('app-mode-agents');
    fireEvent.click(agentsTab);

    // En mode Agents, l'espace de travail Agents est affiché et la galerie Studio est masquée
    await waitFor(() => {
      expect(screen.getByTestId('agents-workspace-view')).toBeInTheDocument();
      expect(screen.getByText('CanvasAreaV3 — Espace de Composition Mini Design')).toBeInTheDocument();
      expect(screen.queryByText('Concept art of an autonomous agent swarm')).not.toBeInTheDocument();
    });

    // Rebascule vers Studio
    const studioTab = screen.getByTestId('app-mode-studio');
    fireEvent.click(studioTab);

    await waitFor(() => {
      expect(screen.queryByTestId('agents-workspace-view')).not.toBeInTheDocument();
      expect(screen.getByText('Concept art of an autonomous agent swarm')).toBeInTheDocument();
    });
  });

  it('synchronizes reactive mode changes from Electron IPC events', async () => {
    let modeListener: ((mode: 'Studio' | 'Agents') => void) | null = null;
    window.electron = {
      switchMode: vi.fn().mockResolvedValue(undefined),
      getAppMode: vi.fn().mockResolvedValue('Studio'),
      onModeChanged: vi.fn().mockImplementation((cb) => {
        modeListener = cb;
        return () => {
          modeListener = null;
        };
      }),
      getSystemStatus: vi.fn().mockResolvedValue({ fastapi: true, port: 8000 }),
      platform: 'linux',
    };

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Concept art of an autonomous agent swarm')).toBeInTheDocument();
    });

    // Déclenchement d'un événement externe Electron IPC (ex: raccourci clavier global ou message menu)
    expect(modeListener).not.toBeNull();
    act(() => {
      if (modeListener) {
        modeListener('Agents');
      }
    });

    await waitFor(() => {
      expect(screen.getByTestId('agents-workspace-view')).toBeInTheDocument();
    });
  });
});
