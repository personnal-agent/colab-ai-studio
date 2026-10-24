import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ArrowUp, Square, Image, Video, Mic, Maximize2, MessageSquare, AlertCircle } from 'lucide-react';
import type {
  ModelDefinition, BrandKit, Generation, GenerationParameters,
  GenerationReferences, GenerationSubmitRequest,
} from '../../types/studio';
import { ConditioningTray } from './conditioning/ConditioningTray';
import { ParameterRegistry } from './ParameterRegistry';
import { PromptEditorWithChip } from '../brand-kit/PromptEditorWithChip';
import { BrandKitSelectorPopover } from '../brand-kit/BrandKitSelectorPopover';
import { BrandKitCreateModal } from '../brand-kit/BrandKitCreateModal';
import { BrandKitInspectorModal } from '../brand-kit/BrandKitInspectorModal';
import { LlmChatView, type ChatMessage } from './LlmChatView';
import { apiClient } from '../../services/apiClient';

export type DockMode = 'image' | 'video' | 'lip_sync' | 'upscale' | 'llm';

interface ModeState {
  prompt: string;
  model: ModelDefinition | null;
  parameters: GenerationParameters;
  references: GenerationReferences;
  selectedBrandKit: BrandKit | null;
  batchCount: number;
  talkingStyle: string;
  upscaleScale: string;
  upscaleQuality: string;
  upscaleFrameRate: string;
  negativePrompt: string;
}

const DEFAULT_PARAMS: GenerationParameters = {
  aspectRatio: '16:9', resolution: '1080p', duration: '5s', seed: -1, enhance: false,
};

const DEFAULT_REFS: GenerationReferences = { imageRefs: [], videoRefs: [], audioRefs: [] };

const createInitialState = (): ModeState => ({
  prompt: '', model: null, parameters: { ...DEFAULT_PARAMS }, references: { ...DEFAULT_REFS },
  selectedBrandKit: null, batchCount: 1, talkingStyle: 'Stable', upscaleScale: '2x',
  upscaleQuality: 'Fast', upscaleFrameRate: 'Same as source', negativePrompt: '',
});

export interface FloatingPromptDockProps {
  models: ModelDefinition[];
  brandKits: BrandKit[];
  activeProjectId?: string | null;
  remixContext?: Generation | null;
  onClearRemix?: () => void;
  onCreateBrandKit?: (data: {
    source: 'blank' | 'website' | 'files'; name: string; overview?: string; url?: string; files?: File[];
  }) => Promise<BrandKit>;
  onSubmitGeneration?: (req: GenerationSubmitRequest) => Promise<void>;
  onBrandKitCreated?: (kit: BrandKit) => void;
  className?: string;
}

export const FloatingPromptDock: React.FC<FloatingPromptDockProps> = ({
  models, brandKits, activeProjectId, remixContext, onClearRemix,
  onCreateBrandKit, onSubmitGeneration, onBrandKitCreated, className = '',
}) => {
  const [activeMode, setActiveMode] = useState<DockMode>('video');
  const [modeStates, setModeStates] = useState<Record<DockMode, ModeState>>({
    image: createInitialState(), video: createInitialState(), lip_sync: createInitialState(),
    upscale: createInitialState(), llm: createInitialState(),
  });

  const [llmMessages, setLlmMessages] = useState<ChatMessage[]>([]);
  const [isLlmStreaming, setIsLlmStreaming] = useState(false);
  const llmAbortRef = useRef<AbortController | null>(null);

  const [isBrandKitPopoverOpen, setIsBrandKitPopoverOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [inspectingKit, setInspectingKit] = useState<BrandKit | null>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [isSubmittingMedia, setIsSubmittingMedia] = useState(false);

  useEffect(() => {
    setModeStates((prev) => {
      const next = { ...prev };
      const modes: DockMode[] = ['image', 'video', 'lip_sync', 'upscale', 'llm'];
      modes.forEach((m) => {
        if (!next[m].model) {
          const typeMatch = m === 'llm' ? 'text' : m;
          const found = models.find((mod) => mod.type === typeMatch || (m === 'llm' && mod.type === 'llm'));
          if (found) next[m].model = found;
        }
      });
      return next;
    });
  }, [models]);

  useEffect(() => {
    if (remixContext) {
      const mediaType = remixContext.mediaType.toLowerCase();
      let targetMode: DockMode = 'image';
      if (mediaType.includes('video')) targetMode = 'video';
      else if (mediaType.includes('lip')) targetMode = 'lip_sync';
      else if (mediaType.includes('up')) targetMode = 'upscale';

      setActiveMode(targetMode);
      setModeStates((prev) => {
        const cur = prev[targetMode];
        const matchingModel = models.find((m) => m.id === remixContext.modelId) || cur.model;
        const matchingKit = remixContext.brandKitSnapshot
          ? brandKits.find((k) => k.id === remixContext.brandKitSnapshot?.id) || null
          : null;
        return {
          ...prev,
          [targetMode]: {
            ...cur, prompt: remixContext.prompt, model: matchingModel,
            parameters: { ...cur.parameters, ...remixContext.parameters },
            references: { ...cur.references, ...remixContext.references },
            selectedBrandKit: matchingKit, negativePrompt: remixContext.negativePrompt || '',
          },
        };
      });
      if (onClearRemix) onClearRemix();
    }
  }, [remixContext, models, brandKits, onClearRemix]);

  const current = modeStates[activeMode];

  const updateCurrent = useCallback((patch: Partial<ModeState>) => {
    setModeStates((prev) => ({
      ...prev, [activeMode]: { ...prev[activeMode], ...patch },
    }));
  }, [activeMode]);

  const handleSubmit = async () => {
    if (activeMode === 'llm') {
      const text = current.prompt.trim();
      if (!text || isLlmStreaming) return;

      const userMsg: ChatMessage = { id: `user_${Date.now()}`, role: 'user', content: text };
      const assistantId = `asst_${Date.now()}`;
      const assistantMsg: ChatMessage = { id: assistantId, role: 'assistant', content: '' };

      const newMessages = [...llmMessages, userMsg];
      setLlmMessages([...newMessages, assistantMsg]);
      updateCurrent({ prompt: '' });
      setIsLlmStreaming(true);

      const controller = new AbortController();
      llmAbortRef.current = controller;

      let chatPayloadMessages = newMessages.map((m) => ({ role: m.role, content: m.content }));
      if (current.selectedBrandKit) {
        const kit = current.selectedBrandKit;
        const brandSummary = [
          `Brand: ${kit.name}`,
          kit.overview ? `Overview: ${kit.overview}` : null,
          kit.colors?.length ? `Colors: ${kit.colors.map((c) => `${c.label} (${c.hex})`).join(', ')}` : null,
          kit.fonts?.length ? `Fonts: ${kit.fonts.map((f) => `${f.family} ${f.weight}`).join(', ')}` : null,
          kit.guidelines?.length ? `Guidelines: ${kit.guidelines.map((g) => `[${g.kind.toUpperCase()}] ${g.text}`).join('; ')}` : null,
        ].filter(Boolean).join('\n');
        chatPayloadMessages = [{ role: 'system', content: `Condition your responses using this Brand Kit:\n${brandSummary}` }, ...chatPayloadMessages];
      }

      try {
        await apiClient.streamChatCompletion(
          { model: current.model?.name || 'Llama-3-8B', messages: chatPayloadMessages },
          (chunk) => {
            setLlmMessages((prev) => prev.map((msg) => (msg.id === assistantId ? { ...msg, content: msg.content + chunk } : msg)));
          },
          controller.signal
        );
      } catch (err: unknown) {
        if ((err as Error)?.name !== 'AbortError') {
          setLlmMessages((prev) =>
            prev.map((msg) => (msg.id === assistantId ? { ...msg, content: msg.content + ` [Erreur: ${(err as Error)?.message || 'Inconnue'}]` } : msg))
          );
        }
      } finally {
        setIsLlmStreaming(false);
        llmAbortRef.current = null;
      }
      return;
    }

    if (activeMode !== 'upscale' && !current.prompt.trim()) return;
    if (isSubmittingMedia) return;

    if (onSubmitGeneration && current.model) {
      setMediaError(null);
      setIsSubmittingMedia(true);
      try {
        const count = Math.max(1, current.batchCount || 1);
        const mediaType = activeMode === 'upscale' ? 'upscale' : activeMode === 'lip_sync' ? 'lip_sync' : activeMode;
        for (let i = 0; i < count; i++) {
          await onSubmitGeneration({
            modelId: current.model.id,
            prompt: current.prompt,
            type: mediaType,
            negativePrompt: current.negativePrompt || undefined,
            parameters: {
              ...current.parameters,
              talkingStyle: current.talkingStyle,
              upscaleScale: current.upscaleScale,
              upscaleQuality: current.upscaleQuality,
              upscaleFrameRate: current.upscaleFrameRate,
            },
            references: current.references,
            projectId: activeProjectId,
            brandKitId: current.selectedBrandKit?.id,
          });
        }
      } catch (err: unknown) {
        setMediaError(err instanceof Error ? err.message : 'Échec de soumission de la génération.');
      } finally {
        setIsSubmittingMedia(false);
      }
    }
  };

  const handleStopLlmStreaming = () => {
    if (llmAbortRef.current) {
      llmAbortRef.current.abort();
      setIsLlmStreaming(false);
    }
  };

  const handleCreateBrandKitInternal = async (data: {
    source: 'blank' | 'website' | 'files'; name: string; overview?: string; url?: string; files?: File[];
  }): Promise<BrandKit> => {
    if (onCreateBrandKit) return await onCreateBrandKit(data);
    return await apiClient.createBrandKit(data);
  };

  const modeTabs: { id: DockMode; label: string; icon: React.ElementType }[] = [
    { id: 'image', label: 'Image', icon: Image },
    { id: 'video', label: 'Video', icon: Video },
    { id: 'lip_sync', label: 'Lip sync', icon: Mic },
    { id: 'upscale', label: 'Upscaling', icon: Maximize2 },
    { id: 'llm', label: 'LLM', icon: MessageSquare },
  ];

  return (
    <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-4xl z-40 px-4 transition-all duration-150 ease-out ${className}`}>
      <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-200/80 dark:border-gray-800 p-3 sm:p-4 flex flex-col space-y-2">
        <div className="flex items-center justify-between pb-1 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center space-x-1 sm:space-x-1.5" role="tablist">
            {modeTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeMode === tab.id;
              return (
                <button
                  key={tab.id} type="button" role="tab" aria-selected={isActive} aria-label={tab.label}
                  onClick={() => { setActiveMode(tab.id); setMediaError(null); }}
                  className={`flex items-center space-x-1.5 py-1 px-2.5 sm:px-3 rounded-full text-xs font-semibold transition-all duration-150 ${isActive ? 'bg-black text-white dark:bg-white dark:text-black shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" /><span>{tab.label}</span>
                </button>
              );
            })}
          </div>
          <div className="flex items-center space-x-2">
            <BrandKitSelectorPopover
              isOpen={isBrandKitPopoverOpen} onOpenChange={setIsBrandKitPopoverOpen}
              brandKits={brandKits} selectedBrandKitId={current.selectedBrandKit?.id}
              onSelectBrandKit={(kit) => updateCurrent({ selectedBrandKit: kit })}
              onInspectBrandKit={(kit) => setInspectingKit(kit)}
              onCreateBrandKitClick={() => setIsCreateModalOpen(true)}
              trigger={
                <button
                  type="button"
                  aria-label="Brand kit options"
                  className="text-xs text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 font-medium py-1 px-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  {current.selectedBrandKit ? `@${current.selectedBrandKit.name}` : 'Brand Kit'}
                </button>
              }
            />
          </div>
        </div>

        {activeMode === 'llm' && (
          <LlmChatView messages={llmMessages} isStreaming={isLlmStreaming} onStopStreaming={handleStopLlmStreaming} />
        )}

        {activeMode !== 'llm' && (
          <ConditioningTray
            mode={activeMode} model={current.model} references={current.references}
            onReferencesChange={(refs) => updateCurrent({ references: refs })}
          />
        )}

        {mediaError && (
          <div className="flex items-center justify-between px-3.5 py-2 text-xs bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-800 animate-in fade-in duration-100">
            <div className="flex items-center space-x-1.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{mediaError}</span>
            </div>
            <button type="button" aria-label="Dismiss error" onClick={() => setMediaError(null)} className="ml-2 font-bold text-gray-400 hover:text-red-700">&times;</button>
          </div>
        )}

        <div className="bg-gray-50 dark:bg-gray-800/60 rounded-2xl p-3 border border-gray-100 dark:border-gray-700/60 focus-within:border-gray-300 dark:focus-within:border-gray-600 transition-colors">
          <PromptEditorWithChip
            prompt={current.prompt}
            onPromptChange={(prompt) => {
              updateCurrent({ prompt });
              if (mediaError) setMediaError(null);
            }}
            selectedBrandKit={current.selectedBrandKit} onRemoveBrandKit={() => updateCurrent({ selectedBrandKit: null })}
            onOpenBrandKitSelector={() => setIsBrandKitPopoverOpen(true)} onSubmit={handleSubmit}
            placeholder={activeMode === 'llm' ? 'Ask the LLM anything or generate prompts, copy and code...' : 'Describe what you want to create or @ to mention a brand kit...'}
          />
          <div className="flex items-center justify-between pt-2.5 mt-2 border-t border-gray-200/60 dark:border-gray-700/60">
            <ParameterRegistry
              mode={activeMode} model={current.model} models={models} onModelChange={(model) => updateCurrent({ model })}
              parameters={current.parameters} onParametersChange={(params) => updateCurrent({ parameters: { ...current.parameters, ...params } })}
              batchCount={current.batchCount} onBatchCountChange={(count) => updateCurrent({ batchCount: count })}
              talkingStyle={current.talkingStyle} onTalkingStyleChange={(style) => updateCurrent({ talkingStyle: style })}
              upscaleScale={current.upscaleScale} onUpscaleScaleChange={(scale) => updateCurrent({ upscaleScale: scale })}
              upscaleQuality={current.upscaleQuality} onUpscaleQualityChange={(quality) => updateCurrent({ upscaleQuality: quality })}
              upscaleFrameRate={current.upscaleFrameRate} onUpscaleFrameRateChange={(fps) => updateCurrent({ upscaleFrameRate: fps })}
              negativePrompt={current.negativePrompt} onNegativePromptChange={(val) => updateCurrent({ negativePrompt: val })}
            />
            <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
              {activeMode === 'llm' && isLlmStreaming ? (
                <button
                  type="button" aria-label="Stop generating" onClick={handleStopLlmStreaming}
                  className="w-9 h-9 flex items-center justify-center rounded-full bg-rose-600 hover:bg-rose-700 active:scale-95 text-white shadow-md transition-all"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  type="button" aria-label="Submit" onClick={handleSubmit} disabled={(!current.prompt.trim() && activeMode !== 'upscale') || isSubmittingMedia}
                  className="w-9 h-9 flex items-center justify-center rounded-full bg-black hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-200 dark:text-black active:scale-95 text-white shadow-md transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isSubmittingMedia ? (
                    <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  ) : (
                    <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <BrandKitCreateModal
        isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)}
        onCreateBrandKit={handleCreateBrandKitInternal}
        onSuccess={(createdKit) => {
          setIsCreateModalOpen(false); setInspectingKit(createdKit); updateCurrent({ selectedBrandKit: createdKit });
          onBrandKitCreated?.(createdKit);
        }}
      />
      <BrandKitInspectorModal
        brandKit={inspectingKit} isOpen={Boolean(inspectingKit)} onClose={() => setInspectingKit(null)}
        onSelectBrandKit={(kit) => { updateCurrent({ selectedBrandKit: kit }); setInspectingKit(null); }}
      />
    </div>
  );
};
