import React from 'react';
import type { BrandKit } from '../../types/studio';

interface BrandKitHoverCardProps {
  kit: BrandKit;
}

export const BrandKitHoverCard: React.FC<BrandKitHoverCardProps> = ({ kit }) => {
  const assetCount = kit.assetCount ?? (kit.palette.length + kit.fonts.length + kit.referenceImages.length);

  return (
    <div className="w-64 p-3.5 bg-white rounded-xl shadow-xl border border-studio-border text-xs space-y-2.5">
      <div className="flex items-center gap-2.5">
        {kit.logoPath ? (
          <img
            src={kit.logoPath}
            alt={kit.name}
            className="w-9 h-9 rounded-lg object-contain bg-studio-subtle p-1 border border-studio-border"
          />
        ) : (
          <div className="w-9 h-9 rounded-lg bg-studio-subtle text-studio-text font-bold text-sm flex items-center justify-center border border-studio-border">
            {kit.name.charAt(0).toUpperCase()}
          </div>
        )}
        <div className="min-w-0">
          <h4 className="font-bold text-studio-text truncate">{kit.name}</h4>
          <span className="text-[11px] text-studio-muted">
            {assetCount} assets · Mis à jour
          </span>
        </div>
      </div>

      {kit.overview && (
        <p className="text-[11px] text-studio-muted line-clamp-2 leading-relaxed">
          {kit.overview}
        </p>
      )}

      {kit.palette && kit.palette.length > 0 && (
        <div className="pt-1.5 border-t border-studio-border/60">
          <div className="text-[10px] font-semibold text-studio-muted mb-1.5">
            Nuancier officiel
          </div>
          <div className="flex items-center gap-1.5">
            {kit.palette.slice(0, 5).map((color, idx) => (
              <div
                key={`${color.hex}-${idx}`}
                data-testid="color-swatch"
                title={`${color.name} (${color.hex})`}
                className="w-5 h-5 rounded-md border border-black/10 shadow-xs"
                style={{ backgroundColor: color.hex }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
