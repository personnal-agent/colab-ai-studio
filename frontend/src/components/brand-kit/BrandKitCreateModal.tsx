import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Globe, UploadCloud, FileEdit } from 'lucide-react';

export type CreateBrandKitMethod = 'blank' | 'files' | 'website';

export interface CreateBrandKitData {
  method: CreateBrandKitMethod;
  name: string;
  websiteUrl?: string;
  files?: File[];
}

interface BrandKitCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onContinue: (data: CreateBrandKitData) => void;
}

export const BrandKitCreateModal: React.FC<BrandKitCreateModalProps> = ({
  isOpen,
  onClose,
  onContinue,
}) => {
  const [method, setMethod] = useState<CreateBrandKitMethod>('blank');
  const [name, setName] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleContinue = (e: React.FormEvent) => {
    e.preventDefault();
    onContinue({
      method,
      name: name.trim() || (method === 'website' && websiteUrl ? new URL(websiteUrl).hostname : 'New Brand Kit'),
      websiteUrl: method === 'website' ? websiteUrl : undefined,
      files: method === 'files' ? selectedFiles : undefined,
    });
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-studio-border p-6 z-50 focus:outline-none space-y-5">
          <div className="flex items-center justify-between border-b border-studio-border pb-3">
            <div>
              <Dialog.Title className="text-base font-bold text-studio-text">
                Create brand kit
              </Dialog.Title>
              <Dialog.Description className="text-xs text-studio-muted">
                Définissez l'identité visuelle et stylistique de votre marque
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Fermer"
                className="p-1.5 rounded-full text-studio-muted hover:text-studio-text hover:bg-studio-subtle transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* 3 Méthodes d'initialisation */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-studio-text">Create from</span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                aria-label="Blank"
                onClick={() => setMethod('blank')}
                className={`py-2 px-3 rounded-xl border text-xs font-medium flex flex-col items-center gap-1.5 transition-colors cursor-pointer ${
                  method === 'blank'
                    ? 'border-studio-text bg-studio-subtle text-studio-text'
                    : 'border-studio-border text-studio-muted hover:border-studio-text/40'
                }`}
              >
                <FileEdit className="w-4 h-4" />
                <span>Blank</span>
              </button>

              <button
                type="button"
                aria-label="Brand files"
                onClick={() => setMethod('files')}
                className={`py-2 px-3 rounded-xl border text-xs font-medium flex flex-col items-center gap-1.5 transition-colors cursor-pointer ${
                  method === 'files'
                    ? 'border-studio-text bg-studio-subtle text-studio-text'
                    : 'border-studio-border text-studio-muted hover:border-studio-text/40'
                }`}
              >
                <UploadCloud className="w-4 h-4" />
                <span>Brand files</span>
              </button>

              <button
                type="button"
                aria-label="Website"
                onClick={() => setMethod('website')}
                className={`py-2 px-3 rounded-xl border text-xs font-medium flex flex-col items-center gap-1.5 transition-colors cursor-pointer ${
                  method === 'website'
                    ? 'border-studio-text bg-studio-subtle text-studio-text'
                    : 'border-studio-border text-studio-muted hover:border-studio-text/40'
                }`}
              >
                <Globe className="w-4 h-4" />
                <span>Website</span>
              </button>
            </div>
          </div>

          {/* Contenu spécifique selon la méthode */}
          <form onSubmit={handleContinue} className="space-y-4">
            <div className="space-y-1">
              <label htmlFor="brand-kit-name" className="block text-xs font-medium text-studio-text">
                Nom de la marque
              </label>
              <input
                id="brand-kit-name"
                type="text"
                placeholder="ex: Apple, Nike, Mon Studio..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-studio-border rounded-lg text-xs focus:ring-1 focus:ring-studio-text focus:outline-none"
              />
            </div>

            {method === 'files' && (
              <div className="space-y-1">
                <span className="block text-xs font-medium text-studio-text">
                  Fichiers de marque (PDF, images, .fig)
                </span>
                <label className="border-2 border-dashed border-studio-border hover:border-studio-text/50 rounded-xl p-5 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors bg-studio-subtle/50">
                  <UploadCloud className="w-6 h-6 text-studio-muted" />
                  <span className="text-xs text-studio-muted">
                    Glissez vos chartes graphiques ou cliquez pour parcourir
                  </span>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg,.svg,.fig"
                    onChange={(e) => {
                      if (e.target.files) {
                        setSelectedFiles(Array.from(e.target.files));
                      }
                    }}
                    className="hidden"
                  />
                  {selectedFiles.length > 0 && (
                    <span className="text-xs font-semibold text-studio-text">
                      {selectedFiles.length} fichier(s) sélectionné(s)
                    </span>
                  )}
                </label>
              </div>
            )}

            {method === 'website' && (
              <div className="space-y-1">
                <label htmlFor="brand-kit-url" className="block text-xs font-medium text-studio-text">
                  Site internet officiel
                </label>
                <input
                  id="brand-kit-url"
                  type="url"
                  placeholder="https://example.com"
                  value={websiteUrl}
                  onChange={(e) => setWebsiteUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-studio-border rounded-lg text-xs focus:ring-1 focus:ring-studio-text focus:outline-none"
                  required
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-studio-border">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-pill text-xs font-medium text-studio-muted hover:bg-studio-subtle transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                aria-label="Continue"
                className="px-5 py-2 rounded-pill bg-studio-text text-white text-xs font-semibold hover:bg-black transition-colors"
              >
                Continue
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
