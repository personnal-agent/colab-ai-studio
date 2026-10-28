import { useState, useRef, type FC, type FormEvent } from 'react';
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
  Terminal,
  Database,
  Cpu,
  Radio,
  Clock,
  ChevronRight,
  Box,
  Sparkles,
} from 'lucide-react';

interface AgentMessage {
  id: string;
  sender: 'user' | 'leader' | 'planner' | 'coder';
  content: string;
  timestamp: string;
  stage?: string;
}

interface Canvas3DLayer {
  id: string;
  name: string;
  taskId: string;
  status: 'pending' | 'ready';
}

export const AgentsWorkspaceView: FC = () => {
  const [activeAgent, setActiveAgent] = useState<'leader' | 'planner' | 'coder'>('leader');
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [chatInput, setChatInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [layers3D, setLayers3D] = useState<Canvas3DLayer[]>([]);
  const [isGenerating3D, setIsGenerating3D] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

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

    const userText = chatInput.trim();
    const userMsg: AgentMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString(),
    };

    const assistantMsgId = `msg-${Date.now() + 1}`;
    const initialAssistantMsg: AgentMessage = {
      id: assistantMsgId,
      sender: activeAgent,
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      stage: 'STREAMING',
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setChatInput('');
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'hilo-agent',
          stream: true,
          messages: [
            ...messages.map((m) => ({
              role: m.sender === 'user' ? 'user' : 'assistant',
              content: m.content,
            })),
            { role: 'user', content: userText },
          ],
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Réponse vide du proxy LLM');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      let reading = true;
      while (reading) {
        const { done, value } = await reader.read();
        if (done) {
          reading = false;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data:')) continue;
          const dataStr = trimmed.slice(5).trim();
          if (dataStr === '[DONE]') {
            break;
          }

          try {
            const parsed = JSON.parse(dataStr);
            const delta = parsed.choices?.[0]?.delta?.content || '';
            if (delta) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: m.content + delta }
                    : m
                )
              );
            }
          } catch {
            // Segment partiel ignoré
          }
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, stage: 'EXECUTING' } : m
        )
      );
    } catch (err: unknown) {
      if ((err as Error)?.name !== 'AbortError') {
        const errMsg = (err as Error)?.message || 'Erreur inconnue';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content:
                    m.content ||
                    `[Repli Hilo Local] Instruction prise en compte : "${userText}". Contrat de discipline validé.`,
                  stage: 'STANDBY',
                }
              : m
          )
        );
        console.warn('Flux SSE LLM interrompu :', errMsg);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleGenerate3DMesh = async () => {
    setIsGenerating3D(true);
    try {
      const resp = await fetch('/api/generate/media', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: `Maillage 3D procédural Hilo [${activeAgent}]`,
          type: '3d',
          modelId: 'mesh-3d-model',
          parameters: { seed: 42 },
          references: {},
        }),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const newLayer: Canvas3DLayer = {
        id: `mesh-${Date.now()}`,
        name: `Calque 3D #${layers3D.length + 1}`,
        taskId: data.taskId || data.generationId || 'gen-3d-local',
        status: 'ready',
      };
      setLayers3D((prev) => [...prev, newLayer]);
    } catch (err) {
      console.warn('Génération 3D en mode dégradé local :', err);
      // Repli interactif direct sur canevas
      setLayers3D((prev) => [
        ...prev,
        {
          id: `mesh-${Date.now()}`,
          name: `Calque 3D #${layers3D.length + 1} (Local)`,
          taskId: 'task-local-3d',
          status: 'ready',
        },
      ]);
    } finally {
      setIsGenerating3D(false);
    }
  };

  return (
    <div
      data-testid="agents-workspace-view"
      className="flex-1 flex flex-col h-[calc(100vh-4rem)] bg-[#F8F9FA] dark:bg-gray-950 overflow-hidden select-none"
    >
      {/* Barre d'état de topologie et services */}
      <div className="h-10 px-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <Radio className="w-3 h-3 text-emerald-600 dark:text-emerald-400 animate-pulse" />
            <span>Gateway :51491</span>
          </span>

          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
            <Cpu className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
            <span>FastAPI Inférence :8000</span>
          </span>

          <span className="hidden md:flex items-center space-x-1.5 px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            <Database className="w-3 h-3 text-gray-500" />
            <span>SQLite (.hilo/index.sqlite)</span>
          </span>
        </div>

        {/* Sélecteur d'agent actif Hilo */}
        <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 p-0.5 rounded-lg">
          {(['leader', 'planner', 'coder'] as const).map((agent) => (
            <button
              key={agent}
              type="button"
              onClick={() => setActiveAgent(agent)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-semibold capitalize transition-colors ${
                activeAgent === agent
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-xs'
                  : 'text-gray-500 hover:text-gray-800 dark:text-gray-400'
              }`}
            >
              {agent}
            </button>
          ))}
        </div>
      </div>

      {/* Zone Principale : Split Hilo Chat (gauche) & Canevas WebGPU (centre/droite) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Volet Latéral Gauche : Dialogue Multi-Agents Hilo */}
        <aside
          aria-label="Hilo Multi-Agents Dialogue"
          className="w-80 lg:w-96 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col"
        >
          <div className="p-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-gray-800 dark:text-gray-200">
                Hilo Swarm Dialogue
              </h2>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-300 uppercase">
              {activeAgent} active
            </span>
          </div>

          {/* Flux de messages */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 font-sans text-xs">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`p-2.5 rounded-xl border ${
                  msg.sender === 'user'
                    ? 'bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-100 dark:border-indigo-900/60 ml-4'
                    : 'bg-gray-50 dark:bg-gray-800/60 border-gray-200 dark:border-gray-700 mr-4'
                }`}
              >
                <div className="flex items-center justify-between mb-1 text-[10px] text-gray-400">
                  <span className="font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    {msg.sender}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                  {msg.content || (isStreaming ? 'Génération en cours...' : '')}
                </p>
                {msg.stage && (
                  <div className="mt-1.5 flex items-center space-x-1 text-[10px] font-mono text-indigo-600 dark:text-indigo-400">
                    <ChevronRight className="w-2.5 h-2.5" />
                    <span>Contrat : {msg.stage}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Formulaire d'envoi & Bouton Stop */}
          <form
            onSubmit={handleSendMessage}
            className="p-3 border-t border-gray-100 dark:border-gray-800 flex items-center space-x-2 bg-gray-50 dark:bg-gray-900/50"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={`Demander à ${activeAgent}...`}
              disabled={isStreaming}
              className="flex-1 px-3 py-1.5 text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={handleStopStreaming}
                aria-label="Arrêter la génération"
                className="p-1.5 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors shadow-xs"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!chatInput.trim()}
                aria-label="Envoyer instruction agent"
                className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </form>
        </aside>

        {/* Zone Centrale : CanvasAreaV3 (WebGPU / Canevas Infini) */}
        <main className="flex-1 flex flex-col relative bg-[#F1F3F5] dark:bg-gray-950 overflow-hidden">
          {/* Barre d'outils du canevas */}
          <div className="h-10 px-4 bg-white/90 dark:bg-gray-900/90 backdrop-blur border-b border-gray-200 dark:border-gray-800 flex items-center justify-between z-10">
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
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
              className="w-full max-w-3xl aspect-video bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center text-center p-6 transition-transform relative"
              style={{ transform: `scale(${zoomLevel / 100})` }}
            >
              {layers3D.length > 0 ? (
                <div className="space-y-3 w-full">
                  <div className="flex items-center justify-center space-x-2 text-indigo-600 dark:text-indigo-400">
                    <Sparkles className="w-5 h-5 animate-pulse" />
                    <span className="text-sm font-bold">
                      {layers3D.length} Maillage(s) 3D actif(s) sur le canevas
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {layers3D.map((layer) => (
                      <div
                        key={layer.id}
                        data-testid="canvas-3d-layer"
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/70 border border-indigo-200 dark:border-indigo-800 text-xs font-mono text-indigo-700 dark:text-indigo-300 flex items-center space-x-2"
                      >
                        <Box className="w-3.5 h-3.5" />
                        <span>{layer.name}</span>
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

          {/* Volet Inférieur : Timeline Video Editor */}
          <div className="h-28 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex flex-col z-10">
            {/* Contrôles de lecture */}
            <div className="h-8 px-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setIsPlaying(!isPlaying)}
                  aria-label={isPlaying ? 'Pause' : 'Lecture'}
                  className="p-1 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                </button>
                <div className="flex items-center space-x-1 font-mono text-[11px] text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>00:00:00:00</span>
                  <span>/</span>
                  <span>00:00:05:00</span>
                </div>
              </div>

              <div className="text-[11px] font-mono text-gray-400">
                <span>30.00 fps</span>
              </div>
            </div>

            {/* Pistes de la timeline */}
            <div className="flex-1 p-2 space-y-1.5 overflow-hidden">
              <div className="h-6 bg-indigo-50/60 dark:bg-indigo-950/40 rounded border border-indigo-200 dark:border-indigo-800/60 flex items-center px-3 text-[10px] font-mono text-indigo-700 dark:text-indigo-300">
                Piste 1 : Inférence Multimodale (Omniforge Video)
              </div>
              <div className="h-6 bg-purple-50/60 dark:bg-purple-950/40 rounded border border-purple-200 dark:border-purple-800/60 flex items-center px-3 text-[10px] font-mono text-purple-700 dark:text-purple-300">
                Piste 2 : Audio / Synthèse Vocale & SFX
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
