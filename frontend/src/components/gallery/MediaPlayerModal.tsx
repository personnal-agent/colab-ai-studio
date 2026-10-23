import * as Dialog from '@radix-ui/react-dialog';
import {
  Check,
  Copy,
  Film,
  HardDrive,
  Image as ImageIcon,
  Sparkles,
  Star,
  Trash2,
  Wand2,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { Generation } from '../../types/studio';

interface MediaPlayerModalProps {
  generation: Generation | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleFavorite: (id: string) => void;
  onRemix: (generation: Generation) => void;
  onDelete: (id: string) => void;
}

export function MediaPlayerModal({
  generation,
  isOpen,
  onClose,
  onToggleFavorite,
  onRemix,
  onDelete,
}: MediaPlayerModalProps) {
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [copiedPath, setCopiedPath] = useState(false);

  if (!generation) return null;

  const isVideo = generation.mediaType === 'video';

  const copyToClipboard = (text: string, type: 'prompt' | 'path') => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      if (type === 'prompt') {
        setCopiedPrompt(true);
        setTimeout(() => setCopiedPrompt(false), 2000);
      } else {
        setCopiedPath(true);
        setTimeout(() => setCopiedPath(false), 2000);
      }
    }
  };

  const handleRemix = () => {
    onRemix(generation);
    onClose();
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 animate-in fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-5xl max-h-[90vh] bg-white rounded-menu shadow-2xl z-50 flex flex-col md:flex-row overflow-hidden border border-studio-border animate-in zoom-in-95">
          {/* Lecteur Média Grand Format (Gauche) */}
          <div className="w-full md:w-3/5 bg-black flex items-center justify-center relative min-h-[320px] md:min-h-[500px]">
            {isVideo && generation.filePath ? (
              <video
                src={generation.filePath}
                controls
                autoPlay
                loop
                playsInline
                className="w-full h-full max-h-[75vh] object-contain"
              />
            ) : generation.filePath || generation.thumbnailPath ? (
              <img
                src={generation.filePath || generation.thumbnailPath || undefined}
                alt={generation.prompt}
                className="w-full h-full max-h-[75vh] object-contain"
              />
            ) : (
              <div className="text-gray-400 text-sm flex flex-col items-center gap-2">
                {isVideo ? (
                  <Film className="w-10 h-10 stroke-gray-600" />
                ) : (
                  <ImageIcon className="w-10 h-10 stroke-gray-600" />
                )}
                <span>Aperçu indisponible</span>
              </div>
            )}
          </div>

          {/* Fiche Technique & Actions (Droite) */}
          <div className="w-full md:w-2/5 p-6 flex flex-col justify-between overflow-y-auto max-h-[75vh] bg-studio-card">
            <div className="space-y-5">
              {/* En-tête */}
              <div className="flex items-center justify-between border-b border-studio-border pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded-pill bg-studio-subtle text-gray-700">
                    {generation.mediaType}
                  </span>
                  <Dialog.Title className="text-sm font-semibold text-gray-900 truncate max-w-[160px]">
                    {generation.modelName || generation.modelId}
                  </Dialog.Title>
                </div>
                <Dialog.Close asChild>
                  <button
                    type="button"
                    aria-label="Fermer"
                    className="p-1 rounded-slot hover:bg-studio-subtle text-gray-400 hover:text-gray-700 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </Dialog.Close>
              </div>

              {/* Prompt original */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-semibold text-gray-700">
                  <span>Prompt utilisateur</span>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(generation.prompt, 'prompt')}
                    className="text-[11px] text-gray-500 hover:text-gray-900 flex items-center gap-1 transition-colors"
                  >
                    {copiedPrompt ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>{copiedPrompt ? 'Copié' : 'Copier'}</span>
                  </button>
                </div>
                <p className="text-xs text-gray-800 bg-studio-canvas p-3 rounded-slot border border-studio-border leading-relaxed max-h-24 overflow-y-auto">
                  {generation.prompt}
                </p>
              </div>

              {/* Prompt enrichi Brand Kit si présent */}
              {generation.compiledPrompt &&
                generation.compiledPrompt !== generation.prompt && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-semibold text-indigo-900 flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Prompt de marque enrichi</span>
                    </div>
                    <p className="text-xs text-indigo-950 bg-indigo-50/60 p-2.5 rounded-slot border border-indigo-100 leading-relaxed max-h-20 overflow-y-auto">
                      {generation.compiledPrompt}
                    </p>
                  </div>
                )}

              {/* Marque associée */}
              {generation.brandKitSnapshot && (
                <div className="p-2.5 rounded-slot bg-studio-canvas border border-studio-border flex items-center justify-between text-xs">
                  <span className="text-gray-600">Brand Kit actif :</span>
                  <div className="flex items-center gap-1.5 font-medium text-gray-900">
                    {generation.brandKitSnapshot.primaryColor && (
                      <span
                        className="w-3 h-3 rounded-full border border-black/10 inline-block"
                        style={{ backgroundColor: generation.brandKitSnapshot.primaryColor }}
                      />
                    )}
                    <span>{generation.brandKitSnapshot.name}</span>
                  </div>
                </div>
              )}

              {/* Fiche des paramètres */}
              <div className="space-y-2 border-t border-studio-border pt-3">
                <span className="text-xs font-semibold text-gray-900">
                  Paramètres d&apos;inférence
                </span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded bg-studio-canvas border border-studio-border">
                    <div className="text-[10px] text-gray-400">Modèle</div>
                    <div className="font-medium text-gray-800 truncate">
                      {generation.modelName || generation.modelId}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-studio-canvas border border-studio-border">
                    <div className="text-[10px] text-gray-400">Seed</div>
                    <div className="font-medium text-gray-800 font-mono">
                      {generation.parameters.seed}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-studio-canvas border border-studio-border">
                    <div className="text-[10px] text-gray-400">Ratio</div>
                    <div className="font-medium text-gray-800">
                      {generation.parameters.aspectRatio}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-studio-canvas border border-studio-border">
                    <div className="text-[10px] text-gray-400">Durée</div>
                    <div className="font-medium text-gray-800">
                      {generation.parameters.duration}
                    </div>
                  </div>
                </div>

                {generation.filePath && (
                  <div className="pt-1">
                    <div className="flex items-center justify-between text-[11px] text-gray-400">
                      <span className="flex items-center gap-1">
                        <HardDrive className="w-3 h-3" />
                        <span>Fichier local :</span>
                      </span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(generation.filePath || '', 'path')}
                        className="text-gray-600 hover:text-black flex items-center gap-1"
                      >
                        {copiedPath ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                        <span>{copiedPath ? 'Copié' : 'Copier'}</span>
                      </button>
                    </div>
                    <div className="text-[10px] font-mono text-gray-600 truncate mt-0.5">
                      {generation.filePath}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Barre d'actions & Remix */}
            <div className="pt-4 border-t border-studio-border space-y-2 mt-4">
              <button
                type="button"
                onClick={handleRemix}
                className="w-full py-2.5 px-4 bg-gray-900 text-white rounded-slot text-sm font-semibold hover:bg-black transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                <Wand2 className="w-4 h-4 text-amber-300" />
                <span>Remix</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => onToggleFavorite(generation.id)}
                  className={`flex-1 py-2 px-3 rounded-slot text-xs font-medium border flex items-center justify-center gap-1.5 transition-colors ${
                    generation.isFavorite
                      ? 'bg-amber-50 text-amber-600 border-amber-200'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-studio-subtle'
                  }`}
                >
                  <Star
                    className={`w-3.5 h-3.5 ${
                      generation.isFavorite ? 'fill-amber-400 stroke-amber-500' : ''
                    }`}
                  />
                  <span>{generation.isFavorite ? 'Favori' : 'Ajouter aux favoris'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    onDelete(generation.id);
                    onClose();
                  }}
                  className="py-2 px-3 rounded-slot text-xs font-medium text-red-600 hover:text-red-700 hover:bg-red-50 border border-transparent hover:border-red-200 transition-colors flex items-center gap-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Supprimer</span>
                </button>
              </div>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
