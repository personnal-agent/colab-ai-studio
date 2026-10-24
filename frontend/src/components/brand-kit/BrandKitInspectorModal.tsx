import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {
  X, Sparkles, Image as ImageIcon, Palette, Type, FolderOpen, Mic,
  MessageSquare, ShieldCheck, CheckCircle2, XCircle, Check,
} from 'lucide-react';
import type { BrandKit } from '../../types/studio';

export interface BrandKitInspectorModalProps {
  brandKit: BrandKit | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectBrandKit: (kit: BrandKit) => void;
}

type SectionKey = 'overview' | 'logos' | 'colors' | 'fonts' | 'reference images' | 'voices' | 'captions' | 'guidelines';

const SECTIONS: { key: SectionKey; label: string; icon: React.ElementType }[] = [
  { key: 'overview', label: 'Overview', icon: Sparkles },
  { key: 'logos', label: 'Logos', icon: ImageIcon },
  { key: 'colors', label: 'Colors', icon: Palette },
  { key: 'fonts', label: 'Fonts', icon: Type },
  { key: 'reference images', label: 'Reference images', icon: FolderOpen },
  { key: 'voices', label: 'Voices', icon: Mic },
  { key: 'captions', label: 'Captions', icon: MessageSquare },
  { key: 'guidelines', label: 'Guidelines', icon: ShieldCheck },
];

export const BrandKitInspectorModal: React.FC<BrandKitInspectorModalProps> = ({
  brandKit, isOpen, onClose, onSelectBrandKit,
}) => {
  const [activeSection, setActiveSection] = useState<SectionKey>('overview');
  if (!brandKit) return null;

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-in fade-in-0 duration-150" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl h-[85vh] max-h-[700px] bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-800 flex overflow-hidden z-50 text-gray-900 dark:text-gray-100 outline-none animate-in fade-in-50 zoom-in-95 duration-150">
          <aside className="w-56 bg-gray-50/70 dark:bg-gray-950/40 border-r border-gray-100 dark:border-gray-800 flex flex-col justify-between p-4 flex-shrink-0">
            <div>
              <div className="flex items-center space-x-2.5 mb-6 px-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                  {brandKit.name.slice(0, 1)}
                </div>
                <div className="min-w-0">
                  <Dialog.Title className="text-sm font-bold truncate">{brandKit.name}</Dialog.Title>
                  <p className="text-[11px] text-gray-400">Brand Kit Identity</p>
                </div>
              </div>
              <nav className="space-y-1">
                {SECTIONS.map((sec) => {
                  const Icon = sec.icon;
                  const isActive = activeSection === sec.key;
                  return (
                    <button
                      key={sec.key} type="button" aria-label={sec.label} onClick={() => setActiveSection(sec.key)}
                      className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-colors text-left ${isActive ? 'bg-black text-white dark:bg-white dark:text-black shadow-sm font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/60'}`}
                    >
                      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                      <span className="truncate">{sec.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
            <div className="pt-4 border-t border-gray-200/60 dark:border-gray-800">
              <button
                type="button" onClick={() => { onSelectBrandKit(brandKit); onClose(); }}
                className="w-full flex items-center justify-center space-x-1.5 py-2.5 px-3 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white rounded-xl text-xs font-semibold shadow-md transition-all"
              >
                <Check className="w-4 h-4" /><span>Use this brand kit</span>
              </button>
            </div>
          </aside>
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-white dark:bg-gray-900">
            <header className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
              <div>
                <h3 className="text-base font-bold capitalize">{activeSection}</h3>
                <p className="text-xs text-gray-400">Inspection et configuration des actifs de la marque {brandKit.name}.</p>
              </div>
              <Dialog.Close asChild>
                <button type="button" aria-label="Close" className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </header>
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeSection === 'overview' && (
                <div className="space-y-6">
                  <div className="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Brand Overview & Narrative</h4>
                    <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{brandKit.overview || 'Aucun brief narratif renseigné.'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Logos ({brandKit.logos?.length || 0})</h4>
                      <div className="flex items-center space-x-2">
                        {brandKit.logos?.slice(0, 3).map((l) => (
                          <span key={l.id} className="text-xs px-2.5 py-1 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">{l.label}</span>
                        ))}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Color Palette ({brandKit.colors?.length || 0})</h4>
                      <div className="flex items-center space-x-2">
                        {brandKit.colors?.map((c, i) => (
                          <div key={i} title={`${c.hex} - ${c.label}`} style={{ backgroundColor: c.hex }} className="w-6 h-6 rounded-full border border-gray-200 dark:border-gray-700 shadow-sm" />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {activeSection === 'logos' && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {brandKit.logos?.length ? (
                    brandKit.logos.map((logo) => (
                      <div key={logo.id} className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-800 flex flex-col items-center justify-center text-center space-y-2">
                        <div className="w-16 h-16 bg-white dark:bg-gray-900 rounded-xl flex items-center justify-center border border-gray-200 dark:border-gray-700 overflow-hidden p-2">
                          <img src={logo.filePath} alt={logo.label} className="max-w-full max-h-full object-contain" onError={(e) => { (e.currentTarget as HTMLElement).style.display = 'none'; }} />
                          <ImageIcon className="w-6 h-6 text-gray-400" />
                        </div>
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{logo.label}</span>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400 col-span-full">Aucun logo configuré.</p>}
                </div>
              )}
              {activeSection === 'colors' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {brandKit.colors?.length ? (
                    brandKit.colors.map((color, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-800 flex items-center space-x-3">
                        <div style={{ backgroundColor: color.hex }} className="w-10 h-10 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center space-x-1.5">
                            <span className="text-xs font-mono font-bold text-gray-900 dark:text-gray-100">{color.hex}</span>
                            {color.isDominant && <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">Dominant</span>}
                          </div>
                          <p className="text-xs text-gray-500 truncate">{color.label}</p>
                        </div>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400 col-span-full">Aucune couleur configurée.</p>}
                </div>
              )}
              {activeSection === 'fonts' && (
                <div className="space-y-3">
                  {brandKit.fonts?.length ? (
                    brandKit.fonts.map((font, idx) => (
                      <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-800 flex items-center justify-between">
                        <div><p className="text-sm font-semibold">{font.family}</p><p className="text-xs text-gray-500">{font.weight}</p></div>
                        <span className="text-xs font-mono text-gray-400">Aa Bb Cc 123</span>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400">Aucune police configurée.</p>}
                </div>
              )}
              {activeSection === 'reference images' && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {brandKit.referenceImages?.length ? (
                    brandKit.referenceImages.map((asset) => (
                      <div key={asset.id} className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700 relative group">
                        <img src={asset.filePath} alt="Brand reference" className="w-full h-full object-cover" onError={(e) => { (e.currentTarget as HTMLElement).style.display = 'none'; }} />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity">
                          <span className="text-xs text-white font-mono">{asset.id}</span>
                        </div>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400 col-span-full">Aucune image de référence enregistrée.</p>}
                </div>
              )}
              {activeSection === 'voices' && (
                <div className="space-y-2">
                  {brandKit.voices?.length ? (
                    brandKit.voices.map((v, i) => (
                      <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800 flex items-center space-x-3">
                        <Mic className="w-4 h-4 text-indigo-500" /><span className="text-xs font-medium">{String(v.name || v.id || `Voice profile #${i + 1}`)}</span>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400">Aucun profil vocal configuré.</p>}
                </div>
              )}
              {activeSection === 'captions' && (
                <div className="space-y-2">
                  {brandKit.captions?.length ? (
                    brandKit.captions.map((cap, i) => (
                      <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800 flex items-center space-x-3">
                        <MessageSquare className="w-4 h-4 text-purple-500" /><span className="text-xs font-medium">{String(cap.format || cap.style || `Caption template #${i + 1}`)}</span>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400">Aucun modèle de sous-titres.</p>}
                </div>
              )}
              {activeSection === 'guidelines' && (
                <div className="space-y-3">
                  {brandKit.guidelines?.length ? (
                    brandKit.guidelines.map((guide, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-2xl border flex items-start space-x-3 ${guide.kind === 'do' ? 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800' : 'bg-rose-50/60 dark:bg-rose-950/20 border-rose-200 dark:border-rose-800'}`}
                      >
                        {guide.kind === 'do' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${guide.kind === 'do' ? 'bg-emerald-200 dark:bg-emerald-800 text-emerald-900 dark:text-emerald-100' : 'bg-rose-200 dark:bg-rose-800 text-rose-900 dark:text-rose-100'}`}>
                            {guide.kind === 'do' ? 'Do' : "Don't"}
                          </span>
                          <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">{guide.text}</p>
                        </div>
                      </div>
                    ))
                  ) : <p className="text-xs text-gray-400">Aucune directive de marque.</p>}
                </div>
              )}
            </div>
          </main>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
