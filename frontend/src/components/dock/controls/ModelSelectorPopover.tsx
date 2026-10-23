import React, { useState, useMemo } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Search } from 'lucide-react';
import type { ModelDefinition } from '../../../types/studio';

interface ModelSelectorPopoverProps {
  activeModelId?: string;
  mediaType?: string;
  models: ModelDefinition[];
  onSelectModel: (modelId: string) => void;
}

export const ModelSelectorPopover: React.FC<ModelSelectorPopoverProps> = ({
  activeModelId,
  mediaType,
  models,
  onSelectModel,
}) => {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const activeModel = useMemo(() => {
    return models.find((m) => m.id === activeModelId) || models[0];
  }, [models, activeModelId]);

  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      // Filtrer par mediaType si précisé et différent de LLM
      if (mediaType && m.mediaType.toLowerCase() !== mediaType.toLowerCase()) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        m.name.toLowerCase().includes(q) ||
        m.id.toLowerCase().includes(q) ||
        (m.description && m.description.toLowerCase().includes(q))
      );
    });
  }, [models, mediaType, searchQuery]);

  const renderBadge = (badge?: string) => {
    if (!badge) return null;
    if (badge.toLowerCase() === 'slow') {
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
          ! Slower than usual
        </span>
      );
    }
    if (badge.toLowerCase() === 'beta') {
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-medium">
          Beta
        </span>
      );
    }
    if (badge.toLowerCase() === 'new') {
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
          New
        </span>
      );
    }
    return (
      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-800 font-medium">
        {badge}
      </span>
    );
  };

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Select model"
          title={`Modèle actif : ${activeModel?.name || activeModelId}`}
          className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer max-w-[200px] truncate"
        >
          <span className="text-studio-muted">🎬</span>
          <span className="truncate">{activeModel?.name || activeModelId || 'Sélectionner un modèle'}</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={8}
          className="z-50 w-80 p-3 bg-white rounded-xl shadow-lg border border-studio-border text-xs focus:outline-none space-y-2.5"
        >
          <div className="flex items-center gap-2 px-2.5 py-1.5 bg-studio-subtle rounded-lg border border-studio-border">
            <Search className="w-3.5 h-3.5 text-studio-muted shrink-0" />
            <input
              type="text"
              placeholder="Search model..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs w-full focus:outline-none placeholder:text-studio-muted"
              autoFocus
            />
          </div>

          <div data-testid="model-list" className="max-h-60 overflow-y-auto space-y-1 pr-1">
            {filteredModels.length === 0 ? (
              <div className="text-center py-4 text-studio-muted text-xs">
                Aucun modèle ne correspond à votre recherche
              </div>
            ) : (
              filteredModels.map((model) => {
                const isSelected = model.id === activeModelId;
                return (
                  <button
                    key={model.id}
                    type="button"
                    data-testid={`model-item-${model.id}`}
                    onClick={() => {
                      onSelectModel(model.id);
                      setOpen(false);
                    }}
                    className={`w-full text-left p-2 rounded-lg transition-colors flex flex-col gap-1 cursor-pointer ${
                      isSelected
                        ? 'bg-studio-subtle border border-studio-border'
                        : 'hover:bg-studio-subtle/70'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-studio-text truncate">
                        {model.name}
                      </span>
                      {renderBadge(model.capabilities?.badge)}
                    </div>
                    {model.description && (
                      <p className="text-[11px] text-studio-muted line-clamp-1">
                        {model.description}
                      </p>
                    )}
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
