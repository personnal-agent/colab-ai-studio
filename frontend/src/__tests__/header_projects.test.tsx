import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { FavoriteFilterToggle } from '../components/header/FavoriteFilterToggle';
import { ProjectsDrawer } from '../components/header/ProjectsDrawer';
import { TopNavBar } from '../components/header/TopNavBar';
import { WorkerStatusAvatar } from '../components/header/WorkerStatusAvatar';
import { apiClient } from '../services/apiClient';
import { HealthResponse, Project } from '../types/studio';

describe('Header & Projects Components', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('FavoriteFilterToggle', () => {
    it('toggles favorite state and invokes callback', () => {
      const onToggle = vi.fn();
      render(<FavoriteFilterToggle isFavoriteOnly={false} onToggle={onToggle} />);

      const button = screen.getByRole('button', { name: /favoris/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-pressed', 'false');

      fireEvent.click(button);
      expect(onToggle).toHaveBeenCalledWith(true);
    });
  });

  describe('WorkerStatusAvatar', () => {
    const mockHealthLocal: HealthResponse = {
      status: 'ok',
      service: 'Colab AI Studio Control Tower',
      version: '1.0.0',
      executionMode: 'local',
      activeWorkerReachable: true,
      worker: {
        reachable: true,
        executionMode: 'local',
        latencyMs: 1.5,
        gpu: 'NVIDIA RTX 5000 Ada',
        vramFreeMb: 14000,
        workerStatus: 'ok',
      },
    };

    it('renders local status with neutral dot and switches to colab', async () => {
      vi.spyOn(apiClient, 'switchExecutionMode').mockResolvedValue({
        switched: true,
        executionMode: 'colab',
      });
      const onModeChange = vi.fn();

      render(
        <WorkerStatusAvatar
          health={mockHealthLocal}
          executionMode="local"
          onModeChange={onModeChange}
        />
      );

      const avatarBtn = screen.getByRole('button', { name: /statut du worker/i });
      expect(avatarBtn).toBeInTheDocument();

      fireEvent.click(avatarBtn);
      expect(screen.getByText(/Mode d'exécution : Local/i)).toBeInTheDocument();

      const switchBtn = screen.getByRole('button', { name: /basculer vers colab/i });
      fireEvent.click(switchBtn);

      await waitFor(() => {
        expect(apiClient.switchExecutionMode).toHaveBeenCalledWith('colab');
        expect(onModeChange).toHaveBeenCalledWith('colab');
      });
    });
  });

  describe('ProjectsDrawer', () => {
    const mockProjects: Project[] = [
      {
        id: 'proj_1',
        name: 'Campagne Automne',
        description: 'Vidéos de saison',
        storagePath: '/mnt/c/Videos/Automne',
        createdAt: '2026-10-01T10:00:00Z',
        updatedAt: '2026-10-01T10:00:00Z',
      },
    ];

    it('lists existing projects and allows project selection', () => {
      const onSelectProject = vi.fn();
      render(
        <ProjectsDrawer
          projects={mockProjects}
          activeProjectId={null}
          onSelectProject={onSelectProject}
          onCreateProject={vi.fn()}
        />
      );

      const openBtn = screen.getByRole('button', { name: /projets/i });
      fireEvent.click(openBtn);

      expect(screen.getByText('Campagne Automne')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Campagne Automne'));
      expect(onSelectProject).toHaveBeenCalledWith('proj_1');
    });

    it('creates a new project with optional storagePath', async () => {
      const onCreateProject = vi.fn().mockResolvedValue({
        id: 'proj_new',
        name: 'Projet Test',
        storagePath: '/data/test',
      });

      render(
        <ProjectsDrawer
          projects={mockProjects}
          activeProjectId={null}
          onSelectProject={vi.fn()}
          onCreateProject={onCreateProject}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /projets/i }));
      fireEvent.click(screen.getByRole('button', { name: /nouveau projet/i }));

      const nameInput = screen.getByPlaceholderText(/nom du projet/i);
      const pathInput = screen.getByPlaceholderText(/chemin de stockage personnalisé/i);
      const submitBtn = screen.getByRole('button', { name: /créer le projet/i });

      fireEvent.change(nameInput, { target: { value: 'Projet Test' } });
      fireEvent.change(pathInput, { target: { value: '/data/test' } });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(onCreateProject).toHaveBeenCalledWith({
          name: 'Projet Test',
          storagePath: '/data/test',
        });
      });
    });
  });

  describe('TopNavBar Integration', () => {
    it('renders brand title and all control actions', () => {
      render(
        <TopNavBar
          isFavoriteOnly={false}
          onToggleFavoriteFilter={vi.fn()}
          projects={[]}
          activeProjectId={null}
          onSelectProject={vi.fn()}
          onCreateProject={vi.fn()}
          executionMode="local"
          health={null}
          onModeChange={vi.fn()}
        />
      );

      expect(screen.getByText('Image & Video')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /favoris/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /projets/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /statut du worker/i })).toBeInTheDocument();
    });
  });
});
