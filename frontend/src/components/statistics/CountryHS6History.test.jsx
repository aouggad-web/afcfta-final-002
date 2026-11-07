import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import CountryHS6History from './CountryHS6History';

vi.mock('axios');
vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }));

const historique = {
  source: 'OEC / BACI',
  country_name: 'Algérie',
  hs_code: '270900',
  currency: 'USD',
  chart_rows: [{ year: 2022, exports: 1_000_000, imports: 500_000, balance: 500_000 }],
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
  axios.get.mockResolvedValue({ data: historique });
});

// PDF des résultats permis à toutes les formules (décision de l'exploitant du
// 06/11/2026).
describe('CountryHS6History — fiche PDF', () => {
  it('propose les deux fiches PDF à un abonné', async () => {
    useAuth.mockReturnValue({ user: { role: 'user', export_formats: ['pdf'] } });
    render(<CountryHS6History language="fr" />);

    expect(await screen.findByTestId('hs6-export-pdf-light')).toBeInTheDocument();
    expect(screen.getByTestId('hs6-export-pdf-dark')).toBeInTheDocument();
  });
});
