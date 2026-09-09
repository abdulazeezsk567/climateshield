import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { PortfolioDashboard } from '../views/PortfolioDashboard.js';
import { AuthProvider } from '../services/authContext.js';

describe('PortfolioDashboard View', () => {
  it('renders dashboard heading and telemetry metrics', async () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <PortfolioDashboard onNavigateToSimulator={handleNavigate} />
      </AuthProvider>
    );

    expect(screen.getByText('MSME Portfolio Climate Risk')).toBeInTheDocument();
    expect(screen.getByText('Spatial Telemetry Layer')).toBeInTheDocument();

    // Verify KPI metric cards render
    await waitFor(() => {
      expect(screen.getByText('Total Monitored Exposure')).toBeInTheDocument();
      expect(screen.getByText('High-Risk Exposure')).toBeInTheDocument();
      expect(screen.getByText('Operational Districts')).toBeInTheDocument();
    });
  });

  it('renders district geospatial heatmap clusters with hazard tags', async () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <PortfolioDashboard onNavigateToSimulator={handleNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Varanasi/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Barabanki/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Patna/i).length).toBeGreaterThan(0);
    });
  });

  it('filters borrower roster when sector filter is changed', async () => {
    const handleNavigate = vi.fn();

    render(
      <AuthProvider>
        <PortfolioDashboard onNavigateToSimulator={handleNavigate} />
      </AuthProvider>
    );

    // Wait for borrowers to load
    await waitFor(() => {
      expect(screen.getByText('SFL-BR-0104')).toBeInTheDocument();
    });

    // Change sector filter to 'Textiles'
    const [sectorSelect] = screen.getAllByRole('combobox');
    fireEvent.change(sectorSelect, { target: { value: 'Textiles' } });

    // Awadh Weaving Mills should be present, while Agri Processors should be filtered out
    await waitFor(() => {
      expect(screen.getByText('SFL-BR-0219')).toBeInTheDocument();
      expect(screen.queryByText('SFL-BR-0104')).not.toBeInTheDocument();
    });
  });
});
