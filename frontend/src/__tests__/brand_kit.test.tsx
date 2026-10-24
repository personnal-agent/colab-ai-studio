import { useState } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrandKitSelectorPopover } from '../components/brand-kit/BrandKitSelectorPopover';
import { BrandKitHoverCard } from '../components/brand-kit/BrandKitHoverCard';
import { PromptEditorWithChip } from '../components/brand-kit/PromptEditorWithChip';
import { BrandKitCreateModal } from '../components/brand-kit/BrandKitCreateModal';
import { BrandKitInspectorModal } from '../components/brand-kit/BrandKitInspectorModal';
import type { BrandKit } from '../types/studio';

const mockBrandKitApple: BrandKit = {
  id: 'bk-apple-1', name: 'Apple', overview: 'Minimalist consumer hardware and software design.',
  logos: [{ id: 'logo-1', filePath: '/assets/apple-black.svg', label: 'Dark mono' }, { id: 'logo-2', filePath: '/assets/apple-white.svg', label: 'Light mono' }],
  colors: [{ hex: '#000000', label: 'Black', isDominant: true }, { hex: '#FFFFFF', label: 'White' }, { hex: '#A2AAAD', label: 'Silver' }],
  fonts: [{ family: 'SF Pro Display', weight: 'Bold' }, { family: 'SF Pro Text', weight: 'Regular' }],
  referenceImages: [{ id: 'ref-1', filePath: '/assets/iphone.png' }],
  voices: [{ id: 'voice-1', name: 'Keynote Speaker', tone: 'Calm and precise' }],
  captions: [{ id: 'cap-1', format: 'Centered uppercase', style: 'minimal' }],
  guidelines: [
    { kind: 'do', text: 'Use generous whitespace and clean typography' },
    { kind: 'dont', text: 'Do not distort the logo or add drop shadows' },
  ],
  createdAt: '2026-01-01T10:00:00Z', updatedAt: '2026-10-24T16:00:00Z', lastUsedAt: '2026-10-24T16:15:00Z',
};

const mockBrandKitNike: BrandKit = {
  id: 'bk-nike-2', name: 'Nike', overview: 'Athletic performance and motivation.',
  logos: [{ id: 'logo-3', filePath: '/assets/swoosh.svg', label: 'Swoosh' }],
  colors: [{ hex: '#FF6600', label: 'Safety Orange', isDominant: true }],
  fonts: [{ family: 'Futura', weight: 'Extra Bold' }],
  referenceImages: [], voices: [], captions: [],
  guidelines: [{ kind: 'do', text: 'Inspire athletes worldwide' }],
  createdAt: '2026-02-01T10:00:00Z', updatedAt: '2026-03-01T10:00:00Z', lastUsedAt: '2026-03-01T10:00:00Z',
};

describe('Brand Kit System (TDD)', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  describe('BrandKitHoverCard', () => {
    it('renders logo, title, asset count, freshness, and hex color swatches', () => {
      render(<BrandKitHoverCard brandKit={mockBrandKitApple} />);
      expect(screen.getByRole('heading', { level: 4, name: 'Apple' })).toBeInTheDocument();
      expect(screen.getByText(/8 assets/i)).toBeInTheDocument();
      expect(screen.getByText(/Updated/i)).toBeInTheDocument();
      expect(screen.getByTitle('#000000 - Black')).toBeInTheDocument();
      expect(screen.getByTitle('#FFFFFF - White')).toBeInTheDocument();
      expect(screen.getByTitle('#A2AAAD - Silver')).toBeInTheDocument();
    });
  });

  describe('BrandKitSelectorPopover', () => {
    it('displays empty state with "Aucun brand kit" and create button when list is empty', () => {
      const onCreateClick = vi.fn();
      render(
        <BrandKitSelectorPopover
          isOpen={true} onOpenChange={vi.fn()} brandKits={[]}
          onSelectBrandKit={vi.fn()} onCreateBrandKitClick={onCreateClick}
        />
      );
      expect(screen.getByText(/Aucun brand kit/i)).toBeInTheDocument();
      const createBtn = screen.getByRole('button', { name: /Create brand kit/i });
      expect(createBtn).toBeInTheDocument();
      fireEvent.click(createBtn);
      expect(onCreateClick).toHaveBeenCalledTimes(1);
    });

    it('displays list of brand kits sorted by lastUsedAt and allows selection and inspection', async () => {
      const onSelect = vi.fn();
      const onInspect = vi.fn();
      render(
        <BrandKitSelectorPopover
          isOpen={true} onOpenChange={vi.fn()}
          brandKits={[mockBrandKitNike, mockBrandKitApple]}
          onSelectBrandKit={onSelect} onInspectBrandKit={onInspect}
          onCreateBrandKitClick={vi.fn()}
        />
      );
      const kitButtons = screen.getAllByTestId('brand-kit-item');
      expect(kitButtons[0]).toHaveTextContent('Apple');
      expect(kitButtons[1]).toHaveTextContent('Nike');

      fireEvent.click(screen.getByRole('button', { name: /Select Apple/i }));
      expect(onSelect).toHaveBeenCalledWith(mockBrandKitApple);

      fireEvent.click(screen.getByRole('button', { name: /Inspect Apple/i }));
      expect(onInspect).toHaveBeenCalledWith(mockBrandKitApple);
    });
  });

  describe('PromptEditorWithChip', () => {
    function ControlledPromptEditor() {
      const [prompt, setPrompt] = useState('Generate a flagship commercial');
      const [selectedKit, setSelectedKit] = useState<BrandKit | null>(mockBrandKitApple);
      return (
        <PromptEditorWithChip
          prompt={prompt} onPromptChange={setPrompt} selectedBrandKit={selectedKit}
          onRemoveBrandKit={() => setSelectedKit(null)} onOpenBrandKitSelector={vi.fn()}
        />
      );
    }

    it('renders prompt input and displays atomic chip [@Apple] that is removed in one block', () => {
      render(<ControlledPromptEditor />);
      const chip = screen.getByTestId('brand-kit-chip');
      expect(chip).toHaveTextContent('[@Apple]');

      fireEvent.click(screen.getByRole('button', { name: /Remove Apple brand kit/i }));
      expect(screen.queryByTestId('brand-kit-chip')).not.toBeInTheDocument();
    });

    it('triggers popover when clicking the @ button or typing @', () => {
      const onOpenSelector = vi.fn();
      render(
        <PromptEditorWithChip
          prompt="Design " onPromptChange={vi.fn()} selectedBrandKit={null}
          onRemoveBrandKit={vi.fn()} onOpenBrandKitSelector={onOpenSelector}
        />
      );
      fireEvent.click(screen.getByRole('button', { name: /@ Brand Kit/i }));
      expect(onOpenSelector).toHaveBeenCalledTimes(1);

      const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);
      fireEvent.change(textarea, { target: { value: 'Design @' } });
      expect(onOpenSelector).toHaveBeenCalledTimes(2);

      // Typing characters after @ must NOT re-trigger selector popover
      fireEvent.change(textarea, { target: { value: 'Design @A' } });
      expect(onOpenSelector).toHaveBeenCalledTimes(2);
    });

    it('does not re-trigger selector when typing elsewhere in a prompt ending with @', () => {
      const onOpenSelector = vi.fn();
      function TestWrapper() {
        const [prompt, setPrompt] = useState('Design @');
        return (
          <PromptEditorWithChip
            prompt={prompt}
            onPromptChange={setPrompt}
            selectedBrandKit={null}
            onRemoveBrandKit={vi.fn()}
            onOpenBrandKitSelector={onOpenSelector}
          />
        );
      }
      render(<TestWrapper />);
      const textarea = screen.getByPlaceholderText(/Describe what you want to create/i);

      // Saisir 'X' au tout début avec curseur en position 1 (le prompt contient toujours '@' à la fin)
      fireEvent.change(textarea, { target: { value: 'XDesign @', selectionStart: 1 } });
      expect(onOpenSelector).not.toHaveBeenCalled();
    });
  });

  describe('BrandKitCreateModal', () => {
    it('supports 3 initialization methods (Blank, Brand files, Website) and triggers creation', async () => {
      const handleCreate = vi.fn().mockResolvedValue(mockBrandKitApple);
      const handleSuccess = vi.fn();
      render(
        <BrandKitCreateModal
          isOpen={true} onClose={vi.fn()} onCreateBrandKit={handleCreate} onSuccess={handleSuccess}
        />
      );
      expect(screen.getByRole('button', { name: /Blank/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Brand files/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Website/i })).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Website/i }));
      fireEvent.change(screen.getByPlaceholderText(/https:\/\/example\.com/i), { target: { value: 'https://apple.com' } });
      fireEvent.change(screen.getByPlaceholderText(/Brand name/i), { target: { value: 'Apple Inc' } });

      fireEvent.click(screen.getByRole('button', { name: /Continue/i }));
      await waitFor(() => {
        expect(handleCreate).toHaveBeenCalledWith(
          expect.objectContaining({ source: 'website', name: 'Apple Inc', url: 'https://apple.com' })
        );
        expect(handleSuccess).toHaveBeenCalledWith(mockBrandKitApple);
      });
    });
  });

  describe('BrandKitInspectorModal', () => {
    it('renders 8 lateral sections and displays respective assets with "Use this brand kit" action', () => {
      const onSelect = vi.fn();
      render(
        <BrandKitInspectorModal
          brandKit={mockBrandKitApple} isOpen={true} onClose={vi.fn()} onSelectBrandKit={onSelect}
        />
      );
      ['Overview', 'Logos', 'Colors', 'Fonts', 'Reference images', 'Voices', 'Captions', 'Guidelines'].forEach((sec) => {
        expect(screen.getByRole('button', { name: sec })).toBeInTheDocument();
      });
      expect(screen.getByText('Minimalist consumer hardware and software design.')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Logos/i }));
      expect(screen.getByText('Dark mono')).toBeInTheDocument();
      expect(screen.getByText('Light mono')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Colors/i }));
      expect(screen.getByText('#000000')).toBeInTheDocument();
      expect(screen.getByText('Black')).toBeInTheDocument();
      expect(screen.getByText('Dominant')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Fonts/i }));
      expect(screen.getByText('SF Pro Display')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Guidelines/i }));
      expect(screen.getByText(/Use generous whitespace/i)).toBeInTheDocument();
      expect(screen.getByText(/Do not distort the logo/i)).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Use this brand kit/i }));
      expect(onSelect).toHaveBeenCalledWith(mockBrandKitApple);
    });
  });
});
