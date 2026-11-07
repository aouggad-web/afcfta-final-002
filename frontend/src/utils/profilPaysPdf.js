/**
 * Rapport PDF du module Profils pays : l'économie d'un pays, chaque chiffre
 * avec son année, son rang en Afrique et sa source.
 *
 * Même bâtisseur que les autres modules (utils/opportunityPdf.js) : bandeau
 * avec le logo du site, cartes, tableaux, pied paginé. Source : la réponse de
 * `GET /country-profile/{code}`, telle que l'écran l'affiche. Une valeur que
 * la source ne publie pas s'écrit « non publié », jamais 0.
 */
import { montant, montantCompact, nombre, nombreCompact, estAnglais } from './nombres';
import { AFRICAN_COUNTRIES } from './countryCodes';
import { getRegionName } from './translations';

const T = {
  fr: {
    module: 'MODULE PROFILS PAYS',
    badge: 'PROFIL ÉCONOMIQUE',
    title: (n) => `Profil économique — ${n}`,
    subtitle: (r, c) => `${r} · code ISO ${c}`,
    na: 'non publié',
    gdp: 'PIB',
    gdpPc: 'PIB par habitant',
    population: 'Population',
    growth: 'Croissance du PIB',
    inflation: 'Inflation',
    unemployment: 'Chômage',
    hdi: 'Indice de développement humain',
    govDebt: 'Dette publique (% du PIB)',
    rankSub: (r, n) => `rang ${r}/${n} en Afrique`,
    macro: 'Indicateurs macroéconomiques',
    cols: { indicator: 'Indicateur', value: 'Valeur', year: 'Année', rank: 'Rang en Afrique', source: 'Source' },
    macroText: [
      "PIB (produit intérieur brut) : valeur de tout ce que le pays produit en un an, en dollars courants. PIB par habitant : ce PIB divisé par la population, mesure courante du niveau de vie.",
      "Inflation : hausse annuelle des prix à la consommation. Chômage : part de la population active sans emploi qui en cherche un.",
      "Le rang en Afrique classe le pays parmi ceux qui publient l'indicateur la même année (1 = valeur la plus élevée, sauf pour l'inflation, le chômage et la dette, où 1 = la plus basse).",
    ],
    imf: 'Projections du FMI',
    imfText: (src) => `Prévisions des Perspectives de l'économie mondiale du FMI${src ? ` (${src})` : ''}. Les années à venir sont des projections, révisées deux fois par an.`,
    imfCols: { year: 'Année', growth: 'Croissance (%)', inflation: 'Inflation (%)', debt: 'Dette publique (% PIB)' },
    society: 'Développement humain et société',
    lifeExp: 'Espérance de vie (ans)',
    gini: 'Indice de Gini (inégalités, 0-100)',
    poverty: 'Pauvreté (< 3 $ par jour, %)',
    urban: 'Population urbaine (%)',
    internet: 'Utilisateurs d’Internet (%)',
    electricity: "Accès à l'électricité (%)",
    femaleLabor: 'Femmes dans la population active (%)',
    mobile: 'Couverture mobile 3G (%)',
    water: 'Stress hydrique (%)',
    ghg: 'Émissions de gaz à effet de serre (Mt)',
    learning: "Pauvreté des apprentissages (%)",
    societyText: "Indice de Gini : 0 = égalité parfaite, 100 = inégalité maximale. Pauvreté des apprentissages : part des enfants de 10 ans incapables de lire et comprendre un texte simple (Banque mondiale).",
    external: 'Finances extérieures',
    extDebt: 'Dette extérieure',
    extDebtGni: 'Dette extérieure (% du RNB)',
    reserves: 'Réserves de change',
    reservesMonths: "Réserves en mois d'importations",
    gold: "Réserves d'or",
    goldRank: (a, g) => `${a ? `rang ${a} en Afrique` : ''}${a && g ? ', ' : ''}${g ? `${g}e mondial` : ''}`,
    externalText: "Les réserves en mois d'importations disent combien de temps le pays peut payer ses importations sur ses seules réserves : 3 mois est le seuil prudentiel usuel.",
    ratings: 'Notations souveraines et risque',
    globalRisk: 'Risque global',
    ratingsText: "Notes des agences sur la capacité de l'État à rembourser sa dette : de AAA (la plus sûre) à D (défaut). En dessous de BBB- (S&P, Fitch) ou Baa3 (Moody's), la dette est dite spéculative.",
    gai: "Attractivité pour l'investissement",
    gaiScore: 'Score GAI 2025',
    gaiRating: 'Note',
    gaiCategory: 'Catégorie',
    gaiRank: 'Rang',
    gaiRankValue: (a, g) => `${a ? `${a}e en Afrique` : ''}${a && g ? ', ' : ''}${g ? `${g}e mondial` : ''}`,
    gaiTrend: 'Tendance',
    trends: { improving: 'en amélioration', declining: 'en recul', stable: 'stable' },
    infra: 'Infrastructures et logistique',
    lpi: 'Indice de performance logistique (infrastructures, 1-5)',
    aidi: 'Indice de transport AIDI (BAD, 0-100)',
    infraRank: 'Rang infrastructures en Afrique',
    infraText: "Indice de performance logistique (LPI, Banque mondiale) : qualité des infrastructures commerciales et de transport, de 1 à 5. Indice AIDI (Banque africaine de développement) : développement des infrastructures de transport, de 0 à 100.",
    customs: 'Administration des douanes',
    customsFields: {
      administration: 'Administration', adresse: 'Adresse', website: 'Site web',
      bureaux_portuaires: 'Bureaux portuaires', bureaux_aeriens: 'Bureaux aériens', bureaux_terrestres: 'Bureaux terrestres',
    },
    projects: 'Projets structurants',
    projectFields: {
      secteur: 'Secteur', statut: 'Statut', budget: 'Budget', echeance: 'Échéance',
      description: 'Description', impact: 'Impact', partenaires: 'Partenaires', source: 'Source',
    },
    warning: 'Avertissement',
    warningText: [
      "Chiffres repris des sources publiques citées (Banque mondiale, FMI, PNUD, BAD, agences de notation), à la date indiquée pour chacun. Les sources révisent leurs séries : vérifier la dernière publication avant une décision.",
      "Ce profil est une synthèse d'information économique : il ne constitue ni un conseil en investissement ni une évaluation de crédit.",
    ],
    filename: 'Profil_pays',
  },
  en: {
    module: 'COUNTRY PROFILES MODULE',
    badge: 'ECONOMIC PROFILE',
    title: (n) => `Economic profile — ${n}`,
    subtitle: (r, c) => `${r} · ISO code ${c}`,
    na: 'not published',
    gdp: 'GDP',
    gdpPc: 'GDP per capita',
    population: 'Population',
    growth: 'GDP growth',
    inflation: 'Inflation',
    unemployment: 'Unemployment',
    hdi: 'Human Development Index',
    govDebt: 'Government debt (% of GDP)',
    rankSub: (r, n) => `rank ${r}/${n} in Africa`,
    macro: 'Macroeconomic indicators',
    cols: { indicator: 'Indicator', value: 'Value', year: 'Year', rank: 'Rank in Africa', source: 'Source' },
    macroText: [
      'GDP (gross domestic product): value of everything the country produces in a year, in current dollars. GDP per capita: that GDP divided by the population, a common measure of living standards.',
      'Inflation: annual rise in consumer prices. Unemployment: share of the labour force without a job and looking for one.',
      'The rank in Africa places the country among those publishing the indicator for the same year (1 = highest value, except for inflation, unemployment and debt, where 1 = lowest).',
    ],
    imf: 'IMF projections',
    imfText: (src) => `IMF World Economic Outlook forecasts${src ? ` (${src})` : ''}. Coming years are projections, revised twice a year.`,
    imfCols: { year: 'Year', growth: 'Growth (%)', inflation: 'Inflation (%)', debt: 'Government debt (% GDP)' },
    society: 'Human development and society',
    lifeExp: 'Life expectancy (years)',
    gini: 'Gini index (inequality, 0-100)',
    poverty: 'Poverty (< $3 a day, %)',
    urban: 'Urban population (%)',
    internet: 'Internet users (%)',
    electricity: 'Access to electricity (%)',
    femaleLabor: 'Women in the labour force (%)',
    mobile: '3G mobile coverage (%)',
    water: 'Water stress (%)',
    ghg: 'Greenhouse gas emissions (Mt)',
    learning: 'Learning poverty (%)',
    societyText: 'Gini index: 0 = perfect equality, 100 = maximum inequality. Learning poverty: share of 10-year-olds unable to read and understand a simple text (World Bank).',
    external: 'External finances',
    extDebt: 'External debt',
    extDebtGni: 'External debt (% of GNI)',
    reserves: 'Foreign exchange reserves',
    reservesMonths: 'Reserves in months of imports',
    gold: 'Gold reserves',
    goldRank: (a, g) => `${a ? `rank ${a} in Africa` : ''}${a && g ? ', ' : ''}${g ? `#${g} worldwide` : ''}`,
    externalText: 'Reserves in months of imports tell how long the country could pay for its imports from reserves alone: 3 months is the usual prudential threshold.',
    ratings: 'Sovereign ratings and risk',
    globalRisk: 'Overall risk',
    ratingsText: "Agency ratings of the government's ability to repay its debt: from AAA (safest) to D (default). Below BBB- (S&P, Fitch) or Baa3 (Moody's), debt is called speculative.",
    gai: 'Investment attractiveness',
    gaiScore: 'GAI 2025 score',
    gaiRating: 'Rating',
    gaiCategory: 'Category',
    gaiRank: 'Rank',
    gaiRankValue: (a, g) => `${a ? `#${a} in Africa` : ''}${a && g ? ', ' : ''}${g ? `#${g} worldwide` : ''}`,
    gaiTrend: 'Trend',
    trends: { improving: 'improving', declining: 'declining', stable: 'stable' },
    infra: 'Infrastructure and logistics',
    lpi: 'Logistics Performance Index (infrastructure, 1-5)',
    aidi: 'AIDI transport index (AfDB, 0-100)',
    infraRank: 'Infrastructure rank in Africa',
    infraText: 'Logistics Performance Index (LPI, World Bank): quality of trade and transport infrastructure, from 1 to 5. AIDI index (African Development Bank): development of transport infrastructure, from 0 to 100.',
    customs: 'Customs administration',
    customsFields: {
      administration: 'Administration', adresse: 'Address', website: 'Website',
      bureaux_portuaires: 'Port offices', bureaux_aeriens: 'Airport offices', bureaux_terrestres: 'Land border offices',
    },
    projects: 'Major projects',
    projectFields: {
      secteur: 'Sector', statut: 'Status', budget: 'Budget', echeance: 'Timeline',
      description: 'Description', impact: 'Impact', partenaires: 'Partners', source: 'Source',
    },
    warning: 'Disclaimer',
    warningText: [
      'Figures taken from the public sources cited (World Bank, IMF, UNDP, AfDB, rating agencies), as of the date shown for each. Sources revise their series: check the latest release before making a decision.',
      'This profile summarises economic information: it is neither investment advice nor a credit assessment.',
    ],
    filename: 'Country_profile',
  },
};

const estNombre = (v) => typeof v === 'number' && Number.isFinite(v);

/** Valeur absente, vide ou « N/A… » : la source ne la publie pas. */
const publiee = (v) => v != null && v !== '' && !(typeof v === 'string' && /^N\/A/.test(v));

export function specProfilPaysPdf(profil, langue = 'fr') {
  const t = T[langue] || T.fr;
  const p = profil.projections || {};
  const rangs = profil.african_rankings || {};
  const ans = p.indicator_years || {};
  const code = profil.country_code || '';
  const nom = AFRICAN_COUNTRIES[code]?.[`name_${langue}`] || profil.country_name || code;
  const region = getRegionName(profil.region, langue) || profil.region || '—';

  const num = (v, d = 1) => (estNombre(v) ? nombre(v, langue, d) : t.na);
  const pct = (v, d = 1) => (estNombre(v) ? `${nombre(v, langue, d)}${estAnglais(langue) ? '' : ' '}%` : t.na);
  // En entier sous le million (PIB par habitant : « 6 051 $ ») ; au-delà, en Md ou M.
  const usd = (v) => (!estNombre(v) ? t.na
    : Math.abs(v) < 1e6 ? montant(v, langue) : montantCompact(v, langue, { B: 1, M: 1 }, { max: true }));
  const rang = (cle) => (rangs[cle]?.rank ? `${rangs[cle].rank}/${rangs[cle].total}` : '—');
  const sousRang = (cle) => (rangs[cle]?.rank ? t.rankSub(rangs[cle].rank, rangs[cle].total) : '');

  const kpis = [
    { label: t.gdp, value: usd(profil.gdp_usd), sub: sousRang('gdp'), accent: 'gold' },
    { label: t.gdpPc, value: usd(profil.gdp_per_capita), sub: sousRang('gdp_per_capita'), accent: 'gold' },
    { label: t.population, value: estNombre(profil.population) ? nombreCompact(profil.population, langue, { M: 1, K: 0 }) : t.na, sub: sousRang('population'), accent: 'terra' },
    { label: t.growth, value: pct(p.gdp_growth_latest), sub: p.gdp_growth_latest_year ? String(p.gdp_growth_latest_year) : '', accent: 'green' },
    { label: t.inflation, value: pct(profil.inflation_rate), sub: ans.inflation ? String(ans.inflation) : '', accent: 'red' },
    { label: t.unemployment, value: pct(profil.unemployment_rate), sub: ans.unemployment ? String(ans.unemployment) : '', accent: 'red' },
    { label: t.hdi, value: num(profil.hdi, 3), sub: profil.hdi_rank ? `${langue === 'en' ? 'world rank' : 'rang mondial'} ${profil.hdi_rank}` : '', accent: 'green' },
    { label: t.govDebt, value: pct(profil.total_debt_pct_gdp), sub: p.debt_year ? String(p.debt_year) : '', accent: 'terra' },
  ];

  const macroRows = [
    { indicator: t.gdp, value: usd(profil.gdp_usd), year: ans.gdp, rank: rang('gdp') },
    { indicator: t.gdpPc, value: usd(profil.gdp_per_capita), year: ans.gdp_per_capita, rank: rang('gdp_per_capita') },
    { indicator: t.population, value: estNombre(profil.population) ? nombre(profil.population, langue) : t.na, year: ans.population, rank: rang('population') },
    { indicator: t.growth, value: pct(p.gdp_growth_latest), year: p.gdp_growth_latest_year, rank: rang('gdp_growth') },
    { indicator: `${t.growth} (projection)`, value: pct(p.gdp_growth_projection_current), year: p.gdp_growth_projection_current_year, rank: rang('gdp_growth_projection') },
    { indicator: t.inflation, value: pct(profil.inflation_rate), year: ans.inflation, rank: rang('inflation') },
    { indicator: t.unemployment, value: pct(profil.unemployment_rate), year: ans.unemployment, rank: rang('unemployment') },
    { indicator: t.govDebt, value: pct(profil.total_debt_pct_gdp), year: p.debt_year, rank: rang('gov_debt') },
    { indicator: t.hdi, value: num(profil.hdi, 3), year: p.hdi_year, rank: rang('hdi') },
  ];

  const sections = [
    {
      title: t.macro,
      table: {
        columns: [
          { key: 'indicator', label: t.cols.indicator, width: 3 },
          { key: 'value', label: t.cols.value, width: 1.6, align: 'right' },
          { key: 'year', label: t.cols.year, width: 0.8, align: 'right', fmt: (v) => (v ? String(v) : '—') },
          { key: 'rank', label: t.cols.rank, width: 1.2, align: 'right' },
        ],
        rows: macroRows,
      },
    },
    { paragraphs: t.macroText },
  ];

  // Projections du FMI : l'année en cours et les cinq suivantes.
  const croissance = p.imf_gdp_growth || {};
  const inflation = p.imf_inflation || {};
  const dette = p.imf_gov_debt || {};
  const debut = Number(p.gdp_growth_projection_current_year) || new Date().getFullYear();
  const annees = Object.keys({ ...croissance, ...inflation, ...dette })
    .map(Number)
    .filter((a) => a >= debut - 1 && a <= debut + 5)
    .sort((a, b) => a - b);
  if (annees.length) {
    sections.push({ title: t.imf, paragraphs: [t.imfText(p.imf_source)] });
    sections.push({
      table: {
        columns: [
          { key: 'year', label: t.imfCols.year, width: 1 },
          { key: 'growth', label: t.imfCols.growth, width: 1.4, align: 'right' },
          { key: 'inflation', label: t.imfCols.inflation, width: 1.4, align: 'right' },
          { key: 'debt', label: t.imfCols.debt, width: 1.6, align: 'right' },
        ],
        rows: annees.map((a) => ({
          year: String(a),
          growth: num(croissance[a]),
          inflation: num(inflation[a]),
          debt: num(dette[a]),
        })),
      },
    });
  }

  const social = [
    [t.lifeExp, p.life_expectancy_2023, p.life_expectancy_2023_year, 'life_expectancy'],
    [t.gini, p.gini_index_2024, p.gini_index_2024_year],
    [t.poverty, p.poverty_rate_3usd_2024, p.poverty_rate_3usd_2024_year],
    [t.urban, p.urban_population_pct_2024, p.urban_population_pct_2024_year],
    [t.internet, p.internet_users_pct_2024, p.internet_users_pct_2024_year, 'internet_users'],
    [t.electricity, p.electricity_access_2022, p.electricity_access_2022_year, 'electricity_access'],
    [t.femaleLabor, p.female_labor_force_pct_2024, p.female_labor_force_pct_2024_year],
    [t.mobile, p.mobile_3g_coverage_2024, p.mobile_3g_coverage_2024_year],
    [t.water, p.water_stress_2022, p.water_stress_2022_year],
    [t.ghg, p.ghg_emissions_mt_2022, p.ghg_emissions_mt_2022_year],
    [t.learning, p.learning_poverty_2023, p.learning_poverty_2023_year],
  ].filter(([, v]) => estNombre(v));
  if (social.length) {
    sections.push({
      title: t.society,
      table: {
        columns: [
          { key: 'indicator', label: t.cols.indicator, width: 3 },
          { key: 'value', label: t.cols.value, width: 1.2, align: 'right' },
          { key: 'year', label: t.cols.year, width: 0.8, align: 'right' },
          { key: 'rank', label: t.cols.rank, width: 1.2, align: 'right' },
        ],
        rows: social.map(([indicator, v, an, cle]) => ({
          indicator, value: num(v), year: an ? String(an) : '—', rank: cle ? rang(cle) : '—',
        })),
      },
    });
    sections.push({ paragraphs: [t.societyText] });
  }

  const ext = [];
  if (estNombre(p.external_debt?.usd)) ext.push({ label: `${t.extDebt} (${p.external_debt.year || '—'})`, value: usd(p.external_debt.usd) });
  if (estNombre(p.external_debt?.pct_gni)) ext.push({ label: t.extDebtGni, value: pct(p.external_debt.pct_gni) });
  if (estNombre(p.reserves?.usd)) ext.push({ label: `${t.reserves} (${p.reserves.year || '—'})`, value: `${usd(p.reserves.usd)}${rangs.reserves?.rank ? ` · ${sousRang('reserves')}` : ''}` });
  if (estNombre(p.reserves?.import_months)) ext.push({ label: t.reservesMonths, value: num(p.reserves.import_months) });
  if (estNombre(p.gold_reserves_tonnes)) ext.push({ label: t.gold, value: `${num(p.gold_reserves_tonnes)} t${p.gold_reserves_rank_africa || p.gold_reserves_rank_global ? ` · ${t.goldRank(p.gold_reserves_rank_africa, p.gold_reserves_rank_global)}` : ''}` });
  if (ext.length) {
    sections.push({ title: t.external, keyValues: ext });
    sections.push({ paragraphs: [t.externalText] });
  }

  const notes = profil.risk_ratings || {};
  const agences = [['S&P', notes.sp], ["Moody's", notes.moodys], ['Fitch', notes.fitch], ['Scope', notes.scope]]
    .filter(([, v]) => publiee(v))
    .map(([label, value]) => ({ label, value }));
  if (publiee(notes.global_risk)) agences.push({ label: t.globalRisk, value: notes.global_risk });
  if (agences.length) {
    sections.push({ title: t.ratings, keyValues: agences });
    sections.push({ paragraphs: [t.ratingsText] });
  }

  if (estNombre(p.gai_2025_score)) {
    const gai = [
      { label: t.gaiScore, value: num(p.gai_2025_score) },
      publiee(p.gai_2025_rating) && { label: t.gaiRating, value: p.gai_2025_rating },
      publiee(p[`gai_2025_category_${langue}`] || p.gai_2025_category_fr) && { label: t.gaiCategory, value: p[`gai_2025_category_${langue}`] || p.gai_2025_category_fr },
      (p.gai_2025_rank_africa || p.gai_2025_rank_global) && { label: t.gaiRank, value: t.gaiRankValue(p.gai_2025_rank_africa, p.gai_2025_rank_global) },
      p.gai_2025_trend && { label: t.gaiTrend, value: t.trends[p.gai_2025_trend] || p.gai_2025_trend },
    ].filter(Boolean);
    sections.push({ title: t.gai, keyValues: gai });
  }

  const infra = profil.infrastructure_ranking || {};
  const infraKv = [
    estNombre(infra.lpi_infrastructure_score) && { label: `${t.lpi}${infra.lpi_edition ? ` (${infra.lpi_edition})` : ''}`, value: num(infra.lpi_infrastructure_score) },
    estNombre(infra.aidi_transport_score) && { label: t.aidi, value: num(infra.aidi_transport_score) },
    infra.africa_rank && { label: t.infraRank, value: String(infra.africa_rank) },
  ].filter(Boolean);
  if (infraKv.length) {
    sections.push({ title: t.infra, keyValues: infraKv });
    sections.push({ paragraphs: [t.infraText] });
  }

  const douane = profil.customs || {};
  const douaneKv = Object.entries(t.customsFields)
    .filter(([cle]) => publiee(douane[cle]))
    .map(([cle, label]) => ({ label, value: douane[cle] }));
  if (douaneKv.length) sections.push({ title: t.customs, keyValues: douaneKv });

  const projets = profil.ongoing_projects || [];
  // Une fiche par projet : son titre, puis ses rubriques publiées.
  projets.forEach((pr, i) => {
    sections.push({
      title: `${i === 0 ? `${t.projects} — ` : ''}${pr.titre || '—'}`,
      keyValues: Object.entries(t.projectFields)
        .filter(([cle]) => publiee(pr[cle]))
        .map(([cle, label]) => ({ label, value: pr[cle] })),
    });
  });

  sections.push({ title: t.warning, notice: t.warningText });

  const sources = [p.gdp_growth_latest_source, p.imf_source, p.hdi_source].filter(Boolean);
  return {
    moduleLabel: t.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(region, code),
    kpis,
    sections,
    source: [...new Set(sources)].join(' ; ') || '—',
    filename: [t.filename, code, new Date().toISOString().slice(0, 10)].filter(Boolean).join('_'),
  };
}
