import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { InterventionLog } from '../views/InterventionLog.js';
import { AuthProvider } from '../services/authContext.js';

describe('InterventionLog View', () => {
  it('renders intervention records with 4-stage state machine pills', async () => {
    render(
      <AuthProvider>
        <InterventionLog />
      </AuthProvider>
    );

    expect(screen.getByText('MSME Intervention & LMS Lifecycle Log')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('INT-2026-00104')).toBeInTheDocument();
      expect(screen.getByText('INT-2026-00105')).toBeInTheDocument();
      expect(screen.getByText('INT-2026-00219')).toBeInTheDocument();
      expect(screen.getByText('INT-2026-00342')).toBeInTheDocument();
    });
  });

  it('displays correlation IDs linking interventions to trigger audit trail', async () => {
    render(
      <AuthProvider>
        <InterventionLog />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/corr-7f8b9a2c-104/i).length).toBeGreaterThan(0);
    });
  });

  it('opens intervention dossier modal upon row click', async () => {
    render(
      <AuthProvider>
        <InterventionLog />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('INT-2026-00104')).toBeInTheDocument();
    });

    const rowItem = screen.getByText('INT-2026-00104');
    fireEvent.click(rowItem);

    await waitFor(() => {
      expect(screen.getByText('Intervention Lifecycle Dossier')).toBeInTheDocument();
      expect(screen.getByText(/Simulated LMS Webhook Payload/i)).toBeInTheDocument();
    });
  });
});
