import { useEffect, useMemo, useState } from 'react';
import { MediaGallery } from './components/gallery/MediaGallery';
import { MediaPlayerModal } from './components/gallery/MediaPlayerModal';
import { SearchAndFilterBar } from './components/gallery/SearchAndFilterBar';
import { TopNavBar } from './components/header/TopNavBar';
import { apiClient } from './services/apiClient';
import { ExecutionMode, Generation, HealthResponse, Project } from './types/studio';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('local');
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  const [generations, setGenerations] = useState<Generation[]>([]);
  const [activeTasks, setActiveTasks] = useState<Generation[]>([]);

  const [isFavoriteOnly, setIsFavoriteOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);

  const [selectedGeneration, setSelectedGeneration] = useState<Generation | null>(null);

  // 1. Initialisation des données au montage
  useEffect(() => {
    const initData = async () => {
      try {
        const [healthRes, configRes, projectsRes, gensRes] = await Promise.all([
          apiClient.getHealth().catch(() => null),
          apiClient.getConfig().catch(() => null),
          apiClient.listProjects().catch(() => []),
          apiClient.listGenerations().catch(() => []),
        ]);

        if (healthRes) {
          setHealth(healthRes);
          setExecutionMode(healthRes.executionMode);
        } else if (configRes) {
          setExecutionMode(configRes.executionMode);
        }

        setProjects(projectsRes);

        const active = gensRes.filter(
          (g) => g.status === 'pending' || g.status === 'running'
        );
        const completed = gensRes.filter(
          (g) => g.status !== 'pending' && g.status !== 'running'
        );
        setActiveTasks(active);
        setGenerations(completed);
      } catch (err) {
        console.error('Erreur lors du chargement initial du Studio', err);
      }
    };

    initData();
  }, []);

  // 2. Gestionnaire de création de projet
  const handleCreateProject = async (payload: {
    name: string;
    description?: string;
    storagePath?: string;
  }): Promise<Project> => {
    const created = await apiClient.createProject(payload);
    setProjects((prev) => [created, ...prev]);
    setActiveProjectId(created.id);
    return created;
  };

  // 3. Basculement Favori
  const handleToggleFavorite = async (id: string) => {
    try {
      const updated = await apiClient.toggleFavorite(id);
      setGenerations((prev) =>
        prev.map((g) => (g.id === id ? { ...g, isFavorite: updated.isFavorite } : g))
      );
      if (selectedGeneration?.id === id) {
        setSelectedGeneration((prev) =>
          prev ? { ...prev, isFavorite: updated.isFavorite } : null
        );
      }
    } catch (err) {
      console.error('Erreur bascule favori', err);
    }
  };

  // 4. Suppression
  const handleDeleteGeneration = async (id: string) => {
    try {
      await apiClient.deleteGeneration(id);
      setGenerations((prev) => prev.filter((g) => g.id !== id));
      if (selectedGeneration?.id === id) {
        setSelectedGeneration(null);
      }
    } catch (err) {
      console.error('Erreur suppression génération', err);
    }
  };

  // 5. Annulation de tâche
  const handleCancelTask = async (taskId: string) => {
    try {
      await apiClient.cancelTask(taskId);
      setActiveTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch (err) {
      console.error('Erreur annulation tâche', err);
    }
  };

  // 6. Action Remix
  const handleRemix = (gen: Generation) => {
    console.info('Remix invoqué pour', gen.id);
    // Invoqué vers le dock flottant (Plan 04)
  };

  // 7. Filtrage cumulatif des médias
  const filteredGenerations = useMemo(() => {
    return generations.filter((gen) => {
      // Filtre projet actif
      if (activeProjectId && gen.projectId !== activeProjectId) {
        return false;
      }

      // Filtre favoris
      if (isFavoriteOnly && !gen.isFavorite) {
        return false;
      }

      // Filtre puces de type (cumulatif)
      if (selectedTypes.length > 0 && !selectedTypes.includes(gen.mediaType)) {
        return false;
      }

      // Filtre recherche textuelle
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchPrompt = gen.prompt.toLowerCase().includes(q);
        const matchModel = (gen.modelName || gen.modelId).toLowerCase().includes(q);
        if (!matchPrompt && !matchModel) {
          return false;
        }
      }

      return true;
    });
  }, [generations, activeProjectId, isFavoriteOnly, selectedTypes, searchQuery]);

  return (
    <div className="min-h-screen bg-studio-canvas text-gray-900 flex flex-col font-sans">
      {/* Barre supérieure avec Favoris, Projets, Ask & Statut Worker */}
      <TopNavBar
        isFavoriteOnly={isFavoriteOnly}
        onToggleFavoriteFilter={setIsFavoriteOnly}
        projects={projects}
        activeProjectId={activeProjectId}
        onSelectProject={setActiveProjectId}
        onCreateProject={handleCreateProject}
        executionMode={executionMode}
        health={health}
        onModeChange={(newMode) => {
          setExecutionMode(newMode);
          if (health) {
            setHealth({ ...health, executionMode: newMode });
          }
        }}
      />

      {/* Corps principal : Barre de recherche + Galerie multimédia */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-4 flex flex-col gap-4">
        <SearchAndFilterBar
          searchQuery={searchQuery}
          selectedTypes={selectedTypes}
          onSearchChange={setSearchQuery}
          onFilterChange={setSelectedTypes}
        />

        <MediaGallery
          activeTasks={activeTasks}
          generations={filteredGenerations}
          onSelectGeneration={setSelectedGeneration}
          onToggleFavorite={handleToggleFavorite}
          onCancelTask={handleCancelTask}
        />
      </main>

      {/* Modale d'inspection grand format & Remix */}
      <MediaPlayerModal
        generation={selectedGeneration}
        isOpen={Boolean(selectedGeneration)}
        onClose={() => setSelectedGeneration(null)}
        onToggleFavorite={handleToggleFavorite}
        onRemix={handleRemix}
        onDelete={handleDeleteGeneration}
      />
    </div>
  );
}
