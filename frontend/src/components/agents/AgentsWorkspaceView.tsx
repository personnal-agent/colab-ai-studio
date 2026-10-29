import { useState, useRef, useEffect, type FC, type FormEvent } from 'react';
import {
  Layers,
  Move,
  ZoomIn,
  ZoomOut,
  Grid,
  Play,
  Pause,
  Sliders,
  Send,
  Square,
  Database,
  Cpu,
  Radio,
  Box,
  Sparkles,
  Film,
  Image as ImageIcon,
  Volume2,
} from 'lucide-react';
import type { CanvasAssetLayer } from '../../types/studio';
import { detectGraphicsCapability } from '../../services/graphicsCapability';
import { Canvas2DFallback } from '../canvas/Canvas2DFallback';

interface AgentMessage {
  id: string;
  sender: 'user' | 'leader' | 'planner' | 'coder';
  content: string;
  timestamp: string;
  stage?: string;
}

export interface AgentsWorkspaceViewProps {
  injectedLayers?: CanvasAssetLayer[];
  onLayerInjected?: (layer: CanvasAssetLayer) => void;
}

export const AgentsWorkspaceView: FC<AgentsWorkspaceViewProps> = ({
  injectedLayers,
  onLayerInjected,
}) => {
  const [activeAgent, setActiveAgent] = useState<'leader' | 'planner' | 'coder'>('leader');
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [chatInput, setChatInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [layers, setLayers] = useState<CanvasAssetLayer[]>(() => injectedLayers || []);
  const [isGenerating3D, setIsGenerating3D] = useState(false);
  const [graphicsMode, setGraphicsMode] = useState<'webgpu' | 'canvas2d'>('webgpu');
  const [gpuInfo, setGpuInfo] = useState<string>('Détection GPU...');
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    let isMounted = true;
    detectGraphicsCapability().then((res) => {
      if (!isMounted) return;
      setGraphicsMode(res.renderer);
      setGpuInfo(
        res.renderer === 'webgpu'
          ? `WebGPU (${res.adapterInfo || 'Hardware'})`
          : `Canvas2D (${res.reason || 'Intel HD 520'})`
      );
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'msg-1',
      sender: 'leader',
      content: 'Système multi-agents Hilo initialisé. En attente d’instructions de conception ou d’animation.',
      timestamp: '12:00:01',
      stage: 'READY',
    },
    {
      id: 'msg-2',
      sender: 'planner',
      content: 'Prêt à décomposer la composition en calques WebGPU, keyframes et requêtes d’inférence 6 pôles.',
      timestamp: '12:00:02',
      stage: 'PLANNING',
    },
  ]);

  useEffect(() => {
    if (injectedLayers && injectedLayers.length > 0) {
      setLayers((prev) => {
        const existingIds = new Set(prev.map((l) => l.id));
        const toAdd = injectedLayers.filter((l) => !existingIds.has(l.id));
        return toAdd.length > 0 ? [...prev, ...toAdd] : prev;
      });
    }
  }, [injectedLayers]);

  useEffect(() => {
    const handleCustomInjection = (e: Event) => {
      const customEvt = e as CustomEvent<CanvasAssetLayer>;
      if (customEvt.detail) {
        const newLayer = customEvt.detail;
        setLayers((prev) => {
          if (prev.some((l) => l.id === newLayer.id)) return prev;
          return [...prev, newLayer];
        });
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}`,
            sender: 'leader',
            content: `Média "${newLayer.name}" (${newLayer.type}) injecté avec succès sur le canevas infini WebGPU.`,
            timestamp: new Date().toLocaleTimeString(),
            stage: 'CANVAS_INJECT',
          },
        ]);
        onLayerInjected?.(newLayer);
      }
    };
    window.addEventListener('omniforge:inject-canvas-asset', handleCustomInjection);
    return () => {
      window.removeEventListener('omniforge:inject-canvas-asset', handleCustomInjection);
    };
  }, [onLayerInjected]);

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  };

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreaming) return;

    const userMsg: AgentMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: chatInput,
      timestamp: new Date().toLocaleTimeString(),
    };

    const targetAgent = activeAgent;
    setMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setIsStreaming(true);

    const agentMsgId = `msg-${Date.now() + 1}`;
    setMessages((prev) => [
      ...prev,
      {
        id: agentMsgId,
        sender: targetAgent,
        content: '',
        timestamp: new Date().toLocaleTimeString(),
        stage: 'STREAMING',
      },
    ]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          model: 'qwen-2.5-coder-32b',
          messages: [
            {
              role: 'system',
              content: `Vous êtes l'agent Hilo ${targetAgent}. Vous pilotez le canevas infini WebGPU et l'orchestration des plans.`,
            },
            { role: 'user', content: userMsg.content },
          ],
          stream: true,
        }),
      });

      if (!res.ok) {
        throw new Error(`Erreur proxy LLM: ${res.status}`);
      }

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let reading = true;

        while (reading) {
          const { done, value } = await reader.read();
          if (done) {
            reading = false;
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data: ')) {
              const dataStr = trimmed.slice(6);
              if (dataStr === '[DONE]') {
                break;
              }
              try {
                const parsed = JSON.parse(dataStr);
                const delta = parsed.choices?.[0]?.delta?.content || '';
                if (delta) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === agentMsgId ? { ...m, content: m.content + delta } : m
                    )
                  );
                }
              } catch {
                // Ignore partial JSON chunks in SSE stream
              }
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentMsgId ? { ...m, content: m.content + ' [Génération interrompue]' } : m
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentMsgId
              ? { ...m, content: 'Erreur lors de la communication avec l’agent local.' }
              : m
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleGenerate3DMesh = async () => {
    setIsGenerating3D(true);
    try {
      const res = await fetch('/api/generate/media', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: '3d',
          prompt: '3D mesh layer generated from agents canvas',
          capabilities: { acceptedInputTypes: ['prompt'] },
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const newLayer: CanvasAssetLayer = {
          id: `mesh-${Date.now()}`,
          name: `Calque 3D #${layers.filter((l) => l.type === 'mesh_3d').length + 1}`,
          type: 'mesh_3d',
          taskId: data.taskId || `task-mesh-${Date.now()}`,
          status: 'ready',
        };
        setLayers((prev) => [...prev, newLayer]);
        onLayerInjected?.(newLayer);
      }
    } catch (err) {
      console.error('Failed to generate 3D mesh:', err);
    } finally {
      setIsGenerating3D(false);
    }
  };

  return (
    <div
      data-testid="agents-workspace-view"
      className="flex-1 flex flex-col h-[calc(100vh-4rem)] bg-studio-canvas text-gray-900 dark:text-gray-100 overflow-hidden"
    >
      {/* Barre supérieure d'état d'orchestration Hilo */}
      <div className="h-10 px-4 border-b border-studio-border bg-white dark:bg-gray-900 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1.5 font-bold tracking-wide text-indigo-600 dark:text-indigo-400">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Hilo Swarm Dialogue</span>
          </span>
          <span className="text-gray-300 dark:text-gray-700">|</span>
          <span className="text-gray-500 font-mono text-[11px]">
            FastAPI: :8000 · NestJS Gateway: :51491 · SQLite WAL
          </span>
        </div>

        <div className="flex items-center space-x-3">
          {/* Badge statut graphique et commutateur WebGPU / Canvas2D */}
          <div className="flex items-center space-x-1.5">
            <div
              data-testid="graphics-mode-badge"
              className={`flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono border ${
                graphicsMode === 'webgpu'
                  ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                  : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800'
              }`}
              title={gpuInfo}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  graphicsMode === 'webgpu' ? 'bg-emerald-500' : 'bg-amber-500'
                } animate-pulse`}
              />
              <span>{graphicsMode === 'webgpu' ? 'WebGPU 60fps' : 'Canvas2D Fallback'}</span>
            </div>

            <button
              type="button"
              data-testid="toggle-renderer-btn"
              onClick={() => setGraphicsMode((m) => (m === 'webgpu' ? 'canvas2d' : 'webgpu'))}
              title="Basculer manuellement le moteur de rendu graphique"
              className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-[10px] font-mono text-gray-600 dark:text-gray-300 transition-colors border border-studio-border"
            >
              {graphicsMode === 'webgpu' ? 'Forcer 2D' : 'Mode GPU'}
            </button>
          </div>

          <div className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 text-[11px]">
            <Cpu className="w-3.5 h-3.5" />
            <span>Intel i7 (2C/4T)</span>
          </div>
          <div className="flex items-center space-x-1 text-gray-500 text-[11px]">
            <Database className="w-3.5 h-3.5" />
            <span>RAM: ~395 Mo</span>
          </div>
        </div>
      </div>

      {/* Corps principal : Volet conversationnel + Canevas infini */}
      <div className="flex-1 flex overflow-hidden">
        {/* Volet conversationnel multi-agents */}
        <div className="w-96 border-r border-studio-border bg-white dark:bg-gray-900 flex flex-col h-full">
          {/* Sélecteur d'agent actif */}
          <div className="p-3 border-b border-studio-border bg-gray-50 dark:bg-gray-800/50">
            <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">
              Agents Hilo Autonomes
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {(['leader', 'planner', 'coder'] as const).map((agent) => (
                <button
                  key={agent}
                  type="button"
                  onClick={() => setActiveAgent(agent)}
                  className={`px-2 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                    activeAgent === agent
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-studio-border'
                  }`}
                >
                  {agent}
                </button>
              ))}
            </div>
            <div className="mt-2 text-[11px] text-gray-500 flex items-center justify-between">
              <span>Rôle actif :</span>
              <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                {activeAgent} active
              </span>
            </div>
          </div>

          {/* Flux de messages */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div className="flex items-center space-x-1.5 mb-1 text-[10px] text-gray-400">
                  <span className="font-semibold uppercase tracking-wider">{msg.sender}</span>
                  <span>·</span>
                  <span className="font-mono">{msg.timestamp}</span>
                  {msg.stage && (
                    <span className="px-1.5 py-0.2 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 font-mono text-[9px]">
                      {msg.stage}
                    </span>
                  )}
                </div>
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-studio-border'
                  }`}
                >
                  {msg.content || (
                    <span className="inline-flex items-center space-x-1 text-gray-400 italic">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                      <span>Génération de la réponse...</span>
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Saisie de message et commande LLM streaming */}
          <form
            onSubmit={handleSendMessage}
            className="p-3 border-t border-studio-border bg-gray-50 dark:bg-gray-800/30 flex items-center space-x-2"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={`Demander à ${activeAgent}...`}
              disabled={isStreaming}
              className="flex-1 px-3 py-1.5 text-xs rounded-lg bg-white dark:bg-gray-900 border border-studio-border focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={handleStopStreaming}
                aria-label="Arrêter la réponse"
                className="p-1.5 rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors shadow-xs"
              >
                <Square className="w-4 h-4 fill-white" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!chatInput.trim()}
                aria-label="Envoyer instruction agent"
                className="p-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors shadow-xs"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </form>
        </div>

        {/* Espace central : Canevas infini WebGPU */}
        <div className="flex-1 flex flex-col bg-studio-canvas relative overflow-hidden">
          {/* Barre d'outils du canevas */}
          <div className="h-10 px-4 border-b border-studio-border bg-white/70 dark:bg-gray-900/70 backdrop-blur-xs flex items-center justify-between z-10">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 p-0.5 rounded-lg">
                <button
                  type="button"
                  title="Déplacer"
                  className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                >
                  <Move className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  title="Calques"
                  className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                >
                  <Layers className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  title="Grille"
                  className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                >
                  <Grid className="w-4 h-4" />
                </button>
              </div>

              {/* Action Passerelle 6 Pôles : Génération 3D */}
              <button
                type="button"
                onClick={handleGenerate3DMesh}
                disabled={isGenerating3D}
                aria-label="Injecter maillage 3D"
                className="flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900 transition-colors shadow-xs"
              >
                <Box className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                <span>{isGenerating3D ? 'Génération 3D...' : 'Ajouter Calque 3D'}</span>
              </button>
            </div>

            <div className="flex items-center space-x-2 text-xs">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(25, z - 10))}
                className="p-1 text-gray-500 hover:text-gray-900 dark:hover:text-white"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="font-mono text-gray-700 dark:text-gray-300 w-12 text-center">
                {zoomLevel}%
              </span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(400, z + 10))}
                className="p-1 text-gray-500 hover:text-gray-900 dark:hover:text-white"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Surface de canevas interactif */}
          <div className="flex-1 relative flex items-center justify-center p-8 overflow-hidden bg-[radial-gradient(#CBD5E1_1px,transparent_1px)] dark:bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:16px_16px]">
            {/* Artboard de travail 16:9 */}
            <div
              className="w-full max-w-3xl aspect-video bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center text-center p-6 transition-transform relative overflow-hidden"
              style={{ transform: `scale(${zoomLevel / 100})` }}
            >
              {graphicsMode === 'canvas2d' && (
                <Canvas2DFallback
                  layers={layers}
                  zoomLevel={zoomLevel}
                  className="absolute inset-0 z-0 opacity-85 pointer-events-none"
                />
              )}
              <div className="relative z-10 w-full flex flex-col items-center justify-center">
                {layers.length > 0 ? (
                  <div className="space-y-3 w-full">
                    <div className="flex items-center justify-center space-x-2 text-indigo-600 dark:text-indigo-400">
                      <Sparkles className="w-5 h-5 animate-pulse" />
                      <span className="text-sm font-bold">
                        {layers.length} Calque(s) actif(s) sur le canevas
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {layers.map((layer) => (
                        <div
                          key={layer.id}
                          data-testid={layer.type === 'mesh_3d' ? 'canvas-3d-layer' : 'canvas-asset-layer'}
                          className="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/70 border border-indigo-200 dark:border-indigo-800 text-xs font-mono text-indigo-700 dark:text-indigo-300 flex items-center space-x-2 shadow-xs"
                        >
                          {layer.type === 'mesh_3d' && <Box className="w-3.5 h-3.5" />}
                          {layer.type === 'video' && <Film className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />}
                          {layer.type === 'image' && <ImageIcon className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
                          {layer.type === 'audio' && <Volume2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
                          <span className="truncate max-w-[180px]">{layer.name}</span>
                          <span className="text-[10px] text-gray-400">[{layer.taskId.slice(0, 8)}]</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center mb-3">
                      <Sliders className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-1">
                      CanvasAreaV3 — Espace de Composition Mini Design
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 max-w-md">
                      Prêt pour le montage des calques WebGPU, la composition d’animations et l’injection directe des maillages 3D et vidéos Omniforge.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Séquenceur temporel en bas du canevas */}
          <div className="h-28 border-t border-studio-border bg-white dark:bg-gray-900 flex flex-col z-10">
            <div className="h-8 px-4 border-b border-studio-border flex items-center justify-between text-xs bg-gray-50/50 dark:bg-gray-800/30">
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                </button>
                <span className="font-mono text-[11px] text-gray-500">00:00:00 / 00:00:10</span>
              </div>
              <div className="flex items-center space-x-2 text-[11px] text-gray-500 font-mono">
                <span>30 FPS</span>
                <span>·</span>
                <span>1920x1080</span>
              </div>
            </div>

            {/* Pistes de montage vidéo / 3D */}
            <div className="flex-1 p-2 space-y-1.5 overflow-x-auto bg-gray-50/30 dark:bg-gray-950/30">
              <div className="h-6 rounded bg-indigo-100/50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 flex items-center px-2 text-[10px] font-mono text-indigo-700 dark:text-indigo-300">
                <span className="font-bold mr-2">Piste 1 (3D / Vidéo)</span>
                <span className="text-gray-400">Plan_01_Cinematic_Establish.mp4</span>
              </div>
              <div className="h-6 rounded bg-purple-100/50 dark:bg-purple-950/50 border border-purple-200 dark:border-purple-800 flex items-center px-2 text-[10px] font-mono text-purple-700 dark:text-purple-300">
                <span className="font-bold mr-2">Piste 2 (FX / Shaders)</span>
                <span className="text-gray-400">Volumetric_Lighting_Pass.fx</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
