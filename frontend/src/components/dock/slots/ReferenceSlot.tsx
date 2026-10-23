import React, { useRef } from 'react';
import { Plus, X } from 'lucide-react';

interface ReferenceSlotProps {
  label: string;
  previewUrl?: string | null;
  countBadge?: string;
  isLimitReached?: boolean;
  accept?: string;
  multiple?: boolean;
  icon?: React.ReactNode;
  onSelectFile?: (files: FileList) => void;
  onRemove?: () => void;
}

export const ReferenceSlot: React.FC<ReferenceSlotProps> = ({
  label,
  previewUrl,
  countBadge,
  isLimitReached,
  accept = 'image/*',
  multiple = false,
  icon,
  onSelectFile,
  onRemove,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && onSelectFile) {
      onSelectFile(e.target.files);
    }
  };

  return (
    <div className="relative group shrink-0">
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
        className="hidden"
      />

      <button
        type="button"
        aria-label={label}
        onClick={handleClick}
        className="w-20 h-16 rounded-slot bg-studio-subtle hover:bg-studio-border/50 border border-studio-border/60 transition-colors flex flex-col items-center justify-center p-1 relative overflow-hidden text-center cursor-pointer select-none"
      >
        {previewUrl ? (
          <img
            src={previewUrl}
            alt={`Preview ${label}`}
            className="w-full h-full object-cover rounded-slot"
          />
        ) : (
          <>
            <div className="text-studio-muted mb-0.5">
              {icon || <Plus className="w-4 h-4 text-studio-muted" />}
            </div>
            <span className="text-[10px] leading-tight font-medium text-studio-text line-clamp-2 px-0.5">
              {label}
            </span>
            {countBadge && (
              <span
                className={`text-[9px] font-semibold mt-0.5 ${
                  isLimitReached ? 'text-amber-600' : 'text-studio-muted'
                }`}
              >
                {countBadge}
              </span>
            )}
          </>
        )}
      </button>

      {previewUrl && onRemove && (
        <button
          type="button"
          aria-label={`Remove ${label}`}
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-studio-text text-white text-[10px] flex items-center justify-center shadow-md hover:bg-black transition-colors"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};
