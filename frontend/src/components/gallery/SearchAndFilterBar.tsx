import React from 'react';
import { Search, X } from 'lucide-react';

interface SearchAndFilterBarProps {
  searchValue: string; onSearchChange: (value: string) => void;
  activePills: string[]; onTogglePill: (pill: string) => void;
}

const PILLS = [{ id: 'image', label: '+ Image' }, { id: 'video', label: '+ Video' }, { id: 'lip_sync', label: '+ Lip sync' }];

export const SearchAndFilterBar: React.FC<SearchAndFilterBarProps> = ({ searchValue, onSearchChange, activePills, onTogglePill }) => {
  return (
    <div className="w-full flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
      <div className="relative flex-1">
        <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input type="text" value={searchValue} onChange={(e) => onSearchChange(e.target.value)} placeholder="Search images, videos, and lip syncs" className="w-full h-10 pl-10 pr-9 bg-white border border-studio-border rounded-full text-xs text-gray-900 placeholder-[#4B5563] focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-sm transition-colors" />
        {searchValue && (
          <button type="button" aria-label="Effacer la recherche" onClick={() => onSearchChange('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5 rounded-full"><X className="w-3.5 h-3.5" /></button>
        )}
      </div>
      <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
        {PILLS.map((pill) => {
          const isActive = activePills.includes(pill.id);
          return (
            <button key={pill.id} type="button" onClick={() => onTogglePill(pill.id)} className={`h-9 px-3.5 rounded-full text-xs font-medium whitespace-nowrap border transition-all flex items-center gap-1 ${isActive ? 'bg-gray-900 text-white border-gray-900 shadow-sm' : 'bg-white text-gray-600 border-studio-border hover:bg-studio-subtle hover:text-gray-900'}`}>
              <span>{pill.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
