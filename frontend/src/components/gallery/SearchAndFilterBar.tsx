import { Search, X } from 'lucide-react';
import React from 'react';

interface SearchAndFilterBarProps {
  searchQuery: string;
  selectedTypes: string[];
  onSearchChange: (query: string) => void;
  onFilterChange: (types: string[]) => void;
}

const FILTER_OPTIONS = [
  { label: '+ Image', type: 'image' },
  { label: '+ Video', type: 'video' },
  { label: '+ Lip sync', type: 'lip_sync' },
];

export function SearchAndFilterBar({
  searchQuery,
  selectedTypes,
  onSearchChange,
  onFilterChange,
}: SearchAndFilterBarProps) {
  const toggleType = (type: string) => {
    if (selectedTypes.includes(type)) {
      onFilterChange(selectedTypes.filter((t) => t !== type));
    } else {
      onFilterChange([...selectedTypes, type]);
    }
  };

  return (
    <div className="w-full flex flex-col sm:flex-row items-center gap-3 py-3">
      {/* Barre de recherche */}
      <div className="relative flex-1 w-full">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-studio-placeholder" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onSearchChange(e.target.value)}
          placeholder="Search images, videos, and lip syncs"
          className="w-full pl-10 pr-9 py-2 bg-studio-card border border-studio-border rounded-pill text-sm text-gray-900 placeholder:text-studio-placeholder shadow-card focus:outline-none focus:ring-1 focus:ring-gray-700 transition-all"
        />
        {searchQuery && (
          <button
            type="button"
            aria-label="Effacer la recherche"
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 rounded-full"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Puces cumulatives */}
      <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
        {FILTER_OPTIONS.map((opt) => {
          const isActive = selectedTypes.includes(opt.type);
          return (
            <button
              key={opt.type}
              type="button"
              aria-pressed={isActive}
              onClick={() => toggleType(opt.type)}
              className={`px-3 py-1.5 rounded-pill text-xs font-medium whitespace-nowrap transition-colors border ${
                isActive
                  ? 'bg-gray-900 text-white border-gray-900 shadow-sm'
                  : 'bg-studio-card text-gray-700 border-studio-border hover:bg-studio-subtle'
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
