import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { User, Plus, Trash2, X, Upload, Sparkles, Check, Mic } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { Character } from '../../types/studio';

export interface CharactersModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCharacterToken?: (token: string) => void;
}

export const CharactersModal: React.FC<CharactersModalProps> = ({
  isOpen,
  onClose,
  onSelectCharacterToken,
}) => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPhysicalPrompt, setNewPhysicalPrompt] = useState('');
  const [newVoiceStyle, setNewVoiceStyle] = useState('feminine_soft');
  const [uploadedImage, setUploadedImage] = useState<{ path: string; url: string } | null>(null);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const fetchCharacters = async () => {
    setLoading(true);
    try {
      const list = await apiClient.listCharacters();
      setCharacters(list);
    } catch (err) {
      console.error('Failed to load characters:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCharacters();
      setIsCreating(false);
    }
  }, [isOpen]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await apiClient.uploadFile(file);
      setUploadedImage({ path: res.filePath, url: res.url });
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newPhysicalPrompt.trim()) return;

    try {
      await apiClient.createCharacter({
        name: newName.trim(),
        physicalPrompt: newPhysicalPrompt.trim(),
        referenceImagePath: uploadedImage?.path || null,
        voiceStyle: newVoiceStyle,
      });
      setNewName('');
      setNewPhysicalPrompt('');
      setUploadedImage(null);
      setIsCreating(false);
      fetchCharacters();
    } catch (err) {
      console.error('Failed to create character:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Supprimer cette fiche personnage ?')) return;
    try {
      await apiClient.deleteCharacter(id);
      setCharacters((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Failed to delete character:', err);
    }
  };

  const handleInsertToken = (token: string) => {
    onSelectCharacterToken?.(token);
    setCopiedToken(token);
    setTimeout(() => {
      setCopiedToken(null);
      onClose();
    }, 400);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl max-h-[85vh] z-50 bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-800 p-6 flex flex-col overflow-hidden outline-none">
          <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <User className="w-4 h-4" />
              </div>
              <div>
                <Dialog.Title className="text-sm font-bold text-gray-900 dark:text-white">
                  Fiches Personnages & Acteurs (@Nom)
                </Dialog.Title>
                <Dialog.Description className="text-xs text-gray-500 dark:text-gray-400">
                  Identité visuelle, description physique et voix persistantes d'une vidéo à l'autre
                </Dialog.Description>
              </div>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Fermer"
                className="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {!isCreating && (
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">
                  {characters.length} personnage(s) enregistré(s)
                </span>
                <button
                  type="button"
                  onClick={() => setIsCreating(true)}
                  className="px-3 py-1.5 rounded-full text-xs font-semibold bg-black text-white dark:bg-white dark:text-black hover:opacity-90 flex items-center space-x-1 transition-all shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Nouveau personnage</span>
                </button>
              </div>
            )}

            {isCreating && (
              <form onSubmit={handleCreateCharacter} className="bg-gray-50 dark:bg-gray-800/40 p-4 rounded-2xl border border-gray-200 dark:border-gray-700 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                    Créer un personnage récurrent
                  </span>
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="text-xs text-gray-500 hover:underline"
                  >
                    Annuler
                  </button>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-gray-700 dark:text-gray-300 block mb-1">
                    Nom du Personnage (ex: Tomate, Clara, John)
                  </label>
                  <input
                    type="text"
                    required
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Tomate"
                    className="w-full text-xs px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-gray-700 dark:text-gray-300 block mb-1">
                    Description physique immuable (Injectée automatiquement dès que @Nom est écrit)
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={newPhysicalPrompt}
                    onChange={(e) => setNewPhysicalPrompt(e.target.value)}
                    placeholder="Anthropomorphic ripe red tomato character, glossy expressive eyes, fine organic skin pores, wearing worn canvas apron with rusted buttons..."
                    className="w-full text-xs px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-semibold text-gray-700 dark:text-gray-300 block mb-1 flex items-center gap-1">
                      <Mic className="w-3 h-3 text-indigo-500" />
                      Profil vocal (Audio Weaver)
                    </label>
                    <select
                      value={newVoiceStyle}
                      onChange={(e) => setNewVoiceStyle(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                    >
                      <option value="feminine_soft">Féminine douce</option>
                      <option value="whisper_intimate">Murmure intime</option>
                      <option value="masculine_deep">Masculine grave</option>
                      <option value="energetic">Énergique / TikTok</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-gray-700 dark:text-gray-300 block mb-1 flex items-center gap-1">
                      <Upload className="w-3 h-3 text-indigo-500" />
                      Image de référence (visage/corps)
                    </label>
                    <label className="flex items-center justify-center px-3 py-1.5 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 text-xs text-gray-600 dark:text-gray-300">
                      <span>{uploadedImage ? '✓ Réf chargée' : 'Choisir une photo...'}</span>
                      <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors mt-2"
                >
                  Enregistrer la fiche personnage
                </button>
              </form>
            )}

            {loading ? (
              <div className="py-8 text-center text-xs text-gray-400">Chargement des personnages...</div>
            ) : characters.length === 0 && !isCreating ? (
              <div className="py-8 text-center space-y-2">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Aucun personnage enregistré. Créez votre première fiche pour maintenir une identité stricte sur vos séries TikTok ou modèles.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {characters.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex flex-col justify-between hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors shadow-xs"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-xs text-gray-900 dark:text-white flex items-center gap-1">
                          <span className="text-indigo-600 dark:text-indigo-400 font-mono">{c.triggerToken}</span>
                          <span className="text-gray-400 font-normal">({c.name})</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => handleDelete(c.id)}
                          className="text-gray-400 hover:text-rose-600 p-1 rounded-full transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <p className="text-[11px] text-gray-600 dark:text-gray-300 line-clamp-2 leading-relaxed">
                        {c.physicalPrompt}
                      </p>
                    </div>

                    <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
                      <span className="text-[10px] text-gray-400 uppercase font-mono">{c.voiceStyle || 'voix douce'}</span>
                      <button
                        type="button"
                        onClick={() => handleInsertToken(c.triggerToken)}
                        className="px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-[11px] font-semibold flex items-center space-x-1 transition-colors"
                      >
                        {copiedToken === c.triggerToken ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span>Inséré !</span>
                          </>
                        ) : (
                          <>
                            <Plus className="w-3 h-3" />
                            <span>Insérer dans prompt</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
