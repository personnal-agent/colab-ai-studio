import React, { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Folder, FolderPlus, Trash2, X } from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { Project } from '../../types/studio';

interface ProjectsDrawerProps {
  activeProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
}

export const ProjectsDrawer: React.FC<ProjectsDrawerProps> = ({ activeProjectId, onSelectProject }) => {
  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [storagePath, setStoragePath] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setProjects(await apiClient.listProjects());
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur chargement'); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (open) void loadProjects(); }, [open]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      setCreating(true); setError(null);
      await apiClient.createProject({ name: name.trim(), storagePath: storagePath.trim() || undefined });
      setName(''); setStoragePath('');
      await loadProjects();
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur création'); }
    finally { setCreating(false); }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.deleteProject(id);
      if (activeProjectId === id && onSelectProject) onSelectProject(null);
      await loadProjects();
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur suppression'); }
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button type="button" aria-label="Dossier Projets & Collections" className="h-9 px-3 rounded-full border border-studio-border bg-white text-gray-700 hover:bg-studio-subtle text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm">
          <Folder className="w-4 h-4 text-amber-500" /><span className="hidden sm:inline">Projets</span>
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/45 z-40 backdrop-blur-sm animate-in fade-in" />
        <Dialog.Content className="fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 p-6 shadow-2xl flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-studio-border pb-4">
              <div className="flex items-center gap-2">
                <Folder className="w-5 h-5 text-amber-500" />
                <Dialog.Title className="text-lg font-semibold text-gray-900">Projets & Collections</Dialog.Title>
              </div>
              <Dialog.Close asChild>
                <button type="button" aria-label="Fermer" className="p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-studio-subtle"><X className="w-5 h-5" /></button>
              </Dialog.Close>
            </div>
            {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">{error}</div>}
            <form onSubmit={handleCreate} className="p-4 bg-studio-canvas border border-studio-border rounded-xl space-y-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-800"><FolderPlus className="w-4 h-4 text-indigo-600" /><span>Nouveau projet</span></div>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du projet *" required className="w-full text-xs px-3 py-2 border border-studio-border rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              <input type="text" value={storagePath} onChange={(e) => setStoragePath(e.target.value)} placeholder="Chemin de stockage personnalisé (ex: /mnt/stockage)" className="w-full text-xs px-3 py-2 border border-studio-border rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              <p className="text-[11px] text-gray-500 italic">Règle d'isolation : si un chemin est spécifié, les générations associées y seront stockées exclusivement.</p>
              <button type="submit" disabled={creating || !name.trim()} className="w-full h-8 text-xs font-medium rounded-lg bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50 transition-colors">{creating ? 'Création...' : 'Créer le projet'}</button>
            </form>
            <div className="space-y-2">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Projets existants</h2>
              <button type="button" onClick={() => { onSelectProject?.(null); setOpen(false); }} className={`w-full text-left p-3 rounded-xl border transition-colors flex items-center justify-between ${activeProjectId === null ? 'border-indigo-500 bg-indigo-50/50' : 'border-studio-border bg-white hover:bg-studio-subtle'}`}>
                <div><div className="text-xs font-semibold text-gray-900">Tous les projets (flux global)</div><div className="text-[11px] text-gray-500">Affichage complet sans filtrage</div></div>
              </button>
              {loading ? <div className="text-xs text-gray-400 py-4 text-center">Chargement...</div> : projects.length === 0 ? <div className="text-xs text-gray-400 py-4 text-center">Aucun projet créé pour l'instant.</div> : (
                projects.map((p) => (
                  <div key={p.id} className={`w-full p-2.5 rounded-xl border transition-colors flex items-center justify-between gap-2 ${activeProjectId === p.id ? 'border-indigo-500 bg-indigo-50/50' : 'border-studio-border bg-white hover:bg-studio-subtle'}`}>
                    <button type="button" aria-label={`Sélectionner le projet ${p.name}`} onClick={() => { onSelectProject?.(p.id); setOpen(false); }} className="flex-1 text-left space-y-0.5 outline-none focus-visible:ring-1 focus-visible:ring-indigo-500 rounded p-0.5">
                      <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: p.colorTag || '#6B7280' }} /><span className="text-xs font-semibold text-gray-900">{p.name}</span></div>
                      {p.storagePath && <div className="text-[11px] text-gray-500 font-mono truncate max-w-[240px]">{p.storagePath}</div>}
                    </button>
                    <button type="button" aria-label={`Supprimer ${p.name}`} onClick={(e) => handleDelete(p.id, e)} className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                ))
              )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
