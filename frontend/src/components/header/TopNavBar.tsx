import React from 'react';
import { AskHelpDrawer } from './AskHelpDrawer';
import { FavoriteFilterToggle } from './FavoriteFilterToggle';
import { type NotificationItem, NotificationsPopover } from './NotificationsPopover';
import { ProjectsDrawer } from './ProjectsDrawer';
import { WorkerStatusAvatar } from './WorkerStatusAvatar';
import { AppModeSwitch, type AppMode } from './AppModeSwitch';

interface TopNavBarProps {
  favoritesOnly: boolean;
  onToggleFavorites: () => void;
  activeProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
  notifications?: NotificationItem[];
  appMode?: AppMode;
  onAppModeChange?: (mode: AppMode) => void;
}

export const TopNavBar: React.FC<TopNavBarProps> = ({
  favoritesOnly,
  onToggleFavorites,
  activeProjectId,
  onSelectProject,
  notifications = [],
  appMode = 'Studio',
  onAppModeChange,
}) => {
  return (
    <header className="h-16 px-6 bg-white border-b border-studio-border flex items-center justify-between sticky top-0 z-30">
      {/* Bloc Gauche : Favoris & Titre */}
      <FavoriteFilterToggle active={favoritesOnly} onToggle={onToggleFavorites} />

      {/* Bloc Centre : Commutateur [ Studio | Agents ] */}
      {onAppModeChange && (
        <AppModeSwitch mode={appMode} onChange={onAppModeChange} />
      )}

      {/* Bloc Droit : Outils, Projets, Notifications & Compte */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        <AskHelpDrawer />
        <ProjectsDrawer
          activeProjectId={activeProjectId}
          onSelectProject={onSelectProject}
        />
        <NotificationsPopover notifications={notifications} />
        <WorkerStatusAvatar />
      </div>
    </header>
  );
};
