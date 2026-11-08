/**
 * Rapport PDF du sous-module Production > Industrie manufacturière, au même
 * format que les rapports Agriculture, Mines et Macro (bâtisseur commun,
 * logo, fr/en/ar, boutons clair et sombre).
 *
 * Il reprend tout ce que l'écran affiche : chiffres clés avec leur nature
 * (officiel, calculé sur l'officiel, UNIDO, estimation), profil industriel,
 * principaux secteurs, produits phares, estimation 2025, comptes de l'office
 * national quand il y en a (Algérie), et la structure par division CITI. Le
 * détail classe par classe (ISIC 4, une quarantaine de pages) garde son
 * propre export. Une valeur absente s'écrit « non publié », jamais 0.
 */
import { montantCompact, nombre, nombreCompact, estAnglais } from './nombres';
import { AFRICAN_COUNTRIES } from './countryCodes';
import { trDonnee } from '../i18n/donnees';

const T = {
  fr: {
    module: 'MODULE PRODUCTION',
    badge: 'INDUSTRIE MANUFACTURIÈRE',
    title: (n) => `Industrie manufacturière — ${n}`,
    subtitle: (r, y) => `${r} · données ${y} · UNIDO et sources nationales`,
    na: 'non publié',
    natures: { officiel: 'officiel', calcul_officiel: "calculé sur l'officiel", unido: 'UNIDO', estimation: 'estimation' },
    mva: 'Valeur ajoutée manufacturière',
    mvaGdp: 'VA manufacturière (% du PIB)',
    mvaCap: 'VA manufacturière par habitant',
    growth: 'Croissance de la VA manufacturière',
    jobs: 'Emplois industriels',
    exports: 'Exportations manufacturières',
    rank: 'Rang en Afrique (VA manufacturière)',
    rankValue: (r, n) => `${r} sur ${n}`,
    profile: 'Profil industriel',
    region: 'Région',
    dataYear: 'Année des données',
    mva2024: 'VA manufacturière 2024',
    growth2024: 'Croissance 2024',
    zones: 'Zones industrielles',
    cip: 'Rang mondial CIP (UNIDO)',
    mht: 'Part moyenne et haute technologie dans la VA',
    industryGdp: "VA de l'industrie (% du PIB)",
    manufExports: 'Part des produits manufacturés dans les exportations',
    mvaCap2015: 'VA manufacturière par habitant (dollars 2015)',
    source: 'Source',
    profileText: [
      "Valeur ajoutée manufacturière (VAM) : ce que produit l'industrie manufacturière (CITI section C, divisions 10 à 33), moins ce qu'elle consomme pour produire. Rapportée au PIB, elle mesure le poids de l'industrie dans l'économie ; par habitant, le niveau d'industrialisation.",
      "CIP (Competitive Industrial Performance) : indice de l'UNIDO qui classe les pays selon leur capacité à produire et exporter des biens manufacturés. Part moyenne et haute technologie : poids des industries comme la chimie, les machines ou l'automobile dans la VAM.",
      'La nature de chaque chiffre est indiquée entre parenthèses : officiel (publié par la statistique nationale), calculé sur l’officiel, UNIDO (base internationale) ou estimation.',
    ],
    sectors: 'Principaux secteurs manufacturiers',
    cols: { code: 'CITI', sector: 'Secteur', share: 'Part de la VAM', value: 'Valeur ajoutée', classes: 'Classes ISIC 4', branch: 'Branche', growthVol: 'Croissance en volume 2024', privateShare: 'Part du privé 2024' },
    sectorsText: 'Part de chaque division CITI (2 chiffres) dans la valeur ajoutée manufacturière, et son montant en dollars courants.',
    products: 'Produits phares',
    estimate: 'Estimation 2025',
    estCentral: 'Valeur ajoutée 2025 (estimation centrale)',
    estRange: 'Fourchette',
    estGrowth: 'Croissance en volume 2025',
    estConfidence: 'Confiance (part de la VA)',
    estBase: 'Base de prix',
    estMethod: 'Méthode',
    estNote: 'Note',
    estText: "Estimation de l'année en cours, présentée avec sa fourchette basse et haute : ce n'est pas un chiffre publié. La confiance indique quelle part de la valeur ajoutée repose sur des indicateurs solides (A, B) ou plus fragiles (C).",
    ons: 'Comptes de l’office national par branche',
    onsText: (u, s) => `Valeur ajoutée par branche, en ${u}. Statut des années : ${s}. Les branches de l'office ne correspondent pas toujours une à une aux divisions CITI.`,
    structure: 'Structure par division CITI',
    structureMeasured: 'Données UNIDO mesurées au niveau de la classe ISIC 4 (INDSTAT, IDSB).',
    structureEstimated: "UNIDO ne publie pas ce pays au niveau de la classe ISIC 4 : la part de chaque division est répartie à parts égales entre ses classes. Ces chiffres situent un secteur ; ils ne comparent pas deux classes entre elles.",
    structureDetail: 'Le détail classe par classe, année par année, est disponible avec le bouton « Exporter en PDF » du tableau ISIC 4 de l’écran.',
    warning: 'Avertissement',
    warningText: [
      'Chiffres repris des sources citées (UNIDO, Banque mondiale, offices statistiques nationaux), à l’année indiquée pour chacun. Les sources révisent leurs séries : vérifier la dernière publication avant une décision.',
      "Ce rapport est une synthèse d'information économique : il ne constitue pas un conseil en investissement.",
    ],
    filename: 'Production_manufacturiere',
  },
  en: {
    module: 'PRODUCTION MODULE',
    badge: 'MANUFACTURING',
    title: (n) => `Manufacturing — ${n}`,
    subtitle: (r, y) => `${r} · data ${y} · UNIDO and national sources`,
    na: 'not published',
    natures: { officiel: 'official', calcul_officiel: 'computed from official data', unido: 'UNIDO', estimation: 'estimate' },
    mva: 'Manufacturing value added',
    mvaGdp: 'MVA (% of GDP)',
    mvaCap: 'MVA per capita',
    growth: 'MVA growth',
    jobs: 'Industrial jobs',
    exports: 'Manufactured exports',
    rank: 'Rank in Africa (MVA)',
    rankValue: (r, n) => `${r} of ${n}`,
    profile: 'Industrial profile',
    region: 'Region',
    dataYear: 'Data year',
    mva2024: 'MVA 2024',
    growth2024: 'Growth 2024',
    zones: 'Industrial zones',
    cip: 'CIP world rank (UNIDO)',
    mht: 'Medium and high-tech share of MVA',
    industryGdp: 'Industry value added (% of GDP)',
    manufExports: 'Manufactures share of exports',
    mvaCap2015: 'MVA per capita (2015 dollars)',
    source: 'Source',
    profileText: [
      'Manufacturing value added (MVA): what manufacturing (ISIC section C, divisions 10 to 33) produces, minus what it consumes to produce. Relative to GDP it measures the weight of industry in the economy; per capita, the level of industrialisation.',
      'CIP (Competitive Industrial Performance): UNIDO index ranking countries by their capacity to produce and export manufactured goods. Medium and high-tech share: weight of industries such as chemicals, machinery or vehicles in MVA.',
      'The nature of each figure is shown in brackets: official (published by the national statistics office), computed from official data, UNIDO (international database) or estimate.',
    ],
    sectors: 'Main manufacturing sectors',
    cols: { code: 'ISIC', sector: 'Sector', share: 'Share of MVA', value: 'Value added', classes: 'ISIC 4 classes', branch: 'Branch', growthVol: 'Volume growth 2024', privateShare: 'Private share 2024' },
    sectorsText: 'Share of each ISIC division (2 digits) in manufacturing value added, and its amount in current dollars.',
    products: 'Flagship products',
    estimate: '2025 estimate',
    estCentral: 'Value added 2025 (central estimate)',
    estRange: 'Range',
    estGrowth: 'Volume growth 2025',
    estConfidence: 'Confidence (share of VA)',
    estBase: 'Price basis',
    estMethod: 'Method',
    estNote: 'Note',
    estText: 'Estimate for the current year, shown with its low and high range: it is not a published figure. Confidence shows which share of value added rests on solid indicators (A, B) or weaker ones (C).',
    ons: 'National statistics office accounts by branch',
    onsText: (u, s) => `Value added by branch, in ${u}. Year status: ${s}. The office's branches do not always match ISIC divisions one to one.`,
    structure: 'Structure by ISIC division',
    structureMeasured: 'UNIDO data measured at ISIC 4 class level (INDSTAT, IDSB).',
    structureEstimated: 'UNIDO does not publish this country at ISIC 4 class level: each division share is split equally across its classes. These figures place a sector; they do not compare two classes.',
    structureDetail: 'The class-by-class detail, year by year, is available from the "Export to PDF" button of the ISIC 4 table on screen.',
    warning: 'Disclaimer',
    warningText: [
      'Figures taken from the sources cited (UNIDO, World Bank, national statistics offices), for the year shown for each. Sources revise their series: check the latest release before making a decision.',
      'This report summarises economic information: it is not investment advice.',
    ],
    filename: 'Manufacturing',
  },
  ar: {
    module: 'وحدة الإنتاج',
    badge: 'الصناعة التحويلية',
    title: (n) => `الصناعة التحويلية — ${n}`,
    subtitle: (r, y) => `${r} · بيانات ${y} · UNIDO والمصادر الوطنية`,
    na: 'غير منشور',
    natures: { officiel: 'رسمي', calcul_officiel: 'محسوب من الرسمي', unido: 'UNIDO', estimation: 'تقدير' },
    mva: 'القيمة المضافة التحويلية',
    mvaGdp: 'القيمة المضافة التحويلية (% من الناتج)',
    mvaCap: 'القيمة المضافة التحويلية للفرد',
    growth: 'نمو القيمة المضافة التحويلية',
    jobs: 'الوظائف الصناعية',
    exports: 'الصادرات المصنّعة',
    rank: 'الترتيب في أفريقيا (القيمة المضافة التحويلية)',
    rankValue: (r, n) => `${r} من ${n}`,
    profile: 'الملف الصناعي',
    region: 'المنطقة',
    dataYear: 'سنة البيانات',
    mva2024: 'القيمة المضافة التحويلية 2024',
    growth2024: 'النمو 2024',
    zones: 'المناطق الصناعية',
    cip: 'الترتيب العالمي CIP (UNIDO)',
    mht: 'حصة التكنولوجيا المتوسطة والعالية من القيمة المضافة',
    industryGdp: 'القيمة المضافة للصناعة (% من الناتج)',
    manufExports: 'حصة المنتجات المصنّعة من الصادرات',
    mvaCap2015: 'القيمة المضافة التحويلية للفرد (دولار 2015)',
    source: 'المصدر',
    profileText: [
      'القيمة المضافة التحويلية: ما تنتجه الصناعة التحويلية (التصنيف ISIC، القسم C، الأقسام 10 إلى 33) مطروحًا منه ما تستهلكه لتنتج. نسبةً إلى الناتج المحلي تقيس وزن الصناعة في الاقتصاد، وللفرد مستوى التصنيع.',
      'CIP (الأداء الصناعي التنافسي): مؤشر UNIDO يرتّب البلدان حسب قدرتها على إنتاج السلع المصنّعة وتصديرها. حصة التكنولوجيا المتوسطة والعالية: وزن صناعات مثل الكيمياء والآلات والسيارات في القيمة المضافة التحويلية.',
      'طبيعة كل رقم مبيّنة بين قوسين: رسمي (ينشره الجهاز الإحصائي الوطني)، أو محسوب من الرسمي، أو UNIDO (قاعدة دولية)، أو تقدير.',
    ],
    sectors: 'أهم القطاعات التحويلية',
    cols: { code: 'ISIC', sector: 'القطاع', share: 'الحصة من القيمة المضافة', value: 'القيمة المضافة', classes: 'فئات ISIC 4', branch: 'الفرع', growthVol: 'النمو الحجمي 2024', privateShare: 'حصة القطاع الخاص 2024' },
    sectorsText: 'حصة كل قسم من أقسام ISIC (رقمان) في القيمة المضافة التحويلية، ومبلغها بالدولار الجاري.',
    products: 'المنتجات الرئيسية',
    estimate: 'تقدير 2025',
    estCentral: 'القيمة المضافة 2025 (التقدير المركزي)',
    estRange: 'المجال',
    estGrowth: 'النمو الحجمي 2025',
    estConfidence: 'الثقة (حصة من القيمة المضافة)',
    estBase: 'أساس الأسعار',
    estMethod: 'المنهج',
    estNote: 'ملاحظة',
    estText: 'تقدير للسنة الجارية مع حدّيه الأدنى والأعلى، وليس رقمًا منشورًا. تبيّن الثقة أي حصة من القيمة المضافة تستند إلى مؤشرات متينة (A وB) أو أضعف (C).',
    ons: 'حسابات الجهاز الإحصائي الوطني حسب الفرع',
    onsText: (u, s) => `القيمة المضافة حسب الفرع، بـ ${u}. حالة السنوات: ${s}. لا تطابق فروع الجهاز دائمًا أقسام ISIC واحدًا بواحد.`,
    structure: 'البنية حسب أقسام ISIC',
    structureMeasured: 'بيانات UNIDO مقيسة على مستوى الفئة ISIC 4 (INDSTAT وIDSB).',
    structureEstimated: 'لا تنشر UNIDO هذا البلد على مستوى الفئة ISIC 4: توزَّع حصة كل قسم بالتساوي على فئاته. تحدّد هذه الأرقام موقع القطاع ولا تقارن بين فئتين.',
    structureDetail: 'التفصيل فئةً بفئة وسنةً بسنة متاح بزر «تصدير بصيغة PDF» في جدول ISIC 4 على الشاشة.',
    warning: 'تنبيه',
    warningText: [
      'أرقام مأخوذة من المصادر المذكورة (UNIDO، البنك الدولي، الأجهزة الإحصائية الوطنية) في السنة المبيّنة لكل منها. تراجع المصادر سلاسلها: يُرجى التحقق من آخر إصدار قبل أي قرار.',
      'هذا التقرير خلاصة لمعلومات اقتصادية ولا يُعدّ نصيحة استثمارية.',
    ],
    filename: 'Production_manufacturiere_ar',
  },
};

const estNombre = (v) => typeof v === 'number' && Number.isFinite(v);

/**
 * @param {object} p
 * @param {object} p.unido      Réponse de GET /production/unido/{iso3}, telle que l'écran la garde.
 * @param {string} p.code       Code ISO3 du pays choisi.
 * @param {number} [p.rang]     Rang en Afrique (classement de l'écran).
 * @param {number} [p.total]    Nombre de pays classés.
 * @param {Array}  [p.divisions] Divisions CITI de l'écran : {division, label, shareMva, valueMlnUsd, sectors}.
 * @param {string} [p.basis]    'UNIDO_MEASURED' | 'ESTIMATED_FROM_ISIC2'.
 * @param {'fr'|'en'|'ar'} langue
 */
export function specManufacturePdf({ unido, code, rang, total, divisions = [], basis }, langue = 'fr') {
  const lang = T[langue] ? langue : 'fr';
  const t = T[lang];
  const u = unido || {};
  const nom = AFRICAN_COUNTRIES[code]?.[`name_${lang}`] || trDonnee(u.country_name, lang) || code;
  const natures = u.natures || {};
  const nature = (cle) => (natures[cle] ? ` (${t.natures[natures[cle]] || natures[cle]})` : '');
  const pct = (v, signe = false) => (estNombre(v)
    ? `${signe && v > 0 ? '+' : ''}${nombre(v, lang, 2)}${estAnglais(lang) ? '' : ' '}%`
    : t.na);
  // Les montants arrivent en millions de dollars.
  const musd = (v) => (estNombre(v) ? montantCompact(v * 1e6, lang, { B: 2, M: 1, u: 0 }, { max: true }) : t.na);
  const usd = (v) => (estNombre(v) ? montantCompact(v, lang, { B: 2, M: 1, u: 0 }, { max: true }) : t.na);
  const annee = u.data_year || 2023;

  const kpis = [
    { label: t.mva, value: musd(u.mva_2023_mln_usd), sub: `2023${nature('mva_2023_mln_usd')}`, accent: 'gold' },
    { label: t.mvaGdp, value: pct(u.mva_gdp_percent), sub: nature('mva_gdp_percent').trim(), accent: 'green' },
    { label: t.mvaCap, value: usd(u.mva_per_capita_usd), sub: nature('mva_per_capita_usd').trim(), accent: 'terra' },
    { label: t.growth, value: pct(u.growth_rate_2023, true), sub: `2023${nature('growth_rate_2023')}`, accent: 'green' },
    { label: t.jobs, value: estNombre(u.industry_employment) ? nombreCompact(u.industry_employment, lang, { M: 2, K: 0 }) : t.na, sub: nature('industry_employment').trim(), accent: 'gold' },
    { label: t.exports, value: musd(u.exports_manuf_mln_usd), sub: nature('exports_manuf_mln_usd').trim(), accent: 'terra' },
    { label: t.rank, value: rang && total ? t.rankValue(rang, total) : t.na, accent: 'gold' },
  ];

  const profil = [
    { label: t.region, value: trDonnee(u.region, lang) || t.na },
    { label: t.dataYear, value: String(annee) },
    estNombre(u.mva_2024_mln_usd) && { label: t.mva2024, value: `${musd(u.mva_2024_mln_usd)}${nature('mva_2024_mln_usd')}` },
    estNombre(u.growth_rate_2024) && { label: t.growth2024, value: `${pct(u.growth_rate_2024, true)}${nature('growth_rate_2024')}` },
    u.industrial_zones != null && { label: t.zones, value: String(u.industrial_zones) },
    u.cip_index_rank != null && { label: t.cip, value: `${u.cip_index_rank}${nature('cip_index_rank')}` },
    estNombre(u.mht_share_mva) && { label: t.mht, value: pct(u.mht_share_mva) },
    estNombre(u.industry_va_gdp_percent) && { label: t.industryGdp, value: pct(u.industry_va_gdp_percent) },
    estNombre(u.manuf_share_exports) && { label: t.manufExports, value: pct(u.manuf_share_exports) },
    estNombre(u.mva_per_capita_2015usd) && { label: t.mvaCap2015, value: usd(u.mva_per_capita_2015usd) },
    (u.source_institution || u.source) && { label: t.source, value: [u.source_institution, u.source_dataset || u.source].filter(Boolean).join(' — ') },
  ].filter(Boolean);

  const sections = [
    { title: t.profile, keyValues: profil },
    { paragraphs: t.profileText },
  ];

  const secteurs = u.structure_indstat_2015?.length ? u.structure_indstat_2015 : (u.top_sectors || []);
  if (secteurs.length) {
    sections.push({
      title: `${t.sectors}${u.structure_indstat_2015?.length ? ' (2015)' : ''}`,
      table: {
        columns: [
          { key: 'code', label: t.cols.code, width: 0.6 },
          { key: 'name', label: t.cols.sector, width: 3 },
          { key: 'share', label: t.cols.share, width: 1.2, align: 'right' },
          { key: 'value', label: t.cols.value, width: 1.3, align: 'right' },
        ],
        rows: secteurs.map((s) => ({
          code: s.isic || '—',
          name: trDonnee(s.name, lang) || '—',
          share: pct(s.share_mva),
          value: musd(s.value_mln_usd),
        })),
      },
    });
    sections.push({ paragraphs: [t.sectorsText] });
  }

  if (u.key_products?.length) {
    sections.push({ title: t.products, paragraphs: u.key_products.map((p) => `• ${trDonnee(p, lang)}`) });
  }

  const est = u.estimation_2025;
  if (est) {
    const confiance = Object.entries(est.confiance_part_va_pct || {})
      .map(([note, part]) => `${note} : ${pct(part)}`).join(' · ');
    sections.push({
      title: t.estimate,
      keyValues: [
        { label: t.estCentral, value: musd(est.va_mln_usd?.central) },
        { label: t.estRange, value: `${musd(est.va_mln_usd?.bas)} – ${musd(est.va_mln_usd?.haut)}` },
        { label: t.estGrowth, value: `${pct(est.croissance_volume_pct?.central, true)} (${pct(est.croissance_volume_pct?.bas, true)} – ${pct(est.croissance_volume_pct?.haut, true)})` },
        confiance && { label: t.estConfidence, value: confiance },
        est.base_prix && { label: t.estBase, value: trDonnee(est.base_prix, lang) },
        est.methode && { label: t.estMethod, value: trDonnee(est.methode, lang) },
        est.note && { label: t.estNote, value: trDonnee(est.note, lang) },
      ].filter(Boolean),
    });
    sections.push({ paragraphs: [t.estText] });
  }

  const ons = u.comptes_ons;
  if (ons?.branches?.length) {
    const ans = Object.keys(ons.statuts || {}).sort();
    const statuts = ans.map((a) => `${a} ${trDonnee(ons.statuts[a], lang)}`).join(', ');
    sections.push({
      title: t.ons,
      table: {
        columns: [
          { key: 'branch', label: t.cols.branch, width: 2.6 },
          ...ans.map((a) => ({ key: `a${a}`, label: a, width: 1, align: 'right' })),
          { key: 'growth', label: t.cols.growthVol, width: 1.1, align: 'right' },
          { key: 'private', label: t.cols.privateShare, width: 1.1, align: 'right' },
        ],
        rows: ons.branches.map((b) => ({
          branch: `${b.code} — ${lang === 'en' ? (b.libelle_en || b.libelle_fr) : trDonnee(b.libelle_fr, lang)}`,
          ...Object.fromEntries(ans.map((a) => [`a${a}`, musd(b.va_musd?.[a])])),
          growth: pct(b.croissance_volume_2024_pct, true),
          private: pct(b.part_privee_va_2024_pct),
        })),
      },
    });
    sections.push({ paragraphs: [t.onsText(trDonnee(ons.unite, lang) || 'USD', statuts), ons.source ? `${t.source} : ${ons.source}` : ''].filter(Boolean) });
  }

  if (divisions.length) {
    sections.push({
      title: t.structure,
      table: {
        columns: [
          { key: 'code', label: t.cols.code, width: 0.6 },
          { key: 'label', label: t.cols.sector, width: 3 },
          { key: 'share', label: t.cols.share, width: 1.2, align: 'right' },
          { key: 'value', label: t.cols.value, width: 1.3, align: 'right' },
          { key: 'classes', label: t.cols.classes, width: 1, align: 'right' },
        ],
        rows: divisions.map((d) => ({
          code: d.division,
          label: trDonnee(d.label, lang) || d.division,
          share: pct(d.shareMva),
          value: musd(d.valueMlnUsd),
          classes: String(d.sectors?.length ?? 0),
        })),
      },
    });
    sections.push({
      paragraphs: [basis === 'ESTIMATED_FROM_ISIC2' ? t.structureEstimated : t.structureMeasured, t.structureDetail],
    });
  }

  sections.push({ title: t.warning, notice: t.warningText });

  return {
    moduleLabel: t.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(trDonnee(u.region, lang) || '—', annee),
    kpis,
    sections,
    source: [u.source_institution || u.source, 'UNIDO'].filter(Boolean).join(' ; '),
    filename: [t.filename, code, new Date().toISOString().slice(0, 10)].filter(Boolean).join('_'),
  };
}
