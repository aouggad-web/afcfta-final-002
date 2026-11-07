import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useAuth } from '../../context/AuthContext';
import OpportunityPdfExport from './OpportunityPdfExport';

vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }));

// PDF des résultats permis à toutes les formules (décision de l'exploitant du
// 06/11/2026) : les deux boutons des écrans Opportunités et Rapports restent.
describe('OpportunityPdfExport', () => {
  it.each([
    ['un abonné free', { user: { role: 'user', export_formats: ['pdf'] } }],
    ['un abonné Business', { user: { role: 'user', export_formats: ['pdf'] } }],
    ['l’administrateur', { user: { role: 'admin', export_formats: ['csv', 'excel', 'pdf'] } }],
  ])('montre les deux boutons PDF à %s', (_, session) => {
    useAuth.mockReturnValue(session);
    render(<OpportunityPdfExport getSpec={() => null} />);

    expect(screen.getByTestId('opportunity-pdf-light')).toBeInTheDocument();
    expect(screen.getByTestId('opportunity-pdf-dark')).toBeInTheDocument();
  });
});
