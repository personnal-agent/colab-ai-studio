import React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { HelpCircle, Play, X } from 'lucide-react';

export const AskHelpDrawer: React.FC = () => {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button type="button" aria-label="Ask - Centre d'aide" className="h-9 px-3.5 rounded-full border border-studio-border bg-white text-gray-700 hover:bg-studio-subtle text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm">
          <Play className="w-3.5 h-3.5 fill-current text-indigo-600" /><span>Ask</span>
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/45 z-40 backdrop-blur-sm animate-in fade-in" />
        <Dialog.Content className="fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 p-6 shadow-2xl flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-studio-border pb-4">
              <div className="flex items-center gap-2"><HelpCircle className="w-5 h-5 text-indigo-600" /><Dialog.Title className="text-lg font-semibold text-gray-900">Centre d'aide & Documentation</Dialog.Title></div>
              <Dialog.Close asChild><button type="button" aria-label="Fermer" className="p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-studio-subtle"><X className="w-5 h-5" /></button></Dialog.Close>
            </div>
            <div className="space-y-4 text-sm text-gray-600">
              <section className="space-y-2">
                <h2 className="text-sm font-semibold text-gray-900">Foire Aux Questions</h2>
                <p><strong>Floating Dock :</strong> Rassemble commandes, ratios, pôle et bouton générer.</p>
                <p><strong>Colab vs Local :</strong> Déport sur GPU Cloud (Tesla T4) vs machine hôte.</p>
              </section>
              <section className="space-y-2">
                <h2 className="text-sm font-semibold text-gray-900">Gestion de la VRAM</h2>
                <p>Le worker GPU bascule automatiquement les modèles. Une seule génération GPU active à la fois.</p>
              </section>
              <section className="space-y-2">
                <h2 className="text-sm font-semibold text-gray-900">Isolation des Projets</h2>
                <p>Les générations associées à un projet avec <code>storagePath</code> y sont stockées exclusivement.</p>
              </section>
            </div>
          </div>
          <div className="pt-6 border-t border-studio-border text-xs text-gray-500">Colab AI Studio — Version 0.3.0</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
