import * as Dialog from '@radix-ui/react-dialog';
import { HelpCircle, Play, X } from 'lucide-react';
import { useState } from 'react';

export function AskHelpDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label="Ask - Aide et documentation"
          className="px-3 py-1.5 rounded-pill text-xs font-medium bg-studio-subtle hover:bg-studio-active text-gray-700 flex items-center gap-1.5 transition-colors border border-studio-border"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Ask</span>
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-in fade-in" />
        <Dialog.Content className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right">
          <div>
            <div className="flex items-center justify-between border-b border-studio-border pb-4">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-gray-700" />
                <Dialog.Title className="text-lg font-semibold text-gray-900">
                  Guide Colab AI Studio
                </Dialog.Title>
              </div>
              <Dialog.Close asChild>
                <button
                  type="button"
                  aria-label="Fermer"
                  className="p-1 rounded-slot hover:bg-studio-subtle text-gray-500"
                >
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>

            <div className="mt-6 space-y-5 text-sm text-gray-600">
              <section>
                <h3 className="font-semibold text-gray-900 mb-1">
                  1. Pôles de Création Multimodale
                </h3>
                <p>
                  Basculez entre Image, Vidéo, Lip Sync et Upscale 4K via les onglets du dock
                  inférieur flottant.
                </p>
              </section>

              <section>
                <h3 className="font-semibold text-gray-900 mb-1">
                  2. Brand Kit & Cohérence de Marque
                </h3>
                <p>
                  Invoquez votre kit de marque avec le bouton <code>@ Brand Kit</code> pour injecter
                  automatiquement palettes, polices et règles Do/Don&apos;t dans le prompt
                  cinématique en anglais.
                </p>
              </section>

              <section>
                <h3 className="font-semibold text-gray-900 mb-1">
                  3. Stockage Sécurisé & Projets
                </h3>
                <p>
                  Tous les fichiers générés sont rapatriés automatiquement sur votre machine. Créez
                  un projet pour isoler vos rendus dans un dossier personnalisé (
                  <code>storagePath</code>).
                </p>
              </section>

              <section>
                <h3 className="font-semibold text-gray-900 mb-1">4. Fonction Remix</h3>
                <p>
                  Cliquez sur n&apos;importe quel média dans la galerie pour inspecter sa fiche
                  technique exacte et rechargez ses paramètres d&apos;inférence d&apos;un clic sur{' '}
                  <strong>Remix</strong>.
                </p>
              </section>
            </div>
          </div>

          <div className="border-t border-studio-border pt-4 text-xs text-gray-400">
            Colab AI Studio v1.0.0 — Contrôleur de Génération Hybride
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
