import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Check, Copy, Download, Folder, Layers, Sparkles, Star, Volume2, X } from 'lucide-react';
import { apiClient, getMediaFileUrl } from '../../services/apiClient';
import type { Generation } from '../../types/studio';

export interface MediaPlayerModalProps {
  generation: Generation | null;
  isOpen: boolean;
  onClose: () => void;
  onRemix: (generation: Generation) => void;
  onFavoriteToggled?: (generation: Generation) => void;
}

export const MediaPlayerModal: React.FC<MediaPlayerModalProps> = ({
  generation, isOpen, onClose, onRemix, onFavoriteToggled,
}) => {
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [copiedPath, setCopiedPath] = useState(false);
  const [isUpdatingFavorite, setIsUpdatingFavorite] = useState(false);

  if (!generation) return null;

  const copyText = async (text: string, setCopied: (v: boolean) => void) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) { console.error('Failed to copy:', err); }
  };

  const handleToggleFavorite = async () => {
    if (isUpdatingFavorite) return;
    setIsUpdatingFavorite(true);
    try {
      const res = await apiClient.toggleFavorite(generation.id);
      onFavoriteToggled?.({ ...generation, isFavorite: res.isFavorite });
    } catch (err) { console.error('Failed to toggle favorite:', err); }
    finally { setIsUpdatingFavorite(false); }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 animate-fade-in" />
        <Dialog.Content className="fixed inset-3 sm:inset-8 z-50 bg-white rounded-dock shadow-2xl flex flex-col md:flex-row overflow-hidden border border-studio-border outline-none">
          <Dialog.Title className="sr-only">Inspection du média : {generation.prompt}</Dialog.Title>
          <Dialog.Description className="sr-only">Fiche technique et lecture du média</Dialog.Description>
          {/* Lecteur grand format */}
          <div className="flex-1 bg-black flex items-center justify-center relative overflow-hidden min-h-[300px]">
            {(generation.mediaType === 'image' || generation.mediaType === 'upscale') && (
              <img src={getMediaFileUrl(generation)} alt={generation.prompt} className="max-h-full max-w-full object-contain" />
            )}
            {(generation.mediaType === 'video' || generation.mediaType === 'lip_sync') && (
              <video src={getMediaFileUrl(generation)} controls autoPlay playsInline className="max-h-full max-w-full object-contain" />
            )}
            {generation.mediaType === 'audio' && (
              <div className="flex flex-col items-center justify-center p-8 gap-4">
                <div className="w-20 h-20 rounded-full bg-indigo-900/60 flex items-center justify-center border border-indigo-500/30">
                  <Volume2 className="w-10 h-10 text-indigo-400 animate-pulse" />
                </div>
                <audio src={getMediaFileUrl(generation)} controls className="mt-4" />
              </div>
            )}
          </div>

          {/* Volet latéral de métadonnées */}
          <div className="w-full md:w-96 flex flex-col justify-between border-t md:border-t-0 md:border-l border-studio-border bg-white overflow-y-auto">
            <div className="p-5 border-b border-studio-border flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur-sm z-10">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                  {generation.modelName}
                </span>
                <span className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold">{generation.mediaType}</span>
              </div>
              <Dialog.Close asChild>
                <button type="button" aria-label="Fermer" onClick={onClose} className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-studio-subtle transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </Dialog.Close>
            </div>

            <div className="p-5 space-y-5 flex-1 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-gray-700 uppercase text-[10px] tracking-wider">Prompt original</span>
                  <button type="button" onClick={() => copyText(generation.prompt, setCopiedPrompt)} aria-label="Copier le prompt" className="text-gray-500 hover:text-indigo-600 flex items-center gap-1 transition-colors">
                    {copiedPrompt ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedPrompt ? 'Copié !' : 'Copier'}</span>
                  </button>
                </div>
                <div className="bg-studio-canvas p-3 rounded-dock border border-studio-border text-gray-800 leading-relaxed max-h-36 overflow-y-auto select-text">
                  {generation.prompt}
                </div>
              </div>

              {generation.compiledPrompt && (
                <div>
                  <span className="font-semibold text-gray-700 uppercase text-[10px] tracking-wider block mb-1.5 flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-indigo-500" /> Prompt compilé (BrandKit)
                  </span>
                  <div className="bg-indigo-50/50 p-3 rounded-dock border border-indigo-100 text-indigo-900 leading-relaxed max-h-36 overflow-y-auto select-text">
                    {generation.compiledPrompt}
                  </div>
                </div>
              )}

              {generation.brandKitSnapshot && (
                <div>
                  <span className="font-semibold text-gray-700 uppercase text-[10px] tracking-wider block mb-1.5 flex items-center gap-1">
                    <Layers className="w-3 h-3 text-purple-500" /> Snapshot BrandKit
                  </span>
                  <div className="bg-purple-50/50 p-2.5 rounded-dock border border-purple-100 space-y-1">
                    <div className="font-medium text-purple-900">{generation.brandKitSnapshot.name}</div>
                    {generation.brandKitSnapshot.overview && (
                      <div className="text-[11px] text-purple-700">{generation.brandKitSnapshot.overview}</div>
                    )}
                  </div>
                </div>
              )}

              <div>
                <span className="font-semibold text-gray-700 uppercase text-[10px] tracking-wider block mb-2">Paramètres de génération</span>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  {[
                    { label: 'Seed', val: generation.parameters?.seed ?? 'Aléatoire' },
                    { label: 'Ratio', val: generation.parameters?.aspectRatio || '16:9' },
                    { label: 'Résolution', val: generation.parameters?.resolution || 'HD' },
                    { label: 'Durée', val: generation.parameters?.duration || '5s' },
                  ].map((p) => (
                    <div key={p.label} className="bg-studio-canvas p-2 rounded border border-studio-border">
                      <span className="text-gray-400 block text-[10px]">{p.label}</span>
                      <span className="font-semibold text-gray-800">{p.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-gray-700 uppercase text-[10px] tracking-wider flex items-center gap-1">
                    <Folder className="w-3 h-3 text-gray-400" /> Chemin de sortie
                  </span>
                  <button type="button" onClick={() => copyText(generation.filePath || '', setCopiedPath)} aria-label="Copier le chemin" className="text-gray-500 hover:text-indigo-600 flex items-center gap-1 transition-colors">
                    {copiedPath ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedPath ? 'Copié !' : 'Copier'}</span>
                  </button>
                </div>
                <div className="bg-studio-canvas p-2 rounded border border-studio-border text-gray-600 font-mono text-[11px] truncate select-all">
                  {generation.filePath}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-studio-border bg-studio-canvas space-y-2">
              <div className="flex items-center gap-2">
                <button type="button" onClick={handleToggleFavorite} disabled={isUpdatingFavorite} aria-label={generation.isFavorite ? 'Retirer des favoris' : 'Favori'} className={`flex-1 h-9 rounded-full border text-xs font-medium flex items-center justify-center gap-1.5 transition-colors ${generation.isFavorite ? 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100' : 'bg-white border-studio-border text-gray-700 hover:bg-gray-50'}`}>
                  <Star className={`w-3.5 h-3.5 ${generation.isFavorite ? 'fill-amber-400 text-amber-400' : 'text-gray-400'}`} />
                  <span>Favori</span>
                </button>
                <a href={generation.filePath || '#'} download className="flex-1 h-9 rounded-full border border-studio-border bg-white hover:bg-gray-50 text-gray-700 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors">
                  <Download className="w-3.5 h-3.5 text-gray-500" />
                  <span>Télécharger</span>
                </a>
              </div>
              <button type="button" onClick={() => onRemix(generation)} aria-label="Remix" className="w-full h-10 rounded-full bg-gray-900 hover:bg-black text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Remix</span>
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
