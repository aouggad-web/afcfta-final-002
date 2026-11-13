import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import axios from 'axios';

import RegulatoryDetailsPanel from './RegulatoryDetailsPanel';

vi.mock('axios');

const droit = (surcharge) => ({
  code: 'DD', libelle: 'DD', famille: 'droit', taux: 5, expression: null,
  assiette: 'CIF', note: null, source: 'douane.gov.dz', base_statistique: false, ...surcharge,
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
  description_ar: 'من العجول',
  droits: [droit({}), droit({ code: 'TVA', famille: 'tva', taux: 0, assiette: 'CIF+DD' })],
  restrictions: [],
  usages: [],
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

// L'antirebond de 500 ms : minuteries simulées, qui avancent aussi avec le temps
// réel pour que les attentes de Testing Library aboutissent.
const avancer = (ms) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

const PROPS = { countryCode: 'DZA', hsCode: '0201101100' };
const panneau = (props = {}) => <RegulatoryDetailsPanel {...PROPS} {...props} />;

// Rend le panneau et laisse passer l'antirebond : la requête part.
const rendre = async (props = {}) => {
  const rendu = render(panneau(props));
  await avancer(500);
  return rendu;
};

describe('RegulatoryDetailsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('source des données', () => {
    it('lit la fiche et les formalités du socle, pas le moteur réglementaire', async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      expect(await screen.findByText('De veaux')).toBeInTheDocument();
      const urls = axios.get.mock.calls.map(([url]) => url);
      // Terminé par le code : le préfixe dépend de VITE_BACKEND_URL, pas le test.
      expect(urls).toEqual(expect.arrayContaining([
        expect.stringMatching(/\/api\/consultation\/DZA\/position\/0201101100$/),
        expect.stringMatching(/\/api\/consultation\/DZA\/formalites\/0201101100$/),
      ]));
      expect(urls.some((url) => url.includes('regulatory-engine'))).toBe(false);
      expect(screen.getByText('5%')).toBeInTheDocument();
      expect(screen.getByText("Déclaration d'importation")).toBeInTheDocument();
    });

    it("n'affiche ni total ni taux ZLECAf : ils dépendent d'une origine que l'onglet ne connaît pas", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.queryByText(/Total ZLECAf/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Total NPF/i)).not.toBeInTheDocument();
      expect(screen.getByText(/dépendent de l'origine et de la date/)).toBeInTheDocument();
    });
  });

  describe('attente et saisie', () => {
    it("attend dès que la saisie est valide : ni ancien contenu ni « données non disponibles » pendant l'antirebond", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      render(panneau());

      expect(screen.getByTestId('regulatory-details-loading')).toBeInTheDocument();
      expect(screen.queryByTestId('regulatory-details-error')).not.toBeInTheDocument();
      expect(axios.get).not.toHaveBeenCalled();

      await avancer(500);
      expect(await screen.findByText('De veaux')).toBeInTheDocument();
      expect(screen.queryByTestId('regulatory-details-loading')).not.toBeInTheDocument();
    });

    it("ne demande rien sous six chiffres, et n'attend rien", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      render(panneau({ hsCode: '02011' }));
      await avancer(1000);

      expect(axios.get).not.toHaveBeenCalled();
      expect(screen.queryByTestId('regulatory-details-loading')).not.toBeInTheDocument();
    });

    it("des saisies rapprochées ne font qu'une demande : celle du dernier code", async () => {
      repondre({ position: fiche({ description_fr: 'Dernier code' }), formalite: formalites() });
      const { rerender } = render(panneau({ hsCode: '0201101100' }));
      await avancer(200);
      rerender(panneau({ hsCode: '0201101900' }));
      await avancer(200);
      rerender(panneau({ hsCode: '0201102000' }));
      await avancer(500);

      expect(await screen.findByText('Dernier code')).toBeInTheDocument();
      const urls = axios.get.mock.calls.map(([url]) => url);
      expect(urls).toHaveLength(2);
      expect(urls.every((url) => url.endsWith('/0201102000'))).toBe(true);
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

      const { rerender } = await rendre();
      expect(axios.get).toHaveBeenCalledTimes(2);

      rerender(panneau({ hsCode: '0201101900' }));
      await avancer(500);
      expect(await screen.findByText('Nouveau code')).toBeInTheDocument();

      expect(reponsesAnciennes).toHaveLength(2);
      reponsesAnciennes.forEach((repondreAncien) => repondreAncien());
      await avancer(50);
      expect(screen.getByText('Nouveau code')).toBeInTheDocument();
      expect(screen.queryByText('Ancien code')).not.toBeInTheDocument();
    });

    it("une saisie qui devient invalide pendant une requête ne laisse ni attente ni réponse tardive", async () => {
      const enAttente = [];
      axios.get.mockImplementation((url) => new Promise((resolve) => {
        enAttente.push(() => resolve({ data: url.includes('/position/') ? fiche({ description_fr: 'Trop tard' }) : formalites() }));
      }));

      const { rerender } = await rendre();
      expect(screen.getByTestId('regulatory-details-loading')).toBeInTheDocument();

      rerender(panneau({ hsCode: '02011' }));
      expect(screen.queryByTestId('regulatory-details-loading')).not.toBeInTheDocument();

      enAttente.forEach((repondreTard) => repondreTard());
      await avancer(50);
      expect(screen.queryByText('Trop tard')).not.toBeInTheDocument();
    });

    it("la requête part avec les seuls chiffres du code saisi", async () => {
      repondre({ position: fiche({ code: '0101210001' }), formalite: formalites() });
      await rendre({ countryCode: 'TUN', hsCode: '0101-21-00-01' });

      await screen.findByText('De veaux');
      const urls = axios.get.mock.calls.map(([url]) => url);
      expect(urls.every((url) => url.endsWith('/TUN/position/0101210001') || url.endsWith('/TUN/formalites/0101210001'))).toBe(true);
    });

    it("l'erreur tardive d'un code déjà remplacé n'écrase pas le code affiché", async () => {
      const tardives = [];
      axios.get.mockImplementation((url) => {
        if (url.includes('/0201101100')) {
          return new Promise((_resolve, reject) => { tardives.push(() => reject(refus(503, ''))); });
        }
        return Promise.resolve({
          data: url.includes('/position/') ? fiche({ code: '0201101900', description_fr: 'Nouveau code' }) : formalites(),
        });
      });

      const { rerender } = await rendre();
      rerender(panneau({ hsCode: '0201101900' }));
      await avancer(500);
      expect(await screen.findByText('Nouveau code')).toBeInTheDocument();

      tardives.forEach((rejeter) => rejeter());
      await avancer(50);
      expect(screen.getByText('Nouveau code')).toBeInTheDocument();
      expect(screen.queryByText('Tarif de ce pays indisponible')).not.toBeInTheDocument();
    });

    it("la réponse tardive d'un code remplacé n'arrête pas l'attente du code en cours", async () => {
      const enAttente = [];
      axios.get.mockImplementation((url) => new Promise((resolve) => {
        const ancien = url.includes('/0201101100');
        enAttente.push({
          ancien,
          repondre: () => resolve({
            data: url.includes('/position/')
              ? fiche({ code: ancien ? '0201101100' : '0201101900', description_fr: ancien ? 'Ancien code' : 'Nouveau code' })
              : formalites(),
          }),
        });
      }));

      const { rerender } = await rendre();
      rerender(panneau({ hsCode: '0201101900' }));
      await avancer(500);
      expect(screen.getByTestId('regulatory-details-loading')).toBeInTheDocument();

      enAttente.filter((r) => r.ancien).forEach((r) => r.repondre());
      await avancer(50);
      // Le code en cours n'a pas répondu : l'écran attend encore, sans rien dire à sa place.
      expect(screen.getByTestId('regulatory-details-loading')).toBeInTheDocument();
      expect(screen.queryByTestId('regulatory-details-error')).not.toBeInTheDocument();
      expect(screen.queryByText('Ancien code')).not.toBeInTheDocument();

      enAttente.filter((r) => !r.ancien).forEach((r) => r.repondre());
      await avancer(50);
      expect(await screen.findByText('Nouveau code')).toBeInTheDocument();
    });

    it("l'ancien contenu quitte l'écran dès que le code change, pas à l'arrivée de la réponse", async () => {
      repondre({ position: fiche({ description_fr: 'Premier code' }), formalite: formalites() });
      const { rerender } = await rendre();
      expect(await screen.findByText('Premier code')).toBeInTheDocument();

      rerender(panneau({ hsCode: '0201101900' }));
      expect(screen.getByTestId('regulatory-details-loading')).toBeInTheDocument();
      expect(screen.queryByText('Premier code')).not.toBeInTheDocument();
    });

    it("vider le champ retire la fiche affichée", async () => {
      repondre({ position: fiche({ description_fr: 'Premier code' }), formalite: formalites() });
      const { rerender } = await rendre();
      expect(await screen.findByText('Premier code')).toBeInTheDocument();

      rerender(panneau({ hsCode: '' }));
      await avancer(10);
      expect(screen.queryByText('Premier code')).not.toBeInTheDocument();
    });

    it("un changement de langue ne relance pas de requête et change la langue à l'écran", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      const { rerender } = await rendre();
      await screen.findByText('De veaux');
      const appels = axios.get.mock.calls.length;

      rerender(panneau({ language: 'en' }));
      expect(await screen.findByText('Regulatory Details')).toBeInTheDocument();
      expect(screen.getByText('Of calves')).toBeInTheDocument();
      expect(axios.get).toHaveBeenCalledTimes(appels);
    });
  });

  describe('taux', () => {
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
      await rendre();

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
      await rendre();

      expect(await screen.findByText('10% or 55c/kg less 90%')).toBeInTheDocument();
    });

    it("une moyenne statistique (WITS/TRAINS) n'est pas un taux publié : la ligne et la fiche le disent", async () => {
      repondre({
        position: fiche({
          droits: [
            droit({ taux: 20, base_statistique: true, source: 'WITS / UNCTAD-TRAINS (Banque mondiale)' }),
            droit({ code: 'TVA', famille: 'tva', taux: 10 }),
          ],
        }),
        formalite: formalites(),
      });
      await rendre();

      await screen.findByText('De veaux');
      const [statistique, nationale] = screen.getAllByTestId('regulatory-measure');
      expect(statistique).toHaveTextContent('Moyenne statistique SH6');
      expect(statistique).toHaveTextContent('Indicatif');
      expect(statistique).not.toHaveTextContent('Taux publié');
      expect(nationale).toHaveTextContent('Taux publié');
      expect(screen.getByTestId('regulatory-statistical-note')).toHaveTextContent('pas le tarif national du pays');
    });

    it('ne parle pas de moyenne statistique quand tous les taux sont ceux du tarif', async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.queryByTestId('regulatory-statistical-note')).not.toBeInTheDocument();
      expect(screen.queryByText('Indicatif')).not.toBeInTheDocument();
    });

    it("les restes de virgule flottante d'une source ne s'affichent pas ; 0 et les décimales utiles restent", async () => {
      repondre({
        position: fiche({
          droits: [
            droit({ code: 'A', taux: 16.6666660308838 }),
            droit({ code: 'B', taux: 0 }),
            droit({ code: 'C', taux: 0.8 }),
            droit({ code: 'D', taux: 3000 }),
          ],
        }),
        formalite: formalites(),
      });
      await rendre();

      await screen.findByText('De veaux');
      const lignes = screen.getAllByTestId('regulatory-measure');
      expect(lignes[0]).toHaveTextContent('16.6667%');
      expect(lignes[0]).not.toHaveTextContent('16.66666');
      expect(lignes[1]).toHaveTextContent('0%');
      expect(lignes[2]).toHaveTextContent('0.8%');
      expect(lignes[3]).toHaveTextContent('3000%');
    });

    it("une mesure de défense commerciale n'est pas un taux manquant : elle dépend de l'origine ou du produit", async () => {
      repondre({
        position: fiche({
          droits: [
            droit({ code: 'AD', taux: null, conditionnel: true }),
            droit({ code: 'DD', taux: null, conditionnel: false }),
          ],
        }),
        formalite: formalites(),
      });
      await rendre();

      await screen.findByText('De veaux');
      const [conditionnelle, manquante] = screen.getAllByTestId('regulatory-measure');
      expect(conditionnelle).toHaveTextContent("Selon l'origine ou le produit");
      expect(conditionnelle).not.toHaveTextContent('À compléter');
      expect(manquante).toHaveTextContent('À compléter');
    });

    it("dit que la liste est incomplète quand la source ne publie pas la TVA", async () => {
      repondre({
        position: fiche({ couverture: { etat: 'PARTIEL', motif: 'aucune TVA à la source', tva: false } }),
        formalite: formalites(),
      });
      await rendre();

      expect(await screen.findByTestId('regulatory-vat-missing')).toHaveTextContent('cette liste est incomplète');
    });

    it('ne dit rien de la TVA quand la source la publie', async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.queryByTestId('regulatory-vat-missing')).not.toBeInTheDocument();
    });

    it("nomme les régimes qui dépendent de l'usage : les lignes servies sont celles du régime courant", async () => {
      repondre({
        position: fiche({
          usages: [{ code: 'USAGE_DOMESTIQUE', libelle: 'Usage domestique', texte: 'ر7018- ضريبة الجدول 5 %' }],
        }),
        formalite: formalites(),
      });
      await rendre();

      const bloc = await screen.findByTestId('regulatory-usages');
      expect(bloc).toHaveTextContent('Usage domestique');
      expect(bloc).toHaveTextContent('ر7018- ضريبة الجدول 5 %');
      expect(bloc).toHaveTextContent('régime courant');
    });

    it("ne parle pas d'usage quand la position n'en a pas", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.queryByTestId('regulatory-usages')).not.toBeInTheDocument();
    });
  });

  describe('position et désignation', () => {
    it('un code national inexistant servi par la ligne SH6 le dit, sous le vrai code', async () => {
      repondre({
        position: fiche({ code: '010121', niveau: 'hs6', hs6: '010121' }),
        formalite: formalites(),
      });
      await rendre({ hsCode: '0101210000' });

      expect(await screen.findByTestId('regulatory-code-substituted')).toHaveTextContent(
        "Le code 0101210000 n'existe pas au tarif de ce pays : la ligne affichée est celle du SH6 010121.",
      );
      expect(screen.getByText('Ligne SH6')).toBeInTheDocument();
      expect(screen.queryByText('Code HS6')).not.toBeInTheDocument();
    });

    it("un code saisi qui n'est pas une ligne du tarif, servi par une autre position, le dit", async () => {
      repondre({ position: fiche({ code: '01012100' }), formalite: formalites() });
      await rendre({ hsCode: '01012199' });

      expect(await screen.findByTestId('regulatory-code-substituted')).toHaveTextContent(
        'la ligne affichée est celle de la position 01012100',
      );
    });

    it.each([
      ['un code exact', '0201101100', '0201101100', 'national'],
      ['un SH6 résolu à sa seule position', '020110', '0201101100', 'national'],
      ['un SH6 de six chiffres servi par sa ligne SH6 (COM, SDN, STP)', '051199', '051199', 'hs6'],
      ['un code saisi avec sa clé de contrôle (TUN)', '01012100015', '0101210001', 'national'],
      ['un code saisi avec des tirets', '0101-21-00-01', '0101210001', 'national'],
      ['un code saisi avec des points et des espaces', '0101.21 00 01', '0101210001', 'national'],
      ["un code plus court que la position servie", '02011011', '0201101100', 'national'],
    ])('ne dit rien pour %s', async (_nom, saisi, servi, niveau) => {
      repondre({ position: fiche({ code: servi, niveau }), formalite: formalites() });
      await rendre({ hsCode: saisi });

      await screen.findByText('De veaux');
      expect(screen.queryByTestId('regulatory-code-substituted')).not.toBeInTheDocument();
    });

    it("la désignation arabe se lit dans l'écran arabe", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre({ language: 'ar' });

      expect(await screen.findByText('من العجول')).toBeInTheDocument();
    });

    it("sans désignation publiée, l'écran le dit au lieu d'une carte vide", async () => {
      repondre({
        position: fiche({ description_fr: '', description_en: '', description_ar: '' }),
        formalite: formalites(),
      });
      await rendre();

      expect(await screen.findByTestId('regulatory-no-description')).toHaveTextContent('Désignation non publiée');
    });

    it("une désignation réduite au code (Libye) cède la place à celle qui dit quelque chose du produit", async () => {
      repondre({
        position: fiche({ description_fr: '010310.00', description_en: '010310.00', description_ar: '- أصيلة للأنسال' }),
        formalite: formalites(),
      });
      await rendre();

      expect(await screen.findByText('- أصيلة للأنسال')).toBeInTheDocument();
      expect(screen.queryByText('010310.00')).not.toBeInTheDocument();
    });
  });

  describe('restrictions', () => {
    it('sert les restrictions telles que la source les écrit', async () => {
      repondre({
        position: fiche({
          restrictions: [{ type: 'restriction(ق)', libelle: null, texte: 'ق3034- لايصرح بتصدير اصناف', portee: null, source: 'customs.gov.eg' }],
        }),
        formalite: formalites(),
      });
      await rendre();

      const bloc = await screen.findByTestId('regulatory-restrictions');
      expect(bloc).toHaveTextContent('ق3034- لايصرح بتصدير اصناف');
      expect(bloc).toHaveTextContent('customs.gov.eg');
    });

    it("une interdiction d'importation se lit : son libellé, son texte, sa portée", async () => {
      repondre({
        position: fiche({
          droits: [droit({ code: 'TSP', taux: null }), droit({ code: 'TP', taux: null })],
          restrictions: [{
            type: 'IMPORTATION_INTERDITE', libelle: 'Importation interdite', texte: 'ممنوع استيراده',
            portee: 'NPF et Ligue arabe', source: 'customs.gov.ly',
          }],
        }),
        formalite: formalites(),
      });
      await rendre();

      const bloc = await screen.findByTestId('regulatory-restriction');
      expect(bloc).toHaveTextContent('Importation interdite');
      expect(bloc).toHaveTextContent('ممنوع استيراده');
      expect(bloc).toHaveTextContent('Portée : NPF et Ligue arabe');
    });

    it("le libellé d'un type connu suit la langue de l'écran", async () => {
      repondre({
        position: fiche({
          restrictions: [{ type: 'IMPORTATION_INTERDITE', libelle: 'Importation interdite', texte: 'ممنوع استيراده', portee: null, source: null }],
        }),
        formalite: formalites(),
      });
      await rendre({ language: 'en' });

      expect(await screen.findByTestId('regulatory-restriction')).toHaveTextContent('Import prohibited');
    });

    it("une restriction ordinaire se lit après les taux, qu'elle n'enfouit pas", async () => {
      repondre({
        position: fiche({
          restrictions: [{ type: 'restriction(ق)', libelle: null, texte: 'ق3034- لايصرح بتصدير اصناف', portee: null, source: 'customs.gov.eg' }],
        }),
        formalite: formalites(),
      });
      await rendre();

      const restrictions = await screen.findByTestId('regulatory-restrictions');
      const premiereLigne = screen.getAllByTestId('regulatory-measure')[0];
      expect(premiereLigne.compareDocumentPosition(restrictions) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    it("une carte repliée à la recherche précédente ne masque pas l'interdiction de la suivante", async () => {
      const ordinaire = { type: 'restriction(ق)', libelle: null, texte: 'ق3034- لايصرح بتصدير اصناف', portee: null, source: 'customs.gov.eg' };
      const interdiction = { type: 'IMPORTATION_INTERDITE', libelle: 'Importation interdite', texte: 'ممنوع استيراده', portee: null, source: 'customs.gov.ly' };
      let position = fiche({ restrictions: [ordinaire, ordinaire, ordinaire] });
      axios.get.mockImplementation((url) => Promise.resolve({ data: url.includes('/position/') ? position : formalites() }));

      const { rerender } = await rendre({ countryCode: 'EGY' });
      expect(await screen.findAllByTestId('regulatory-restriction')).toHaveLength(3);
      // L'opérateur replie la carte.
      await act(async () => { screen.getByText('Restrictions').click(); });
      expect(screen.queryAllByTestId('regulatory-restriction')).toHaveLength(0);

      // Recherche suivante : une position interdite. La carte ne doit pas rester repliée.
      position = fiche({ restrictions: [interdiction] });
      rerender(panneau({ countryCode: 'LBY', hsCode: '0101210000' }));
      await avancer(500);

      expect(await screen.findByText('Importation interdite')).toBeInTheDocument();
      expect(screen.getAllByTestId('regulatory-restriction')).toHaveLength(1);
    });

    it("les textes de la source se coupent plutôt que de déborder (mots collés, arabe long)", async () => {
      repondre({
        position: fiche({
          description_fr: 'DÉSIGNATION-SANS-ESPACE',
          restrictions: [{ type: 'restriction(ق)', libelle: null, texte: 'ق3034-نصطويلبلافراغات', portee: null, source: 'customs.gov.eg' }],
          usages: [{ code: 'U', libelle: 'Usage', texte: 'ر7018-نصطويلبلافراغات' }],
        }),
        formalite: formalites({
          formalities: [{ code: '4046', texte: 'نصرسميطويلبلافراغات', document_fr: 'Traduction', traduction_non_officielle: true, base_legale: 'Base-légale-sans-espace' }],
        }),
      });
      await rendre();

      for (const texte of ['DÉSIGNATION-SANS-ESPACE', 'ق3034-نصطويلبلافراغات', 'ر7018-نصطويلبلافراغات', 'نصرسميطويلبلافراغات', 'Base-légale-sans-espace']) {
        expect(await screen.findByText(texte)).toHaveClass('break-words');
      }
    });

    it("l'interdiction se lit avant les taux, pas après", async () => {
      repondre({
        position: fiche({
          restrictions: [{ type: 'IMPORTATION_INTERDITE', libelle: 'Importation interdite', texte: 'ممنوع استيراده', portee: null, source: null }],
        }),
        formalite: formalites(),
      });
      await rendre();

      const restrictions = await screen.findByTestId('regulatory-restrictions');
      const premiereLigne = screen.getAllByTestId('regulatory-measure')[0];
      expect(restrictions.compareDocumentPosition(premiereLigne) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });
  });

  describe('formalités', () => {
    it("Égypte : le texte officiel arabe d'abord, la traduction dite non officielle ensuite", async () => {
      repondre({
        position: fiche(),
        formalite: formalites({
          formalities: [{
            code: '4046', texte: 'الموافقة المسبقة للحجر البيطري',
            document_fr: "L'importation requiert l'approbation préalable.", document_en: 'Prior approval is required.',
            traduction_non_officielle: true,
          }],
        }),
      });
      await rendre();

      const officiel = await screen.findByText('الموافقة المسبقة للحجر البيطري');
      const traduction = screen.getByText(/L'importation requiert l'approbation préalable\./);
      expect(traduction).toHaveTextContent('traduction non officielle');
      expect(officiel.compareDocumentPosition(traduction) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    it("hors Égypte, une formalité ne porte ni texte arabe ni mention de traduction", async () => {
      repondre({ position: fiche(), formalite: formalites() });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.getByTestId('regulatory-formality')).not.toHaveTextContent('traduction non officielle');
    });

    it("la base légale et l'autorité émettrice de la source se lisent", async () => {
      repondre({
        position: fiche(),
        formalite: formalites({
          formalities: [{
            code: 'A1', document_fr: 'Permis', document_en: 'Permit',
            base_legale: 'Code des douanes, loi 2017-035, art. 111', issuing_authority: 'Animal Diseases Act, 1984',
          }],
        }),
      });
      await rendre();

      const formalite = await screen.findByTestId('regulatory-formality');
      expect(formalite).toHaveTextContent('Code des douanes, loi 2017-035, art. 111');
      expect(formalite).toHaveTextContent('Animal Diseases Act, 1984');
    });

    it('des formalités indisponibles ne font pas tomber les droits, et ne se lisent pas « aucune »', async () => {
      repondre({ position: fiche(), formalite: refus(500, '') });
      await rendre();

      expect(await screen.findByText('De veaux')).toBeInTheDocument();
      expect(screen.getByText('5%')).toBeInTheDocument();
      expect(screen.getByTestId('regulatory-formalities-unavailable')).toHaveTextContent(
        "Une absence d'information n'est pas une absence d'obligation",
      );
    });

    it('le statut des formalités accompagne la liste, même vide (français : le texte du serveur)', async () => {
      repondre({
        position: fiche(),
        formalite: formalites({
          formalities: [],
          statut: 'NON_ETABLIES',
          reserve: 'Formalités non établies pour cette position.',
        }),
      });
      await rendre();

      await screen.findByText('De veaux');
      expect(screen.getByTestId('regulatory-formalities-status')).toHaveTextContent('Formalités non établies');
    });

    it('le statut des formalités est traduit dans la langue de l\'écran', async () => {
      repondre({
        position: fiche(),
        formalite: formalites({
          formalities: [],
          statut: 'NON_ETABLIES',
          reserve: 'Formalités non établies pour cette position.',
        }),
      });
      await rendre({ language: 'en' });

      const statut = await screen.findByTestId('regulatory-formalities-status');
      expect(statut).toHaveTextContent('Formalities not established for this position');
      expect(statut).not.toHaveTextContent('Formalités non établies');
    });

    it('un statut inconnu garde le texte du serveur plutôt que de se taire', async () => {
      repondre({
        position: fiche(),
        formalite: formalites({ formalities: [], statut: 'STATUT_FUTUR', reserve: 'Texte du serveur.' }),
      });
      await rendre({ language: 'en' });

      expect(await screen.findByTestId('regulatory-formalities-status')).toHaveTextContent('Texte du serveur.');
    });
  });

  describe('erreurs', () => {
    it('un SH6 à plusieurs positions est un choix à faire, pas une panne', async () => {
      repondre({
        position: refus(422, {
          code: 'POSITION_NATIONALE_REQUISE',
          message: 'DZA/020110 : 4 positions nationales sous ce SH6 — choisir la position.',
          positions: [{ code: '0201101100' }, { code: '0201101900' }, { code: '0201102100' }, { code: '0201102900' }],
        }),
        formalite: refus(422, {}),
      });
      await rendre({ hsCode: '020110' });

      const carte = await screen.findByTestId('regulatory-details-choice');
      expect(carte).toHaveTextContent('4 positions nationales');
      expect(screen.queryByTestId('regulatory-details-error')).not.toBeInTheDocument();
      expect(console.error).not.toHaveBeenCalled();
    });

    it('une position absente se dit, avec le pays', async () => {
      repondre({ position: refus(404, 'DZA/9999999999 : position absente du socle'), formalite: refus(404, '') });
      await rendre({ hsCode: '9999999999' });

      expect(await screen.findByText('Position introuvable dans les données servies pour ce pays')).toBeInTheDocument();
    });

    it("un code invalide refusé par la route (422 sans choix) se dit position introuvable", async () => {
      repondre({ position: refus(422, "code SH invalide : 'abc' (six chiffres au minimum)"), formalite: refus(422, '') });
      await rendre();

      expect(await screen.findByText('Position introuvable dans les données servies pour ce pays')).toBeInTheDocument();
      expect(screen.queryByTestId('regulatory-details-choice')).not.toBeInTheDocument();
    });

    it('un tarif indisponible se dit indisponible, sans promettre son retour', async () => {
      repondre({ position: refus(503, 'DZA n\'est pas au socle'), formalite: refus(503, '') });
      await rendre();

      expect(await screen.findByText('Tarif de ce pays indisponible')).toBeInTheDocument();
      expect(screen.queryByText(/momentanément/)).not.toBeInTheDocument();
    });

    it("le message d'erreur suit la langue de l'écran, même changée après la requête", async () => {
      repondre({ position: refus(503, ''), formalite: refus(503, '') });
      const { rerender } = await rendre();
      await screen.findByText('Tarif de ce pays indisponible');

      rerender(panneau({ language: 'en' }));
      expect(await screen.findByText("This country's tariff is unavailable")).toBeInTheDocument();
      expect(screen.queryByText('Tarif de ce pays indisponible')).not.toBeInTheDocument();
    });
  });

  it("parle la langue de l'interface", async () => {
    repondre({ position: fiche(), formalite: formalites() });
    await rendre({ language: 'en' });

    expect(await screen.findByText('Of calves')).toBeInTheDocument();
    expect(screen.getByText('Duties and Taxes')).toBeInTheDocument();
    expect(screen.getByText('Import declaration')).toBeInTheDocument();
  });
});
