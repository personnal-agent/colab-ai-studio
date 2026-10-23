import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {
  X,
  FileText,
  Image as ImageIcon,
  Palette,
  Type,
  Camera,
  Mic,
  Subtitles,
  ShieldAlert,
  Check,
} from 'lucide-react';
import type { BrandKit } from '../../types/studio';

export type BrandKitSection =
  | 'Overview'
  | 'Logos'
  | 'Colors'
  | 'Fonts'
  | 'Reference images'
  | 'Voices'
  | 'Captions'
  | 'Guidelines';

interface BrandKitInspectorModalProps {
  isOpen: boolean;
  kit: BrandKit | null;
  onClose: () => void;
  onUseKit: (kit: BrandKit) => void;
}

const SECTIONS: { id: BrandKitSection; label: string; icon: React.ReactNode }[] = [
  { id: 'Overview', label: 'Overview', icon: <FileText className="w-4 h-4" /> },
  { id: 'Logos', label: 'Logos', icon: <ImageIcon className="w-4 h-4" /> },
  { id: 'Colors', label: 'Colors', icon: <Palette className="w-4 h-4" /> },
  { id: 'Fonts', label: 'Fonts', icon: <Type className="w-4 h-4" /> },
  { id: 'Reference images', label: 'Reference images', icon: <Camera className="w-4 h-4" /> },
  { id: 'Voices', label: 'Voices', icon: <Mic className="w-4 h-4" /> },
  { id: 'Captions', label: 'Captions', icon: <Subtitles className="w-4 h-4" /> },
  { id: 'Guidelines', label: 'Guidelines', icon: <ShieldAlert className="w-4 h-4" /> },
];

export const BrandKitInspectorModal: React.FC<BrandKitInspectorModalProps> = ({
  isOpen,
  kit,
  onClose,
  onUseKit,
}) => {
  const [activeSection, setActiveSection] = useState<BrandKitSection>('Overview');

  if (!kit) return null;

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl h-[640px] max-h-[90vh] bg-white rounded-2xl shadow-2xl border border-studio-border z-50 flex flex-col overflow-hidden focus:outline-none">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-studio-border shrink-0">
            <div className="flex items-center gap-3">
              {kit.logoPath ? (
                <img
                  src={kit.logoPath}
                  alt={kit.name}
                  className="w-8 h-8 rounded-lg object-contain bg-studio-subtle p-0.5 border border-studio-border"
                />
              ) : (
                <div className="w-8 h-8 rounded-lg bg-studio-text text-white font-bold text-sm flex items-center justify-center">
                  {kit.name.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <Dialog.Title className="text-base font-bold text-studio-text">
                  {kit.name}
                </Dialog.Title>
                <Dialog.Description className="text-xs text-studio-muted">
                  ADN de marque & Charte de génération automatisée
                </Dialog.Description>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label="Use this brand kit"
                onClick={() => {
                  onUseKit(kit);
                  onClose();
                }}
                className="px-4 py-1.5 rounded-pill bg-studio-text text-white text-xs font-semibold hover:bg-black transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Use this brand kit</span>
              </button>

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
          </div>

          {/* Corps avec navigation latérale à 8 sections */}
          <div className="flex flex-1 min-h-0">
            {/* Colonne latérale */}
            <aside className="w-52 border-r border-studio-border p-3 flex flex-col gap-1 bg-studio-subtle/30 shrink-0 overflow-y-auto">
              {SECTIONS.map((section) => {
                const isActive = section.id === activeSection;
                return (
                  <button
                    key={section.id}
                    type="button"
                    aria-label={section.label}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-studio-text text-white'
                        : 'text-studio-text hover:bg-studio-subtle'
                    }`}
                  >
                    {section.icon}
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </aside>

            {/* Zone centrale de contenu */}
            <main className="flex-1 p-6 overflow-y-auto">
              {activeSection === 'Overview' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Synthèse de la marque</h3>
                  <p className="text-xs text-studio-text leading-relaxed bg-studio-subtle/50 p-4 rounded-xl border border-studio-border">
                    {kit.overview || 'Aucune synthèse disponible.'}
                  </p>

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="p-3 bg-white border border-studio-border rounded-xl">
                      <span className="text-xs font-semibold text-studio-muted block mb-1">
                        Couleurs primaires
                      </span>
                      <div className="flex items-center gap-1.5">
                        {kit.palette.map((c, i) => (
                          <div
                            key={i}
                            title={`${c.name} (${c.hex})`}
                            className="w-6 h-6 rounded-md border border-black/10"
                            style={{ backgroundColor: c.hex }}
                          />
                        ))}
                      </div>
                    </div>

                    <div className="p-3 bg-white border border-studio-border rounded-xl">
                      <span className="text-xs font-semibold text-studio-muted block mb-1">
                        Typographies
                      </span>
                      <div className="text-xs text-studio-text">
                        {kit.fonts.join(', ') || 'Polices par défaut'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'Logos' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Logos officiels</h3>
                  {kit.logoPath ? (
                    <div className="p-6 bg-studio-subtle rounded-xl border border-studio-border flex items-center justify-center max-w-xs">
                      <img src={kit.logoPath} alt={kit.name} className="max-h-24 object-contain" />
                    </div>
                  ) : (
                    <p className="text-xs text-studio-muted">Aucun logo téléversé.</p>
                  )}
                </div>
              )}

              {activeSection === 'Colors' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Nuancier et palettes</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {kit.palette.map((color, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-white border border-studio-border rounded-xl flex items-center gap-3 shadow-2xs"
                      >
                        <div
                          className="w-10 h-10 rounded-lg border border-black/10 shrink-0"
                          style={{ backgroundColor: color.hex }}
                        />
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-studio-text block truncate">
                            {color.name}
                          </span>
                          <span className="text-[11px] font-mono text-studio-muted">
                            {color.hex}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeSection === 'Fonts' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Polices et typographies</h3>
                  <div className="space-y-2">
                    {kit.fonts.map((font, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-studio-subtle/50 border border-studio-border rounded-xl flex items-center justify-between"
                      >
                        <span className="text-sm font-medium">{font}</span>
                        <span className="text-xs text-studio-muted">Display & Body</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeSection === 'Reference images' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Photothèque & Références</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {kit.referenceImages.map((img, idx) => (
                      <img
                        key={idx}
                        src={img}
                        alt={`Ref ${idx + 1}`}
                        className="w-full h-28 object-cover rounded-xl border border-studio-border"
                      />
                    ))}
                    {kit.referenceImages.length === 0 && (
                      <p className="text-xs text-studio-muted col-span-3">
                        Aucune image de référence associée.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {activeSection === 'Voices' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Profils vocaux & TTS</h3>
                  <p className="text-xs text-studio-muted">
                    Profils vocaux d'identité de marque synchronisés pour les générations Lip Sync.
                  </p>
                </div>
              )}

              {activeSection === 'Captions' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Sous-titres & Accroches</h3>
                  <p className="text-xs text-studio-muted">
                    Directives de sous-titrage et mentions obligatoires de marque.
                  </p>
                </div>
              )}

              {activeSection === 'Guidelines' && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-studio-text">Directives Do's & Don'ts</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-emerald-700 flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5" /> À privilégier (Do's)
                      </h4>
                      <ul className="space-y-1.5 text-xs text-studio-text">
                        {kit.dos.map((d, i) => (
                          <li key={i} className="p-2 bg-emerald-50 rounded-lg border border-emerald-200">
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-red-700 flex items-center gap-1.5">
                        <X className="w-3.5 h-3.5" /> À proscrire (Don'ts)
                      </h4>
                      <ul className="space-y-1.5 text-xs text-studio-text">
                        {kit.donts.map((d, i) => (
                          <li key={i} className="p-2 bg-red-50 rounded-lg border border-red-200">
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </main>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
