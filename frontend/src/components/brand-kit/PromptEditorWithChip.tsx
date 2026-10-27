import React, { useRef, useState } from 'react';
import { AtSign, Maximize2, Minimize2, X } from 'lucide-react';
import type { BrandKit } from '../../types/studio';

export interface PromptEditorWithChipProps {
  prompt: string;
  onPromptChange: (value: string) => void;
  selectedBrandKit: BrandKit | null;
  onRemoveBrandKit: () => void;
  onOpenBrandKitSelector: () => void;
  placeholder?: string;
  disabled?: boolean;
  onSubmit?: () => void;
  className?: string;
}

export const PromptEditorWithChip: React.FC<PromptEditorWithChipProps> = ({
  prompt,
  onPromptChange,
  selectedBrandKit,
  onRemoveBrandKit,
  onOpenBrandKitSelector,
  placeholder = 'Describe what you want to create or type @ to select a brand kit...',
  disabled = false,
  onSubmit,
  className = '',
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isTallMode, setIsTallMode] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Backspace' && textareaRef.current?.selectionStart === 0 && selectedBrandKit) {
      // Backspace at the very beginning of the prompt removes the brand kit chip in one block
      e.preventDefault();
      onRemoveBrandKit();
      return;
    }

    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (onSubmit) onSubmit();
      return;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    onPromptChange(val);

    // If selectionStart is available and > 0, use it. Otherwise fall back to val.length (e.g. typing at end or synthetic change events).
    const cursorPos = (typeof e.target.selectionStart === 'number' && e.target.selectionStart > 0)
      ? e.target.selectionStart
      : val.length;

    // Only open when the character just typed at the cursor position is an '@'
    // at the beginning of the prompt or immediately following whitespace.
    const atTyped = val.length > prompt.length && (
      (cursorPos === 1 && val[0] === '@') ||
      (cursorPos > 1 && val[cursorPos - 1] === '@' && /\s/.test(val[cursorPos - 2]))
    );

    if (atTyped) {
      onOpenBrandKitSelector();
    }
  };

  return (
    <div className={`relative flex flex-col w-full bg-transparent ${className}`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
          {selectedBrandKit && (
            <span
              data-testid="brand-kit-chip"
              className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 animate-in fade-in zoom-in-95 duration-100"
            >
              <span>{`[@${selectedBrandKit.name}]`}</span>
              <button
                type="button"
                aria-label={`Remove ${selectedBrandKit.name} brand kit`}
                onClick={onRemoveBrandKit}
                className="hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded-full p-0.5 text-indigo-600 dark:text-indigo-300 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={() => setIsTallMode(!isTallMode)}
            aria-label={isTallMode ? 'Hauteur standard' : 'Grand format'}
            title={isTallMode ? 'Réduire à la hauteur normale' : 'Agrandir la hauteur de saisie'}
            className="inline-flex items-center space-x-1 text-xs font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors py-0.5 px-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {isTallMode ? (
              <>
                <Minimize2 className="w-3 h-3 text-gray-500" />
                <span className="hidden sm:inline">Hauteur standard</span>
              </>
            ) : (
              <>
                <Maximize2 className="w-3 h-3 text-gray-500" />
                <span className="hidden sm:inline">Grand format</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onOpenBrandKitSelector}
            aria-label="@ Brand Kit"
            title="Attach or change Brand Kit"
            className="inline-flex items-center space-x-1 text-xs font-medium text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors py-0.5 px-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <AtSign className="w-3.5 h-3.5" />
            <span>Brand Kit</span>
          </button>
        </div>
      </div>

      <textarea
        ref={textareaRef}
        value={prompt}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={isTallMode ? 9 : 4}
        className={`w-full resize-y ${
          isTallMode ? 'min-h-[210px]' : 'min-h-[115px]'
        } max-h-[480px] bg-transparent text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-0 border-0 p-0 leading-relaxed overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600`}
      />
    </div>
  );
};
