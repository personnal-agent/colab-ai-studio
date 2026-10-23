import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../App';

describe('Smoke Test App', () => {
  it('renders application title', () => {
    render(<App />);
    expect(screen.getByText('Image & Video')).toBeInTheDocument();
  });
});
