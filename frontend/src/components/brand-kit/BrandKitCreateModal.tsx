import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, UploadCloud, Globe, Sparkles, Loader2, FileText } from 'lucide-react';
import type { BrandKit } from '../../types/studio';

export interface BrandKitCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateBrandKit: (data: {
    source: 'blank' | 'website' | 'files';
    name: string;
    overview?: string;
    url?: string;
    files?: File[];
  }) => Promise<BrandKit>;
  onSuccess: (createdKit: BrandKit) => void;
}

type CreateSource = 'blank' | 'files' | 'website';

export const BrandKitCreateModal: React.FC<BrandKitCreateModalProps> = ({
  isOpen, onClose, onCreateBrandKit, onSuccess,
}) => {
  const [source, setSource] = useState<CreateSource>('blank');
  const [name, setName] = useState('');
  const [overview, setOverview] = useState('');
  const [url, setUrl] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setSource('blank'); setName(''); setOverview(''); setUrl(''); setFiles([]); setError(null); setIsSubmitting(false);
  };

  const handleClose = () => {
    if (isSubmitting) return;
    resetForm();
    onClose();
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles((prev) => [...prev, ...newFiles]);
      if (!name && newFiles[0]) {
        const baseName = newFiles[0].name.replace(/\.[^/.]+$/, '');
        setName(baseName.charAt(0).toUpperCase() + baseName.slice(1));
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
      if (!name && newFiles[0]) {
        const baseName = newFiles[0].name.replace(/\.[^/.]+$/, '');
        setName(baseName.charAt(0).toUpperCase() + baseName.slice(1));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const kitName = name.trim();
    if (!kitName) { setError('Veuillez spécifier un nom pour ce brand kit.'); return; }
    if (source === 'website' && !url.trim()) { setError('Veuillez entrer une adresse de site web valide.'); return; }
    if (source === 'files' && files.length === 0) { setError('Veuillez déposer au moins un fichier ou asset de marque.'); return; }

    setIsSubmitting(true);
    try {
      const createdKit = await onCreateBrandKit({
        source, name: kitName, overview: overview.trim() || undefined,
        url: source === 'website' ? url.trim() : undefined,
        files: source === 'files' ? files : undefined,
      });
      resetForm();
      onSuccess(createdKit);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue lors de la création.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in-0 duration-150" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-800 p-6 z-50 text-gray-900 dark:text-gray-100 outline-none animate-in fade-in-50 zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
            <div>
              <Dialog.Title className="text-lg font-bold">Create Brand Kit</Dialog.Title>
              <Dialog.Description className="text-xs text-gray-500 dark:text-gray-400">
                Initialisez l’identité de marque pour conditionner automatiquement vos modèles.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" disabled={isSubmitting} className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          <div className="grid grid-cols-3 gap-2 mt-4 p-1 bg-gray-100 dark:bg-gray-800/80 rounded-2xl">
            <button
              type="button" onClick={() => setSource('blank')}
              className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${source === 'blank' ? 'bg-white dark:bg-gray-900 text-black dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}`}
            >
              <Sparkles className="w-3.5 h-3.5" /><span>Blank</span>
            </button>
            <button
              type="button" onClick={() => setSource('files')}
              className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${source === 'files' ? 'bg-white dark:bg-gray-900 text-black dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}`}
            >
              <UploadCloud className="w-3.5 h-3.5" /><span>Brand files</span>
            </button>
            <button
              type="button" onClick={() => setSource('website')}
              className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${source === 'website' ? 'bg-white dark:bg-gray-900 text-black dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}`}
            >
              <Globe className="w-3.5 h-3.5" /><span>Website</span>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-xs rounded-xl border border-red-200 dark:border-red-800">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="brand-kit-name" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Brand name *</label>
              <input
                id="brand-kit-name" type="text" required value={name} onChange={(e) => setName(e.target.value)}
                placeholder="Brand name (e.g. Apple, Nike, Acme)"
                className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white"
              />
            </div>
            {source === 'website' && (
              <div>
                <label htmlFor="brand-kit-url" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Website URL *</label>
                <div className="relative">
                  <Globe className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
                  <input
                    id="brand-kit-url" type="url" required value={url} onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white"
                  />
                </div>
                <p className="text-[11px] text-gray-500 mt-1">Extraction automatique des logos, polices et couleurs CSS depuis l’URL.</p>
              </div>
            )}
            {source === 'files' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Brand files & assets (PDF, images, .fig) *</label>
                <div
                  onDragOver={(e) => e.preventDefault()} onDrop={handleFileDrop}
                  className="border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-2xl p-4 text-center hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <UploadCloud className="w-8 h-8 mx-auto mb-1 text-gray-400" />
                  <p className="text-xs text-gray-600 dark:text-gray-300">
                    Glissez-déposez vos fichiers de marque ou{' '}
                    <label className="text-indigo-600 dark:text-indigo-400 underline cursor-pointer">
                      parcourez
                      <input type="file" multiple accept="image/*,.pdf,.fig" className="hidden" onChange={handleFileInputChange} />
                    </label>
                  </p>
                  <p className="text-[10px] text-gray-400 mt-0.5">Images (.png, .jpg, .svg), chartes PDF ou fichiers Figma.</p>
                </div>
                {files.length > 0 && (
                  <div className="mt-2 space-y-1 max-h-24 overflow-y-auto">
                    {files.map((file, i) => (
                      <div key={i} className="flex items-center justify-between text-xs py-1 px-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center space-x-1.5 truncate">
                          <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" /><span className="truncate">{file.name}</span>
                        </div>
                        <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="text-gray-400 hover:text-red-500 ml-2">&times;</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div>
              <label htmlFor="brand-kit-overview" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Brief / Overview (optionnel)</label>
              <textarea
                id="brand-kit-overview" rows={2} value={overview} onChange={(e) => setOverview(e.target.value)}
                placeholder="Description narrative, positionnement ou mission..."
                className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white resize-none"
              />
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-gray-100 dark:border-gray-800">
              <button
                type="button" onClick={handleClose} disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit" disabled={isSubmitting}
                className="inline-flex items-center space-x-1.5 px-5 py-2 bg-black text-white dark:bg-white dark:text-black text-xs font-semibold rounded-full hover:opacity-90 active:scale-95 transition-all shadow-md disabled:opacity-50"
              >
                {isSubmitting ? (<><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Extraction...</span></>) : (<span>Continue</span>)}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
