import { describe, it, expect, beforeAll } from 'vitest';
import { writeFileSync } from 'node:fs';
import { buildOpportunityPdf } from './opportunityPdf';
import { specFichePortPdf, specFicheAeroportPdf, specFicheCorridorPdf } from './logistiqueFichesPdf';
import { chargerPoliceArabe } from './pdfArabe';
import port from './__fixtures__/logistiquePortDZA.json';
import aeroport from './__fixtures__/logistiqueAeroportJNB.json';
import corridor from './__fixtures__/logistiqueCorridorAbidjanLagos.json';

// Réponses réelles du backend, prises le 08/11/2026 :
// GET /logistics/ports/DZA-ALG-001, GET /logistics/air/airports/ZAF-JNB-001,
// et l'élément CORR-ABIDJAN-LAGOS-002 de GET /logistics/land/corridors.

const ecrire = (doc, nom) => {
  // Pour regarder le rendu : PDF_SORTIE=/chemin/dossier npx vitest run …
  if (process.env.PDF_SORTIE) writeFileSync(`${process.env.PDF_SORTIE}/${nom}`, Buffer.from(doc.output('arraybuffer')));
};
const titres = (spec) => spec.sections.map((s) => s.title).filter(Boolean);
const valeur = (spec, titre, label) => spec.sections.find((s) => s.title === titre).keyValues.find((kv) => kv.label === label).value;

const FICHES = [
  ['port', specFichePortPdf, port, {
    fr: ["Port d'Alger", 'FICHE PORT'], en: ["Port d'Alger", 'PORT PROFILE'], ar: ['ميناء الجزائر', 'بطاقة ميناء'],
  }],
  ['aeroport', specFicheAeroportPdf, aeroport, {
    fr: ['Johannesburg - O.R. Tambo International', 'FICHE AÉROPORT'],
    en: ['Johannesburg - O.R. Tambo International', 'AIRPORT PROFILE'],
    ar: ['جوهانسبرغ - أو. آر. تامبو الدولي', 'بطاقة مطار'],
  }],
  ['corridor', specFicheCorridorPdf, corridor, {
    fr: ['Corridor Abidjan-Lagos', 'FICHE CORRIDOR'], en: ['Corridor Abidjan-Lagos', 'CORRIDOR PROFILE'], ar: ['ممر أبيدجان-لاغوس', 'بطاقة ممر'],
  }],
];

beforeAll(async () => {
  await chargerPoliceArabe();
});

describe('Fiches PDF du module Logistique', () => {
  FICHES.forEach(([nom, spec, donnees, attendus]) => {
    ['fr', 'en', 'ar'].forEach((langue) => {
      it(`${nom} : se construit en ${langue}, titre et pastille dans la langue`, () => {
        const s = spec(donnees, langue);
        const [titre, badge] = attendus[langue];
        expect(s.title).toBe(titre);
        expect(s.badge).toBe(badge);
        expect(s.sections.at(-1).notice).toHaveLength(2);
        // Aucun tableau vide.
        s.sections.filter((x) => x.table).forEach((x) => expect(x.table.rows.length).toBeGreaterThan(0));
        const doc = buildOpportunityPdf({ ...s, language: langue });
        if (langue === 'ar') expect(doc.output()).toContain('/BaseFont /NotoArabe');
        if (langue !== 'en') ecrire(doc, `${nom}-${langue}.pdf`);
      });
    });
  });

  it('port : autorité avec contacts, terminaux, trafic par année, agents', () => {
    const s = specFichePortPdf(port, 'fr');
    expect(s.subtitle).toBe('Algérie · UN/LOCODE DZALG · Maritime Commercial');
    expect(titres(s)).toEqual(expect.arrayContaining([
      'Identité du port', 'Autorité portuaire', 'Infrastructures — terminaux', 'Statistiques de trafic',
      'Évolution du trafic', 'Performance portuaire', 'Temps de séjour des conteneurs (dwell time) et TRS',
      'Lignes maritimes régulières', 'Agents maritimes et opérateurs', 'Avertissement',
    ]));
    expect(valeur(s, 'Autorité portuaire', 'Téléphone')).toBe('+213 21 24 34 96');
    expect(valeur(s, 'Autorité portuaire', 'Capitainerie')).toContain('VHF Canal 16');
    const trafic = s.sections.find((x) => x.title === 'Évolution du trafic').table;
    expect(trafic.rows.map((r) => r.year.slice(0, 4))).toEqual(port.traffic_evolution.map((r) => String(r.year)).sort());
    const agents = s.sections.find((x) => x.title === 'Agents maritimes et opérateurs').table.rows;
    expect(agents).toHaveLength(port.agents.length);
    expect(agents[0].contact.split('\n')[0]).toBe(port.agents[0].contact);
    // Les pictogrammes des données (ℹ️, ⚠️) ne passent pas dans le PDF.
    expect(JSON.stringify(s)).not.toMatch(/[ℹ⚠️]/u);
  });

  it('port : une valeur absente s’écrit « non publié », jamais 0', () => {
    const p = structuredClone(port);
    delete p.latest_stats.vessel_calls;
    p.performance_metrics.avg_waiting_time_hours = null;
    p.trs_analysis.container_dwell_time_days = 'NA';
    p.port_authority.contact_phone = 'Voir site officiel';
    const fr = specFichePortPdf(p, 'fr');
    expect(fr.kpis.find((k) => k.label === 'Escales navires').value).toBe('non publié');
    expect(fr.kpis.find((k) => k.label === 'Attente au mouillage').value).toBe('non publié');
    expect(fr.kpis.find((k) => k.label === 'Dwell time').value).toBe('non publié');
    expect(valeur(fr, 'Autorité portuaire', 'Téléphone')).toBe('non publié');
    expect(specFichePortPdf(p, 'en').kpis.find((k) => k.label === 'Vessel calls').value).toBe('not published');
    expect(specFichePortPdf(p, 'ar').kpis.find((k) => k.label === 'توقفات السفن').value).toBe('غير منشور');
  });

  it('port : aucune valeur générée, les estimations portent « estimé »', () => {
    const s = specFichePortPdf(port, 'fr');
    const texte = JSON.stringify(s);
    // Productivité, séjour au port et note d'efficacité ne sont plus servis.
    expect(texte).not.toMatch(/mouvements\/heure|Productivité|Note d'efficacité|Séjour au port/);
    const annees = s.sections.find((x) => x.title === 'Évolution du trafic').table.rows.map((r) => r.year);
    expect(annees).toContain('2019 (estimé)');
    expect(annees).toContain('2024');
    expect(s.kpis.find((k) => k.label === 'Dwell time').sub).toContain('estimé');
    expect(valeur(s, 'Performance portuaire', 'Source')).toContain('Kuehne+Nagel');

    const p = structuredClone(port);
    p.performance_metrics.nature = 'estimation';
    const e = specFichePortPdf(p, 'en');
    expect(e.kpis.find((k) => k.label === 'Anchorage waiting').sub).toBe('estimated');
    expect(valeur(e, 'Port performance', 'Anchorage waiting time')).toMatch(/^144 h \(estimated\)/);
  });

  it('aéroport : statistiques, acteurs, lignes cargo et non publié', () => {
    const s = specFicheAeroportPdf(aeroport, 'fr');
    expect(s.subtitle).toBe('Afrique du Sud · IATA JNB · OACI FAOR');
    const histo = s.sections.find((x) => x.title === 'Statistiques historiques').table.rows;
    expect(histo.map((r) => r.year)).toEqual(aeroport.historical_stats.map((h) => String(h.year)).sort().reverse());
    const routes = s.sections.find((x) => x.title === 'Lignes cargo régulières').table.rows;
    expect(routes[0]).toMatchObject({ carrier: 'Ethiopian Cargo', rotation: 'ADD-NBO-JNB-HKG', aircraft: 'B777F, B787F' });
    expect(s.sections.find((x) => x.title === 'Acteurs du fret aérien').table.rows).toHaveLength(aeroport.actors.length);

    const a = structuredClone(aeroport);
    a.historical_stats[0].mail_throughput_tons = null;
    delete a.annual_capacity_tons;
    const k = specFicheAeroportPdf(a, 'fr').kpis;
    expect(k.find((x) => x.label === 'Courrier').value).toBe('non publié');
    expect(k.find((x) => x.label === 'Capacité annuelle').value).toBe('non publié');
    expect(k.find((x) => x.label === 'Taux d’utilisation').value).toBe('non publié');
  });

  it('corridor : tracé, postes-frontières, opérateurs, agents avec téléphones', () => {
    const s = specFicheCorridorPdf(corridor, 'fr');
    expect(s.subtitle).toBe("Autoroute Transafricaine · Routier · Côte d'Ivoire - Ghana - Togo - Bénin - Nigéria");
    expect(s.kpis.find((k) => k.label === 'Postes OSBP').value).toBe('2');
    const noeuds = s.sections.find((x) => x.title === 'Nœuds logistiques et postes-frontières').table.rows;
    expect(noeuds).toHaveLength(corridor.nodes.length);
    expect(noeuds[1]).toMatchObject({ type: 'Poste-frontière', osbp: 'oui' });
    const agents = s.sections.find((x) => x.title === 'Agents locaux').table.rows;
    const total = Object.values(corridor.logistics_network.local_agents_by_country).flat().length;
    expect(agents).toHaveLength(total);
    expect(agents[0].contact.split('\n')[0]).toBe('+225 27 20 21 03 03');
  });

  it('corridor sans statistiques : « non publié », jamais 0', () => {
    const c = { ...corridor, stats: undefined, logistics_network: undefined, operators: [] };
    const s = specFicheCorridorPdf(c, 'fr');
    ['Fret annuel', 'Temps de transit', 'Passage frontière', 'Trafic quotidien']
      .forEach((label) => expect(s.kpis.find((k) => k.label === label).value).toBe('non publié'));
    expect(valeur(s, 'Statistiques du corridor', 'Camions par jour')).toBe('non publié');
    expect(specFicheCorridorPdf(c, 'ar').kpis.find((k) => k.label === 'الشحن السنوي').value).toBe('غير منشور');
    expect(() => buildOpportunityPdf({ ...s, language: 'fr' })).not.toThrow();
  });
});
