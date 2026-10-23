import React, { useRef } from 'react';
import { X } from 'lucide-react';
import type { BrandKit } from '../../types/studio';

interface PromptEditorWithChipProps {
  prompt: string;
  selectedKit?: BrandKit | null;
  mediaType?: string;
  onChange: (prompt: string) => void;
  onRemoveKit?: () => void;
  onTriggerKitPicker?: () => void;
  onSubmit?: () => void;
}

export const PromptEditorWithChip: React.FC<PromptEditorWithChipProps> = ({
  prompt,
  selectedKit,
  mediaType = 'video',
  onChange,
  onRemoveKit,
  onTriggerKitPicker,
  onSubmit,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const placeholder =
    mediaType.toLowerCase() === 'video'
      ? 'Describe your video or reference by using @...'
      : 'Describe your image or reference by using @...';

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Si touche @ saisie, déclencher l'ouverture du sélecteur
    if (e.key === '@' && onTriggerKitPicker) {
      onTriggerKitPicker();
    }
    // Si Backspace au début du champ texte et qu'un kit est actif, supprimer le kit
    if (e.key === 'Backspace' && textareaRef.current) {
      const { selectionStart, selectionEnd } = textareaRef.current;
      if (selectionStart === 0 && selectionEnd === 0 && selectedKit && onRemoveKit) {
        e.preventDefault();
        onRemoveKit();
      }
    }
    // Entrée sans shift pour soumettre
    if (e.key === 'Enter' && !e.shiftKey && onSubmit) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="w-full flex flex-col gap-1.5 focus-within:ring-0">
      <div className="flex flex-wrap items-center gap-1.5">
        {selectedKit && (
          <div
            data-testid="brand-kit-chip"
            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-studio-text text-white text-xs font-semibold shadow-xs select-none"
          >
            <span>{`[@${selectedKit.name}]`}</span>
            {onRemoveKit && (
              <button
                type="button"
                aria-label="Remove brand kit"
                onClick={onRemoveKit}
                className="w-3.5 h-3.5 rounded-full hover:bg-white/20 flex items-center justify-center transition-colors"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            )}
          </div>
        )}
      </div>

      <textarea
        ref={textareaRef}
        rows={2}
        value={prompt}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full bg-transparent resize-none border-0 p-0 text-xs sm:text-sm text-studio-text placeholder:text-[#4B5563] focus:ring-0 focus:outline-none leading-relaxed"
      />
    </div>
  );
};
