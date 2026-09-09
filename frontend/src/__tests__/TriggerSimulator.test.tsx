import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TriggerSimulator } from '../views/TriggerSimulator.js';
import { AuthProvider } from '../services/authContext.js';

describe('TriggerSimulator View', () => {
  it('renders 3-point visual deviation calculation panel', () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <TriggerSimulator initialDistrict="Varanasi" onNavigateToInterventions={handleNavigate} />
      </AuthProvider>
    );

    expect(screen.getByText('Interactive Climate Anomaly Simulator')).toBeInTheDocument();
    expect(screen.getByText(/10-Year Historical Normal/i)).toBeInTheDocument();
    expect(screen.getByText(/Extreme P95 Trigger Threshold/i)).toBeInTheDocument();
    expect(screen.getByText(/Selected \/ Injected Observation/i)).toBeInTheDocument();
  });

  it('switches hazard type to drought and updates unit labels', () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <TriggerSimulator initialDistrict="Varanasi" onNavigateToInterventions={handleNavigate} />
      </AuthProvider>
    );

    const droughtBtn = screen.getByRole('button', { name: /drought/i });
    fireEvent.click(droughtBtn);

    // Baseline should now reflect dry days
    expect(screen.getAllByText(/dry days/i).length).toBeGreaterThan(0);
  });

  it('executes parametric simulation and displays automated LMS action', async () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <TriggerSimulator initialDistrict="Varanasi" onNavigateToInterventions={handleNavigate} />
      </AuthProvider>
    );

    const executeBtn = screen.getByRole('button', { name: /execute parametric simulation/i });
    fireEvent.click(executeBtn);

    // Wait for simulation outcome to render
    await waitFor(() => {
      expect(screen.getByText('Parametric Relief Action Dispatched')).toBeInTheDocument();
      expect(screen.getByText('LMS Actions Dispatched')).toBeInTheDocument();
      expect(screen.getByText('Relief Capital Volume')).toBeInTheDocument();
    });
  });
});
