import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from '../App.js';

describe('End-to-End Operational Workflow', () => {
  it('completes the full flow: login -> portfolio dashboard -> simulate trigger -> intervention log', async () => {
    render(<App />);

    // Step 1: Verify authenticated dashboard shell loads
    await waitFor(() => {
      expect(screen.getByText('MSME Portfolio Climate Risk')).toBeInTheDocument();
      expect(screen.getByText('SFL-GATEWAY : ONLINE')).toBeInTheDocument();
    });

    // Step 2: Navigate to Trigger Simulator via top navbar tab
    const simulatorTab = screen.getByRole('tab', { name: /trigger simulator/i });
    fireEvent.click(simulatorTab);

    // Verify Trigger Simulator view is active
    await waitFor(() => {
      expect(screen.getByText('Interactive Climate Anomaly Simulator')).toBeInTheDocument();
      expect(screen.getByText(/Extreme P95 Trigger Threshold/i)).toBeInTheDocument();
    });

    // Step 3: Configure and execute parametric simulation in Varanasi
    const executeBtn = screen.getByRole('button', { name: /execute parametric simulation/i });
    fireEvent.click(executeBtn);

    // Verify simulation output with LMS dispatch is displayed
    await waitFor(() => {
      expect(screen.getByText('Parametric Relief Action Dispatched')).toBeInTheDocument();
      expect(screen.getByText(/Open Intervention Log/i)).toBeInTheDocument();
    });

    // Step 4: Follow the deep link button into the Intervention Log
    const openInterventionsBtn = screen.getByRole('button', { name: /open intervention log/i });
    fireEvent.click(openInterventionsBtn);

    // Step 5: Verify the Intervention Log renders the 4-stage LMS state machine entries
    await waitFor(() => {
      expect(screen.getByText('MSME Intervention & LMS Lifecycle Log')).toBeInTheDocument();
      expect(screen.getAllByText(/corr-7f8b9a2c/i).length).toBeGreaterThan(0);
      expect(screen.getByText('INT-2026-00104')).toBeInTheDocument();
    });
  });
});
