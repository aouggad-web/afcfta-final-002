/**
 * Écran Export : les pays proposés sont ceux dont le socle porte des droits de
 * sortie, et une ligne que la source ne permet pas de chiffrer est montrée avec
 * sa raison — jamais comme un zéro.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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
    axios.get.mockResolvedValue({ data: {
      pays: { CIV: 97, TUN: 17530, MDG: 266, GHA: 11516, MLI: 0 },
      questions: {
        MDG: {
          champ: 'produit_minier',
          question: 'Produit des mines au sens du Code minier (substance minérale ni de carrière ni fossile) ?',
          question_transformation: 'Substance transformée au sens du Code (abattement de 30 %, art. 288) ?',
        },
        MLI: {
          champ: 'produit_minier',
          question: 'Or ou autre produit minier, exporté par un exportateur non régi par le Code minier ?',
          question_transformation: null,
        },
      },
    } });
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
    // Rien de chiffré : pas de total, qui se lirait « rien à payer ».
    expect(screen.queryByText(/Droits de sortie chiffrés/)).not.toBeInTheDocument();
  });

  it("dit dans quelle unité la quantité est réclamée", async () => {
    axios.post.mockResolvedValue({ data: {
      pays: 'TUN',
      position: { designation: 'Piles hors d’usage' },
      provenance: { devise_nationale: 'TND' },
      export: {
        etat: 'PARTIEL',
        total_droits: 0,
        manques: [{ code: 'TAXE/FERRAILLES.EXP', motif: 'QUANTITE_REQUISE' }],
        lignes: [
          { code: 'TAXE/FERRAILLES.EXP', libelle: 'TAXE/FERRAILLES.EXP', specifique: '0.7 dinars', unite_quantite: 'centaine', montant: null, statut: 'QUANTITE_REQUISE' },
          { code: 'RPD/EXPOR', libelle: 'REDEV.PREST.DOUA/EXP', montant: null, statut: 'ASSIETTE_INCOMPLETE' },
        ],
      },
    } });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('TUN — 17530 positions avec droit de sortie'));
    await userEvent.type(screen.getByLabelText('Position nationale'), '8549141000');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '1000');
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(await screen.findByText('Quantité requise (centaine)')).toBeInTheDocument();
    expect(screen.getByText('0.7 dinars / centaine')).toBeInTheDocument();
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

  it('demande le taux comme on le lit et envoie au moteur son inverse', async () => {
    const ferrailles = {
      pays: 'TUN',
      position: { designation: 'Ferrailles' },
      provenance: { devise_nationale: 'TND' },
      export: {
        etat: 'COMPLET',
        total_droits: 483.87,
        manques: [],
        lignes: [{ code: 'TAXE/FERRAILLES.EXP', libelle: 'TAXE/FERRAILLES.EXP', montant: 483.87, statut: 'CALCULE' }],
      },
    };
    // Contrat réel de l'API : la paire attendue est dite par `change_requis`.
    axios.post
      .mockResolvedValueOnce({ data: {
        ...ferrailles,
        export: { etat: 'INDISPONIBLE', total_droits: 0, manques: [], lignes: [
          { code: 'TAXE/FERRAILLES.EXP', libelle: 'TAXE/FERRAILLES.EXP', montant: null, statut: 'TAUX_DE_CHANGE_REQUIS' },
        ] },
        change_requis: [{ devise_droit: 'TND', devise_valeur: 'USD' }],
      } })
      .mockResolvedValueOnce({ data: ferrailles });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('TUN — 17530 positions avec droit de sortie'));
    const devise = screen.getByLabelText('Devise');
    await userEvent.clear(devise);
    await userEvent.type(devise, 'usd');
    await userEvent.type(screen.getByLabelText('Position nationale'), '2620110000');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '10000');
    await userEvent.type(screen.getByLabelText('Quantité (unité du droit)'), '5000');
    // Aucun taux n'est demandé avant que l'API dise la paire.
    expect(screen.queryByLabelText(/= \?/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId('export-calculer'));
    expect(axios.post.mock.calls[0][1].taux_de_change).toBeUndefined();

    await userEvent.type(await screen.findByLabelText('1 USD = ? TND'), '3.1');
    await userEvent.click(screen.getByTestId('export-calculer'));

    const corps = axios.post.mock.calls[1][1];
    expect(corps.devise).toBe('USD');
    expect(corps.taux_de_change).toBeCloseTo(1 / 3.1, 10);
    // La devise affichée est celle envoyée, même si le champ change ensuite.
    await userEvent.clear(devise);
    await userEvent.type(devise, 'EUR');
    expect(await screen.findAllByText(/483,87\s*USD/)).not.toHaveLength(0);
  });

  it('à Madagascar, exige la réponse sur le produit des mines et la transmet', async () => {
    axios.post.mockResolvedValue({ data: {
      pays: 'MDG', position: { designation: 'Or' }, provenance: { devise_nationale: 'MGA' },
      export: { etat: 'COMPLET', total_droits: 35000, manques: [], lignes: [] },
    } });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('MDG — 266 positions avec droit de sortie'));
    await userEvent.type(screen.getByLabelText('Position nationale'), '71081200');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '1000000');
    // Sans réponse, pas de calcul : le DS exonéré seul se lirait « rien à payer ».
    expect(screen.getByTestId('export-calculer')).toBeDisabled();

    await userEvent.click(screen.getByLabelText('Oui'));
    await userEvent.click(screen.getByLabelText(/abattement de 30 %/));
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(axios.post.mock.calls[0][1]).toMatchObject({
      pays: 'MDG', devise: 'MGA', produit_minier: true, produit_minier_transforme: true,
    });
  });

  it('au Mali, taxe hors tarif : la question sans abattement', async () => {
    axios.post.mockResolvedValue({ data: {
      pays: 'MLI', position: { designation: 'Or' }, provenance: { devise_nationale: 'XOF' },
      export: { etat: 'COMPLET', total_droits: 20000, manques: [], lignes: [] },
    } });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('MLI — taxe de sortie hors tarif'));
    expect(screen.getByLabelText('Devise')).toHaveValue('XOF');
    expect(screen.getByText(/non régi par le Code minier/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Position nationale'), '7108120000');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '1000000');
    await userEvent.click(screen.getByLabelText('Oui'));
    expect(screen.queryByText(/abattement/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(axios.post.mock.calls[0][1]).toMatchObject({ pays: 'MLI', devise: 'XOF', produit_minier: true });
  });

  it("ailleurs, ne pose pas la question", async () => {
    render(<ExportCalculator />);
    await userEvent.click(await screen.findByText('TUN — 17530 positions avec droit de sortie'));
    expect(screen.queryByTestId('export-question-hors-tarif')).not.toBeInTheDocument();
  });

  it('droit publié en dollars : demande « 1 USD = ? GHS » et l\'envoie tel quel', async () => {
    // La ligne réelle ne dit pas la devise du droit ; `change_requis` la dit.
    const ligne = (statut, montant) => ({
      code: 'EXPORT', libelle: 'Droit de sortie', specifique: '0.02 USD/litre', unite_quantite: 'litre', statut, montant,
    });
    axios.post
      .mockResolvedValueOnce({ data: {
        pays: 'GHA', position: { designation: 'Gas-oil' }, provenance: { devise_nationale: 'GHS' },
        export: { etat: 'INDISPONIBLE', total_droits: 0, manques: [], lignes: [ligne('TAUX_DE_CHANGE_REQUIS', null)] },
        change_requis: [{ devise_droit: 'USD', devise_valeur: 'GHS' }],
      } })
      .mockResolvedValueOnce({ data: {
        pays: 'GHA', position: { designation: 'Gas-oil' }, provenance: { devise_nationale: 'GHS' },
        export: { etat: 'COMPLET', total_droits: 300, manques: [], lignes: [ligne('CALCULE', 300)] },
      } });
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('GHA — 11516 positions avec droit de sortie'));
    expect(screen.getByLabelText('Devise')).toHaveValue('GHS');
    await userEvent.type(screen.getByLabelText('Position nationale'), '2710192100');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '10000');
    await userEvent.type(screen.getByLabelText('Quantité (unité du droit)'), '1000');
    await userEvent.click(screen.getByTestId('export-calculer'));

    await userEvent.type(await screen.findByLabelText('1 USD = ? GHS'), '15');
    await userEvent.click(screen.getByTestId('export-calculer'));

    expect(axios.post.mock.calls[1][1].taux_de_change).toBe(15);
  });

  it("ignore la réponse d'un calcul lancé avant un changement de devise", async () => {
    let repondre;
    axios.post.mockReturnValueOnce(new Promise((resolve) => { repondre = resolve; }));
    render(<ExportCalculator />);

    await userEvent.click(await screen.findByText('GHA — 11516 positions avec droit de sortie'));
    await userEvent.type(screen.getByLabelText('Position nationale'), '2710192100');
    await userEvent.type(screen.getByLabelText('Valeur en douane'), '10000');
    await userEvent.click(screen.getByTestId('export-calculer'));

    const devise = screen.getByLabelText('Devise');
    await userEvent.clear(devise);
    await userEvent.type(devise, 'EUR');
    repondre({ data: {
      pays: 'GHA', position: { designation: 'Gas-oil' }, provenance: { devise_nationale: 'GHS' },
      export: { etat: 'INDISPONIBLE', total_droits: 0, manques: [], lignes: [] },
      change_requis: [{ devise_droit: 'USD', devise_valeur: 'GHS' }],
    } });

    await waitFor(() => expect(screen.getByTestId('export-calculer')).not.toBeDisabled());
    expect(screen.queryByLabelText('1 USD = ? GHS')).not.toBeInTheDocument();
  });
});
