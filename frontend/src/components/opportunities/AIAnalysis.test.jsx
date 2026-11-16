/**
 * Onglet Analyse IA — le repli factuel doit ARRIVER À L'ÉCRAN.
 *
 * Ce test existe à cause d'une erreur précise, déjà commise dans ce chantier :
 * le repli sans clé d'API avait été vérifié au niveau du service, où il
 * fonctionnait, puis annoncé livré. La route le convertissait en HTTP 500, et
 * plus tard le composant n'affichait que `data.opportunities` — vide par
 * construction dans ce cas. La fonctionnalité n'atteignait aucun lecteur.
 *
 * Trois couches, trois tests ailleurs (service, route, ici). Vérifier une
 * couche ne vaut pas vérifier une fonctionnalité.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import AIAnalysis from './AIAnalysis';

vi.mock('axios');

vi.mock('../ui/select', async () => {
  const React = await import('react');
  const Ctx = React.createContext({ value: '', onValueChange: () => {} });
  const Select = ({ value = '', onValueChange, children }) => (
    <Ctx.Provider value={{ value, onValueChange }}>{children}</Ctx.Provider>
  );
  const SelectTrigger = React.forwardRef(({ children, ...p }, ref) => (
    <button ref={ref} type="button" role="combobox" {...p}>{children}</button>
  ));
  const SelectValue = ({ placeholder }) => {
    const { value } = React.useContext(Ctx);
    return <span>{value || placeholder}</span>;
  };
  const SelectContent = ({ children }) => <div>{children}</div>;
  const SelectItem = React.forwardRef(({ children, value, ...p }, ref) => {
    const { onValueChange } = React.useContext(Ctx);
    return (
      <button ref={ref} type="button" role="option" onClick={() => onValueChange(value)} {...p}>
        {children}
      </button>
    );
  });
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
});

const DEGRADED = {
  country: 'Kenya',
  country_iso3: 'KEN',
  mode: 'export',
  ai_available: false,
  degraded: true,
  notice: "Analyse narrative indisponible : aucune clé d'API n'est configurée.",
  grounding: 'VERIFIED PRODUCTION OF Kenya — Tea (HS 0902): 2,687,200 tonnes',
  grounding_stats: { production_products: 20, oec_flows: 0, oec_year: null },
  opportunities: [],
};

const mockApi = (opportunitiesResponse) =>
  axios.get.mockImplementation((url) => {
    if (url.includes('/substitution/countries')) {
      return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
    }
    if (url.includes('/ai/health')) return Promise.resolve({ data: { ready: true } });
    if (url.includes('/ai/opportunities/')) return opportunitiesResponse();
    return Promise.resolve({ data: {} });
  });

async function lancerAnalyse() {
  await userEvent.click(await screen.findByRole('option', { name: /Kenya/ }));
  const boutons = screen.getAllByRole('button');
  const lancer = boutons.find((b) => /analyser/i.test(b.textContent || ''));
  await userEvent.click(lancer);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AIAnalysis', () => {
  it('affiche l’ancrage factuel quand l’analyse narrative est indisponible', async () => {
    mockApi(() => Promise.resolve({ data: DEGRADED }));
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();

    const bloc = await screen.findByTestId('ai-degraded');
    expect(bloc).toHaveTextContent(/aucune clé d'API n'est configurée/i);
    // Ce qui compte n'est pas l'avis d'indisponibilité mais la DONNÉE qui
    // reste servie malgré elle : sans cela, l'écran serait simplement vide.
    expect(screen.getByTestId('ai-degraded-grounding')).toHaveTextContent(/Tea \(HS 0902\)/);
    expect(bloc).toHaveTextContent(/20 produits de production réelle/);
  });

  it('montre l’erreur du service quand l’appel échoue vraiment', async () => {
    mockApi(() => Promise.reject({ response: { data: { detail: 'Service en panne' } } }));
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();
    expect(await screen.findByText('Service en panne')).toBeInTheDocument();
    expect(screen.queryByTestId('ai-degraded')).not.toBeInTheDocument();
  });

  it('ne laisse aucune clé i18n brute à l’écran', async () => {
    mockApi(() => Promise.resolve({ data: DEGRADED }));
    const { container } = render(<AIAnalysis language="fr" />);
    await lancerAnalyse();
    await screen.findByTestId('ai-degraded');
    expect(container.textContent).not.toMatch(/opportunities\.[a-zA-Z]+\./);
  });
});

describe("AIAnalysis — règle d'origine officielle d'une opportunité", () => {
  const NOTE_25 =
    "Note 2.5 de l'Appendice IV: la valeur des matières non originaires sera automatiquement ramenée de 60 % à 55 % à la fin d'une période de cinq (5) ans, à compter du 1er janvier 2021.";
  // GET /api/rules-of-origin/841810, réduite à ce que lit la carte.
  const regle8418 = {
    hs_code: '841810',
    status: 'AGREED',
    rules: {
      primary_rule: {
        code: 'VA60',
        name: 'Max 55% valeur non-originaire',
        explanation:
          "Critère de la teneur des matières non originaires prévu à l'article 6(1)(b) de l'Annexe 2 sur les Règles d'Origine : la valeur des matières non originaires utilisées dans la fabrication ne doit pas dépasser 55 % du prix départ usine (art. 1(k)) du produit fini. Sur une ligne marquée d'un astérisque, la note 2.5 de l'Appendice IV ramène automatiquement le seuil imprimé de 60 % à 55 % à la fin d'une période de cinq ans à compter du 1er janvier 2021, soit depuis le 1er janvier 2026.",
      },
      threshold_note_fr: NOTE_25,
    },
  };

  it('note 2.5 : la carte nomme le seuil de 55 % et cite la note', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('/substitution/countries')) {
        return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
      }
      if (url.includes('/ai/health')) return Promise.resolve({ data: { ready: true } });
      if (url.includes('/ai/opportunities/')) {
        return Promise.resolve({
          data: {
            country: 'Kenya', country_iso3: 'KEN', mode: 'export', ai_available: true,
            opportunities: [{
              product: { name: 'Réfrigérateurs', hs6Code: '841810' },
              potentialPartner: 'Tanzania', potentialTradeValue: 12,
              rulesOfOrigin: 'Règle citée par l’analyse',
            }],
          },
        });
      }
      if (url.includes('/rules-of-origin/841810')) return Promise.resolve({ data: regle8418 });
      return Promise.resolve({ data: {} });
    });
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();

    expect(await screen.findByTestId('official-rule-threshold-note')).toHaveTextContent(NOTE_25);
    expect(screen.getByText('Max 55% valeur non-originaire')).toBeInTheDocument();
    expect(screen.queryByText(/Max 60/)).not.toBeInTheDocument();
  });

  it('ligne à règle propre (21.05) : la carte montre le texte officiel de la règle', async () => {
    const TEXTE_2105 =
      'Fabrication dans laquelle les matières des chapitres 2, 4, 7, 8, 17 et 18 utilisées doivent être originaires';
    // GET /api/rules-of-origin/210500, réduite à ce que lit la carte : pas
    // d'explication générique, le texte de l'Appendice IV fait foi.
    const regle2105 = {
      hs_code: '210500',
      status: 'AGREED',
      rules: {
        primary_rule: {
          code: 'WO',
          name: "Règle propre à cette ligne de l'Appendice IV",
          explanation: '',
          matches_text: false,
        },
        rule_text_fr: TEXTE_2105,
        threshold_note_fr: null,
      },
    };
    axios.get.mockImplementation((url) => {
      if (url.includes('/substitution/countries')) {
        return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
      }
      if (url.includes('/ai/health')) return Promise.resolve({ data: { ready: true } });
      if (url.includes('/ai/opportunities/')) {
        return Promise.resolve({
          data: {
            country: 'Kenya', country_iso3: 'KEN', mode: 'export', ai_available: true,
            opportunities: [{
              product: { name: 'Glaces de consommation', hs6Code: '210500' },
              potentialPartner: 'Tanzania', potentialTradeValue: 3,
              rulesOfOrigin: 'Règle citée par l’analyse',
            }],
          },
        });
      }
      if (url.includes('/rules-of-origin/210500')) return Promise.resolve({ data: regle2105 });
      return Promise.resolve({ data: {} });
    });
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();

    expect(await screen.findByTestId('official-rule-text')).toHaveTextContent(TEXTE_2105);
    expect(screen.getByText("Règle propre à cette ligne de l'Appendice IV")).toBeInTheDocument();
  });
});
