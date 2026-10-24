import React from 'react';
import type { BrandKit } from '../../types/studio';

export interface BrandKitHoverCardProps {
  brandKit: BrandKit;
  className?: string;
}

export const BrandKitHoverCard: React.FC<BrandKitHoverCardProps> = ({ brandKit, className = '' }) => {
  const assetsCount =
    (brandKit.logos?.length || 0) +
    (brandKit.colors?.length || 0) +
    (brandKit.fonts?.length || 0) +
    (brandKit.referenceImages?.length || 0);

  const mainLogo = brandKit.logos?.[0];

  return (
    <div
      data-testid="brand-kit-hover-card"
      className={`w-64 p-3 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 pointer-events-none z-50 text-left ${className}`}
    >
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden border border-gray-200 dark:border-gray-600 flex-shrink-0">
          {mainLogo ? (
            <img
              src={mainLogo.filePath}
              alt={brandKit.name}
              className="w-full h-full object-contain p-1"
              onError={(e) => {
                // Fallback to text initials if image fails to load in tests / offline
                (e.currentTarget as HTMLElement).style.display = 'none';
              }}
            />
          ) : (
            <span className="text-xs font-bold text-gray-500 uppercase">
              {brandKit.name.slice(0, 2)}
            </span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
            {brandKit.name}
          </h4>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {assetsCount} assets · Updated
          </p>
        </div>
      </div>

      {brandKit.overview && (
        <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 mb-2">
          {brandKit.overview}
        </p>
      )}

      {brandKit.colors && brandKit.colors.length > 0 && (
        <div className="flex items-center space-x-1.5 pt-1 border-t border-gray-100 dark:border-gray-700">
          {brandKit.colors.slice(0, 6).map((color, idx) => (
            <div
              key={idx}
              title={`${color.hex} - ${color.label}`}
              style={{ backgroundColor: color.hex }}
              className="w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 shadow-sm flex-shrink-0"
            />
          ))}
          {brandKit.colors.length > 6 && (
            <span className="text-[10px] text-gray-400 font-mono">
              +{brandKit.colors.length - 6}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
