import { Star } from 'lucide-react';

interface FavoriteFilterToggleProps {
  isFavoriteOnly: boolean;
  onToggle: (active: boolean) => void;
}

export function FavoriteFilterToggle({ isFavoriteOnly, onToggle }: FavoriteFilterToggleProps) {
  return (
    <button
      type="button"
      aria-label="Filtrer les favoris"
      aria-pressed={isFavoriteOnly}
      onClick={() => onToggle(!isFavoriteOnly)}
      className={`p-2 rounded-slot transition-colors flex items-center justify-center ${
        isFavoriteOnly
          ? 'bg-amber-50 text-amber-500 hover:bg-amber-100'
          : 'text-gray-400 hover:text-gray-700 hover:bg-studio-subtle'
      }`}
      title={isFavoriteOnly ? 'Afficher tous les médias' : 'Afficher uniquement les favoris'}
    >
      <Star
        className={`w-5 h-5 ${isFavoriteOnly ? 'fill-amber-400 stroke-amber-500' : 'stroke-current'}`}
      />
    </button>
  );
}
