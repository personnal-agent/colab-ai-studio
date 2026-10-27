import React, { useRef } from 'react';
import { UploadCloud, X, Music, Video as VideoIcon } from 'lucide-react';

export interface ReferenceSlotProps {
  label: string;
  fileUrl?: string | null;
  mediaType?: 'image' | 'video' | 'audio';
  accept?: string;
  onFileSelected?: (file: File) => void;
  onClear?: () => void;
  disabled?: boolean;
  badge?: string;
  isWarning?: boolean;
}

const getDisplayUrl = (url: string | null | undefined): string | undefined => {
  if (!url) return undefined;
  if (url.startsWith('blob:') || url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/api/')) {
    return url;
  }
  const normalized = url.replace(/\\/g, '/');
  if (normalized.includes('/uploads/')) {
    const fn = normalized.split('/uploads/')[1];
    return `/api/uploads/${fn}`;
  }
  if (normalized.includes('/outputs/')) {
    const fn = normalized.split('/outputs/')[1];
    return `/api/generations/file/${fn}`;
  }
  return url;
};

export const ReferenceSlot: React.FC<ReferenceSlotProps> = ({
  label,
  fileUrl,
  mediaType = 'image',
  accept = 'image/*,video/*',
  onFileSelected,
  onClear,
  disabled = false,
  badge,
  isWarning = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (disabled || fileUrl) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onFileSelected) {
      onFileSelected(file);
    }
    // Réinitialiser pour permettre de re-sélectionner le même fichier si besoin
    if (e.target) e.target.value = '';
  };

  return (
    <div className="flex flex-col items-center gap-1 select-none">
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={fileUrl ? label : `Ajouter une référence : ${label}`}
        onClick={handleClick}
        onDragOver={(e) => {
          if (disabled || fileUrl) return;
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
        }}
        onDrop={(e) => {
          if (disabled || fileUrl) return;
          e.preventDefault();
          const file = e.dataTransfer.files?.[0];
          if (file && onFileSelected) {
            onFileSelected(file);
          }
        }}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !fileUrl) {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className={`relative w-20 h-16 rounded-slot border overflow-hidden flex flex-col items-center justify-center transition-all ${
          isWarning
            ? 'border-rose-400 bg-rose-50/50'
            : fileUrl
            ? 'border-studio-border bg-gray-900 shadow-sm'
            : 'border-dashed border-gray-300 hover:border-gray-500 bg-white hover:bg-studio-subtle cursor-pointer'
        } ${disabled ? 'opacity-40 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          data-testid="reference-slot-input"
          onChange={handleFileChange}
          className="hidden"
        />

        {fileUrl ? (
          <>
            {mediaType === 'audio' ? (
              <div className="flex flex-col items-center justify-center text-indigo-400">
                <Music className="w-5 h-5" />
                <span className="text-[9px] font-mono mt-0.5 text-gray-300">Audio</span>
              </div>
            ) : mediaType === 'video' || fileUrl.endsWith('.mp4') ? (
              <div className="relative w-full h-full bg-black flex items-center justify-center">
                <video src={getDisplayUrl(fileUrl)} className="w-full h-full object-cover" muted />
                <VideoIcon className="w-4 h-4 text-white/80 absolute" />
              </div>
            ) : (
              <img src={getDisplayUrl(fileUrl)} alt={label} className="w-full h-full object-cover" />
            )}

            {onClear && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onClear();
                }}
                aria-label={`Supprimer la référence ${label}`}
                className="absolute top-1 right-1 w-4 h-4 rounded-full bg-black/70 hover:bg-black text-white flex items-center justify-center text-[10px] transition-colors"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            )}

            {badge && (
              <span className="absolute bottom-1 left-1 px-1 py-0.2 rounded bg-black/70 text-[9px] font-semibold text-white">
                {badge}
              </span>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-400 p-1 text-center">
            <UploadCloud className="w-4 h-4 mb-0.5" />
            <span className="text-[10px] font-medium leading-tight text-gray-600 line-clamp-2">
              {label}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
