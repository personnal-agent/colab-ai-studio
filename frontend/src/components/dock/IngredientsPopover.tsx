import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Search, X, User, Image as ImageIcon, Video, Mic, Upload, Sparkles,
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { Character, Generation, BrandKit } from '../../types/studio';

export type IngredientTab = 'characters' | 'images' | 'videos' | 'voices' | 'uploads';

export interface IngredientsPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectIngredient: (token: string, metadata?: Record<string, unknown>) => void;
  brandKits?: BrandKit[];
  generations?: Generation[];
  className?: string;
}

export const IngredientsPopover: React.FC<IngredientsPopoverProps> = ({
  isOpen,
  onClose,
  onSelectIngredient,
  brandKits = [],
  generations = [],
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<IngredientTab>('characters');
  const [searchQuery, setSearchQuery] = useState('');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loadingChars, setLoadingChars] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setLoadingChars(true);
      if (apiClient.listCharacters) {
        apiClient.listCharacters()
          .then((chars) => setCharacters(chars))
          .catch((err) => console.error('Failed to load characters for ingredients:', err))
          .finally(() => setLoadingChars(false));
      } else {
        setLoadingChars(false);
      }
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const filteredCharacters = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return characters;
    return characters.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.triggerToken.toLowerCase().includes(q) ||
        (c.archetype && c.archetype.toLowerCase().includes(q)) ||
        (c.visualAnchors && c.visualAnchors.some((a) => a.toLowerCase().includes(q))),
    );
  }, [characters, searchQuery]);

  const filteredImages = useMemo(() => {
    const images = generations.filter((g) => g.mediaType === 'image' && g.status === 'completed');
    const q = searchQuery.toLowerCase().trim();
    if (!q) return images;
    return images.filter((g) => g.prompt.toLowerCase().includes(q));
  }, [generations, searchQuery]);

  const filteredVideos = useMemo(() => {
    const videos = generations.filter((g) => g.mediaType === 'video' && g.status === 'completed');
    const q = searchQuery.toLowerCase().trim();
    if (!q) return videos;
    return videos.filter((g) => g.prompt.toLowerCase().includes(q));
  }, [generations, searchQuery]);

  const voicePresets = useMemo(
    () => [
      { id: 'feminine_soft', name: 'Féminine douce', tone: 'Intime, posée', token: '@Voice(feminine_soft)' },
      { id: 'whisper_intimate', name: 'Murmure ASMR', tone: 'Sensuel, feutré', token: '@Voice(whisper_intimate)' },
      { id: 'masculine_deep', name: 'Masculine grave', tone: 'Baryton, narrateur cinéma', token: '@Voice(masculine_deep)' },
      { id: 'energetic', name: 'Énergique TikTok', tone: 'Rapide, captivant', token: '@Voice(energetic)' },
    ],
    [],
  );

  const filteredVoices = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return voicePresets;
    return voicePresets.filter((v) => v.name.toLowerCase().includes(q) || v.tone.toLowerCase().includes(q));
  }, [voicePresets, searchQuery]);

  const filteredBrandKits = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return brandKits;
    return brandKits.filter((b) => b.name.toLowerCase().includes(q) || b.overview?.toLowerCase().includes(q));
  }, [brandKits, searchQuery]);

  if (!isOpen) return null;

  return (
    <div
      ref={containerRef}
      data-testid="ingredients-popover"
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in ${className}`}
    >
      <div className="w-full max-w-xl max-h-[85vh] bg-[#16171b] text-white rounded-3xl border border-white/10 shadow-2xl flex flex-col overflow-hidden outline-none">
        {/* Header */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold flex items-center gap-2">
                <span>Ingrédients & Actifs Google Flow Pro</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-neutral-300">
                  @ Menu
                </span>
              </div>
              <div className="text-[11px] text-neutral-400">
                Insérez des personnages, images de départ, voix ou brand kits dans votre prompt
              </div>
            </div>
          </div>
          <button
            type="button"
            aria-label="Fermer"
            onClick={onClose}
            className="w-7 h-7 rounded-full flex items-center justify-center text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 5 Tabs */}
        <div className="flex items-center gap-1 px-4 pt-3 border-b border-white/5 overflow-x-auto text-xs scrollbar-none">
          <button
            type="button"
            onClick={() => setActiveTab('characters')}
            className={`pb-2.5 px-3 font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
              activeTab === 'characters'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Personnages ({characters.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('images')}
            className={`pb-2.5 px-3 font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
              activeTab === 'images'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Images ({filteredImages.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('videos')}
            className={`pb-2.5 px-3 font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
              activeTab === 'videos'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Vidéos ({filteredVideos.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('voices')}
            className={`pb-2.5 px-3 font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
              activeTab === 'voices'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Voix ({voicePresets.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('uploads')}
            className={`pb-2.5 px-3 font-semibold border-b-2 flex items-center gap-1.5 transition-colors whitespace-nowrap ${
              activeTab === 'uploads'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Brand Kits ({brandKits.length})</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="px-4 py-3 border-b border-white/5">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-neutral-400 absolute left-3 pointer-events-none" />
            <input
              type="text"
              autoFocus
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Rechercher dans ${activeTab}...`}
              className="w-full pl-9 pr-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {/* CHARACTERS TAB */}
          {activeTab === 'characters' && (
            <div>
              {loadingChars ? (
                <div className="py-8 text-center text-xs text-neutral-400">Chargement des personnages...</div>
              ) : filteredCharacters.length === 0 ? (
                <div className="py-8 text-center text-xs text-neutral-400">
                  Aucun personnage trouvé. Créez-en un dans la modale Personnages.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {filteredCharacters.map((char) => (
                    <button
                      key={char.id}
                      type="button"
                      onClick={() => {
                        onSelectIngredient(char.triggerToken, { characterId: char.id });
                        onClose();
                      }}
                      className="p-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-indigo-500/10 hover:border-indigo-500/40 text-left transition-colors flex items-start gap-2.5 group"
                    >
                      <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-300 font-mono text-xs flex-shrink-0">
                        {char.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold text-indigo-400 group-hover:underline">
                            {char.triggerToken}
                          </span>
                          {char.archetype && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/10 text-neutral-300">
                              {char.archetype}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-white truncate font-medium">{char.name}</div>
                        {char.visualAnchors && char.visualAnchors.length > 0 && (
                          <div className="text-[10px] text-neutral-400 truncate mt-0.5">
                            {char.visualAnchors.join(' • ')}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* IMAGES TAB */}
          {activeTab === 'images' && (
            <div>
              {filteredImages.length === 0 ? (
                <div className="py-8 text-center text-xs text-neutral-400">
                  Aucune image terminée dans la galerie.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {filteredImages.map((img) => (
                    <button
                      key={img.id}
                      type="button"
                      onClick={() => {
                        onSelectIngredient(`[Image:${img.id}]`, { imageId: img.id, filePath: img.filePath });
                        onClose();
                      }}
                      className="relative rounded-xl overflow-hidden border border-white/10 hover:border-indigo-400 group aspect-video bg-black/40 flex flex-col justify-end text-left p-1.5"
                    >
                      {img.filePath && (
                        <img
                          src={img.filePath}
                          alt={img.prompt}
                          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform"
                        />
                      )}
                      <div className="relative z-10 bg-black/70 backdrop-blur-xs p-1 rounded text-[10px] text-white line-clamp-1">
                        {img.prompt}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* VIDEOS TAB */}
          {activeTab === 'videos' && (
            <div>
              {filteredVideos.length === 0 ? (
                <div className="py-8 text-center text-xs text-neutral-400">
                  Aucune vidéo terminée dans la galerie.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {filteredVideos.map((vid) => (
                    <button
                      key={vid.id}
                      type="button"
                      onClick={() => {
                        onSelectIngredient(`[Video:${vid.id}]`, { videoId: vid.id, filePath: vid.filePath });
                        onClose();
                      }}
                      className="relative rounded-xl overflow-hidden border border-white/10 hover:border-indigo-400 group aspect-video bg-black/40 flex flex-col justify-end text-left p-1.5"
                    >
                      {vid.thumbnailPath && (
                        <img
                          src={vid.thumbnailPath}
                          alt={vid.prompt}
                          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform"
                        />
                      )}
                      <div className="relative z-10 bg-black/70 backdrop-blur-xs p-1 rounded text-[10px] text-white line-clamp-1">
                        {vid.prompt}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* VOICES TAB */}
          {activeTab === 'voices' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {filteredVoices.map((voice) => (
                <button
                  key={voice.id}
                  type="button"
                  onClick={() => {
                    onSelectIngredient(voice.token, { voiceId: voice.id });
                    onClose();
                  }}
                  className="p-3 rounded-xl border border-white/10 bg-white/5 hover:bg-indigo-500/10 hover:border-indigo-500/40 text-left transition-colors flex items-center gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
                    <Mic className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">{voice.name}</div>
                    <div className="text-[10px] text-neutral-400">{voice.tone}</div>
                    <div className="text-[9px] font-mono text-indigo-400 mt-0.5">{voice.token}</div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* UPLOADS / BRAND KITS TAB */}
          {activeTab === 'uploads' && (
            <div>
              {filteredBrandKits.length === 0 ? (
                <div className="py-8 text-center text-xs text-neutral-400">
                  Aucun Brand Kit enregistré.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {filteredBrandKits.map((kit) => (
                    <button
                      key={kit.id}
                      type="button"
                      onClick={() => {
                        onSelectIngredient(`[@${kit.name}]`, { brandKitId: kit.id, brandKit: kit });
                        onClose();
                      }}
                      className="p-3 rounded-xl border border-white/10 bg-white/5 hover:bg-indigo-500/10 hover:border-indigo-500/40 text-left transition-colors flex items-start gap-2.5"
                    >
                      <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-300 font-bold text-xs flex-shrink-0">
                        {kit.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-bold text-white truncate">{kit.name}</div>
                        <div className="text-[10px] text-neutral-400 line-clamp-1">{kit.overview || 'Brand assets'}</div>
                        <div className="text-[9px] font-mono text-amber-400 mt-0.5">[@{kit.name}]</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
