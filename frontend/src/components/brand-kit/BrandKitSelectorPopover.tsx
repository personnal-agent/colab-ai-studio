import React, { useState, useMemo } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Plus, Sparkles } from 'lucide-react';
import type { BrandKit } from '../../types/studio';
import { BrandKitHoverCard } from './BrandKitHoverCard';

interface BrandKitSelectorPopoverProps {
  brandKits: BrandKit[];
  activeKitId?: string | null;
  onSelectKit: (kit: BrandKit) => void;
  onCreateNewKit: () => void;
}

export const BrandKitSelectorPopover: React.FC<BrandKitSelectorPopoverProps> = ({
  brandKits,
  activeKitId,
  onSelectKit,
  onCreateNewKit,
}) => {
  const [open, setOpen] = useState(false);
  const [hoveredKit, setHoveredKit] = useState<BrandKit | null>(null);

  const sortedKits = useMemo(() => {
    return [...brandKits].sort((a, b) => {
      const timeA = a.lastUsedAt ? new Date(a.lastUsedAt).getTime() : 0;
      const timeB = b.lastUsedAt ? new Date(b.lastUsedAt).getTime() : 0;
      return timeB - timeA;
    });
  }, [brandKits]);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="@ Brand Kit"
          title="Associer une identité de marque Brand Kit"
          className="h-8 px-3 rounded-pill border border-studio-border bg-white text-studio-text hover:bg-studio-subtle transition-colors duration-150 text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer select-none"
        >
          <span className="text-studio-muted">@</span>
          <span>Brand Kit</span>
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-50 w-72 p-3 bg-white rounded-xl shadow-xl border border-studio-border text-xs focus:outline-none relative"
        >
          {sortedKits.length === 0 ? (
            <div className="py-3 px-2 text-center space-y-3">
              <div className="w-9 h-9 rounded-full bg-studio-subtle text-studio-muted mx-auto flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <p className="text-studio-muted leading-relaxed text-[11.5px]">
                Aucun brand kit. Définissez votre marque une fois, puis utilisez-la pour générer.
              </p>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onCreateNewKit();
                }}
                className="w-full py-1.5 px-3 rounded-pill bg-studio-text text-white font-medium hover:bg-black transition-colors"
              >
                Create brand kit
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between px-1">
                <span className="font-semibold text-studio-text">Brand kits</span>
                <button
                  type="button"
                  aria-label="Create brand kit"
                  onClick={() => {
                    setOpen(false);
                    onCreateNewKit();
                  }}
                  className="p-1 rounded-full text-studio-muted hover:text-studio-text hover:bg-studio-subtle transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="max-h-56 overflow-y-auto space-y-1">
                {sortedKits.map((kit) => {
                  const isSelected = kit.id === activeKitId;
                  const assetCount =
                    kit.assetCount ??
                    (kit.palette.length + kit.fonts.length + kit.referenceImages.length);

                  return (
                    <div
                      key={kit.id}
                      className="relative"
                      onMouseEnter={() => setHoveredKit(kit)}
                      onMouseLeave={() => setHoveredKit(null)}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          onSelectKit(kit);
                          setOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between transition-colors ${
                          isSelected
                            ? 'bg-studio-subtle font-semibold text-studio-text'
                            : 'hover:bg-studio-subtle/70 text-studio-text'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          {kit.logoPath ? (
                            <img
                              src={kit.logoPath}
                              alt=""
                              className="w-5 h-5 rounded object-contain bg-studio-subtle"
                            />
                          ) : (
                            <span className="w-5 h-5 rounded bg-studio-subtle text-[11px] font-bold flex items-center justify-center text-studio-muted">
                              {kit.name.charAt(0).toUpperCase()}
                            </span>
                          )}
                          <span className="truncate">{kit.name}</span>
                        </div>
                        <span className="text-[10px] text-studio-muted shrink-0 ml-2">
                          {assetCount} assets
                        </span>
                      </button>

                      {hoveredKit?.id === kit.id && (
                        <div className="absolute left-full top-0 ml-2 z-50 pointer-events-none hidden md:block">
                          <BrandKitHoverCard kit={kit} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
