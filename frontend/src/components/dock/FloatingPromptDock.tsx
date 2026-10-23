import React, { useState, useMemo } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { ArrowUp, Loader2 } from 'lucide-react';
import type {
  ModelDefinition,
  BrandKit,
  GenerationParameters,
  GenerationReferences,
} from '../../types/studio';
import { ConditioningTray } from './slots/ConditioningTray';
import { PromptEditorWithChip } from '../brand-kit/PromptEditorWithChip';
import { BrandKitSelectorPopover } from '../brand-kit/BrandKitSelectorPopover';
import { BrandKitCreateModal, CreateBrandKitData } from '../brand-kit/BrandKitCreateModal';
import { BrandKitInspectorModal } from '../brand-kit/BrandKitInspectorModal';
import { ParameterRegistry } from './controls/ParameterRegistry';
import { LlmChatView } from './llm/LlmChatView';
import { ModelSelectorPopover } from './controls/ModelSelectorPopover';

export type DockMode = 'image' | 'video' | 'lip_sync' | 'upscale' | 'llm';

export interface SubmitTaskPayload {
  modelId: string;
  mediaType: string;
  prompt: string;
  parameters: GenerationParameters;
  references: GenerationReferences;
  brandKitId?: string | null;
}

interface ModeDraft {
  prompt: string;
  modelId: string;
  parameters: GenerationParameters;
  references: GenerationReferences;
}

interface FloatingPromptDockProps {
  models: ModelDefinition[];
  brandKits?: BrandKit[];
  isGenerating?: boolean;
  onSubmitTask: (payload: SubmitTaskPayload) => void;
  onCreateBrandKit?: (data: CreateBrandKitData) => Promise<BrandKit>;
}

const DEFAULT_PARAMS: GenerationParameters = {
  seed: -1,
  aspectRatio: '16:9',
  resolution: '720p',
  duration: '5s',
  audio: true,
  enhance: true,
  batchCount: 1,
};

export const FloatingPromptDock: React.FC<FloatingPromptDockProps> = ({
  models,
  brandKits = [],
  isGenerating = false,
  onSubmitTask,
  onCreateBrandKit,
}) => {
  const [activeTab, setActiveTab] = useState<DockMode>('video');
  const [selectedKit, setSelectedKit] = useState<BrandKit | null>(null);

  // Modales Brand Kit
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [inspectedKit, setInspectedKit] = useState<BrandKit | null>(null);

  // Pseudo-état d'Historique [H] : sauvegarde du brouillon par onglet
  const [drafts, setDrafts] = useState<Record<DockMode, ModeDraft>>(() => {
    const findDefaultModel = (type: string) =>
      models.find((m) => m.mediaType.toLowerCase() === type.toLowerCase())?.id || models[0]?.id || '';

    return {
      image: {
        prompt: '',
        modelId: findDefaultModel('image'),
        parameters: { ...DEFAULT_PARAMS, resolution: '1K', duration: '' },
        references: {},
      },
      video: {
        prompt: '',
        modelId: findDefaultModel('video'),
        parameters: { ...DEFAULT_PARAMS },
        references: {},
      },
      lip_sync: {
        prompt: '',
        modelId: findDefaultModel('lip_sync'),
        parameters: { ...DEFAULT_PARAMS, talkingStyle: 'Stable' },
        references: {},
      },
      upscale: {
        prompt: '',
        modelId: findDefaultModel('upscale'),
        parameters: { ...DEFAULT_PARAMS, scaleFactor: '2x', upscaleQuality: 'Fast' },
        references: {},
      },
      llm: {
        prompt: '',
        modelId: findDefaultModel('llm'),
        parameters: { ...DEFAULT_PARAMS },
        references: {},
      },
    };
  });

  const currentDraft = drafts[activeTab];

  // Modèle actif pour le mode courant
  const activeModel = useMemo(() => {
    const found = models.find((m) => m.id === currentDraft?.modelId);
    if (found) return found;
    // repli sur le premier modèle du mediaType
    const fallback = models.find((m) => m.mediaType.toLowerCase() === activeTab.toLowerCase());
    return fallback || models[0];
  }, [models, currentDraft?.modelId, activeTab]);

  const updateCurrentDraft = (partial: Partial<ModeDraft>) => {
    setDrafts((prev) => ({
      ...prev,
      [activeTab]: {
        ...prev[activeTab],
        ...partial,
      },
    }));
  };

  const handleTabChange = (val: string) => {
    setActiveTab(val as DockMode);
  };

  const handleModelChange = (modelId: string) => {
    updateCurrentDraft({ modelId });
  };

  const handleParametersChange = (parameters: GenerationParameters) => {
    updateCurrentDraft({ parameters });
  };

  const handleReferencesChange = (references: GenerationReferences) => {
    updateCurrentDraft({ references });
  };

  const handlePromptChange = (prompt: string) => {
    updateCurrentDraft({ prompt });
  };

  const handleFormSubmit = () => {
    if (isGenerating || activeTab === 'llm' || !activeModel) return;

    onSubmitTask({
      modelId: activeModel.id,
      mediaType: activeModel.mediaType,
      prompt: currentDraft.prompt,
      parameters: currentDraft.parameters,
      references: currentDraft.references,
      brandKitId: selectedKit?.id,
    });
  };

  const handleCreateBrandKitContinue = async (data: CreateBrandKitData) => {
    setIsCreateModalOpen(false);
    if (onCreateBrandKit) {
      const created = await onCreateBrandKit(data);
      setInspectedKit(created);
      setIsInspectorOpen(true);
    } else {
      // Fallback local mock
      const newKit: BrandKit = {
        id: `kit_${Date.now()}`,
        name: data.name,
        overview: `Identité de marque créée via la méthode ${data.method}`,
        palette: [{ hex: '#111827', name: 'Primary' }],
        fonts: ['Inter'],
        dos: ['Cohérence visuelle'],
        donts: ['Déformation de logo'],
        referenceImages: [],
        updatedAt: new Date().toISOString(),
      };
      setInspectedKit(newKit);
      setIsInspectorOpen(true);
    }
  };

  return (
    <>
      <div className="fixed bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 w-full max-w-4xl px-4 z-40">
        <div className="bg-white rounded-dock shadow-floating-dock border border-studio-border p-4 sm:p-5 space-y-3 transition-all duration-150">
          {/* Ligne Supérieure : Onglets de Mode et Bouton @ Brand Kit */}
          <div className="flex items-center justify-between border-b border-studio-border/60 pb-2">
            <Tabs.Root value={activeTab} onValueChange={handleTabChange}>
              <Tabs.List className="flex items-center gap-1">
                {(
                  [
                    { id: 'image', label: 'Image' },
                    { id: 'video', label: 'Video' },
                    { id: 'lip_sync', label: 'Lip sync' },
                    { id: 'upscale', label: 'Upscaling' },
                    { id: 'llm', label: 'LLM' },
                  ] as const
                ).map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                    <Tabs.Trigger
                      key={tab.id}
                      value={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={`px-3 py-1.5 rounded-pill text-xs font-semibold transition-colors cursor-pointer ${
                        isActive
                          ? 'bg-studio-text text-white shadow-xs'
                          : 'text-studio-muted hover:text-studio-text hover:bg-studio-subtle'
                      }`}
                    >
                      {tab.label}
                    </Tabs.Trigger>
                  );
                })}
              </Tabs.List>
            </Tabs.Root>

            <BrandKitSelectorPopover
              brandKits={brandKits}
              activeKitId={selectedKit?.id}
              onSelectKit={(kit) => setSelectedKit(kit)}
              onCreateNewKit={() => setIsCreateModalOpen(true)}
            />
          </div>

          {/* Corps central du Dock : Conditionnement média OU vue LLM */}
          {activeTab === 'llm' ? (
            <LlmChatView
              modelId={activeModel?.id || 'qwen3.8-turbo'}
              selectedKit={selectedKit}
            />
          ) : (
            <div className="space-y-2.5">
              {/* Plateau de fentes de conditionnement */}
              {activeModel && (
                <ConditioningTray
                  model={activeModel}
                  references={currentDraft.references}
                  onChange={handleReferencesChange}
                />
              )}

              {/* Saisie de prompt avec Chip atomique */}
              <PromptEditorWithChip
                prompt={currentDraft.prompt}
                selectedKit={selectedKit}
                mediaType={activeTab}
                onChange={handlePromptChange}
                onRemoveKit={() => setSelectedKit(null)}
                onSubmit={handleFormSubmit}
              />
            </div>
          )}

          {/* Ligne Inférieure : Pilules de paramètres et bouton circulaire de soumission */}
          <div className="flex items-center justify-between pt-1 border-t border-studio-border/60">
            {activeTab === 'llm' ? (
              <div className="flex items-center gap-2">
                <ModelSelectorPopover
                  activeModelId={activeModel?.id}
                  mediaType="llm"
                  models={models}
                  onSelectModel={handleModelChange}
                />
              </div>
            ) : (
              activeModel && (
                <ParameterRegistry
                  activeModel={activeModel}
                  models={models}
                  parameters={currentDraft.parameters}
                  onParametersChange={handleParametersChange}
                  onModelChange={handleModelChange}
                />
              )
            )}

            {/* Bouton circulaire de soumission (↑) */}
            {activeTab !== 'llm' && (
              <button
                type="button"
                aria-label="Generate"
                title="Lancer la génération (Entrée)"
                disabled={isGenerating}
                onClick={handleFormSubmit}
                className="w-10 h-10 rounded-full bg-studio-text text-white flex items-center justify-center hover:bg-black transition-colors shrink-0 shadow-md disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer ml-2"
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <ArrowUp className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Modales Brand Kit */}
      <BrandKitCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onContinue={handleCreateBrandKitContinue}
      />

      <BrandKitInspectorModal
        isOpen={isInspectorOpen}
        kit={inspectedKit}
        onClose={() => setIsInspectorOpen(false)}
        onUseKit={(kit) => setSelectedKit(kit)}
      />
    </>
  );
};
