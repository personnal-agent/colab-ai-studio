import { ExecutionMode, HealthResponse, Project } from '../../types/studio';
import { AskHelpDrawer } from './AskHelpDrawer';
import { FavoriteFilterToggle } from './FavoriteFilterToggle';
import { NotificationsPopover } from './NotificationsPopover';
import { ProjectsDrawer } from './ProjectsDrawer';
import { WorkerStatusAvatar } from './WorkerStatusAvatar';

interface TopNavBarProps {
  isFavoriteOnly: boolean;
  onToggleFavoriteFilter: (active: boolean) => void;
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string | null) => void;
  onCreateProject: (payload: {
    name: string;
    description?: string;
    storagePath?: string;
  }) => Promise<Project>;
  executionMode: ExecutionMode;
  health: HealthResponse | null;
  onModeChange: (newMode: ExecutionMode) => void;
}

export function TopNavBar({
  isFavoriteOnly,
  onToggleFavoriteFilter,
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  executionMode,
  health,
  onModeChange,
}: TopNavBarProps) {
  return (
    <header className="sticky top-0 z-40 h-16 bg-studio-card border-b border-studio-border px-6 flex items-center justify-between shadow-card">
      {/* Bloc gauche : Favoris & Titre */}
      <div className="flex items-center gap-3">
        <FavoriteFilterToggle
          isFavoriteOnly={isFavoriteOnly}
          onToggle={onToggleFavoriteFilter}
        />
        <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
          Image & Video
        </h1>
      </div>

      {/* Bloc droit : Ask, Projets, Notifications, Avatar Worker */}
      <div className="flex items-center gap-3">
        <AskHelpDrawer />
        <div className="h-5 w-px bg-studio-divider" />
        <ProjectsDrawer
          projects={projects}
          activeProjectId={activeProjectId}
          onSelectProject={onSelectProject}
          onCreateProject={onCreateProject}
        />
        <NotificationsPopover />
        <WorkerStatusAvatar
          health={health}
          executionMode={executionMode}
          onModeChange={onModeChange}
        />
      </div>
    </header>
  );
}
