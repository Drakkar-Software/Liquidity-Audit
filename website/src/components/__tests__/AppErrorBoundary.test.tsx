import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppErrorBoundary } from '../AppErrorBoundary';

vi.mock('../../lib/monitoring', () => ({
  captureAppError: vi.fn(),
}));

function ThrowOnRender(): null {
  throw new Error('Test render failure');
}

describe('AppErrorBoundary', () => {
  it('renders fallback UI when a child throws during render', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <MemoryRouter>
        <AppErrorBoundary>
          <ThrowOnRender />
        </AppErrorBoundary>
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reload page' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back home' })).toHaveAttribute('href', '/');

    consoleError.mockRestore();
  });
});
