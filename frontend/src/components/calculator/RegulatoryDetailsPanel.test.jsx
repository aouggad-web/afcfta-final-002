import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';

import RegulatoryDetailsPanel from './RegulatoryDetailsPanel';

vi.mock('axios');

const droit = (surcharge) => ({
  code: 'DD', libelle: 'DD', famille: 'droit', taux: 5, expression: null,
  assiette: 'CIF', note: null, source: 'douane.gov.dz', ...surcharge,
});

const fiche = (surcharge = {}) => ({
  success: true,
  country_iso3: 'DZA',
  code: '0201101100',
  niveau: 'national',
  hs6: '020110',
  chapitre: '02',
  unite: null,
  description_fr: 'De veaux',
  description_en: 'Of calves',
  droits: [droit({}), droit({ code: 'TVA', famille: 'tva', taux: 0, assiette: 'CIF+DD' })],
  restrictions: [],
  couverture: { etat: 'PARTIEL', motif: null, tva: true },
  source: 'socle',
  ...surcharge,
});

const formalites = (surcharge = {}) => ({
  success: true,
  formalities: [{ code: '910', document_fr: "Déclaration d'importation", document_en: 'Import declaration' }],
  statut: 'DOCUMENTEES',
  reserve: null,
  ...surcharge,
});

// Répond à chacune des deux routes que le panneau interroge.
const repondre = ({ position, formalite }) => {
  axios.get.mockImplementation((url) => {
    const reponse = url.includes('/position/') ? position : formalite;
    return reponse instanceof Error ? Promise.reject(reponse) : Promise.resolve({ data: reponse });
  });
};

const refus = (status, detail) => Object.assign(new Error(`HTTP ${status}`), { response: { status, data: { detail } } });

const rendre = (props = {}) => render(
  <RegulatoryDetailsPanel countryCode="DZA" hsCode="0201101100" {...props} />,
);

describe('RegulatoryDetailsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('lit la fiche et les formalités du socle, pas le moteur réglementaire', async () => {
    repondre({ position: fiche(), formalite: formalites() });
    rendre();

    expect(await screen.findByText('De veaux')).toBeInTheDocument();
    const urls = axios.get.mock.calls.map(([url]) => url);
    expect(urls).toContain('/api/consultation/DZA/position/0201101100');
    expect(urls).toContain('/api/consultation/DZA/formalites/0201101100');
    expect(urls.some((url) => url.includes('regulatory-engine'))).toBe(false);
    expect(screen.getByText('5%')).toBeInTheDocument();
    expect(screen.getByText("Déclaration d'importation")).toBeInTheDocument();
  });

  it("n'affiche ni total ni taux ZLECAf : ils dépendent d'une origine que l'onglet ne connaît pas", async () => {
    repondre({ position: fiche(), formalite: formalites() });
    rendre();

    await screen.findByText('De veaux');
    expect(screen.queryByText(/Total ZLECAf/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Total NPF/i)).not.toBeInTheDocument();
    expect(screen.getByText(/dépendent de l'origine/)).toBeInTheDocument();
  });

  it('un taux publié à 0 % reste 0 % ; un taux absent se lit « à compléter », jamais 0 %', async () => {
    repondre({
      position: fiche({
        droits: [
          droit({ code: 'TVA', famille: 'tva', taux: 0 }),
          droit({ code: 'DD', taux: null, expression: null }),
        ],
      }),
      formalite: formalites(),
    });
    rendre();

    await screen.findByText('De veaux');
    const lignes = screen.getAllByTestId('regulatory-measure');
    expect(lignes[0]).toHaveTextContent('0%');
    expect(lignes[1]).toHaveTextContent('À compléter');
    expect(lignes[1]).not.toHaveTextContent('0%');
  });

  it("un droit composé se lit en entier : l'expression, pas une de ses composantes", async () => {
    repondre({
      position: fiche({ droits: [droit({ taux: null, expression: '10% or 55c/kg less 90%' })] }),
      formalite: formalites(),
    });
    rendre();

    expect(await screen.findByText('10% or 55c/kg less 90%')).toBeInTheDocument();
  });

  it('un SH6 à plusieurs positions est un choix à faire, pas une panne', async () => {
    repondre({
      position: refus(422, {
        code: 'POSITION_NATIONALE_REQUISE',
        message: 'DZA/020110 : 4 positions nationales sous ce SH6 — choisir la position.',
        positions: [{ code: '0201101100' }, { code: '0201101900' }, { code: '0201102100' }, { code: '0201102900' }],
      }),
      formalite: refus(422, {}),
    });
    rendre({ hsCode: '020110' });

    const carte = await screen.findByTestId('regulatory-details-choice');
    expect(carte).toHaveTextContent('4 positions nationales');
    expect(screen.queryByTestId('regulatory-details-error')).not.toBeInTheDocument();
  });

  it('une position absente se dit, avec le pays', async () => {
    repondre({ position: refus(404, 'DZA/9999999999 : position absente du socle'), formalite: refus(404, '') });
    rendre({ hsCode: '9999999999' });

    expect(await screen.findByText('Position introuvable dans les données servies pour ce pays')).toBeInTheDocument();
  });

  it('un socle indisponible se dit indisponible, pas absent', async () => {
    repondre({ position: refus(503, 'DZA n\'est pas au socle'), formalite: refus(503, '') });
    rendre();

    expect(await screen.findByText('Tarif de ce pays momentanément indisponible')).toBeInTheDocument();
  });

  it('des formalités indisponibles ne font pas tomber les droits, et ne se lisent pas « aucune »', async () => {
    repondre({ position: fiche(), formalite: refus(500, '') });
    rendre();

    expect(await screen.findByText('De veaux')).toBeInTheDocument();
    expect(screen.getByText('5%')).toBeInTheDocument();
    expect(screen.getByTestId('regulatory-formalities-unavailable')).toHaveTextContent(
      "Une absence d'information n'est pas une absence d'obligation",
    );
  });

  it("le statut des formalités accompagne la liste, même vide", async () => {
    repondre({
      position: fiche(),
      formalite: formalites({
        formalities: [],
        statut: 'NON_ETABLIES',
        reserve: 'Formalités non établies pour cette position.',
      }),
    });
    rendre();

    await screen.findByText('De veaux');
    expect(screen.getByTestId('regulatory-formalities-status')).toHaveTextContent('Formalités non établies');
  });

  it("dit que la liste est incomplète quand la source ne publie pas la TVA", async () => {
    repondre({
      position: fiche({ couverture: { etat: 'PARTIEL', motif: 'aucune TVA à la source', tva: false } }),
      formalite: formalites(),
    });
    rendre();

    expect(await screen.findByTestId('regulatory-vat-missing')).toHaveTextContent('cette liste est incomplète');
  });

  it('ne dit rien de la TVA quand la source la publie', async () => {
    repondre({ position: fiche(), formalite: formalites() });
    rendre();

    await screen.findByText('De veaux');
    expect(screen.queryByTestId('regulatory-vat-missing')).not.toBeInTheDocument();
  });

  it('sert les restrictions telles que la source les écrit', async () => {
    repondre({
      position: fiche({
        restrictions: [{ text_verbatim: 'ق3034- لايصرح بتصدير اصناف', source: 'customs.gov.eg' }],
      }),
      formalite: formalites(),
    });
    rendre();

    const bloc = await screen.findByTestId('regulatory-restrictions');
    expect(bloc).toHaveTextContent('ق3034- لايصرح بتصدير اصناف');
    expect(bloc).toHaveTextContent('customs.gov.eg');
  });

  it("ne demande rien sous six chiffres", async () => {
    repondre({ position: fiche(), formalite: formalites() });
    rendre({ hsCode: '02011' });

    await new Promise((resolve) => setTimeout(resolve, 700));
    expect(axios.get).not.toHaveBeenCalled();
  });

  it("la réponse d'un code déjà remplacé n'écrase pas celle du code affiché", async () => {
    // Les DEUX requêtes de l'ancien code (position, formalités) restent en
    // attente : l'une résolue seule ne ferait jamais aboutir le panneau.
    const reponsesAnciennes = [];
    axios.get.mockImplementation((url) => {
      if (url.includes('/0201101100')) {
        // Réponse lente : elle n'arrive qu'après celle du code suivant.
        return new Promise((resolve) => {
          reponsesAnciennes.push(() => resolve({
            data: url.includes('/position/') ? fiche({ description_fr: 'Ancien code' }) : formalites(),
          }));
        });
      }
      return Promise.resolve({
        data: url.includes('/position/')
          ? fiche({ code: '0201101900', description_fr: 'Nouveau code' })
          : formalites(),
      });
    });

    const { rerender } = rendre();
    await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(2));

    rerender(<RegulatoryDetailsPanel countryCode="DZA" hsCode="0201101900" />);
    expect(await screen.findByText('Nouveau code')).toBeInTheDocument();

    expect(reponsesAnciennes).toHaveLength(2);
    reponsesAnciennes.forEach((repondreAncien) => repondreAncien());
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.getByText('Nouveau code')).toBeInTheDocument();
    expect(screen.queryByText('Ancien code')).not.toBeInTheDocument();
  });

  it("parle la langue de l'interface", async () => {
    repondre({ position: fiche(), formalite: formalites() });
    rendre({ language: 'en' });

    expect(await screen.findByText('Of calves')).toBeInTheDocument();
    expect(screen.getByText('Duties and Taxes')).toBeInTheDocument();
    expect(screen.getByText('Import declaration')).toBeInTheDocument();
  });
});
