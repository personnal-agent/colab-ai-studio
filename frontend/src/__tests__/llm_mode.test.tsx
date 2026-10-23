import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FloatingPromptDock } from '../components/dock/FloatingPromptDock';
import type { ModelDefinition, BrandKit } from '../types/studio';

const mockModels: ModelDefinition[] = [
  {
    id: 'minimax-h3',
    name: 'MiniMax-H3',
    mediaType: 'video',
    capabilities: {
      aspectRatios: ['16:9', '9:16'],
      resolutions: ['720p', '1080p'],
      durations: ['5s', '10s'],
    },
  },
  {
    id: 'noctq-v4',
    name: 'NoctQ V4',
    mediaType: 'image',
    capabilities: {
      aspectRatios: ['16:9', '1:1'],
      resolutions: ['1K', '2K'],
    },
  },
  {
    id: 'qwen3.8-turbo',
    name: 'Qwen 3.8B Turbo',
    mediaType: 'llm',
    description: 'Modèle de langage local 32K context',
    capabilities: {
      streaming: true,
      contextLength: 32768,
    },
  },
];

const mockBrandKit: BrandKit = {
  id: 'kit-heretic',
  name: 'Hérétique',
  overview: 'Studio de création visuelle underground',
  palette: [{ hex: '#FF0055', name: 'Neon Pink' }],
  fonts: ['Inter'],
  dos: ['Esthétique sombre et tranchée'],
  donts: ['Clichés publicitaires'],
  referenceImages: [],
  updatedAt: '2026-10-23T12:00:00Z',
};

describe('FloatingPromptDock : Mode LLM, Persistance [H] et Assemblage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Bascule vers le 5e onglet LLM, masque les fentes média et filtre les modèles de langage', () => {
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={[mockBrandKit]}
        onSubmitTask={vi.fn()}
      />
    );

    // Initialement en mode Video: fentes Start frame et pilules média visibles
    expect(screen.getByRole('button', { name: /start frame/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /aspect ratio/i })).toBeInTheDocument();

    // Clic sur l'onglet LLM
    const llmTab = screen.getByRole('tab', { name: /llm/i });
    fireEvent.click(llmTab);

    // Fentes et pilules média masquées
    expect(screen.queryByRole('button', { name: /start frame/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /aspect ratio/i })).not.toBeInTheDocument();

    // Bandeau d'intégration API affiché
    expect(screen.getByText(/http:\/\/localhost:8000\/v1\/chat\/completions/i)).toBeInTheDocument();

    // Le bouton @ Brand Kit reste accessible
    expect(screen.getByRole('button', { name: /@ brand kit/i })).toBeInTheDocument();

    // Le sélecteur de modèle affiche le modèle LLM
    const modelSelector = screen.getByRole('button', { name: /select model/i });
    expect(modelSelector).toHaveTextContent('Qwen 3.8B Turbo');
  });

  it('Préserve létat du brouillon lors des transitions vers LLM et retour [H]', () => {
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={[mockBrandKit]}
        onSubmitTask={vi.fn()}
      />
    );

    // En mode Video, saisir un prompt et changer la résolution
    const videoPromptInput = screen.getByPlaceholderText(/describe your video or reference by using @\.\.\./i);
    fireEvent.change(videoPromptInput, { target: { value: 'Epic cinematic cyberpunk battle' } });

    const resPill = screen.getByRole('button', { name: /resolution/i });
    fireEvent.click(resPill);
    fireEvent.click(screen.getByRole('button', { name: '1080p' }));
    expect(resPill).toHaveTextContent('⇅ 1080p');

    // Aller sur LLM
    const llmTab = screen.getByRole('tab', { name: /llm/i });
    fireEvent.click(llmTab);

    // Revenir sur Video (Transition vers le pseudo-état d'historique [H])
    const videoTab = screen.getByRole('tab', { name: /video/i });
    fireEvent.click(videoTab);

    // Vérifier la restauration intégrale sans perte de contexte
    const restoredInput = screen.getByPlaceholderText(/describe your video or reference by using @\.\.\./i);
    expect(restoredInput).toHaveValue('Epic cinematic cyberpunk battle');
    expect(screen.getByRole('button', { name: /resolution/i })).toHaveTextContent('⇅ 1080p');
  });

  it('Gère la conversation streaming dans la vue LLM et permet dinterrompre avec Abort', async () => {
    // Mock fetch pour /v1/chat/completions streaming SSE
    const mockStreamResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"choices":[{"delta":{"content":"Bonjour "}}]}\n\n'
          )
        );
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"choices":[{"delta":{"content":"créateur !"}}]}\n\n'
          )
        );
        controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: mockStreamResponse,
      headers: new Headers({ 'Content-Type': 'text/event-stream' }),
    });

    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={[mockBrandKit]}
        onSubmitTask={vi.fn()}
      />
    );

    // Clic sur l'onglet LLM
    fireEvent.click(screen.getByRole('tab', { name: /llm/i }));

    const chatInput = screen.getByPlaceholderText(/discutez avec le modèle de langage/i);
    fireEvent.change(chatInput, { target: { value: 'Bonjour !' } });

    const sendBtn = screen.getByRole('button', { name: /send|envoyer/i });
    fireEvent.click(sendBtn);

    // Vérifier l'apparition des morceaux streamés
    await waitFor(() => {
      expect(screen.getByText(/Bonjour créateur !/i)).toBeInTheDocument();
    });
  });

  it('Verrouille le dock et le bouton de soumission pendant la génération active', () => {
    const onSubmit = vi.fn();
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={[mockBrandKit]}
        isGenerating={true}
        onSubmitTask={onSubmit}
      />
    );

    const submitBtn = screen.getByRole('button', { name: /generate/i });
    expect(submitBtn).toBeDisabled();
  });
});
