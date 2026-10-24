import React, { useState, useMemo } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Search, Sparkles } from 'lucide-react';
import type { ModelDefinition } from '../../../types/studio';

interface ModelSelectorPopoverProps {
  activeModel?: ModelDefinition | null;
  models: ModelDefinition[];
  mode?: string;
  onSelect: (model: ModelDefinition) => void;
}

const CATEGORY_TABS = [
  { id: 'all', label: 'Tous' },
  { id: 'image', label: 'Image' },
  { id: 'video', label: 'Vidéo' },
  { id: 'lip_sync', label: 'Lip sync' },
  { id: 'upscale', label: 'Upscale' },
  { id: 'text', label: 'LLM' },
];

export const ModelSelectorPopover: React.FC<ModelSelectorPopoverProps> = ({
  activeModel,
  models,
  mode,
  onSelect,
}) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedTab, setSelectedTab] = useState('all');

  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      // Si en mode LLM, forcer text
      if (mode === 'llm' || mode === 'text') {
        if (m.type !== 'text' && m.type !== 'llm') return false;
      } else if (selectedTab !== 'all') {
        if (m.type !== selectedTab) return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase().trim();
        const matchName = m.name.toLowerCase().includes(q);
        const matchDesc = m.description?.toLowerCase().includes(q);
        if (!matchName && !matchDesc) return false;
      }
      return true;
    });
  }, [models, mode, selectedTab, search]);

  const renderBadge = (badge?: string) => {
    if (!badge) return null;
    let colorClass = 'bg-gray-100 text-gray-700';
    if (badge === 'New') colorClass = 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    if (badge === 'Beta') colorClass = 'bg-amber-50 text-amber-700 border border-amber-200';
    if (badge.includes('Slow')) colorClass = 'bg-rose-50 text-rose-700 border border-rose-200';

    return (
      <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-semibold ${colorClass}`}>
        {badge}
      </span>
    );
  };

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Modèle ${activeModel?.name || 'Sélectionner'}`}
          className="h-8 px-2.5 rounded-pill text-xs font-semibold border border-studio-border bg-white hover:bg-gray-50 text-gray-900 flex items-center gap-1.5 transition-colors shadow-sm select-none max-w-[200px]"
        >
          <span className="text-gray-400">🎬</span>
          <span className="truncate">{activeModel?.name || 'Choisir un modèle'}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="start"
          sideOffset={8}
          className="z-50 w-80 p-3 rounded-2xl bg-white border border-studio-border shadow-float text-gray-800 text-xs flex flex-col gap-2.5 focus:outline-none"
        >
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher un modèle..."
              className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          {mode !== 'llm' && mode !== 'text' && (
            <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-none border-b border-gray-100">
              {CATEGORY_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedTab(tab.id)}
                  className={`px-2 py-1 rounded-lg text-[11px] font-medium whitespace-nowrap transition-colors ${
                    selectedTab === tab.id
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}

          <div className="max-h-56 overflow-y-auto flex flex-col gap-1 pr-1">
            {filteredModels.length === 0 ? (
              <div className="py-6 text-center text-gray-400 text-xs">
                Aucun modèle ne correspond à votre recherche.
              </div>
            ) : (
              filteredModels.map((m) => {
                const isSelected = activeModel?.id === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      onSelect(m);
                      setOpen(false);
                    }}
                    className={`p-2 rounded-xl text-left transition-colors flex items-start justify-between gap-2 ${
                      isSelected
                        ? 'bg-gray-900 text-white'
                        : 'hover:bg-studio-subtle text-gray-800'
                    }`}
                  >
                    <div className="flex flex-col min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Sparkles className={`w-3 h-3 ${isSelected ? 'text-amber-300' : 'text-gray-400'}`} />
                        <span className="font-semibold text-xs truncate">{m.name}</span>
                      </div>
                      {m.description && (
                        <p className={`text-[11px] truncate mt-0.5 ${isSelected ? 'text-gray-300' : 'text-gray-500'}`}>
                          {m.description}
                        </p>
                      )}
                    </div>
                    {renderBadge(m.badge)}
                  </button>
                );
              })
            )}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
