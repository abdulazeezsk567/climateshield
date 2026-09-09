import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MaskedField } from '../components/MaskedField.js';
import { AuthProvider } from '../services/authContext.js';

describe('MaskedField Component', () => {
  it('renders masked bullets by default', () => {
    render(
      <AuthProvider>
        <MaskedField value="Ganga Agro Processors" fieldName="BORROWER_NAME" targetId="SFL-BR-0104" />
      </AuthProvider>
    );

    expect(screen.queryByText('Ganga Agro Processors')).not.toBeInTheDocument();
    expect(screen.getByText('••••••••••••')).toBeInTheDocument();
  });

  it('unmasks the value upon clicking the toggle button', () => {
    render(
      <AuthProvider>
        <MaskedField value="Ganga Agro Processors" fieldName="BORROWER_NAME" targetId="SFL-BR-0104" />
      </AuthProvider>
    );

    const toggleBtn = screen.getByRole('button', { name: /reveal sensitive data/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByText('Ganga Agro Processors')).toBeInTheDocument();
    expect(screen.queryByText('••••••••••••')).not.toBeInTheDocument();
  });

  it('masks the value again when clicked a second time', () => {
    render(
      <AuthProvider>
        <MaskedField value="Ganga Agro Processors" fieldName="BORROWER_NAME" targetId="SFL-BR-0104" />
      </AuthProvider>
    );

    const toggleBtn = screen.getByRole('button', { name: /reveal sensitive data/i });
    // Reveal
    fireEvent.click(toggleBtn);
    expect(screen.getByText('Ganga Agro Processors')).toBeInTheDocument();

    // Hide again
    fireEvent.click(toggleBtn);
    expect(screen.getByText('••••••••••••')).toBeInTheDocument();
    expect(screen.queryByText('Ganga Agro Processors')).not.toBeInTheDocument();
  });
});
