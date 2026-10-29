import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FloatingPromptDock } from '../components/dock/FloatingPromptDock';
import { apiClient } from '../services/apiClient';
import type { ModelDefinition, BrandKit } from '../types/studio';

const mockModels: ModelDefinition[] = [
  {
    id: 'minimax-h3',
    name: 'MiniMax H3 Video',
    type: 'video',
    badge: 'Local',
    capabilities: {
      aspectRatios: ['16:9', '9:16'],
      resolutions: ['1080p'],
      durations: ['5s', '10s'],
    },
  },
];

const mockBrandKits: BrandKit[] = [
  {
    id: 'bk-1',
    name: 'CyberpunkStudios',
    overview: 'Cyberpunk visual identity and assets',
    colors: [],
    logos: [],
    fonts: [],
    referenceImages: [],
    voices: [],
    captions: [],
    guidelines: [],
    createdAt: '2026-10-29T10:00:00Z',
    updatedAt: '2026-10-29T10:00:00Z',
  },
];

const mockInstructions = [
  {
    id: 'inst-1',
    title: 'Volumetric Cinematic Lighting',
    description: 'Use 35mm lens with soft atmospheric mist',
    isActive: true,
    referenceAssetUrls: [],
    order: 0,
    createdAt: '2026-10-29T10:00:00Z',
    updatedAt: '2026-10-29T10:00:00Z',
  },
];

describe('FloatingPromptDock - Google Flow Pro Alignment', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(apiClient, 'listAgentInstructions').mockResolvedValue(mockInstructions);
    vi.spyOn(apiClient, 'listCharacters').mockResolvedValue([]);
    vi.spyOn(apiClient, 'estimateWorkload').mockResolvedValue({
      mediaType: 'video',
      modelId: 'minimax-h3',
      numSegments: 1,
      totalDurationSec: 5,
      isChained: false,
      estimatedSecondsGpu: 60,
      estimatedVramGb: 12,
      vramTotalGb: 16,
      detectedCharacters: [],
      detectedDialoguesCount: 0,
    });
  });

  it('renders Agent switch and toggles state', async () => {
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={mockBrandKits}
        onSubmitGeneration={vi.fn()}
      />,
    );

    const agentToggle = await screen.findByRole('switch', { name: /Basculer Agent/i });
    expect(agentToggle).toBeInTheDocument();
    expect(screen.getByText(/Agent ON/i)).toBeInTheDocument();

    fireEvent.click(agentToggle);
    expect(screen.getByText(/Agent OFF/i)).toBeInTheDocument();
  });

  it('renders EngineSelectorPill and allows switching engine preference', async () => {
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={mockBrandKits}
        onSubmitGeneration={vi.fn()}
      />,
    );

    const pill = await screen.findByRole('button', { name: /Moteur: Local RTX 5000 Ada/i });
    expect(pill).toBeInTheDocument();

    fireEvent.click(pill);

    // Menu should appear with Cloud API and Hybride
    const cloudOption = await screen.findByRole('button', { name: /Option Cloud API/i });
    fireEvent.click(cloudOption);

    expect(screen.getByRole('button', { name: /Moteur: Cloud API/i })).toBeInTheDocument();
  });

  it('opens Agent Instructions drawer and Ingredients popover', async () => {
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={mockBrandKits}
        onSubmitGeneration={vi.fn()}
      />,
    );

    // Open Agent Instructions Drawer
    const instructionsBtn = await screen.findByRole('button', { name: /Agent Instructions/i });
    fireEvent.click(instructionsBtn);

    expect(await screen.findByTestId('agent-instructions-drawer')).toBeInTheDocument();

    // Close drawer
    fireEvent.click(screen.getByLabelText('Fermer'));

    // Open Ingredients Popover
    const ingredientsBtn = screen.getAllByRole('button', { name: /@ Ingrédients/i })[0];
    fireEvent.click(ingredientsBtn);

    expect(await screen.findByTestId('ingredients-popover')).toBeInTheDocument();
  });

  it('submits generation with agentEnabled, enginePreference, and activeInstructionIds', async () => {
    const mockSubmit = vi.fn().mockResolvedValue({});
    render(
      <FloatingPromptDock
        models={mockModels}
        brandKits={mockBrandKits}
        onSubmitGeneration={mockSubmit}
      />,
    );

    await screen.findByRole('switch', { name: /Basculer Agent/i });

    // Type prompt
    const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);
    fireEvent.change(textarea, { target: { value: 'Epic drone shot of cyberpunk neon city' } });

    // Submit
    const submitBtn = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: 'Epic drone shot of cyberpunk neon city',
          parameters: expect.objectContaining({
            agentEnabled: true,
            enginePreference: 'local',
            activeInstructionIds: ['inst-1'],
          }),
        }),
      );
    });
  });
});
