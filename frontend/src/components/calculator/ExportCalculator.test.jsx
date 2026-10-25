/**
 * Écran Export : les pays proposés sont ceux dont le socle porte des droits de
 * sortie, et une ligne que la source ne permet pas de chiffrer est montrée avec
 * sa raison — jamais comme un zéro.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ExportCalculator from './ExportCalculator';

vi.mock('axios');

// Même parti pris que CountryComparison : le vrai Select Radix dépasse les
// délais sur les runners CI, sans rien apporter au contrat testé.
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

const CACAO = {
  pays: 'CIV',
  position: { designation: '--- Fèves de cacao' },
  valeur: 1000000,
  droits_export_publies: true,
  export: {
    etat: 'INDISPONIBLE',
    total_droits: 0,
    manques: [{ code: 'DUS', statut: 'ASSIETTE_INDISPONIBLE' }],
    lignes: [{
      code: 'DUS',
      libelle: 'Droit Unique de Sortie (export)',
      montant: null,
      statut: 'ASSIETTE_INDISPONIBLE',
      note: 'Procédure DGD : « CACAO (TAUX = 14.6 % DU PRIX CAF DE REFERENCE) »',
    }],
  },
};

describe('ExportCalculator', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    axios.get.mockResolvedValue({ data: { pays: { CIV: 97, TUN: 17530 } } });
  });

  it("propose les pays couverts et montre la raison d'un droit non chiffré", async () => {
    axios.post.mockResolvedValue({ data: CACAO });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('CIV — 97 positions avec droit de sortie'));
    expect(screen.getByLabelText('Devise')).toHaveValue('XOF');
    await userEvent.type(screen.getByLabelText('Position nationale'), '1801001100');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '1000000');
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/calcul\/export$/),
      { pays: 'CIV', code_sh: '1801001100', valeur: 1000000, devise: 'XOF' },
    );
    expect(await screen.findByText('Assiette non établie')).toBeInTheDocument();
    expect(screen.getByText(/PRIX CAF DE REFERENCE/)).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.getByText('Non chiffrable')).toBeInTheDocument();
  });

  it("dit qu'une position nationale est requise", async () => {
    axios.post.mockRejectedValue({ response: { data: { detail: { code: 'POSITION_NATIONALE_REQUISE' } } } });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('TUN — 17530 positions avec droit de sortie'));
    await userEvent.type(screen.getByLabelText('Position nationale'), '080410');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '1000');
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(await screen.findByRole('alert')).toHaveTextContent('Position nationale requise');
  });
});
