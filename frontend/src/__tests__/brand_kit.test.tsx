import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrandKitSelectorPopover } from '../components/brand-kit/BrandKitSelectorPopover';
import { BrandKitHoverCard } from '../components/brand-kit/BrandKitHoverCard';
import { PromptEditorWithChip } from '../components/brand-kit/PromptEditorWithChip';
import { BrandKitCreateModal } from '../components/brand-kit/BrandKitCreateModal';
import { BrandKitInspectorModal } from '../components/brand-kit/BrandKitInspectorModal';
import type { BrandKit } from '../types/studio';

const mockKits: BrandKit[] = [
  {
    id: 'kit-apple',
    name: 'Apple',
    overview: 'Design minimaliste et technologie haut de gamme.',
    palette: [
      { hex: '#000000', name: 'Black' },
      { hex: '#F5F5F7', name: 'Off White' },
      { hex: '#0071E3', name: 'Apple Blue' },
    ],
    fonts: ['SF Pro Display', 'SF Pro Text'],
    dos: ['Lignes épurées', 'Contraste net'],
    donts: ['Bruit visuel excessif'],
    referenceImages: ['https://example.com/apple1.jpg'],
    logoPath: 'https://example.com/apple-logo.png',
    updatedAt: '2026-10-23T12:00:00Z',
    lastUsedAt: '2026-10-23T16:00:00Z',
    assetCount: 15,
  },
  {
    id: 'kit-nike',
    name: 'Nike',
    overview: 'Just do it. Athlétisme et performance.',
    palette: [{ hex: '#FF5722', name: 'Orange Swoosh' }],
    fonts: ['Futura'],
    dos: ['Dynamisme'],
    donts: ['Statisme'],
    referenceImages: [],
    updatedAt: '2026-10-20T10:00:00Z',
    lastUsedAt: '2026-10-21T10:00:00Z',
    assetCount: 8,
  },
];

describe('Système Brand Kit complet', () => {
  it('BrandKitHoverCard affiche le logo, nom, compteur dactifs et nuancier', () => {
    render(<BrandKitHoverCard kit={mockKits[0]} />);

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText(/15 assets/i)).toBeInTheDocument();
    expect(screen.getByText('Design minimaliste et technologie haut de gamme.')).toBeInTheDocument();

    const colorSwatches = screen.getAllByTestId('color-swatch');
    expect(colorSwatches.length).toBe(3);
  });

  it('BrandKitSelectorPopover gère létat vide initial avec incitation', () => {
    const onCreate = vi.fn();
    render(
      <BrandKitSelectorPopover
        brandKits={[]}
        onSelectKit={vi.fn()}
        onCreateNewKit={onCreate}
      />
    );

    const trigger = screen.getByRole('button', { name: /@ brand kit/i });
    fireEvent.click(trigger);

    expect(
      screen.getByText(/Aucun brand kit\. Définissez votre marque une fois, puis utilisez-la pour générer\./i)
    ).toBeInTheDocument();

    const createBtn = screen.getByRole('button', { name: /create brand kit/i });
    fireEvent.click(createBtn);
    expect(onCreate).toHaveBeenCalled();
  });

  it('BrandKitSelectorPopover liste les kits triés par lastUsedAt et permet de sélectionner', () => {
    const onSelect = vi.fn();
    render(
      <BrandKitSelectorPopover
        brandKits={mockKits}
        onSelectKit={onSelect}
        onCreateNewKit={vi.fn()}
      />
    );

    const trigger = screen.getByRole('button', { name: /@ brand kit/i });
    fireEvent.click(trigger);

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('Nike')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Apple'));
    expect(onSelect).toHaveBeenCalledWith(mockKits[0]);
  });

  it('PromptEditorWithChip insère un chip atomique et le supprime en un bloc par Backspace', () => {
    const onRemoveKit = vi.fn();
    const onPromptChange = vi.fn();

    const { rerender } = render(
      <PromptEditorWithChip
        prompt="A futuristic sneaker commercial"
        selectedKit={null}
        mediaType="video"
        onChange={onPromptChange}
        onRemoveKit={onRemoveKit}
        onTriggerKitPicker={vi.fn()}
      />
    );

    const textarea = screen.getByPlaceholderText(/describe your video or reference by using @\.\.\./i);
    expect(textarea).toHaveValue('A futuristic sneaker commercial');

    // Rerender avec kit actif
    rerender(
      <PromptEditorWithChip
        prompt="A futuristic sneaker commercial"
        selectedKit={mockKits[0]}
        mediaType="video"
        onChange={onPromptChange}
        onRemoveKit={onRemoveKit}
        onTriggerKitPicker={vi.fn()}
      />
    );

    const chip = screen.getByTestId('brand-kit-chip');
    expect(chip).toHaveTextContent('[@Apple]');

    // Suppression via la croix du chip ou Backspace
    const deleteBtn = screen.getByRole('button', { name: /remove brand kit/i });
    fireEvent.click(deleteBtn);
    expect(onRemoveKit).toHaveBeenCalled();
  });

  it('BrandKitCreateModal propose les 3 méthodes Blank, Brand files et Website', async () => {
    const onContinue = vi.fn();
    const onClose = vi.fn();

    render(
      <BrandKitCreateModal
        isOpen={true}
        onClose={onClose}
        onContinue={onContinue}
      />
    );

    expect(screen.getByRole('button', { name: /blank/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /brand files/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /website/i })).toBeInTheDocument();

    // Passer en mode Website
    fireEvent.click(screen.getByRole('button', { name: /website/i }));
    const urlInput = screen.getByPlaceholderText(/https:\/\/example\.com/i);
    fireEvent.change(urlInput, { target: { value: 'https://apple.com' } });

    const continueBtn = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(continueBtn);

    expect(onContinue).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'website',
        websiteUrl: 'https://apple.com',
      })
    );
  });

  it('BrandKitInspectorModal navigue entre les 8 sections et offre le bouton Use this brand kit', () => {
    const onUseKit = vi.fn();
    const onClose = vi.fn();

    render(
      <BrandKitInspectorModal
        isOpen={true}
        kit={mockKits[0]}
        onClose={onClose}
        onUseKit={onUseKit}
      />
    );

    // Vérification des 8 sections latérales
    const sections = [
      'Overview',
      'Logos',
      'Colors',
      'Fonts',
      'Reference images',
      'Voices',
      'Captions',
      'Guidelines',
    ];

    sections.forEach((section) => {
      expect(screen.getByRole('button', { name: section })).toBeInTheDocument();
    });

    // Basculer vers Colors
    fireEvent.click(screen.getByRole('button', { name: /colors/i }));
    expect(screen.getByText('Apple Blue')).toBeInTheDocument();

    // Bouton d'utilisation
    const useBtn = screen.getByRole('button', { name: /use this brand kit/i });
    fireEvent.click(useBtn);
    expect(onUseKit).toHaveBeenCalledWith(mockKits[0]);
  });
});
