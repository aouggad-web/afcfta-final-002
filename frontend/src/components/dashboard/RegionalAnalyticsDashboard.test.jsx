import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import RegionalAnalyticsDashboard from './RegionalAnalyticsDashboard';

vi.mock('axios');
vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }));

beforeEach(() => {
  axios.get.mockResolvedValue({ data: {} });
});

// Décision de l'exploitant du 06/11/2026 : l'export Excel est réservé à
// l'administrateur, le PDF permis à toutes les formules.
describe('RegionalAnalyticsDashboard — exports', () => {
  it('ne propose que le PDF à un abonné', () => {
    useAuth.mockReturnValue({ user: { role: 'user', export_formats: ['pdf'] } });
    render(<RegionalAnalyticsDashboard language="fr" />);

    expect(screen.queryByRole('button', { name: /Excel/ })).toBeNull();
    expect(screen.getByRole('button', { name: /PDF/ })).toBeInTheDocument();
  });

  it('propose Excel et PDF à l’administrateur', () => {
    useAuth.mockReturnValue({ user: { role: 'admin', export_formats: ['csv', 'excel', 'pdf'] } });
    render(<RegionalAnalyticsDashboard language="fr" />);

    expect(screen.getByRole('button', { name: /Excel/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /PDF/ })).toBeInTheDocument();
  });
});
