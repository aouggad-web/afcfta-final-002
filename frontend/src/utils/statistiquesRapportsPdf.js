/**
 * Rapports PDF du module Statistiques : vue d'ensemble du commerce africain,
 * analyses d'un pays (avantage comparatif révélé, complémentarité, marge
 * préférentielle ZLECAf) et comparaison multi-pays.
 *
 * Même bâtisseur que les autres modules (utils/opportunityPdf.js) : chaque
 * fonction décrit son rapport en données, à partir de la réponse de l'API
 * telle que l'écran l'affiche — le PDF ne recalcule rien, sauf ce que
 * l'écran calcule lui-même (projections du commerce intra-africain, indices
 * du radar), refait ici avec la même règle.
 *
 * Règle commune : une valeur que la source ne publie pas s'écrit « non
 * publié », jamais 0. Les libellés que l'API ne donne qu'en une langue
 * (noms de produits OEC en anglais, secteurs) restent tels quels, sauf
 * traduction arabe connue (trDonnee).
 */
import { estAnglais, montant, montantCompact, montantUnite, nombre } from './nombres';
import { AFRICAN_COUNTRIES } from './countryCodes';
import { trDonnee } from '../i18n/donnees';

const NBSP = ' ';

const COMMUN = {
  fr: {
    module: 'MODULE STATISTIQUES',
    na: 'non publié',
    warning: 'Avertissement',
    revised: 'Les sources révisent leurs séries : vérifier la dernière publication avant toute décision.',
    advice: "Ce rapport est une synthèse d'information statistique : il ne constitue pas un conseil en investissement.",
    country: 'Pays',
    year: 'Année',
    source: 'Source',
    consulted: 'Données consultées le',
    hsLevel: 'Niveau SH',
    levels: { HS2: 'SH2 — chapitres', HS4: 'SH4 — positions', HS6: 'SH6 — sous-positions' },
  },
  en: {
    module: 'STATISTICS MODULE',
    na: 'not published',
    warning: 'Disclaimer',
    revised: 'Sources revise their series: check the latest release before making any decision.',
    advice: 'This report summarises statistical information: it is not investment advice.',
    country: 'Country',
    year: 'Year',
    source: 'Source',
    consulted: 'Data retrieved on',
    hsLevel: 'HS level',
    levels: { HS2: 'HS2 — chapters', HS4: 'HS4 — headings', HS6: 'HS6 — subheadings' },
  },
  ar: {
    module: 'وحدة الإحصائيات',
    na: 'غير منشور',
    warning: 'تنبيه',
    revised: 'تراجع المصادر سلاسلها: يُرجى التحقق من آخر إصدار قبل أي قرار.',
    advice: 'هذا التقرير خلاصة لمعلومات إحصائية: لا يُعدّ نصيحة استثمارية.',
    country: 'البلد',
    year: 'السنة',
    source: 'المصدر',
    consulted: 'تاريخ استرجاع البيانات',
    hsLevel: 'مستوى SH',
    levels: { HS2: 'SH2 — الفصول', HS4: 'SH4 — البنود', HS6: 'SH6 — البنود الفرعية' },
  },
};

const langueValide = (langue) => (COMMUN[langue] ? langue : 'fr');
const estNombre = (v) => typeof v === 'number' && Number.isFinite(v);
const date = () => new Date().toISOString().slice(0, 10);

/** Formateurs d'une langue : toute valeur absente donne « non publié ». */
function formats(langue) {
  const na = COMMUN[langue].na;
  const sep = estAnglais(langue) ? '' : NBSP;
  return {
    na,
    num: (v, d = 1) => (estNombre(v) ? nombre(v, langue, d) : na),
    pct: (v, d = 1) => (estNombre(v) ? `${nombre(v, langue, d)}${sep}%` : na),
    // Valeur déjà exprimée en milliards de dollars.
    md: (v, d = 1) => (estNombre(v) ? montantUnite(v, 'B', langue, d, { max: true }) : na),
    usd: (v) => (!estNombre(v) ? na
      : Math.abs(v) < 1e6 ? montant(v, langue) : montantCompact(v, langue, { T: 2, B: 1, M: 1 }, { max: true })),
    entier: (v) => (estNombre(v) ? nombre(v, langue, 0) : na),
    // Part en % : une petite part (0,0016 %) garde ses chiffres, jamais « 0 % ».
    part: (v) => (estNombre(v) ? `${nombre(v, langue, Math.abs(v) < 0.1 ? 4 : 2)}${sep}%` : na),
  };
}

/** « 1.5% » (chaîne de l'API) → nombre ; « N/A » → null. */
const nombreDe = (v) => {
  if (estNombre(v)) return v;
  const n = parseFloat(String(v ?? '').replace(',', '.'));
  return Number.isFinite(n) ? n : null;
};

// Noms que l'API écrit autrement que countryCodes.js.
const ALIAS_PAYS = { 'RD Congo': 'COD' };

/** Nom du pays dans la langue du rapport, depuis son ISO3 ou son nom (fr/en). */
function nomPays(cle, langue, repli) {
  if (!cle) return repli || '—';
  const iso = AFRICAN_COUNTRIES[cle] ? cle : ALIAS_PAYS[cle]
    || Object.keys(AFRICAN_COUNTRIES).find((k) => AFRICAN_COUNTRIES[k].name_fr === cle || AFRICAN_COUNTRIES[k].name_en === cle);
  if (iso) return AFRICAN_COUNTRIES[iso][`name_${langue}`] || AFRICAN_COUNTRIES[iso].name_fr;
  return trDonnee(repli || cle, langue);
}

/** Date ISO de l'API (retrieved_at) en jj/mm/aaaa. */
const dateLisible = (iso) => {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : null;
};

const avertissement = (langue, sources) => {
  const c = COMMUN[langue];
  return { title: c.warning, notice: [sources, c.revised, c.advice] };
};

/* ───────────────────────── 1. Vue d'ensemble ───────────────────────── */

const SECTEURS = {
  hydrocarbures: { fr: 'Hydrocarbures', en: 'Hydrocarbons', ar: 'المحروقات' },
  minerais_metaux: { fr: 'Minerais et métaux', en: 'Ores and metals', ar: 'الخامات والمعادن' },
  agriculture: { fr: 'Agriculture', en: 'Agriculture', ar: 'الزراعة' },
  produits_manufactures: { fr: 'Produits manufacturés', en: 'Manufactured goods', ar: 'المنتجات المصنَّعة' },
  automobile_transport: { fr: 'Automobile et transport', en: 'Automotive and transport', ar: 'السيارات والنقل' },
  chimie_pharmaceutique: { fr: 'Chimie et pharmacie', en: 'Chemicals and pharmaceuticals', ar: 'الكيمياء والصيدلة' },
  textile_habillement: { fr: 'Textile et habillement', en: 'Textiles and clothing', ar: 'النسيج والملابس' },
  autres: { fr: 'Autres', en: 'Other', ar: 'أخرى' },
};

const VUE = {
  fr: {
    badge: "VUE D'ENSEMBLE",
    title: "Commerce africain — vue d'ensemble",
    subtitle: (a) => `Échanges de marchandises des 54 pays africains · ${a} · ZLECAf`,
    gdp: 'PIB combiné',
    gdpSub: 'estimation, 54 pays',
    exports: 'Exportations totales',
    imports: 'Importations totales',
    flowSub: (a) => `${a} · OEC/BACI`,
    members: 'Pays membres',
    membersSub: 'États parties ZLECAf',
    totals: "Échanges de l'Afrique avec le monde",
    totalsText: (a, solde) => [
      `Exportations et importations : somme des échanges de marchandises enregistrés des pays africains avec le reste du monde en ${a}, en dollars courants (OEC, à partir de la base BACI du CEPII, qui harmonise les déclarations douanières UN Comtrade). Solde commercial de l'ensemble : ${solde}.`,
      "Le PIB combiné est une estimation agrégée (FMI, Banque mondiale) donnée pour ordre de grandeur ; l'écran l'affiche sous l'intitulé « Valeur totale commerce ».",
    ],
    topExp: (a) => `Top 10 exportateurs africains — ${a}`,
    topImp: (a) => `Top 10 importateurs africains — ${a}`,
    cols: { rank: '#', country: 'Pays', exp: 'Exportations', imp: 'Importations', share: "Part de l'Afrique" },
    topText: (a) => `Valeurs ${a} en dollars courants (OEC/BACI). La part rapporte le flux du pays au total africain de la même année : une poignée de pays concentre l'essentiel du commerce extérieur du continent.`,
    gdpTop: 'Top 10 PIB africains',
    gdpCols: { rank: '#', country: 'Pays', gdp: 'PIB', year: 'Année', growth: 'Croissance 2024', proj: 'Projection 2025' },
    gdpText: (src) => `PIB en dollars courants ; croissance réelle annuelle du PIB. ${src ? `Source : ${src}.` : ''} L'année indiquée est celle de la valeur de PIB publiée par la source.`,
    intra: 'Évolution du commerce intra-africain',
    intraCols: { year: 'Année', value: 'Commerce intra-africain', nature: 'Nature' },
    observed: 'observé',
    projection: 'projection',
    intraText: (g, cible) => [
      `Commerce intra-africain : échanges de marchandises entre pays africains, en milliards de dollars. Croissance 2023-2024 : ${g}.`,
      `Les années 2025, 2027 et 2030 sont des projections de l'écran (respectivement +12 %, +30 % et +52 % par rapport à 2024), non des observations. Objectif ZLECAf 2030 affiché : ${cible}.`,
    ],
    top5: 'Top 5 PIB — commerce mondial et intra-africain (2024)',
    top5Cols: { country: 'Pays', gdp: 'PIB', expW: 'Exp. monde', expI: 'Exp. intra-Afr.', pctI: 'Part intra', impW: 'Imp. monde', impI: 'Imp. intra-Afr.' },
    top5Text: "Part intra : part des exportations du pays destinées à d'autres pays africains. Le PIB de ce tableau est celui que publie cette série ; il peut différer du tableau Top 10 PIB (millésime ou source différents).",
    sectors: 'Exportations africaines par secteur (2024)',
    sectorCols: { sector: 'Secteur', share: 'Part des exportations', value: 'Valeur 2024' },
    sectorText: 'Répartition des exportations africaines de marchandises par grand secteur économique, en part du total et en milliards de dollars.',
    sources: 'Sources publiques citées : FMI (Perspectives de l’économie mondiale), Banque mondiale (WDI), CNUCED, OEC/BACI, Secrétariat de la ZLECAf, Banque africaine de développement. Chiffres repris tels que publiés, à la date indiquée pour chacun.',
    filename: 'Statistiques_vue_ensemble',
  },
  en: {
    badge: 'OVERVIEW',
    title: 'African trade — overview',
    subtitle: (a) => `Merchandise trade of the 54 African countries · ${a} · AfCFTA`,
    gdp: 'Combined GDP',
    gdpSub: 'estimate, 54 countries',
    exports: 'Total exports',
    imports: 'Total imports',
    flowSub: (a) => `${a} · OEC/BACI`,
    members: 'Member countries',
    membersSub: 'AfCFTA State Parties',
    totals: "Africa's trade with the world",
    totalsText: (a, solde) => [
      `Exports and imports: sum of the recorded merchandise trade of African countries with the rest of the world in ${a}, in current dollars (OEC, based on CEPII's BACI database, which harmonises UN Comtrade customs declarations). Overall trade balance: ${solde}.`,
      'Combined GDP is an aggregate estimate (IMF, World Bank) given as an order of magnitude; the screen shows it under the heading "Total trade value".',
    ],
    topExp: (a) => `Top 10 African exporters — ${a}`,
    topImp: (a) => `Top 10 African importers — ${a}`,
    cols: { rank: '#', country: 'Country', exp: 'Exports', imp: 'Imports', share: 'Share of Africa' },
    topText: (a) => `${a} values in current dollars (OEC/BACI). The share relates the country's flow to the African total for the same year: a handful of countries account for most of the continent's external trade.`,
    gdpTop: 'Top 10 African GDP',
    gdpCols: { rank: '#', country: 'Country', gdp: 'GDP', year: 'Year', growth: 'Growth 2024', proj: '2025 projection' },
    gdpText: (src) => `GDP in current dollars; annual real GDP growth. ${src ? `Source: ${src}.` : ''} The year shown is that of the GDP value published by the source.`,
    intra: 'Intra-African trade over time',
    intraCols: { year: 'Year', value: 'Intra-African trade', nature: 'Type' },
    observed: 'observed',
    projection: 'projection',
    intraText: (g, cible) => [
      `Intra-African trade: merchandise trade between African countries, in billions of dollars. Growth 2023-2024: ${g}.`,
      `2025, 2027 and 2030 are the screen's projections (+12%, +30% and +52% over 2024 respectively), not observations. AfCFTA 2030 target shown: ${cible}.`,
    ],
    top5: 'Top 5 GDP — world and intra-African trade (2024)',
    top5Cols: { country: 'Country', gdp: 'GDP', expW: 'Exp. world', expI: 'Exp. intra-Afr.', pctI: 'Intra share', impW: 'Imp. world', impI: 'Imp. intra-Afr.' },
    top5Text: "Intra share: share of the country's exports going to other African countries. The GDP in this table is the one published by this series; it may differ from the Top 10 GDP table (different vintage or source).",
    sectors: 'African exports by sector (2024)',
    sectorCols: { sector: 'Sector', share: 'Share of exports', value: '2024 value' },
    sectorText: 'Breakdown of African merchandise exports by broad economic sector, as a share of the total and in billions of dollars.',
    sources: 'Public sources cited: IMF (World Economic Outlook), World Bank (WDI), UNCTAD, OEC/BACI, AfCFTA Secretariat, African Development Bank. Figures reproduced as published, as of the date shown for each.',
    filename: 'Statistics_overview',
  },
  ar: {
    badge: 'نظرة عامة',
    title: 'التجارة الأفريقية — نظرة عامة',
    subtitle: (a) => `تجارة السلع للبلدان الأفريقية الـ54 · ${a} · زليكاف`,
    gdp: 'الناتج المحلي المجمَّع',
    gdpSub: 'تقدير، 54 بلدًا',
    exports: 'إجمالي الصادرات',
    imports: 'إجمالي الواردات',
    flowSub: (a) => `${a} · OEC/BACI`,
    members: 'البلدان الأعضاء',
    membersSub: 'الدول الأطراف في زليكاف',
    totals: 'تجارة أفريقيا مع العالم',
    totalsText: (a, solde) => [
      `الصادرات والواردات: مجموع تجارة السلع المسجَّلة للبلدان الأفريقية مع بقية العالم في ${a}، بالدولار الجاري (OEC، استنادًا إلى قاعدة BACI لمركز CEPII التي توحّد البيانات الجمركية لـ UN Comtrade). الميزان التجاري الإجمالي: ${solde}.`,
      'الناتج المحلي المجمَّع تقدير إجمالي (صندوق النقد الدولي، البنك الدولي) يُعطى للدلالة على الحجم؛ وتعرضه الشاشة تحت عنوان «القيمة الإجمالية للتجارة».',
    ],
    topExp: (a) => `أكبر 10 مصدِّرين أفارقة — ${a}`,
    topImp: (a) => `أكبر 10 مستوردين أفارقة — ${a}`,
    cols: { rank: '#', country: 'البلد', exp: 'الصادرات', imp: 'الواردات', share: 'الحصة من أفريقيا' },
    topText: (a) => `قيم ${a} بالدولار الجاري (OEC/BACI). تنسب الحصة تدفق البلد إلى المجموع الأفريقي للسنة نفسها: عدد قليل من البلدان يستأثر بمعظم التجارة الخارجية للقارة.`,
    gdpTop: 'أكبر 10 اقتصادات أفريقية',
    gdpCols: { rank: '#', country: 'البلد', gdp: 'الناتج المحلي', year: 'السنة', growth: 'النمو 2024', proj: 'توقع 2025' },
    gdpText: (src) => `الناتج المحلي بالدولار الجاري؛ النمو الحقيقي السنوي للناتج. ${src ? `المصدر: ${src}.` : ''} السنة المبيَّنة هي سنة قيمة الناتج التي نشرها المصدر.`,
    intra: 'تطور التجارة البينية الأفريقية',
    intraCols: { year: 'السنة', value: 'التجارة البينية الأفريقية', nature: 'الطبيعة' },
    observed: 'مرصود',
    projection: 'توقع',
    intraText: (g, cible) => [
      `التجارة البينية الأفريقية: تجارة السلع بين البلدان الأفريقية، بمليارات الدولارات. النمو 2023-2024: ${g}.`,
      `السنوات 2025 و2027 و2030 توقعات تحسبها الشاشة (+12% و+30% و+52% على التوالي مقارنة بعام 2024)، وليست بيانات مرصودة. هدف زليكاف لعام 2030 المعروض: ${cible}.`,
    ],
    top5: 'أكبر 5 اقتصادات — التجارة العالمية والبينية الأفريقية (2024)',
    top5Cols: { country: 'البلد', gdp: 'الناتج المحلي', expW: 'صادرات عالمية', expI: 'صادرات بينية', pctI: 'الحصة البينية', impW: 'واردات عالمية', impI: 'واردات بينية' },
    top5Text: 'الحصة البينية: نسبة صادرات البلد المتجهة إلى بلدان أفريقية أخرى. الناتج المحلي في هذا الجدول هو ما تنشره هذه السلسلة، وقد يختلف عن جدول أكبر 10 اقتصادات (إصدار أو مصدر مختلف).',
    sectors: 'الصادرات الأفريقية حسب القطاع (2024)',
    sectorCols: { sector: 'القطاع', share: 'الحصة من الصادرات', value: 'القيمة 2024' },
    sectorText: 'توزيع الصادرات الأفريقية من السلع حسب القطاع الاقتصادي الرئيسي، كنسبة من المجموع وبمليارات الدولارات.',
    sources: 'المصادر العامة المذكورة: صندوق النقد الدولي (آفاق الاقتصاد العالمي)، البنك الدولي (WDI)، الأونكتاد، OEC/BACI، أمانة زليكاف، البنك الأفريقي للتنمية. الأرقام كما نُشرت، في التاريخ المبيَّن لكل منها.',
    filename: 'Statistiques_vue_ensemble_ar',
  },
};

/**
 * Vue d'ensemble : réponses de GET /statistics (`statistics`) et de
 * GET /oec/africa/totals?year=2024 (`totaux`, facultatif).
 */
export function specVueEnsemblePdf({ statistics, totaux } = {}, langue = 'fr') {
  const lang = langueValide(langue);
  const t = VUE[lang];
  const f = formats(lang);
  const s = statistics || {};
  const ov = s.overview || {};
  const an = totaux?.year || 2024;

  const kpis = [
    { label: t.gdp, value: estNombre(ov.estimated_combined_gdp) ? f.md(ov.estimated_combined_gdp / 1e9, 0) : f.na, sub: t.gdpSub, accent: 'gold' },
    { label: t.exports, value: f.md(totaux?.exports_billions), sub: t.flowSub(an), accent: 'green' },
    { label: t.imports, value: f.md(totaux?.imports_billions), sub: t.flowSub(an), accent: 'terra' },
    { label: t.members, value: f.entier(ov.african_countries_members), sub: t.membersSub, accent: 'gold' },
  ];

  const solde = estNombre(totaux?.trade_balance) ? f.usd(totaux.trade_balance) : f.na;
  const sections = [{ title: t.totals, paragraphs: t.totalsText(an, solde) }];

  const classement = (liste, cle, libelle) => ({
    columns: [
      { key: 'rank', label: t.cols.rank, width: 0.4 },
      { key: 'country', label: t.cols.country, width: 2.4 },
      { key: 'value', label: libelle, width: 1.4, align: 'right' },
      { key: 'share', label: t.cols.share, width: 1.3, align: 'right' },
    ],
    rows: liste.slice(0, 10).map((x, i) => ({
      rank: String(i + 1),
      country: nomPays(x.name, lang),
      value: estNombre(x[cle]) ? f.md(x[cle] / 1e9) : f.na,
      share: f.pct(x.share_pct),
    })),
  });
  if (s.top_exporters_2024?.length) {
    sections.push({ title: t.topExp(an), table: classement(s.top_exporters_2024, 'exports_2024', t.cols.exp) });
  }
  if (s.top_importers_2024?.length) {
    sections.push({ title: t.topImp(an), table: classement(s.top_importers_2024, 'imports_2024', t.cols.imp) });
  }
  if (s.top_exporters_2024?.length || s.top_importers_2024?.length) sections.push({ paragraphs: [t.topText(an)] });

  if (s.top_10_gdp_2024?.length) {
    sections.push({
      title: t.gdpTop,
      table: {
        columns: [
          { key: 'rank', label: t.gdpCols.rank, width: 0.4 },
          { key: 'country', label: t.gdpCols.country, width: 2.2 },
          { key: 'gdp', label: t.gdpCols.gdp, width: 1.2, align: 'right' },
          { key: 'year', label: t.gdpCols.year, width: 0.7, align: 'right' },
          { key: 'growth', label: t.gdpCols.growth, width: 1.2, align: 'right' },
          { key: 'proj', label: t.gdpCols.proj, width: 1.2, align: 'right' },
        ],
        rows: s.top_10_gdp_2024.map((c, i) => ({
          rank: String(c.rank ?? i + 1),
          country: nomPays(c.iso3 || c.country, lang, c.country),
          gdp: f.md(c.gdp_2024_billion),
          year: c.gdp_2024_year ? String(c.gdp_2024_year) : '—',
          growth: f.pct(nombreDe(c.growth_2024)),
          proj: f.pct(nombreDe(c.growth_projection_2025)),
        })),
      },
    });
    sections.push({ paragraphs: [t.gdpText(s.top_10_gdp_2024_source)] });
  }

  const evo = s.trade_evolution;
  const base = nombreDe(evo?.intra_african_trade_2024);
  if (evo) {
    // Mêmes points et mêmes coefficients que le graphique de l'écran.
    const points = [
      ['2023', nombreDe(evo.intra_african_trade_2023), false],
      ['2024', base, false],
      ['2025', base != null ? base * 1.12 : null, true],
      ['2027', base != null ? base * 1.30 : null, true],
      ['2030', base != null ? base * 1.52 : null, true],
    ];
    sections.push({
      title: t.intra,
      table: {
        columns: [
          { key: 'year', label: t.intraCols.year, width: 1 },
          { key: 'value', label: t.intraCols.value, width: 2, align: 'right' },
          { key: 'nature', label: t.intraCols.nature, width: 1.4 },
        ],
        rows: points.map(([year, v, proj]) => ({ year, value: f.md(v), nature: proj ? t.projection : t.observed })),
      },
    });
    sections.push({ paragraphs: t.intraText(f.pct(nombreDe(evo.growth_rate_2023_2024 ?? evo.growth_rate_2024)), f.md(nombreDe(evo.zlecaf_target_2030), 0)) });
  }

  if (s.top_5_gdp_trade_comparison?.length) {
    const c5 = t.top5Cols;
    sections.push({
      title: t.top5,
      table: {
        columns: [
          { key: 'country', label: c5.country, width: 1.7 },
          { key: 'gdp', label: c5.gdp, width: 1, align: 'right' },
          { key: 'expW', label: c5.expW, width: 1, align: 'right' },
          { key: 'expI', label: c5.expI, width: 1.1, align: 'right' },
          { key: 'pctI', label: c5.pctI, width: 0.9, align: 'right' },
          { key: 'impW', label: c5.impW, width: 1, align: 'right' },
          { key: 'impI', label: c5.impI, width: 1.1, align: 'right' },
        ],
        rows: s.top_5_gdp_trade_comparison.map((c) => ({
          country: nomPays(c.country, lang),
          gdp: f.md(nombreDe(c.gdp_2024), 0),
          expW: f.md(nombreDe(c.exports_world)),
          expI: f.md(nombreDe(c.exports_intra_african)),
          pctI: f.pct(nombreDe(c.intra_african_percentage)),
          impW: f.md(nombreDe(c.imports_world)),
          impI: f.md(nombreDe(c.imports_intra_african)),
        })),
      },
    });
    sections.push({ paragraphs: [t.top5Text] });
  }

  const secteurs = Object.entries(s.sector_performance || {}).slice(0, 8);
  if (secteurs.length) {
    sections.push({
      title: t.sectors,
      table: {
        columns: [
          { key: 'sector', label: t.sectorCols.sector, width: 2.6 },
          { key: 'share', label: t.sectorCols.share, width: 1.4, align: 'right' },
          { key: 'value', label: t.sectorCols.value, width: 1.2, align: 'right' },
        ],
        rows: secteurs.map(([cle, v]) => ({
          sector: SECTEURS[cle]?.[lang] || trDonnee(cle.replace(/_/g, ' '), lang),
          share: f.pct(nombreDe(typeof v === 'object' ? v?.share : v)),
          value: f.md(nombreDe(typeof v === 'object' ? v?.value_2024 : null)),
        })),
      },
    });
    sections.push({ paragraphs: [t.sectorText] });
  }

  sections.push(avertissement(lang, t.sources));

  return {
    moduleLabel: COMMUN[lang].module,
    badge: t.badge,
    title: t.title,
    subtitle: t.subtitle(an),
    kpis,
    sections,
    source: [s.source, s.last_updated && `${s.last_updated}`].filter(Boolean).join(' · ') || 'OEC/BACI',
    filename: [t.filename, an, date()].join('_'),
  };
}

/* ─────────────────── 2a. Avantage comparatif révélé ─────────────────── */

const RCA = {
  fr: {
    badge: 'AVANTAGE COMPARATIF',
    title: (n) => `Avantage comparatif révélé — ${n}`,
    subtitle: (a, niv) => `Indice de Balassa par produit · ${a} · ${niv} · OEC/BACI`,
    kAdv: 'Produits à avantage',
    kAdvSub: (n) => `RCA ≥ 1, sur ${n} produits analysés`,
    kExp: 'Exportations du pays',
    kTop: 'RCA le plus élevé',
    kWorld: 'Exportations mondiales',
    params: 'Paramètres de l’analyse',
    how: 'Comment lire le RCA',
    howText: [
      "RCA (indice de Balassa) = part du produit dans les exportations du pays ÷ part du produit dans les exportations mondiales. Les deux parts sont calculées sur la même année et au même niveau de la nomenclature SH.",
      "RCA > 1 : le produit pèse plus dans les exportations du pays que dans le commerce mondial — le pays y est relativement spécialisé (avantage comparatif révélé). RCA < 1 : pas de spécialisation relative. Un RCA très élevé peut venir d'un petit marché mondial ; il ne dit rien des volumes ni de la rentabilité.",
    ],
    table: (n) => `Les ${n} produits au RCA le plus élevé`,
    cols: { code: 'Code', product: 'Produit', rca: 'RCA', cs: 'Part nationale', ws: 'Part mondiale', adv: 'Avantage' },
    yes: 'Oui', no: 'Non',
    tableText: "Part nationale : poids du produit dans les exportations du pays ; part mondiale : poids du produit dans les exportations mondiales. Désignations des produits telles que publiées par l'OEC (en anglais).",
    sources: "Source publique citée : OEC (Observatoire de la complexité économique), données BACI du CEPII harmonisant les déclarations douanières UN Comtrade, interrogées en direct à la date indiquée.",
    filename: 'RCA',
  },
  en: {
    badge: 'COMPARATIVE ADVANTAGE',
    title: (n) => `Revealed comparative advantage — ${n}`,
    subtitle: (a, niv) => `Balassa index by product · ${a} · ${niv} · OEC/BACI`,
    kAdv: 'Products with advantage',
    kAdvSub: (n) => `RCA ≥ 1, out of ${n} products analysed`,
    kExp: 'Country exports',
    kTop: 'Highest RCA',
    kWorld: 'World exports',
    params: 'Analysis parameters',
    how: 'How to read RCA',
    howText: [
      "RCA (Balassa index) = product share in the country's exports ÷ product share in world exports. Both shares are computed for the same year and at the same level of the HS nomenclature.",
      "RCA > 1: the product weighs more in the country's exports than in world trade — the country is relatively specialised in it (revealed comparative advantage). RCA < 1: no relative specialisation. A very high RCA may stem from a small world market; it says nothing about volumes or profitability.",
    ],
    table: (n) => `The ${n} products with the highest RCA`,
    cols: { code: 'Code', product: 'Product', rca: 'RCA', cs: 'National share', ws: 'World share', adv: 'Advantage' },
    yes: 'Yes', no: 'No',
    tableText: "National share: weight of the product in the country's exports; world share: weight of the product in world exports. Product names as published by OEC.",
    sources: "Public source cited: OEC (Observatory of Economic Complexity), CEPII BACI data harmonising UN Comtrade customs declarations, queried live on the date shown.",
    filename: 'RCA',
  },
  ar: {
    badge: 'الميزة النسبية',
    title: (n) => `الميزة النسبية الظاهرة — ${n}`,
    subtitle: (a, niv) => `مؤشر بالاسا حسب المنتج · ${a} · ${niv} · OEC/BACI`,
    kAdv: 'منتجات ذات ميزة',
    kAdvSub: (n) => `RCA ≥ 1، من أصل ${n} منتجًا`,
    kExp: 'صادرات البلد',
    kTop: 'أعلى RCA',
    kWorld: 'الصادرات العالمية',
    params: 'معايير التحليل',
    how: 'كيف يُقرأ مؤشر RCA',
    howText: [
      'RCA (مؤشر بالاسا) = حصة المنتج في صادرات البلد ÷ حصة المنتج في الصادرات العالمية. تُحسب الحصتان للسنة نفسها وعلى المستوى نفسه من نظام SH.',
      'RCA > 1: وزن المنتج في صادرات البلد أكبر من وزنه في التجارة العالمية — البلد متخصص فيه نسبيًا (ميزة نسبية ظاهرة). RCA < 1: لا تخصص نسبي. قد ينتج RCA مرتفع جدًا عن سوق عالمية صغيرة؛ ولا يدل على الأحجام ولا على الربحية.',
    ],
    table: (n) => `المنتجات الـ${n} ذات أعلى RCA`,
    cols: { code: 'الرمز', product: 'المنتج', rca: 'RCA', cs: 'الحصة الوطنية', ws: 'الحصة العالمية', adv: 'الميزة' },
    yes: 'نعم', no: 'لا',
    tableText: 'الحصة الوطنية: وزن المنتج في صادرات البلد؛ الحصة العالمية: وزن المنتج في الصادرات العالمية. أسماء المنتجات كما ينشرها OEC (بالإنجليزية).',
    sources: 'المصدر العام المذكور: OEC (مرصد التعقيد الاقتصادي)، بيانات BACI لمركز CEPII الموحِّدة للبيانات الجمركية لـ UN Comtrade، مستعلَم عنها مباشرة في التاريخ المبيَّن.',
    filename: 'RCA_ar',
  },
};

/** RCA : réponse de GET /oec/rca/{iso3} ; `pays` = ISO3 choisi à l'écran. */
export function specRcaPdf(reponse, { pays } = {}, langue = 'fr') {
  const lang = langueValide(langue);
  const t = RCA[lang];
  const c = COMMUN[lang];
  const f = formats(lang);
  const r = reponse || {};
  const rows = r.data || [];
  const nom = nomPays(pays, lang, r.country?.[`name_${lang}`] || r.country?.name_fr);
  const niveau = c.levels[r.hs_level] || r.hs_level || '—';
  const annee = r.year ? String(r.year) : f.na;
  const top = rows[0];

  const kpis = [
    { label: t.kAdv, value: f.entier(r.products_with_advantage), sub: t.kAdvSub(f.entier(r.total_products)), accent: 'green' },
    { label: t.kExp, value: f.usd(r.total_exports), sub: annee, accent: 'gold' },
    { label: t.kTop, value: top ? f.num(top.rca, 2) : f.na, sub: top ? `${top.hs_code} · ${trDonnee(top.product, lang)}` : '', accent: 'terra' },
    { label: t.kWorld, value: f.usd(r.world_exports), sub: annee, accent: 'gold' },
  ];

  const sections = [
    {
      title: t.params,
      keyValues: [
        { label: c.country, value: nom },
        { label: c.year, value: annee },
        { label: c.hsLevel, value: niveau },
        { label: c.source, value: r.source || 'OEC/BACI' },
        dateLisible(r.retrieved_at) && { label: c.consulted, value: dateLisible(r.retrieved_at) },
      ].filter(Boolean),
    },
    { title: t.how, paragraphs: t.howText },
  ];
  if (rows.length) {
    sections.push({
      title: t.table(rows.length),
      table: {
        columns: [
          { key: 'hs_code', label: t.cols.code, width: 0.7 },
          { key: 'product', label: t.cols.product, width: 3 },
          { key: 'rca', label: t.cols.rca, width: 0.8, align: 'right', fmt: (v) => f.num(v, 2) },
          { key: 'country_share', label: t.cols.cs, width: 1.1, align: 'right', fmt: f.part },
          { key: 'world_share', label: t.cols.ws, width: 1.1, align: 'right', fmt: f.part },
          { key: 'has_advantage', label: t.cols.adv, width: 0.8, fmt: (v) => (v ? t.yes : t.no) },
        ],
        rows: rows.map((d) => ({ ...d, product: trDonnee(d.product, lang) || '—' })),
      },
    });
    sections.push({ paragraphs: [t.tableText] });
  }
  sections.push(avertissement(lang, t.sources));

  return {
    moduleLabel: c.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(annee, niveau),
    kpis,
    sections,
    source: `${r.source || 'OEC/BACI'} · ${annee}`,
    filename: [t.filename, pays || r.country?.oec_id, r.year, r.hs_level, date()].filter(Boolean).join('_'),
  };
}

/* ───────────────────── 2b. Complémentarité commerciale ───────────────────── */

const TCI = {
  fr: {
    badge: 'COMPLÉMENTARITÉ',
    title: 'Complémentarité commerciale (TCI)',
    subtitle: (e, i, a, niv) => `${e} (exportateur) → ${i} (importateur) · ${a} · ${niv}`,
    kTci: 'Indice TCI (0-100)',
    level: (v) => (v >= 50 ? 'Forte complémentarité' : v >= 30 ? 'Complémentarité modérée' : 'Faible complémentarité'),
    kMatch: 'Produits en recouvrement',
    kMatchSub: 'exportés par l’un et importés par l’autre',
    kYear: 'Année des données',
    exporter: 'Exportateur',
    importer: 'Importateur',
    params: 'Paramètres de l’analyse',
    how: "Comment l'indice est calculé et se lit",
    howText: [
      "TCI = 100 × (1 − S ÷ 2), où S est la somme, sur tous les produits du niveau SH choisi, des écarts en valeur absolue entre la part du produit dans les importations du partenaire et sa part dans les exportations du pays.",
      "0 : ce que l'exportateur vend ne correspond en rien à ce que l'importateur achète ; 100 : les deux profils coïncident exactement. Repères de l'écran : 50 et plus = forte complémentarité, de 30 à 50 = modérée, moins de 30 = faible. L'indice mesure un potentiel d'échange, pas le commerce effectif entre les deux pays.",
    ],
    table: 'Principales opportunités (offre et demande)',
    cols: { code: 'Code', product: 'Produit', exp: 'Part export', imp: 'Part import', match: 'Recouvrement' },
    tableText: "Part export : poids du produit dans les exportations de l'exportateur ; part import : poids du produit dans les importations de l'importateur. Recouvrement : la plus petite des deux parts — la contribution du produit à l'indice. Désignations telles que publiées par l'OEC (en anglais).",
    sources: "Source publique citée : OEC (Observatoire de la complexité économique), données BACI du CEPII harmonisant les déclarations douanières UN Comtrade, interrogées en direct à la date indiquée.",
    filename: 'Complementarite',
  },
  en: {
    badge: 'COMPLEMENTARITY',
    title: 'Trade complementarity (TCI)',
    subtitle: (e, i, a, niv) => `${e} (exporter) → ${i} (importer) · ${a} · ${niv}`,
    kTci: 'TCI index (0-100)',
    level: (v) => (v >= 50 ? 'Strong complementarity' : v >= 30 ? 'Moderate complementarity' : 'Weak complementarity'),
    kMatch: 'Overlapping products',
    kMatchSub: 'exported by one, imported by the other',
    kYear: 'Data year',
    exporter: 'Exporter',
    importer: 'Importer',
    params: 'Analysis parameters',
    how: 'How the index is computed and read',
    howText: [
      "TCI = 100 × (1 − S ÷ 2), where S is the sum, over all products at the chosen HS level, of the absolute gaps between the product's share in the partner's imports and its share in the country's exports.",
      "0: what the exporter sells does not match what the importer buys at all; 100: both profiles coincide exactly. Screen benchmarks: 50 and above = strong complementarity, 30 to 50 = moderate, below 30 = weak. The index measures trade potential, not actual trade between the two countries.",
    ],
    table: 'Top opportunities (supply and demand)',
    cols: { code: 'Code', product: 'Product', exp: 'Export share', imp: 'Import share', match: 'Overlap' },
    tableText: "Export share: weight of the product in the exporter's exports; import share: weight of the product in the importer's imports. Overlap: the smaller of the two shares — the product's contribution to the index. Names as published by OEC.",
    sources: 'Public source cited: OEC (Observatory of Economic Complexity), CEPII BACI data harmonising UN Comtrade customs declarations, queried live on the date shown.',
    filename: 'Complementarity',
  },
  ar: {
    badge: 'التكامل',
    title: 'التكامل التجاري (TCI)',
    subtitle: (e, i, a, niv) => `المصدِّر: ${e} · المستورد: ${i} · ${a} · ${niv}`,
    kTci: 'مؤشر TCI (0-100)',
    level: (v) => (v >= 50 ? 'تكامل قوي' : v >= 30 ? 'تكامل متوسط' : 'تكامل ضعيف'),
    kMatch: 'منتجات متداخلة',
    kMatchSub: 'يصدّرها أحدهما ويستوردها الآخر',
    kYear: 'سنة البيانات',
    exporter: 'المصدِّر',
    importer: 'المستورد',
    params: 'معايير التحليل',
    how: 'كيف يُحسب المؤشر وكيف يُقرأ',
    howText: [
      'TCI = 100 × (1 − S ÷ 2)، حيث S مجموع الفروق المطلقة، على كل منتجات مستوى SH المختار، بين حصة المنتج في واردات الشريك وحصته في صادرات البلد.',
      '0: ما يبيعه المصدِّر لا يتوافق إطلاقًا مع ما يشتريه المستورد؛ 100: يتطابق الملفّان تمامًا. مرجعيات الشاشة: 50 فأكثر = تكامل قوي، من 30 إلى 50 = متوسط، أقل من 30 = ضعيف. يقيس المؤشر إمكانات التبادل، لا التجارة الفعلية بين البلدين.',
    ],
    table: 'أبرز الفرص (العرض والطلب)',
    cols: { code: 'الرمز', product: 'المنتج', exp: 'حصة التصدير', imp: 'حصة الاستيراد', match: 'التداخل' },
    tableText: 'حصة التصدير: وزن المنتج في صادرات المصدِّر؛ حصة الاستيراد: وزن المنتج في واردات المستورد. التداخل: أصغر الحصتين — مساهمة المنتج في المؤشر. الأسماء كما ينشرها OEC (بالإنجليزية).',
    sources: 'المصدر العام المذكور: OEC (مرصد التعقيد الاقتصادي)، بيانات BACI لمركز CEPII الموحِّدة للبيانات الجمركية لـ UN Comtrade، مستعلَم عنها مباشرة في التاريخ المبيَّن.',
    filename: 'Complementarite_ar',
  },
};

/** TCI : réponse de GET /oec/complementarity/{exp}/{imp} ; ISO3 choisis à l'écran. */
export function specComplementaritePdf(reponse, { exportateur, importateur } = {}, langue = 'fr') {
  const lang = langueValide(langue);
  const t = TCI[lang];
  const c = COMMUN[lang];
  const f = formats(lang);
  const r = reponse || {};
  const rows = r.top_opportunities || [];
  const nomE = nomPays(exportateur, lang, r.exporter?.name_fr || r.exporter?.name_en);
  const nomI = nomPays(importateur, lang, r.importer?.name_fr || r.importer?.name_en);
  const niveau = c.levels[r.hs_level] || r.hs_level || '—';
  const annee = r.year ? String(r.year) : f.na;

  const kpis = [
    { label: t.kTci, value: f.num(r.tci, 1), sub: estNombre(r.tci) ? t.level(r.tci) : '', accent: 'gold' },
    { label: t.kMatch, value: f.entier(r.matching_products), sub: t.kMatchSub, accent: 'green' },
    { label: t.kYear, value: annee, sub: niveau, accent: 'terra' },
  ];

  const sections = [
    {
      title: t.params,
      keyValues: [
        { label: t.exporter, value: nomE },
        { label: t.importer, value: nomI },
        { label: c.year, value: annee },
        { label: c.hsLevel, value: niveau },
        { label: c.source, value: r.source || 'OEC/BACI' },
        dateLisible(r.retrieved_at) && { label: c.consulted, value: dateLisible(r.retrieved_at) },
      ].filter(Boolean),
    },
    { title: t.how, paragraphs: t.howText },
  ];
  if (rows.length) {
    sections.push({
      title: t.table,
      table: {
        columns: [
          { key: 'hs_code', label: t.cols.code, width: 0.7 },
          { key: 'product', label: t.cols.product, width: 3 },
          { key: 'exporter_export_share', label: t.cols.exp, width: 1.1, align: 'right', fmt: f.part },
          { key: 'importer_import_share', label: t.cols.imp, width: 1.1, align: 'right', fmt: f.part },
          { key: 'match_score', label: t.cols.match, width: 1.1, align: 'right', fmt: f.part },
        ],
        rows: rows.map((o) => ({ ...o, product: trDonnee(o.product, lang) || '—' })),
      },
    });
    sections.push({ paragraphs: [t.tableText] });
  }
  sections.push(avertissement(lang, t.sources));

  return {
    moduleLabel: c.module,
    badge: t.badge,
    title: t.title,
    subtitle: t.subtitle(nomE, nomI, annee, niveau),
    kpis,
    sections,
    source: `${r.source || 'OEC/BACI'} · ${annee}`,
    filename: [t.filename, exportateur, importateur, r.year, r.hs_level, date()].filter(Boolean).join('_'),
  };
}

/* ───────────────────── 2c. Marge préférentielle ZLECAf ───────────────────── */

const PREF = {
  fr: {
    badge: 'MARGE PRÉFÉRENTIELLE',
    title: (n) => `Marge préférentielle ZLECAf — ${n}`,
    subtitle: 'Potentiel préférentiel (NPF − ZLECAf) · tarifs nationaux',
    kNpf: 'NPF moyen', kZl: 'ZLECAf moyen', kMargin: 'Marge moyenne', kPref: 'Lignes avec préférence',
    kFree: 'Déjà en franchise', kLines: 'Lignes analysées',
    kNpfSub: 'droit de douane normal', kZlSub: 'taux préférentiel', kMarginSub: 'points de pourcentage',
    kPrefSub: 'marge > 0', kFreeSub: 'NPF = 0 %', kLinesSub: 'lignes tarifaires SH6',
    pts: 'pts',
    how: 'Comment lire la marge préférentielle',
    howText: [
      "Marge préférentielle = taux NPF (droit appliqué à tout partenaire de l'OMC, « nation la plus favorisée ») − taux ZLECAf, ligne par ligne au niveau SH6 (jamais négative). C'est l'économie de droits de douane qu'offre l'accord à un produit originaire d'un État partie.",
      "Les moyennes sont des moyennes simples sur les lignes tarifaires, non pondérées par les échanges. Elles mesurent le potentiel préférentiel offert par le tarif, non le taux d'utilisation effectif des préférences, qui exige les données douanières de demandes d'origine.",
    ],
    sens: 'Ventilation par sensibilité',
    sensText: "Normal : ligne libéralisée selon le calendrier général. Sensible : libéralisation plus lente. Exclu : ligne soustraite au démantèlement. Le statut vient du fichier tarifaire national.",
    sensLabels: { normal: 'Normal', sensitive: 'Sensible', excluded: 'Exclu', unknown: 'Inconnu' },
    sensCols: { cat: 'Sensibilité', count: 'Lignes', share: 'Part', npf: 'NPF moyen', margin: 'Marge moy.' },
    sectors: 'Secteurs à plus forte marge préférentielle',
    secCols: { sector: 'Secteur', count: 'Lignes', margin: 'Marge moy. (pts)' },
    sources: "Source citée : fichiers tarifaires nationaux (droits NPF publiés par les administrations douanières) et taux ZLECAf des offres tarifaires, tels qu'agrégés par l'application à la date de consultation.",
    filename: 'Marge_preferentielle',
  },
  en: {
    badge: 'PREFERENCE MARGIN',
    title: (n) => `AfCFTA preference margin — ${n}`,
    subtitle: 'Preference potential (MFN − AfCFTA) · national tariffs',
    kNpf: 'Avg MFN', kZl: 'Avg AfCFTA', kMargin: 'Avg margin', kPref: 'Lines with preference',
    kFree: 'Already duty-free', kLines: 'Lines analysed',
    kNpfSub: 'normal customs duty', kZlSub: 'preferential rate', kMarginSub: 'percentage points',
    kPrefSub: 'margin > 0', kFreeSub: 'MFN = 0%', kLinesSub: 'HS6 tariff lines',
    pts: 'pts',
    how: 'How to read the preference margin',
    howText: [
      'Preference margin = MFN rate (duty applied to any WTO partner, "most favoured nation") − AfCFTA rate, line by line at HS6 level (never negative). It is the customs duty saving the agreement offers a product originating in a State Party.',
      'Averages are simple averages over tariff lines, not trade-weighted. They measure the preference potential offered by the tariff, not the actual preference utilisation rate, which requires customs data on origin claims.',
    ],
    sens: 'Breakdown by sensitivity',
    sensText: 'Normal: line liberalised on the general schedule. Sensitive: slower liberalisation. Excluded: line kept out of tariff dismantling. The status comes from the national tariff file.',
    sensLabels: { normal: 'Normal', sensitive: 'Sensitive', excluded: 'Excluded', unknown: 'Unknown' },
    sensCols: { cat: 'Sensitivity', count: 'Lines', share: 'Share', npf: 'Avg MFN', margin: 'Avg margin' },
    sectors: 'Sectors with the highest preference margin',
    secCols: { sector: 'Sector', count: 'Lines', margin: 'Avg margin (pts)' },
    sources: 'Source cited: national tariff files (MFN duties published by customs administrations) and AfCFTA rates from tariff offers, as aggregated by the application on the retrieval date.',
    filename: 'Preference_margin',
  },
  ar: {
    badge: 'الهامش التفضيلي',
    title: (n) => `الهامش التفضيلي في زليكاف — ${n}`,
    subtitle: 'الإمكانات التفضيلية (NPF − زليكاف) · التعريفات الوطنية',
    kNpf: 'متوسط NPF', kZl: 'متوسط زليكاف', kMargin: 'متوسط الهامش', kPref: 'بنود بتفضيل',
    kFree: 'معفاة أصلًا', kLines: 'البنود المحلَّلة',
    kNpfSub: 'الرسم الجمركي العادي', kZlSub: 'المعدل التفضيلي', kMarginSub: 'نقاط مئوية',
    kPrefSub: 'هامش > 0', kFreeSub: 'NPF = 0%', kLinesSub: 'بنود تعريفية SH6',
    pts: 'نقطة',
    how: 'كيف يُقرأ الهامش التفضيلي',
    howText: [
      'الهامش التفضيلي = معدل NPF (الرسم المطبَّق على أي شريك في منظمة التجارة العالمية، «الدولة الأولى بالرعاية») − معدل زليكاف، بندًا بندًا على مستوى SH6 (لا يكون سالبًا أبدًا). وهو الوفر في الرسوم الجمركية الذي يمنحه الاتفاق لمنتج ناشئ في دولة طرف.',
      'المتوسطات بسيطة على البنود التعريفية وغير مرجَّحة بالتجارة. وهي تقيس الإمكانات التفضيلية التي تتيحها التعريفة، لا معدل الاستخدام الفعلي للتفضيلات الذي يتطلب بيانات جمركية عن طلبات المنشأ.',
    ],
    sens: 'التوزيع حسب الحساسية',
    sensText: 'عادي: بند يُحرَّر وفق الجدول العام. حساس: تحرير أبطأ. مستبعد: بند خارج التفكيك التعريفي. يأتي التصنيف من الملف التعريفي الوطني.',
    sensLabels: { normal: 'عادي', sensitive: 'حساس', excluded: 'مستبعد', unknown: 'غير معروف' },
    sensCols: { cat: 'الحساسية', count: 'البنود', share: 'الحصة', npf: 'متوسط NPF', margin: 'متوسط الهامش' },
    sectors: 'القطاعات ذات أعلى هامش تفضيلي',
    secCols: { sector: 'القطاع', count: 'البنود', margin: 'متوسط الهامش (نقاط)' },
    sources: 'المصدر المذكور: الملفات التعريفية الوطنية (رسوم NPF التي تنشرها الإدارات الجمركية) ومعدلات زليكاف من العروض التعريفية، كما جمعها التطبيق في تاريخ الاطلاع.',
    filename: 'Marge_preferentielle_ar',
  },
};

/** Marge préférentielle : réponse de GET /dismantlement/preference-profile/{iso3}. */
export function specMargePreferencePdf(donnees, { pays } = {}, langue = 'fr') {
  const lang = langueValide(langue);
  const t = PREF[lang];
  const f = formats(lang);
  const d = donnees || {};
  const iso = pays || d.country_iso3;
  const nom = nomPays(iso, lang);
  const pts = (v) => (estNombre(v) ? `${nombre(v, lang, 2)}${NBSP}${t.pts}` : f.na);

  const kpis = [
    { label: t.kNpf, value: f.pct(d.avg_npf_rate, 2), sub: t.kNpfSub, accent: 'red' },
    { label: t.kZl, value: f.pct(d.avg_zlecaf_rate, 2), sub: t.kZlSub, accent: 'green' },
    { label: t.kMargin, value: pts(d.avg_preference_margin), sub: t.kMarginSub, accent: 'terra' },
    { label: t.kPref, value: f.pct(d.lines_with_preference_pct), sub: t.kPrefSub, accent: 'green' },
    { label: t.kFree, value: f.pct(d.lines_already_duty_free_pct), sub: t.kFreeSub, accent: 'gold' },
    { label: t.kLines, value: f.entier(d.total_lines_analyzed), sub: t.kLinesSub, accent: 'gold' },
  ];

  const sections = [{ title: t.how, paragraphs: t.howText }];
  const sens = Object.entries(d.sensitivity_breakdown || {});
  if (sens.length) {
    sections.push({
      title: t.sens,
      table: {
        columns: [
          { key: 'cat', label: t.sensCols.cat, width: 1.8 },
          { key: 'count', label: t.sensCols.count, width: 1, align: 'right' },
          { key: 'share', label: t.sensCols.share, width: 1, align: 'right' },
          { key: 'npf', label: t.sensCols.npf, width: 1.1, align: 'right' },
          { key: 'margin', label: t.sensCols.margin, width: 1.1, align: 'right' },
        ],
        rows: sens.map(([k, v]) => ({
          cat: t.sensLabels[k] || k,
          count: f.entier(v?.count),
          share: f.pct(v?.share_pct),
          npf: f.pct(v?.avg_npf_rate, 2),
          margin: pts(v?.avg_preference_margin),
        })),
      },
    });
    sections.push({ paragraphs: [t.sensText] });
  }
  const secteurs = d.top_sectors_by_margin || [];
  if (secteurs.length) {
    sections.push({
      title: t.sectors,
      table: {
        columns: [
          { key: 'sector', label: t.secCols.sector, width: 3 },
          { key: 'count', label: t.secCols.count, width: 1, align: 'right' },
          { key: 'margin', label: t.secCols.margin, width: 1.3, align: 'right' },
        ],
        rows: secteurs.map((s) => ({ sector: trDonnee(s.sector, lang) || '—', count: f.entier(s.count), margin: pts(s.avg_preference_margin) })),
      },
    });
  }
  sections.push(avertissement(lang, t.sources));

  return {
    moduleLabel: COMMUN[lang].module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle,
    kpis,
    sections,
    source: d.source || '—',
    filename: [t.filename, iso, date()].filter(Boolean).join('_'),
  };
}

/* ───────────────────────── 3. Comparaison multi-pays ───────────────────────── */

const CMP = {
  fr: {
    badge: 'COMPARAISON',
    title: 'Comparaison multi-pays',
    subtitle: (noms) => noms.join(' · '),
    kGdpSub: 'PIB',
    indicator: 'Indicateur',
    eco: 'Indicateurs économiques',
    gdp: 'PIB', gdpPc: 'PIB par habitant', inflation: 'Inflation', unemployment: 'Chômage', population: 'Population',
    ecoText: "PIB en dollars courants ; inflation : hausse annuelle des prix à la consommation ; chômage : part de la population active sans emploi. Dernière année publiée par la Banque mondiale (WDI 2024) et le FMI (WEO 2024).",
    trade: 'Indicateurs commerciaux',
    exports: 'Exportations', imports: 'Importations', balance: 'Balance commerciale', intra: 'Commerce intra-africain',
    tradeText: "Échanges de marchandises avec le monde, en dollars courants (OEC/BACI). Balance = exportations − importations. Commerce intra-africain : part des échanges du pays réalisée avec d'autres pays africains.",
    dev: 'Indices de développement',
    hdi: 'IDH (score)', hdiRank: 'IDH (rang mondial)', gai: 'GAI (score)', gaiRank: 'GAI (rang mondial)',
    devText: "IDH (indice de développement humain, PNUD) : de 0 à 1, combine santé, éducation et revenu. GAI : score de 0 à 100 et rang mondial, selon la source indiquée par l'API.",
    radar: 'Indices du radar (0-100)',
    radarText: "Valeurs que trace le radar de l'écran : PIB, exportations et importations rapportés au plus élevé des pays comparés (= 100) ; IDH × 100 ; GAI tel quel ; part du commerce intra-africain en %. Ces indices servent à comparer, pas à mesurer.",
    sourcesBy: (s) => `Sources par pays (API) : ${s}.`,
    sources: "Sources publiques citées : Banque mondiale (WDI), FMI (Perspectives de l'économie mondiale), PNUD, OEC/BACI, indice GAI. Chiffres repris tels que publiés ; l'année exacte peut varier d'un pays à l'autre selon la dernière publication disponible.",
    filename: 'Comparaison_pays',
  },
  en: {
    badge: 'COMPARISON',
    title: 'Multi-country comparison',
    subtitle: (noms) => noms.join(' · '),
    kGdpSub: 'GDP',
    indicator: 'Indicator',
    eco: 'Economic indicators',
    gdp: 'GDP', gdpPc: 'GDP per capita', inflation: 'Inflation', unemployment: 'Unemployment', population: 'Population',
    ecoText: 'GDP in current dollars; inflation: annual rise in consumer prices; unemployment: share of the labour force without a job. Latest year published by the World Bank (WDI 2024) and the IMF (WEO 2024).',
    trade: 'Trade indicators',
    exports: 'Exports', imports: 'Imports', balance: 'Trade balance', intra: 'Intra-African trade',
    tradeText: "Merchandise trade with the world, in current dollars (OEC/BACI). Balance = exports − imports. Intra-African trade: share of the country's trade conducted with other African countries.",
    dev: 'Development indices',
    hdi: 'HDI (score)', hdiRank: 'HDI (world rank)', gai: 'GAI (score)', gaiRank: 'GAI (world rank)',
    devText: 'HDI (Human Development Index, UNDP): from 0 to 1, combining health, education and income. GAI: score from 0 to 100 and world rank, according to the source given by the API.',
    radar: 'Radar indices (0-100)',
    radarText: "Values plotted by the screen's radar: GDP, exports and imports relative to the highest of the compared countries (= 100); HDI × 100; GAI as is; intra-African trade share in %. These indices are for comparison, not measurement.",
    sourcesBy: (s) => `Sources by country (API): ${s}.`,
    sources: 'Public sources cited: World Bank (WDI), IMF (World Economic Outlook), UNDP, OEC/BACI, GAI index. Figures reproduced as published; the exact year may vary between countries depending on the latest available release.',
    filename: 'Country_comparison',
  },
  ar: {
    badge: 'المقارنة',
    title: 'مقارنة متعددة البلدان',
    subtitle: (noms) => noms.join(' · '),
    kGdpSub: 'الناتج المحلي',
    indicator: 'المؤشر',
    eco: 'المؤشرات الاقتصادية',
    gdp: 'الناتج المحلي الإجمالي', gdpPc: 'نصيب الفرد من الناتج', inflation: 'التضخم', unemployment: 'البطالة', population: 'السكان',
    ecoText: 'الناتج المحلي بالدولار الجاري؛ التضخم: الارتفاع السنوي في أسعار الاستهلاك؛ البطالة: نسبة القوى العاملة بلا عمل. آخر سنة نشرها البنك الدولي (WDI 2024) وصندوق النقد الدولي (WEO 2024).',
    trade: 'المؤشرات التجارية',
    exports: 'الصادرات', imports: 'الواردات', balance: 'الميزان التجاري', intra: 'التجارة البينية الأفريقية',
    tradeText: 'تجارة السلع مع العالم بالدولار الجاري (OEC/BACI). الميزان = الصادرات − الواردات. التجارة البينية الأفريقية: نسبة تجارة البلد مع بلدان أفريقية أخرى.',
    dev: 'مؤشرات التنمية',
    hdi: 'مؤشر التنمية البشرية (الدرجة)', hdiRank: 'مؤشر التنمية البشرية (الترتيب العالمي)', gai: 'GAI (الدرجة)', gaiRank: 'GAI (الترتيب العالمي)',
    devText: 'مؤشر التنمية البشرية (برنامج الأمم المتحدة الإنمائي): من 0 إلى 1، يجمع الصحة والتعليم والدخل. GAI: درجة من 0 إلى 100 وترتيب عالمي، وفق المصدر الذي تذكره الواجهة البرمجية.',
    radar: 'مؤشرات الرادار (0-100)',
    radarText: 'القيم التي يرسمها رادار الشاشة: الناتج والصادرات والواردات منسوبة إلى أعلى البلدان المقارَنة (= 100)؛ مؤشر التنمية البشرية × 100؛ GAI كما هو؛ حصة التجارة البينية الأفريقية بالنسبة المئوية. هذه المؤشرات للمقارنة لا للقياس.',
    sourcesBy: (s) => `المصادر حسب البلد (الواجهة البرمجية): ${s}.`,
    sources: 'المصادر العامة المذكورة: البنك الدولي (WDI)، صندوق النقد الدولي (آفاق الاقتصاد العالمي)، برنامج الأمم المتحدة الإنمائي، OEC/BACI، مؤشر GAI. الأرقام كما نُشرت؛ وقد تختلف السنة الدقيقة من بلد لآخر بحسب آخر إصدار متاح.',
    filename: 'Comparaison_pays_ar',
  },
};

/**
 * Comparaison : `pays` = ISO3 sélectionnés (ordre de l'écran), `donnees` =
 * { ISO3: réponse de GET /statistics/country-comparison/{iso3} }.
 */
export function specComparaisonPdf({ pays = [], donnees = {} } = {}, langue = 'fr') {
  const lang = langueValide(langue);
  const t = CMP[lang];
  const f = formats(lang);
  const liste = pays.filter((iso) => donnees[iso]);
  const fiches = liste.map((iso) => {
    const d = donnees[iso] || {};
    const eco = d.economic_indicators || d.economics || {};
    const tr = d.trade_summary || d.trade || {};
    const dev = d.development_indices || d.development || {};
    return {
      iso,
      nom: nomPays(iso, lang, d.country_name),
      gdp: eco.gdp_billion_usd ?? eco.gdp,
      gdpPc: eco.gdp_per_capita_usd ?? eco.gdp_per_capita,
      inflation: eco.inflation_percent ?? eco.inflation,
      unemployment: eco.unemployment_percent ?? eco.unemployment,
      population: eco.population_millions ?? (estNombre(eco.population) ? eco.population / 1e6 : null),
      exports: tr.total_exports_musd ?? tr.exports,
      imports: tr.total_imports_musd ?? tr.imports,
      balance: tr.trade_balance_musd ?? tr.balance,
      intra: tr.intra_african_trade_percent ?? tr.intra_african,
      hdi: dev.hdi_score ?? dev.hdi,
      hdiRank: dev.hdi_world_rank ?? dev.hdi_rank,
      gai: dev.gai_score ?? dev.gai,
      gaiRank: dev.gai_world_rank ?? dev.gai_rank,
      source: d.data_source,
    };
  });

  const musd = (v) => (estNombre(v) ? f.usd(v * 1e6) : f.na);
  const signe = (v) => (estNombre(v) ? `${v > 0 ? '+' : ''}${musd(v)}` : f.na);
  const rang = (v) => (estNombre(v) ? `#${v}` : f.na);

  // Une ligne par indicateur, une colonne par pays — comme les tableaux de l'écran.
  const tableau = (lignes) => ({
    columns: [
      { key: 'indicator', label: t.indicator, width: 2.2 },
      ...fiches.map((p) => ({ key: p.iso, label: p.nom, width: 1.3, align: 'right' })),
    ],
    rows: lignes.map(([indicator, rendu]) => ({
      indicator,
      ...Object.fromEntries(fiches.map((p) => [p.iso, rendu(p)])),
    })),
  });

  const max = (cle) => Math.max(0, ...fiches.map((p) => (estNombre(p[cle]) ? p[cle] : 0)));
  const relatif = (cle) => {
    const m = max(cle);
    return (p) => (estNombre(p[cle]) && m > 0 ? f.entier(Math.round(Math.min(100, (p[cle] / m) * 100))) : f.na);
  };
  const brut = (cle, k = 1) => (p) => (estNombre(p[cle]) ? f.entier(Math.round(p[cle] * k)) : f.na);

  const accents = ['gold', 'green', 'terra', 'red'];
  const kpis = fiches.map((p, i) => ({ label: p.nom, value: f.md(p.gdp), sub: t.kGdpSub, accent: accents[i % 4] }));

  const sourcesPays = [...new Set(fiches.map((p) => p.source).filter(Boolean))];
  const sections = [
    {
      title: t.eco,
      table: tableau([
        [t.gdp, (p) => f.md(p.gdp)],
        [t.gdpPc, (p) => f.usd(p.gdpPc)],
        [t.inflation, (p) => f.pct(p.inflation)],
        [t.unemployment, (p) => f.pct(p.unemployment)],
        [t.population, (p) => (estNombre(p.population) ? `${nombre(p.population, lang, 1)}${NBSP}${lang === 'ar' ? 'مليون' : 'M'}` : f.na)],
      ]),
    },
    { paragraphs: [t.ecoText] },
    {
      title: t.trade,
      table: tableau([
        [t.exports, (p) => musd(p.exports)],
        [t.imports, (p) => musd(p.imports)],
        [t.balance, (p) => signe(p.balance)],
        [t.intra, (p) => f.pct(p.intra)],
      ]),
    },
    { paragraphs: [t.tradeText] },
    {
      title: t.dev,
      table: tableau([
        [t.hdi, (p) => f.num(p.hdi, 3)],
        [t.hdiRank, (p) => rang(p.hdiRank)],
        [t.gai, (p) => f.num(p.gai, 1)],
        [t.gaiRank, (p) => rang(p.gaiRank)],
      ]),
    },
    { paragraphs: [t.devText] },
    {
      title: t.radar,
      table: tableau([
        [t.gdp, relatif('gdp')],
        [t.exports, relatif('exports')],
        [t.imports, relatif('imports')],
        [t.hdi, brut('hdi', 100)],
        [t.gai, brut('gai')],
        [t.intra, brut('intra')],
      ]),
    },
    { paragraphs: [t.radarText] },
  ];
  sections.push(avertissement(lang, `${t.sources}${sourcesPays.length ? ` ${t.sourcesBy(sourcesPays.join(' ; '))}` : ''}`));

  return {
    moduleLabel: COMMUN[lang].module,
    badge: t.badge,
    title: t.title,
    subtitle: t.subtitle(fiches.map((p) => p.nom)),
    kpis,
    sections,
    source: sourcesPays.join(' ; ') || 'IMF WEO, World Bank, UNDP, OEC',
    filename: [t.filename, ...liste, date()].join('_'),
  };
}
