import React, { useState } from 'react';
import { MediaGallery } from './components/gallery/MediaGallery';
import { MediaPlayerModal } from './components/gallery/MediaPlayerModal';
import { TopNavBar } from './components/header/TopNavBar';
import type { Generation } from './types/studio';

export default function App(): React.ReactElement {
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [selectedGeneration, setSelectedGeneration] = useState<Generation | null>(null);

  const handleRemix = (gen: Generation) => {
    // Le dock flottant (Plan 04) sera abonné à cet événement de remix
    console.info('Remix generation:', gen.id, gen.prompt);
    setSelectedGeneration(null);
  };

  const handleFavoriteToggled = (updated: Generation) => {
    if (selectedGeneration && selectedGeneration.id === updated.id) {
      setSelectedGeneration(updated);
    }
  };

  return (
    <div className="min-h-screen bg-studio-canvas text-gray-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Barre supérieure unifiée */}
      <TopNavBar
        favoritesOnly={favoritesOnly}
        onToggleFavorites={() => setFavoritesOnly((prev) => !prev)}
        activeProjectId={activeProjectId}
        onSelectProject={setActiveProjectId}
      />

      {/* Contenu principal : Galerie & Recherche */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 className="sr-only">Colab AI Studio</h1>
        <MediaGallery
          favoritesOnly={favoritesOnly}
          activeProjectId={activeProjectId}
          onSelectGeneration={setSelectedGeneration}
        />
      </main>

      {/* Modale d'inspection grand format */}
      <MediaPlayerModal
        generation={selectedGeneration}
        isOpen={Boolean(selectedGeneration)}
        onClose={() => setSelectedGeneration(null)}
        onRemix={handleRemix}
        onFavoriteToggled={handleFavoriteToggled}
      />
    </div>
  );
}
