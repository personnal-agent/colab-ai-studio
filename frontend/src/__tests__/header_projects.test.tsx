import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AskHelpDrawer } from '../components/header/AskHelpDrawer';
import { FavoriteFilterToggle } from '../components/header/FavoriteFilterToggle';
import { NotificationsPopover } from '../components/header/NotificationsPopover';
import { ProjectsDrawer } from '../components/header/ProjectsDrawer';
import { TopNavBar } from '../components/header/TopNavBar';
import { WorkerStatusAvatar } from '../components/header/WorkerStatusAvatar';
import { apiClient } from '../services/apiClient';
import type { HealthResponse, Project, StudioConfig } from '../types/studio';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    getConfig: vi.fn(), switchExecutionMode: vi.fn(), updateColabUrl: vi.fn(),
    getHealth: vi.fn(), listProjects: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn(),
  },
}));

describe('TopNavBar and Header Components', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  describe('FavoriteFilterToggle', () => {
    it('renders favorite toggle button and title', () => {
      const onToggle = vi.fn();
      render(<FavoriteFilterToggle active={false} onToggle={onToggle} />);
      expect(screen.getByText('Image & Video')).toBeInTheDocument();
      const btn = screen.getByRole('button', { name: /favoris/i });
      fireEvent.click(btn);
      expect(onToggle).toHaveBeenCalledTimes(1);
    });

    it('displays active state with filled star styling', () => {
      render(<FavoriteFilterToggle active={true} onToggle={() => {}} />);
      expect(screen.getByRole('button', { name: /favoris/i })).toHaveClass('text-amber-500');
    });
  });

  describe('AskHelpDrawer', () => {
    it('opens help modal when clicked', async () => {
      render(<AskHelpDrawer />);
      fireEvent.click(screen.getByRole('button', { name: /ask/i }));
      await waitFor(() => {
        expect(screen.getByText(/Centre d'aide & Documentation/i)).toBeInTheDocument();
      });
      expect(screen.getByText(/Foire Aux Questions/i)).toBeInTheDocument();
      expect(screen.getByText(/Gestion de la VRAM/i)).toBeInTheDocument();
    });
  });

  describe('ProjectsDrawer', () => {
    const mockProjects: Project[] = [{
      id: 'proj_1', name: 'Campagne Été', description: 'Vidéos de lancement',
      colorTag: '#3B82F6', storagePath: '/mnt/storage/ete', createdAt: '2026-10-24T12:00:00Z', updatedAt: '2026-10-24T12:00:00Z',
    }];

    it('renders project list and allows creating a new project with storagePath', async () => {
      vi.mocked(apiClient.listProjects).mockResolvedValue(mockProjects);
      vi.mocked(apiClient.createProject).mockResolvedValue({
        id: 'proj_2', name: 'Projet Automne', description: 'Teaser',
        colorTag: '', storagePath: '/mnt/storage/automne', createdAt: '2026-10-24T13:00:00Z', updatedAt: '2026-10-24T13:00:00Z',
      });

      render(<ProjectsDrawer activeProjectId={null} onSelectProject={vi.fn()} />);
      fireEvent.click(screen.getByRole('button', { name: /projets/i }));

      await waitFor(() => {
        expect(screen.getByText('Campagne Été')).toBeInTheDocument();
        expect(screen.getByText('/mnt/storage/ete')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText(/Nom du projet/i), { target: { value: 'Projet Automne' } });
      fireEvent.change(screen.getByPlaceholderText(/Chemin de stockage personnalisé/i), { target: { value: '/mnt/storage/automne' } });
      fireEvent.click(screen.getByRole('button', { name: /Créer le projet/i }));

      await waitFor(() => {
        expect(apiClient.createProject).toHaveBeenCalledWith({
          name: 'Projet Automne', description: undefined, colorTag: undefined, storagePath: '/mnt/storage/automne',
        });
      });
    });
  });

  describe('NotificationsPopover', () => {
    it('renders notifications popover with empty state or items', async () => {
      render(<NotificationsPopover notifications={[{ id: 'notif_1', title: 'Tâche terminée', message: 'Génération réussie', time: '12:45' }]} />);
      fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
      await waitFor(() => {
        expect(screen.getByText('Tâche terminée')).toBeInTheDocument();
        expect(screen.getByText('Génération réussie')).toBeInTheDocument();
      });
    });
  });

  describe('WorkerStatusAvatar', () => {
    const colabConfig: Partial<StudioConfig> = {
      executionMode: 'colab',
      colab: { tunnelUrl: 'https://test-tunnel.ngrok-free.app', accountEmail: 'user@gmail.com' },
    };
    const colabHealth: Partial<HealthResponse> = {
      executionMode: 'colab', status: 'healthy',
      worker: { reachable: true, gpu: 'Tesla T4', vramFreeMb: 14200, latencyMs: 38 },
    };

    it('renders Colab active indicator and displays popover with telemetry', async () => {
      vi.mocked(apiClient.getConfig).mockResolvedValue(colabConfig as StudioConfig);
      vi.mocked(apiClient.getHealth).mockResolvedValue(colabHealth as HealthResponse);
      render(<WorkerStatusAvatar />);

      await waitFor(() => { expect(screen.getByRole('button', { name: /statut worker/i })).toBeInTheDocument(); });
      fireEvent.click(screen.getByRole('button', { name: /statut worker/i }));

      await waitFor(() => {
        expect(screen.getByText(/Mode Google Colab/i)).toBeInTheDocument();
        expect(screen.getByText(/Tesla T4/i)).toBeInTheDocument();
        expect(screen.getByText(/14200 Mo libre/i)).toBeInTheDocument();
        expect(screen.getByText(/38 ms/i)).toBeInTheDocument();
      });
    });

    it('renders inert gray circle in local mode with switch option', async () => {
      const localConfig: Partial<StudioConfig> = {
        executionMode: 'local', local: { device: 'cpu', threads: 4, workerUrl: 'http://127.0.0.1:8190' },
      };
      const localHealth: Partial<HealthResponse> = {
        executionMode: 'local', status: 'healthy',
        worker: { reachable: true, gpu: null, vramFreeMb: null, latencyMs: 2 },
      };
      vi.mocked(apiClient.getConfig).mockResolvedValue(localConfig as StudioConfig);
      vi.mocked(apiClient.getHealth).mockResolvedValue(localHealth as HealthResponse);

      render(<WorkerStatusAvatar />);
      await waitFor(() => { expect(screen.getByRole('button', { name: /statut worker/i })).toBeInTheDocument(); });
      fireEvent.click(screen.getByRole('button', { name: /statut worker/i }));
      await waitFor(() => { expect(screen.getByText(/Mode Local/i)).toBeInTheDocument(); });
    });
  });

  describe('TopNavBar', () => {
    it('renders all sections and propagates favorite toggle', async () => {
      vi.mocked(apiClient.getConfig).mockResolvedValue({ executionMode: 'colab' } as StudioConfig);
      vi.mocked(apiClient.getHealth).mockResolvedValue({ worker: { reachable: true } } as HealthResponse);
      render(<TopNavBar favoritesOnly={false} onToggleFavorites={vi.fn()} activeProjectId={null} onSelectProject={() => {}} />);

      await waitFor(() => { expect(screen.getByText('Image & Video')).toBeInTheDocument(); });
      expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /projets/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();
    });
  });
});
