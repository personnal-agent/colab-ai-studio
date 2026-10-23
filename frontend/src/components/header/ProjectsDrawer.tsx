import * as Dialog from '@radix-ui/react-dialog';
import { Check, Folder, FolderPlus, Plus, X } from 'lucide-react';
import React, { useState } from 'react';
import { Project } from '../../types/studio';

interface ProjectsDrawerProps {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string | null) => void;
  onCreateProject: (payload: {
    name: string;
    description?: string;
    storagePath?: string;
  }) => Promise<Project>;
}

export function ProjectsDrawer({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
}: ProjectsDrawerProps) {
  const [open, setOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [storagePath, setStoragePath] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Le nom du projet est obligatoire');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreateProject({
        name: name.trim(),
        description: description.trim() || undefined,
        storagePath: storagePath.trim() || undefined,
      });
      setName('');
      setDescription('');
      setStoragePath('');
      setIsCreating(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création du projet');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeProject = projects.find((p) => p.id === activeProjectId);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label="Projets"
          className="p-2 rounded-slot text-gray-600 hover:text-gray-900 hover:bg-studio-subtle transition-colors flex items-center gap-1.5"
          title={activeProject ? `Projet actif : ${activeProject.name}` : 'Gérer les projets'}
        >
          <Folder className="w-5 h-5" />
          {activeProject && (
            <span className="text-xs font-medium max-w-[100px] truncate text-gray-800">
              {activeProject.name}
            </span>
          )}
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-in fade-in" />
        <Dialog.Content className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right">
          <div>
            <div className="flex items-center justify-between border-b border-studio-border pb-4">
              <div className="flex items-center gap-2">
                <Folder className="w-5 h-5 text-gray-700" />
                <Dialog.Title className="text-lg font-semibold text-gray-900">
                  Dossiers & Projets
                </Dialog.Title>
              </div>
              <Dialog.Close asChild>
                <button
                  type="button"
                  aria-label="Fermer"
                  className="p-1 rounded-slot hover:bg-studio-subtle text-gray-500"
                >
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>

            {/* Liste des projets */}
            <div className="mt-6 space-y-2">
              <button
                type="button"
                onClick={() => {
                  onSelectProject(null);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-2.5 rounded-slot text-sm flex items-center justify-between transition-colors ${
                  activeProjectId === null
                    ? 'bg-studio-subtle font-medium text-gray-900'
                    : 'text-gray-600 hover:bg-studio-canvas'
                }`}
              >
                <span>Tous les médias (hors projet)</span>
                {activeProjectId === null && <Check className="w-4 h-4 text-gray-700" />}
              </button>

              {projects.map((proj) => (
                <button
                  key={proj.id}
                  type="button"
                  onClick={() => {
                    onSelectProject(proj.id);
                    setOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-slot text-sm flex items-center justify-between transition-colors border ${
                    activeProjectId === proj.id
                      ? 'bg-studio-subtle border-studio-border font-medium text-gray-900'
                      : 'border-transparent text-gray-700 hover:bg-studio-canvas'
                  }`}
                >
                  <div>
                    <div className="font-medium">{proj.name}</div>
                    {proj.storagePath && (
                      <div className="text-xs text-gray-400 truncate max-w-[280px]">
                        📁 {proj.storagePath}
                      </div>
                    )}
                  </div>
                  {activeProjectId === proj.id && <Check className="w-4 h-4 text-gray-700" />}
                </button>
              ))}
            </div>

            {/* Formulaire de création */}
            <div className="mt-6 pt-6 border-t border-studio-border">
              {!isCreating ? (
                <button
                  type="button"
                  onClick={() => setIsCreating(true)}
                  className="w-full py-2 px-3 border border-dashed border-gray-300 rounded-slot text-sm font-medium text-gray-700 hover:border-gray-400 hover:bg-studio-canvas flex items-center justify-center gap-2 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>Nouveau projet</span>
                </button>
              ) : (
                <form onSubmit={handleCreate} className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
                    <FolderPlus className="w-4 h-4" />
                    <span>Créer un nouveau projet</span>
                  </h4>

                  {error && <div className="text-xs text-red-600 bg-red-50 p-2 rounded">{error}</div>}

                  <div>
                    <input
                      type="text"
                      placeholder="Nom du projet *"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-slot focus:outline-none focus:ring-1 focus:ring-gray-800"
                      required
                    />
                  </div>

                  <div>
                    <input
                      type="text"
                      placeholder="Description (optionnelle)"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-slot focus:outline-none focus:ring-1 focus:ring-gray-800"
                    />
                  </div>

                  <div>
                    <input
                      type="text"
                      placeholder="Chemin de stockage personnalisé (optionnel)"
                      value={storagePath}
                      onChange={(e) => setStoragePath(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-slot focus:outline-none focus:ring-1 focus:ring-gray-800 font-mono text-xs"
                    />
                    <p className="text-[11px] text-gray-400 mt-1">
                      Les rendus seront enregistrés directement dans ce répertoire sans duplication.
                    </p>
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-1 py-1.5 px-3 bg-gray-900 text-white rounded-slot text-xs font-medium hover:bg-black transition-colors disabled:opacity-50"
                    >
                      {isSubmitting ? 'Création...' : 'Créer le projet'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsCreating(false)}
                      className="py-1.5 px-3 bg-studio-subtle text-gray-700 rounded-slot text-xs font-medium hover:bg-studio-active transition-colors"
                    >
                      Annuler
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>

          <div className="border-t border-studio-border pt-4 text-xs text-gray-400">
            Partitionnement automatique des rendus
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
