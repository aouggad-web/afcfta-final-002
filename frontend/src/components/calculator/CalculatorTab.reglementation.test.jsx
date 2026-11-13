import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';

import CalculatorTab from './CalculatorTab';

vi.mock('axios');

// L'onglet Réglementation du calculateur : ce que CalculatorTab ajoute au panneau
// (la position choisie, le badge « Disponible »). Le panneau a ses propres tests.

const POSITIONS = [
  { code: '0201101100', national_code: '0201101100', digits: 10, description_fr: 'Veaux POSITION-A', description_en: 'Calves A', dd_rate: 5, dd_expression: null },
  { code: '0201101900', national_code: '0201101900', digits: 10, description_fr: 'Veaux POSITION-B', description_en: 'Calves B', dd_rate: 5, dd_expression: null },
];
const COUNTRIES = [
  { code: 'DZA', iso2: 'DZ', name: 'Algérie' },
  { code: 'TUN', iso2: 'TN', name: 'Tunisie' },
  { code: 'KEN', iso2: 'KE', name: 'Kenya' },
];

const fiche = (code) => ({
  success: true, country_iso3: 'DZA', code, niveau: 'national', hs6: code.slice(0, 6), chapitre: code.slice(0, 2), unite: null,
  description_fr: `FICHE-${code}`, description_en: `FICHE-${code}`, description_ar: `FICHE-${code}`,
  droits: [{ code: 'DD', libelle: 'DD', famille: 'droit', taux: 5, expression: null, assiette: 'CIF', note: null, source: 'x', base_statistique: false, conditionnel: false }],
  restrictions: [], usages: [], couverture: { etat: 'PARTIEL', motif: null, tva: true }, source: 'socle',
});

// Les pays que le socle sert : l'Algérie, pas la Tunisie (zéro position).
const PAYS = { DZA: { positions: 17345 }, TUN: { positions: 0 } };

const repondre = ({ pays = Promise.resolve({ data: { pays: PAYS } }) } = {}) => {
  axios.get.mockImplementation((url) => {
    if (url.includes('/calcul/pays')) return pays;
    if (url.includes('/sous-positions/')) return Promise.resolve({ data: { sub_positions: POSITIONS } });
    if (url.includes('/position/')) return Promise.resolve({ data: fiche(url.split('/position/')[1]) });
    if (url.includes('/formalites/')) return Promise.resolve({ data: { success: true, formalities: [], statut: 'NON_ETABLIES', reserve: 'Formalités non établies' } });
    return Promise.resolve({ data: {} });
  });
  axios.post.mockResolvedValue({ data: {} });
};

const originesDemandees = () => axios.get.mock.calls
  .filter(([url]) => url.includes('/position/'))
  .map(([, config]) => config?.params?.origine);

const appelsRegulatoires = () => axios.get.mock.calls.map(([url]) => url).filter((url) => /\/(position|formalites)\//.test(url));

describe('CalculatorTab — onglet Réglementation', () => {
  let user;

  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    user = userEvent.setup({ advanceTimers: (ms) => vi.advanceTimersByTime(ms) });
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const avancer = (ms) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

  // Pays et SH6 saisis dans l'onglet Réglementation, puis une position choisie.
  const choisirUnePosition = async () => {
    render(<CalculatorTab countries={COUNTRIES} language="fr" />);
    await user.click(screen.getByTestId('calculator-regulatory-tab'));
    await user.click(await screen.findByTestId('regulatory-country-select'));
    await user.click(await screen.findByRole('option', { name: /Algérie/ }));
    await user.type(screen.getByTestId('regulatory-hs-input'), '020110');
    await user.click(await screen.findByText('0201101100'));
    await avancer(600);
    await screen.findByText('FICHE-0201101100');
    expect(screen.getByText(/Intitulé exact de la position nationale/)).toBeInTheDocument();
  };

  it('changer de pays efface la position choisie : elle ne sert pas au tarif d\'un autre pays', async () => {
    repondre();
    await choisirUnePosition();
    const avant = appelsRegulatoires().length;

    await user.click(screen.getByTestId('regulatory-country-select'));
    await user.click(await screen.findByRole('option', { name: /Tunisie/ }));
    await avancer(1000);

    expect(screen.queryByText(/Intitulé exact de la position nationale/)).not.toBeInTheDocument();
    const nouveaux = appelsRegulatoires().slice(avant);
    // La position d'Alger n'est jamais redemandée au tarif de Tunis.
    expect(nouveaux.some((url) => url.includes('/TUN/') && url.includes('0201101100'))).toBe(false);
    expect(nouveaux.some((url) => url.includes('/TUN/position/020110'))).toBe(true);
  });

  it("changer le code SH dans l'onglet Calculateur efface la position choisie dans Réglementation", async () => {
    repondre();
    await choisirUnePosition();

    await user.click(screen.getByTestId('calculator-single-tab'));
    await user.click(await screen.findByText(/Mode simple/));
    const champ = await screen.findByTestId('hs-code-simple-input');
    await user.clear(champ);
    await user.type(champ, '030211');
    await user.click(screen.getByTestId('calculator-regulatory-tab'));
    await screen.findByTestId('regulatory-hs-input');
    await avancer(1000);

    // Le champ porte le nouveau code ; l'ancienne position et sa fiche ont disparu.
    expect(screen.getByTestId('regulatory-hs-input')).toHaveValue('030211');
    expect(screen.queryByText(/Intitulé exact de la position nationale/)).not.toBeInTheDocument();
    expect(screen.queryByText('FICHE-0201101100')).not.toBeInTheDocument();
    expect(await screen.findByText('FICHE-030211')).toBeInTheDocument();
  });

  it('choisir une position ne l\'efface pas : le pays et le code n\'ont pas changé', async () => {
    repondre();
    await choisirUnePosition();
    await avancer(1000);

    expect(screen.getByText(/Intitulé exact de la position nationale/)).toBeInTheDocument();
    expect(screen.getByText('FICHE-0201101100')).toBeInTheDocument();
  });

  it('le badge « Disponible » vient des pays que le socle sert, pas d\'une liste', async () => {
    repondre();
    render(<CalculatorTab countries={COUNTRIES} language="fr" />);
    await user.click(screen.getByTestId('calculator-regulatory-tab'));
    await avancer(100);
    await user.click(await screen.findByTestId('regulatory-country-select'));

    expect(await screen.findByRole('option', { name: /Algérie.*Disponible/ })).toBeInTheDocument();
    // La Tunisie est listée, sans position au socle : pas de badge.
    expect(screen.getByRole('option', { name: /Tunisie/ })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /Tunisie.*Disponible/ })).not.toBeInTheDocument();
  });

  it('sans réponse du socle, aucun badge : jamais un badge sans preuve', async () => {
    repondre({ pays: Promise.reject(new Error('503')) });
    render(<CalculatorTab countries={COUNTRIES} language="fr" />);
    await user.click(screen.getByTestId('calculator-regulatory-tab'));
    await avancer(100);
    await user.click(await screen.findByTestId('regulatory-country-select'));

    expect(await screen.findByRole('option', { name: /Algérie/ })).toBeInTheDocument();
    expect(screen.queryByText('Disponible')).not.toBeInTheDocument();
  });

  describe("pays d'origine", () => {
    // Pays de destination et code SH6 saisis, sans position choisie : la fiche est celle du SH6.
    const ouvrir = async () => {
      render(<CalculatorTab countries={COUNTRIES} language="fr" />);
      await user.click(screen.getByTestId('calculator-regulatory-tab'));
      await user.click(await screen.findByTestId('regulatory-country-select'));
      await user.click(await screen.findByRole('option', { name: /Algérie/ }));
      await user.type(screen.getByTestId('regulatory-hs-input'), '030211');
      await avancer(600);
      await screen.findByText('FICHE-030211');
    };
    const choisirOrigine = async (nom) => {
      await user.click(screen.getByTestId('regulatory-origin-select'));
      await user.click(await screen.findByRole('option', { name: nom }));
      await avancer(600);
    };

    it("l'origine est facultative : sans elle, la fiche se demande sans origine", async () => {
      repondre();
      await ouvrir();

      expect(screen.getByTestId('regulatory-origin-select')).toBeInTheDocument();
      expect(screen.getByText(/Aucune : tarif seul/)).toBeInTheDocument();
      expect(originesDemandees()).toEqual([undefined]);
    });

    it("choisir une origine redemande la fiche avec cette origine", async () => {
      repondre();
      await ouvrir();
      await choisirOrigine(/Kenya/);

      expect(originesDemandees()).toEqual([undefined, 'KEN']);
    });

    it("« Aucune » efface l'origine : la fiche revient au tarif seul", async () => {
      repondre();
      await ouvrir();
      await choisirOrigine(/Kenya/);
      await choisirOrigine(/Aucune : tarif seul/);

      expect(originesDemandees()).toEqual([undefined, 'KEN', undefined]);
    });

    it("l'origine choisie ici est celle du Calculateur : un seul pays d'origine dans l'onglet", async () => {
      repondre();
      await ouvrir();
      await choisirOrigine(/Kenya/);

      await user.click(screen.getByTestId('calculator-single-tab'));
      expect(await screen.findByTestId('origin-country-select')).toHaveTextContent('Kenya');
    });
  });
});
