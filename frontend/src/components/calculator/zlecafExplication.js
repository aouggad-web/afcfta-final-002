import { isDisplayableZlecafResult } from './zlecafAvailability';

/**
 * Explication du résultat ZLECAf, en quatre questions fixes : statut de la
 * préférence, taux retenu et sa source, effet sur le calcul, réserves.
 *
 * Aucune valeur n'est calculée ici : la fonction met en mots les champs que
 * le calcul a déjà renvoyés. Un taux d'offre n'est jamais présenté comme
 * appliqué, et un champ absent reste absent (pas de 0 % de repli).
 */

const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

const pct = (value) => `${Number(value.toFixed(2))} %`;

const titreSource = (source) => {
  if (!source) return null;
  if (typeof source === 'string') return source;
  return source.title || null;
};

const lienSource = (source) => (source && typeof source === 'object' ? source.url || null : null);

const TEXTES = {
  fr: {
    statut: 'Statut de la préférence',
    taux: 'Taux retenu et source',
    effet: 'Effet sur le calcul',
    reserves: 'Réserves',
    titres: {
      APPLICATION_DOCUMENTEE: 'Application documentée',
      SANS_AVANTAGE: 'Application documentée — sans avantage sur cette ligne',
      SIMULATION_CONDITIONNELLE: 'Simulation conditionnelle',
      SIMULATION_OFFRE: 'Simulation sur offre',
      UNION_DOUANIERE: 'Union douanière — hors ZLECAf',
      NON_CALCULABLE: 'Non calculable',
    },
    sansOrigine: 'Aucun pays d’origine sélectionné : la préférence ZLECAf dépend de l’origine du produit.',
    appliquee: 'La destination applique la ZLECAf à cette origine.',
    offreSeule:
      'Une offre tarifaire officielle est publiée, mais sa mise en œuvre pour cette origine n’est pas établie.',
    notification:
      'Le texte national est en vigueur, mais la liste des origines admises n’est pas publiée : admission de l’origine à confirmer auprès de la douane de destination.',
    tauxLigne: (taux) => `Taux ZLECAf de la ligne : ${taux}.`,
    tauxOffre: (taux) => `Taux prévu par l’offre publiée : ${taux}.`,
    tauxAbsent: 'Aucun taux ZLECAf exploitable pour cette ligne.',
    source: (titre) => `Source : ${titre}.`,
    baisse: (npf, zl) => `Le droit de douane passe de ${npf} (NPF) à ${zl}.`,
    egal: (taux) =>
      `Taux identique au taux normal (NPF) de ${taux} : aucun avantage sur cette ligne.`,
    tauxSansNpf: (zl) => `Le droit de douane est liquidé au taux ZLECAf de ${zl}.`,
    nonApplique: 'Ce taux n’est pas appliqué au total : le calcul affiché reste au taux normal (NPF).',
    unionEffet: 'Le droit de douane de l’union douanière s’applique à la place de la ZLECAf.',
    nonCalculableEffet: 'Le calcul affiché reste au taux normal (NPF).',
    plancher: 'Le taux préférentiel dépassait le taux normal : le taux normal (NPF) est retenu.',
    certificat: 'Certificat d’origine ZLECAf requis.',
    nonOpposable: 'Simulation informative — non opposable à l’administration douanière.',
  },
  en: {
    statut: 'Preference status',
    taux: 'Rate used and source',
    effet: 'Effect on the calculation',
    reserves: 'Reservations',
    titres: {
      APPLICATION_DOCUMENTEE: 'Documented application',
      SANS_AVANTAGE: 'Documented application — no advantage on this line',
      SIMULATION_CONDITIONNELLE: 'Conditional simulation',
      SIMULATION_OFFRE: 'Offer-based simulation',
      UNION_DOUANIERE: 'Customs union — outside AfCFTA',
      NON_CALCULABLE: 'Not calculable',
    },
    sansOrigine: 'No country of origin selected: the AfCFTA preference depends on the origin of the goods.',
    appliquee: 'The destination applies the AfCFTA to this origin.',
    offreSeule:
      'An official tariff offer is published, but its implementation for this origin is not established.',
    notification:
      'The national instrument is in force, but the list of admitted origins is not published: admission of the origin must be confirmed with destination customs.',
    tauxLigne: (taux) => `AfCFTA rate for this line: ${taux}.`,
    tauxOffre: (taux) => `Rate in the published offer: ${taux}.`,
    tauxAbsent: 'No usable AfCFTA rate for this line.',
    source: (titre) => `Source: ${titre}.`,
    baisse: (npf, zl) => `Customs duty goes from ${npf} (MFN) to ${zl}.`,
    egal: (taux) => `Rate identical to the normal (MFN) rate of ${taux}: no advantage on this line.`,
    tauxSansNpf: (zl) => `Customs duty is assessed at the AfCFTA rate of ${zl}.`,
    nonApplique: 'This rate is not applied to the total: the calculation shown stays at the normal (MFN) rate.',
    unionEffet: 'The customs union duty applies instead of the AfCFTA.',
    nonCalculableEffet: 'The calculation shown stays at the normal (MFN) rate.',
    plancher: 'The preferential rate exceeded the normal rate: the normal (MFN) rate is used.',
    certificat: 'AfCFTA certificate of origin required.',
    nonOpposable: 'Informative simulation — not binding on customs authorities.',
  },
};

function niveauDe(result) {
  if (result?.trade_regime === 'CUSTOMS_UNION') return 'UNION_DOUANIERE';
  if (isDisplayableZlecafResult(result)) {
    const zl = result.zlecaf_tariff_rate * 100;
    const npf = result.npf_dd_rate_pct;
    return isNumber(npf) && zl >= npf - 1e-9 ? 'SANS_AVANTAGE' : 'APPLICATION_DOCUMENTEE';
  }
  if (result?.zlecaf_status === 'OFFER_ONLY') return 'SIMULATION_OFFRE';
  if (result?.zlecaf_status === 'PARTNER_NOTICE_REQUIRED') return 'SIMULATION_CONDITIONNELLE';
  return 'NON_CALCULABLE';
}

export function expliquerZlecaf(result, language = 'fr') {
  const t = TEXTES[language === 'en' ? 'en' : 'fr'];
  const niveau = niveauDe(result);
  const note = result?.zlecaf_note || result?.trade_regime_note || null;
  const npf = isNumber(result?.npf_dd_rate_pct) ? result.npf_dd_rate_pct : null;

  let statut;
  let taux;
  let source = null;
  let effet;
  const reserves = [];

  if (niveau === 'APPLICATION_DOCUMENTEE' || niveau === 'SANS_AVANTAGE') {
    const zl = result.zlecaf_tariff_rate * 100;
    statut = t.appliquee;
    taux = t.tauxLigne(result.zlecaf_rate_expression || pct(zl));
    source = result.zlecaf_rate_source;
    if (niveau === 'SANS_AVANTAGE') effet = t.egal(pct(npf));
    else effet = npf !== null ? t.baisse(pct(npf), pct(zl)) : t.tauxSansNpf(pct(zl));
    if (result.plancher_npf) reserves.push(t.plancher);
    if (result.zlecaf_reserve) reserves.push(result.zlecaf_reserve);
    reserves.push(t.certificat);
  } else if (niveau === 'SIMULATION_OFFRE' || niveau === 'SIMULATION_CONDITIONNELLE') {
    statut = niveau === 'SIMULATION_OFFRE' ? t.offreSeule : t.notification;
    const offre = result.zlecaf_offer_rate_expression
      || (isNumber(result.zlecaf_offer_rate_pct) ? pct(result.zlecaf_offer_rate_pct) : null);
    taux = offre ? t.tauxOffre(offre) : t.tauxAbsent;
    source = offre ? result.zlecaf_offer_rate_source : null;
    effet = t.nonApplique;
    reserves.push(t.certificat);
  } else if (niveau === 'UNION_DOUANIERE') {
    statut = note;
    taux = null;
    effet = t.unionEffet;
  } else {
    const origine = result?.origin_country_iso3 || result?.origin_country;
    statut = origine ? note || t.tauxAbsent : t.sansOrigine;
    taux = null;
    effet = t.nonCalculableEffet;
  }
  reserves.push(t.nonOpposable);

  const titre = titreSource(source);
  const lignes = [
    { cle: 'statut', label: t.statut, texte: statut },
    {
      cle: 'taux',
      label: t.taux,
      texte: taux ? [taux, titre ? t.source(titre) : null].filter(Boolean).join(' ') : null,
      lien: taux ? lienSource(source) : null,
    },
    { cle: 'effet', label: t.effet, texte: effet },
    { cle: 'reserves', label: t.reserves, texte: reserves.filter(Boolean).join(' ') },
  ].filter((ligne) => ligne.texte);

  return { niveau, titre: t.titres[niveau], lignes };
}
