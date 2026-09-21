/**
 * Onglet Comparaison — l'appel, le rendu, et l'erreur dite.
 *
 * Le point sensible de cet écran est que la comparaison est INTERROGÉE, pas
 * calculée localement : deux pays choisis, un appel, un verdict affiché. Si
 * l'appel échoue et que l'écran retombe silencieusement sur son état
 * d'accueil, le lecteur croit avoir oublié de cliquer — et refait l'analyse
 * en boucle sans jamais savoir que le service est en panne.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import CountryComparison from './CountryComparison';

vi.mock('axios');

// Même parti pris que RegulatoryComplianceTab : le vrai Select Radix dépasse
// les délais sur les runners CI, sans rien apporter au contrat testé.
vi.mock('../ui/select', async () => {
  const React = await import('react');
  const SelectContext = React.createContext({ value: '', onValueChange: () => {} });
  const Select = ({ value = '', onValueChange, children }) => (
    <SelectContext.Provider value={{ value, onValueChange }}>{children}</SelectContext.Provider>
  );
  const SelectTrigger = React.forwardRef(({ children, ...props }, ref) => (
    <button ref={ref} type="button" role="combobox" {...props}>{children}</button>
  ));
  const SelectValue = ({ placeholder }) => {
    const { value } = React.useContext(SelectContext);
    return <span>{value || placeholder}</span>;
  };
  const SelectContent = ({ children }) => <div>{children}</div>;
  const SelectItem = React.forwardRef(({ children, value, ...props }, ref) => {
    const { onValueChange } = React.useContext(SelectContext);
    return (
      <button ref={ref} type="button" role="option" onClick={() => onValueChange(value)} {...props}>
        {children}
      </button>
    );
  });
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
});

const COMPARISON = {
  economic_comparison: { gdp_a: 400, gdp_b: 250 },
  bilateral_trade: { exports_a_to_b_musd: 120, exports_b_to_a_musd: 80, balance_musd: 40 },
  trade_complementarity: { score: 0.61 },
  afcfta_potential: {},
  sources: ['IMF', 'OEC'],
  note: null,
};

/** Choisit un pays dans chacun des deux sélecteurs, puis lance l'analyse. */
async function comparerDeuxPays() {
  const options = screen.getAllByRole('option');
  await userEvent.click(options[0]);                       // pays A
  await userEvent.click(options[options.length - 1]);      // pays B
  const boutons = screen.getAllByRole('button');
  const lancer = boutons.find((b) => /analyser|comparer/i.test(b.textContent || ''));
  await userEvent.click(lancer);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('CountryComparison', () => {
  it('invite à choisir deux pays tant que rien n’est sélectionné', () => {
    render(<CountryComparison language="fr" />);
    expect(screen.getByText(/Sélectionnez deux pays/i)).toBeInTheDocument();
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('interroge la comparaison et affiche le résultat', async () => {
    axios.get.mockResolvedValue({ data: COMPARISON });
    render(<CountryComparison language="fr" />);
    await comparerDeuxPays();
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    expect(axios.get.mock.calls[0][0]).toMatch(/\/ai\/compare$/);
    await waitFor(() =>
      expect(screen.queryByText(/Sélectionnez deux pays/i)).not.toBeInTheDocument());
  });

  it('montre l’erreur du service au lieu de retomber sur l’écran d’accueil', async () => {
    axios.get.mockRejectedValue({ response: { data: { detail: 'Comparaison indisponible' } } });
    render(<CountryComparison language="fr" />);
    await comparerDeuxPays();
    expect(await screen.findByText('Comparaison indisponible')).toBeInTheDocument();
  });
});
