import { useState } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FloatingPromptDock } from '../components/dock/FloatingPromptDock';
import { LlmChatView } from '../components/dock/LlmChatView';
import type { ModelDefinition, BrandKit } from '../types/studio';

const mockModels: ModelDefinition[] = [
  { id: 'kling-video', name: 'Kling Video 1.5', type: 'video', capabilities: { durations: ['5s', '10s'], supportsAudio: true, maxImageRefs: 5 } },
  { id: 'flux-image', name: 'Flux.1 Dev', type: 'image', capabilities: { aspectRatios: ['16:9', '1:1', '9:16'], resolutions: ['1K', '2K'] } },
  { id: 'llama-3-8b', name: 'Llama 3 8B Instruct', type: 'text', capabilities: {} },
  { id: 'qwen-2.5-7b', name: 'Qwen 2.5 7B', type: 'text', capabilities: {} },
];

const mockBrandKit: BrandKit = {
  id: 'bk-test-1', name: 'Acme', overview: 'Test overview',
  logos: [], colors: [{ hex: '#111111', label: 'Dark', isDominant: true }],
  fonts: [], referenceImages: [], voices: [], captions: [], guidelines: [],
  createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z',
};

describe('LLM Mode & FloatingPromptDock Integration (TDD)', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  describe('LlmChatView', () => {
    it('displays external API integration banner with http://localhost:8000/v1/chat/completions and copyable snippets', () => {
      render(<LlmChatView messages={[]} isStreaming={false} onStopStreaming={vi.fn()} />);
      expect(screen.getAllByText(/http:\/\/localhost:8000\/v1\/chat\/completions/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole('button', { name: /cURL/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Python/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cursor/i })).toBeInTheDocument();
    });

    it('renders message history and stop button during streaming', () => {
      const onStop = vi.fn();
      render(
        <LlmChatView
          messages={[
            { id: '1', role: 'user', content: 'Explain quantum computing' },
            { id: '2', role: 'assistant', content: 'Quantum computing uses qubits...' },
          ]}
          isStreaming={true} onStopStreaming={onStop}
        />
      );
      expect(screen.getByText('Explain quantum computing')).toBeInTheDocument();
      expect(screen.getByText(/Quantum computing uses qubits/i)).toBeInTheDocument();

      const stopBtn = screen.getByRole('button', { name: /Stop generating/i });
      expect(stopBtn).toBeInTheDocument();
      fireEvent.click(stopBtn);
      expect(onStop).toHaveBeenCalledTimes(1);
    });
  });

  describe('FloatingPromptDock', () => {
    function ControlledDockWrapper() {
      const [brandKits] = useState<BrandKit[]>([mockBrandKit]);
      return (
        <FloatingPromptDock
          models={mockModels} brandKits={brandKits}
          onCreateBrandKit={vi.fn()} onSubmitGeneration={vi.fn()}
        />
      );
    }

    it('switches to LLM tab, hides media conditioning tray and multimedia pills, but keeps @ Brand Kit button', () => {
      render(<ControlledDockWrapper />);
      fireEvent.click(screen.getByRole('tab', { name: /Video/i }));
      expect(screen.getByText(/Start frame/i)).toBeInTheDocument();

      // Switch to the 5th tab [ LLM ]
      fireEvent.click(screen.getByRole('tab', { name: /LLM/i }));
      expect(screen.queryByText(/Start frame/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/End frame/i)).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /16:9/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /5s/i })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /@ Brand Kit/i })).toBeInTheDocument();
    });

    it('filters model selector to text/LLM models in LLM mode', async () => {
      render(<ControlledDockWrapper />);
      fireEvent.click(screen.getByRole('tab', { name: /LLM/i }));
      fireEvent.click(screen.getByRole('button', { name: /Modèle/i }));

      await waitFor(() => {
        expect(screen.getAllByText('Llama 3 8B Instruct').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Qwen 2.5 7B')).toBeInTheDocument();
        expect(screen.queryByText('Kling Video 1.5')).not.toBeInTheDocument();
      });
    });

    it('preserves shallow history [H] without loss of context when switching between modes', () => {
      render(<ControlledDockWrapper />);
      const videoTab = screen.getByRole('tab', { name: /Video/i });
      fireEvent.click(videoTab);

      const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);
      fireEvent.change(textarea, { target: { value: 'Epic cinematic space battle in 4K' } });

      const llmTab = screen.getByRole('tab', { name: /LLM/i });
      fireEvent.click(llmTab);
      expect(textarea).toHaveValue('');

      fireEvent.change(textarea, { target: { value: 'Draft a system prompt for video generation' } });
      expect(textarea).toHaveValue('Draft a system prompt for video generation');

      fireEvent.click(videoTab);
      expect(textarea).toHaveValue('Epic cinematic space battle in 4K');

      fireEvent.click(llmTab);
      expect(textarea).toHaveValue('Draft a system prompt for video generation');
    });

    it('submits generation with exact mode type and catches submission errors', async () => {
      const mockSubmit = vi.fn().mockRejectedValueOnce(new Error('GPU worker offline'));
      render(
        <FloatingPromptDock
          models={mockModels} brandKits={[mockBrandKit]}
          onSubmitGeneration={mockSubmit}
        />
      );

      // In Image mode
      fireEvent.click(screen.getByRole('tab', { name: /Image/i }));
      const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);
      fireEvent.change(textarea, { target: { value: 'Futuristic city' } });

      // Click submit
      fireEvent.click(screen.getByRole('button', { name: /Submit/i }));
      await waitFor(() => {
        expect(mockSubmit).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'image', prompt: 'Futuristic city' })
        );
      });

      // Error banner must be displayed
      await waitFor(() => {
        expect(screen.getByText(/GPU worker offline/i)).toBeInTheDocument();
      });

      // Dismiss error
      fireEvent.click(screen.getByRole('button', { name: /Dismiss error/i }));
      expect(screen.queryByText(/GPU worker offline/i)).not.toBeInTheDocument();
    });

    it('allows minimizing and restoring the dock to view the gallery, preserving user input', () => {
      render(
        <FloatingPromptDock
          models={mockModels} brandKits={[mockBrandKit]}
        />
      );

      const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);
      fireEvent.change(textarea, { target: { value: 'Prompt de test pour la vidéo' } });

      // Click "Réduire"
      const reduceBtn = screen.getByRole('button', { name: /Réduire la fenêtre de saisie/i });
      fireEvent.click(reduceBtn);

      // Dock is minimized: textarea is hidden, prompt preview and "Restaurer" button appear
      expect(screen.queryByPlaceholderText(/Describe what you want to create/i)).not.toBeInTheDocument();
      expect(screen.getByText('Prompt de test pour la vidéo')).toBeInTheDocument();
      const restoreBtn = screen.getByRole('button', { name: /Restaurer la fenêtre de saisie/i });
      expect(restoreBtn).toBeInTheDocument();

      // Click "Restaurer"
      fireEvent.click(restoreBtn);

      // Dock is restored: textarea is back with preserved prompt
      const restoredTextarea = screen.getByPlaceholderText(/Describe what you want to create/i);
      expect(restoredTextarea).toBeInTheDocument();
      expect(restoredTextarea).toHaveValue('Prompt de test pour la vidéo');
    });
  });
});
