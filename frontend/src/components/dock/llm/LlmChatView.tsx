import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Copy, Check, Terminal } from 'lucide-react';
import type { BrandKit } from '../../../types/studio';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface LlmChatViewProps {
  modelId: string;
  selectedKit?: BrandKit | null;
}

export const LlmChatView: React.FC<LlmChatViewProps> = ({ modelId, selectedKit }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeSnippetTab, setActiveSnippetTab] = useState<'cursor' | 'python' | 'curl'>('curl');
  const [copied, setCopied] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleCopySnippet = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const snippets = {
    cursor: 'http://localhost:8000/v1',
    python: `import openai\nclient = openai.OpenAI(base_url="http://localhost:8000/v1", api_key="local-proxy")\nresp = client.chat.completions.create(model="${modelId}", messages=[{"role": "user", "content": "..."}])`,
    curl: `curl http://localhost:8000/v1/chat/completions \\\n  -H "Content-Type: application/json" \\\n  -d '{"model":"${modelId}","messages":[{"role":"user","content":"..."}]}'`,
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    const assistantId = `ast_${Date.now()}`;
    setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }]);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      // Préparation du message système si Brand Kit est actif
      const systemMessages = selectedKit
        ? [
            {
              role: 'system',
              content: `Vous incarnez la marque "${selectedKit.name}". Overview: ${selectedKit.overview}. Directives: ${selectedKit.dos.join(', ')}.`,
            },
          ]
        : [];

      const response = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: modelId,
          messages: [...systemMessages, ...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';
      let buffer = '';

      let reading = true;
      while (reading) {
        const { value, done } = await reader.read();
        if (done) {
          reading = false;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed === 'data: [DONE]') break;
          if (trimmed.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(trimmed.slice(6));
              const delta = parsed.choices?.[0]?.delta?.content || '';
              if (delta) {
                accumulated += delta;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantId ? { ...msg, content: accumulated } : msg
                  )
                );
              }
            } catch {
              // ignore malformed SSE line
            }
          }
        }
      }
    } catch {
      // Ignorer l'erreur d'annulation
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="w-full flex flex-col gap-2.5">
      {/* Bandeau d'intégration API compatible OpenAI */}
      <div className="p-2.5 bg-studio-subtle/80 rounded-xl border border-studio-border text-xs space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-studio-muted">
            <Terminal className="w-3.5 h-3.5" />
            <span className="font-semibold text-studio-text">API OpenAI locale :</span>
            <code className="bg-white px-1.5 py-0.5 rounded border border-studio-border font-mono text-[11px] text-studio-text">
              http://localhost:8000/v1/chat/completions
            </code>
          </div>

          <div className="flex items-center gap-1">
            {(['curl', 'python', 'cursor'] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveSnippetTab(tab)}
                className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                  activeSnippetTab === tab
                    ? 'bg-studio-text text-white'
                    : 'text-studio-muted hover:text-studio-text'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
            <button
              type="button"
              aria-label="Copy snippet"
              onClick={() => handleCopySnippet(snippets[activeSnippetTab])}
              className="p-1 rounded text-studio-muted hover:text-studio-text transition-colors"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>
      </div>

      {/* Messages conversationnels */}
      <div
        ref={scrollRef}
        className="max-h-48 overflow-y-auto space-y-2 pr-1 text-xs leading-relaxed"
      >
        {messages.length === 0 ? (
          <div className="text-center py-4 text-studio-muted italic">
            Posez une question, demandez de concevoir un prompt ou discutez avec le modèle de langage local.
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`p-2.5 rounded-xl max-w-[85%] whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'ml-auto bg-studio-text text-white'
                  : 'mr-auto bg-studio-subtle text-studio-text border border-studio-border'
              }`}
            >
              {msg.content || (
                <span className="inline-block w-2 h-3.5 bg-studio-text animate-pulse" />
              )}
            </div>
          ))
        )}
      </div>

      {/* Zone de saisie du dialogue */}
      <form onSubmit={handleSend} className="flex items-center gap-2 pt-1 border-t border-studio-border">
        <input
          type="text"
          value={input}
          placeholder="Discutez avec le modèle de langage ou demandez de l'aide..."
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-transparent text-xs sm:text-sm text-studio-text placeholder:text-[#4B5563] focus:outline-none"
        />

        {isStreaming ? (
          <button
            type="button"
            aria-label="Stop"
            onClick={handleStop}
            className="w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center hover:bg-red-700 transition-colors shadow-xs"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        ) : (
          <button
            type="submit"
            aria-label="Send"
            disabled={!input.trim()}
            className="w-8 h-8 rounded-full bg-studio-text text-white flex items-center justify-center hover:bg-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        )}
      </form>
    </div>
  );
};
