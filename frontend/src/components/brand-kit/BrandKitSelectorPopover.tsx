import React, { useState, useMemo } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Plus, Eye, Sparkles } from 'lucide-react';
import type { BrandKit } from '../../types/studio';
import { BrandKitHoverCard } from './BrandKitHoverCard';

export interface BrandKitSelectorPopoverProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  brandKits: BrandKit[];
  selectedBrandKitId?: string | null;
  onSelectBrandKit: (kit: BrandKit) => void;
  onInspectBrandKit?: (kit: BrandKit) => void;
  onCreateBrandKitClick: () => void;
  trigger?: React.ReactNode;
}

export const BrandKitSelectorPopover: React.FC<BrandKitSelectorPopoverProps> = ({
  isOpen,
  onOpenChange,
  brandKits,
  selectedBrandKitId,
  onSelectBrandKit,
  onInspectBrandKit,
  onCreateBrandKitClick,
  trigger,
}) => {
  const [hoveredKit, setHoveredKit] = useState<BrandKit | null>(null);

  const sortedKits = useMemo(() => {
    return [...brandKits].sort((a, b) => {
      const timeA = a.lastUsedAt || a.updatedAt || a.createdAt;
      const timeB = b.lastUsedAt || b.updatedAt || b.createdAt;
      return new Date(timeB).getTime() - new Date(timeA).getTime();
    });
  }, [brandKits]);

  return (
    <Popover.Root open={isOpen} onOpenChange={onOpenChange}>
      {trigger ? <Popover.Trigger asChild>{trigger}</Popover.Trigger> : <Popover.Anchor />}
      <Popover.Portal>
        <Popover.Content
          side="top"
          align="end"
          sideOffset={8}
          className="w-72 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 p-2 z-50 text-gray-900 dark:text-gray-100 outline-none animate-in fade-in-50 zoom-in-95 duration-150"
        >
          {sortedKits.length === 0 ? (
            <div className="p-4 text-center">
              <Sparkles className="w-8 h-8 mx-auto mb-2 text-indigo-400 opacity-80" />
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Aucun brand kit disponible
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                Créez une identité de marque pour conditionner vos prompts.
              </p>
              <button
                type="button"
                onClick={() => {
                  onOpenChange(false);
                  onCreateBrandKitClick();
                }}
                className="w-full inline-flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-black text-white dark:bg-white dark:text-black rounded-lg text-xs font-semibold hover:opacity-90 transition-opacity"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create brand kit</span>
              </button>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between px-2.5 py-1.5 mb-1 border-b border-gray-100 dark:border-gray-800">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Brand kits
                </span>
                <button
                  type="button"
                  onClick={() => {
                    onOpenChange(false);
                    onCreateBrandKitClick();
                  }}
                  title="Create new brand kit"
                  className="w-6 h-6 flex items-center justify-center rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="max-h-60 overflow-y-auto space-y-1 py-1">
                {sortedKits.map((kit) => {
                  const assetsCount =
                    (kit.logos?.length || 0) +
                    (kit.colors?.length || 0) +
                    (kit.fonts?.length || 0) +
                    (kit.referenceImages?.length || 0);

                  const dominantColor = kit.colors?.find((c) => c.isDominant)?.hex || kit.colors?.[0]?.hex || '#4F46E5';
                  const isSelected = selectedBrandKitId === kit.id;

                  return (
                    <div
                      key={kit.id}
                      data-testid="brand-kit-item"
                      onMouseEnter={() => setHoveredKit(kit)}
                      onMouseLeave={() => setHoveredKit(null)}
                      className={`group relative flex items-center justify-between p-2 rounded-xl transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800/60'
                      }`}
                    >
                      <button
                        type="button"
                        aria-label={`Select ${kit.name}`}
                        onClick={() => {
                          onSelectBrandKit(kit);
                          onOpenChange(false);
                        }}
                        className="flex items-center space-x-2.5 min-w-0 flex-1 text-left"
                      >
                        <div
                          style={{ backgroundColor: dominantColor }}
                          className="w-5 h-5 rounded-md flex-shrink-0 flex items-center justify-center text-[10px] text-white font-bold shadow-sm"
                        >
                          {kit.name.slice(0, 1)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold truncate">{kit.name}</p>
                          <p className="text-[10px] text-gray-400">{assetsCount} assets</p>
                        </div>
                      </button>

                      {onInspectBrandKit && (
                        <button
                          type="button"
                          aria-label={`Inspect ${kit.name}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspectBrandKit(kit);
                            onOpenChange(false);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-opacity"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {hoveredKit && (
                <div className="absolute right-full top-0 mr-2">
                  <BrandKitHoverCard brandKit={hoveredKit} />
                </div>
              )}
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
