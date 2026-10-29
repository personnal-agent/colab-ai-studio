import React, { useState, useEffect, useCallback } from 'react';
import {
  X, Plus, Trash2, ArrowUp, ArrowDown, Sparkles, Sliders,
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import type { AgentInstruction } from '../../types/studio';

export interface AgentInstructionsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onInstructionsChange?: (instructions: AgentInstruction[]) => void;
}

export const AgentInstructionsDrawer: React.FC<AgentInstructionsDrawerProps> = ({
  isOpen,
  onClose,
  onInstructionsChange,
}) => {
  const [instructions, setInstructions] = useState<AgentInstruction[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');

  const fetchInstructions = useCallback(async () => {
    setLoading(true);
    try {
      if (apiClient.listAgentInstructions) {
        const list = await apiClient.listAgentInstructions();
        setInstructions(list);
        onInstructionsChange?.(list);
      }
    } catch (err) {
      console.error('Failed to load agent instructions:', err);
    } finally {
      setLoading(false);
    }
  }, [onInstructionsChange]);

  useEffect(() => {
    if (isOpen) {
      fetchInstructions();
    }
  }, [isOpen, fetchInstructions]);

  const handleToggle = async (id: string, currentActive: boolean) => {
    try {
      const updated = await apiClient.toggleAgentInstruction(id, !currentActive);
      setInstructions((prev) => {
        const next = prev.map((inst) => (inst.id === id ? updated : inst));
        onInstructionsChange?.(next);
        return next;
      });
    } catch (err) {
      console.error('Failed to toggle instruction:', err);
    }
  };

  const handleMove = async (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= instructions.length) return;

    const newOrder = [...instructions];
    const [moved] = newOrder.splice(index, 1);
    newOrder.splice(targetIndex, 0, moved);

    // Optimistic update
    setInstructions(newOrder);
    onInstructionsChange?.(newOrder);

    try {
      const ids = newOrder.map((i) => i.id);
      await apiClient.reorderAgentInstructions(ids);
    } catch (err) {
      console.error('Failed to reorder instructions:', err);
      fetchInstructions(); // Rollback on error
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Supprimer cette directive agent ?')) return;
    try {
      await apiClient.deleteAgentInstruction(id);
      setInstructions((prev) => {
        const next = prev.filter((i) => i.id !== id);
        onInstructionsChange?.(next);
        return next;
      });
    } catch (err) {
      console.error('Failed to delete instruction:', err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) return;

    try {
      const created = await apiClient.createAgentInstruction({
        title: newTitle.trim(),
        description: newDescription.trim(),
        isActive: true,
      });
      setInstructions((prev) => {
        const next = [...prev, created];
        onInstructionsChange?.(next);
        return next;
      });
      setNewTitle('');
      setNewDescription('');
      setIsCreating(false);
    } catch (err) {
      console.error('Failed to create instruction:', err);
    }
  };

  if (!isOpen) return null;

  const activeCount = instructions.filter((i) => i.isActive).length;

  return (
    <div
      data-testid="agent-instructions-drawer"
      className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-[#141518] text-white border-l border-white/10 shadow-2xl flex flex-col animate-slide-left outline-none"
    >
      {/* Drawer Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm font-bold flex items-center gap-2">
              <span>Agent Instructions</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                {activeCount} active(s)
              </span>
            </div>
            <div className="text-[11px] text-neutral-400">
              Règles modulaires empilées injectées dans le prompt
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

      {/* Action Bar */}
      <div className="px-4 py-2.5 border-b border-white/5 flex items-center justify-between bg-white/5">
        <span className="text-xs text-neutral-300 font-medium">
          Directives d'exécution
        </span>
        {!isCreating && (
          <button
            type="button"
            onClick={() => setIsCreating(true)}
            className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1 transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Ajouter règle</span>
          </button>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isCreating && (
          <form onSubmit={handleCreate} className="p-3.5 rounded-2xl bg-white/5 border border-indigo-500/40 space-y-3 mb-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Nouvelle directive agent
              </span>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="text-xs text-neutral-400 hover:text-white"
              >
                Annuler
              </button>
            </div>
            <div>
              <label className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider block mb-1">
                Titre de la règle
              </label>
              <input
                type="text"
                required
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Ex: Éclairage cinématique anamorphique"
                className="w-full text-xs px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-white placeholder-neutral-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider block mb-1">
                Instruction détaillée injectée
              </label>
              <textarea
                required
                rows={3}
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Toujours employer un éclairage volumétrique doux, focale 35mm, zéro grain excessif..."
                className="w-full text-xs px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-white placeholder-neutral-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
            >
              Enregistrer la règle
            </button>
          </form>
        )}

        {loading ? (
          <div className="py-8 text-center text-xs text-neutral-400">Chargement des règles...</div>
        ) : instructions.length === 0 ? (
          <div className="py-8 text-center space-y-2">
            <p className="text-xs text-neutral-400">
              Aucune directive configurée. Ajoutez vos règles de cadrage, de style ou d'interdiction pour guider l'agent de génération.
            </p>
          </div>
        ) : (
          instructions.map((inst, idx) => (
            <div
              key={inst.id}
              className={`p-3 rounded-2xl border transition-all ${
                inst.isActive
                  ? 'bg-white/5 border-white/10'
                  : 'bg-black/20 border-white/5 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-white">{inst.title}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                        inst.isActive
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-white/5 text-neutral-400'
                      }`}
                    >
                      {inst.isActive ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-300 mt-1 leading-relaxed">
                    {inst.description}
                  </p>
                </div>

                {/* ON / OFF Switch */}
                <button
                  type="button"
                  role="switch"
                  aria-checked={inst.isActive}
                  aria-label={`Bascule ${inst.title}`}
                  onClick={() => handleToggle(inst.id, inst.isActive)}
                  className={`w-9 h-5 rounded-full p-0.5 transition-colors flex items-center flex-shrink-0 ${
                    inst.isActive ? 'bg-indigo-600 justify-end' : 'bg-neutral-700 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-sm" />
                </button>
              </div>

              {/* Footer controls: Reorder & Delete */}
              <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-neutral-400">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    disabled={idx === 0}
                    onClick={() => handleMove(idx, 'up')}
                    aria-label="Monter"
                    className="p-1 rounded hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-neutral-400 hover:text-white"
                  >
                    <ArrowUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    disabled={idx === instructions.length - 1}
                    onClick={() => handleMove(idx, 'down')}
                    aria-label="Descendre"
                    className="p-1 rounded hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-neutral-400 hover:text-white"
                  >
                    <ArrowDown className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-[10px] font-mono ml-1 text-neutral-500">#{idx + 1}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(inst.id)}
                  aria-label={`Supprimer ${inst.title}`}
                  className="p-1 rounded hover:bg-rose-500/10 hover:text-rose-400 text-neutral-400 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Drawer Footer */}
      <div className="p-3 border-t border-white/10 bg-black/40 text-[11px] text-neutral-400 flex items-center justify-between">
        <span>Google Flow Pro Engine</span>
        <span className="font-mono text-indigo-400">Auto-injecté</span>
      </div>
    </div>
  );
};
