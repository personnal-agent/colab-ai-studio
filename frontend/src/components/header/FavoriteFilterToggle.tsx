import React from 'react';
import { Star } from 'lucide-react';

interface FavoriteFilterToggleProps {
  active: boolean;
  onToggle: () => void;
}

export const FavoriteFilterToggle: React.FC<FavoriteFilterToggleProps> = ({ active, onToggle }) => {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        aria-label="Filtrer par favoris"
        onClick={onToggle}
        className={`p-2 rounded-full border transition-colors flex items-center justify-center ${
          active
            ? 'bg-amber-50 border-amber-300 text-amber-500 shadow-sm'
            : 'bg-white border-studio-border text-gray-500 hover:text-gray-700 hover:bg-studio-subtle'
        }`}
      >
        <Star className={`w-5 h-5 ${active ? 'fill-amber-500 text-amber-500' : ''}`} />
      </button>
      <h1 className="text-2xl font-semibold leading-8 text-gray-900 tracking-tight">
        Image & Video
      </h1>
    </div>
  );
};
