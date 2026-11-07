/**
 * Rapport PDF du calculateur : la liquidation des droits et taxes d'une
 * importation, expliquée ligne par ligne.
 *
 * Réutilise le bâtisseur déclaratif de utils/opportunityPdf.js (bandeau avec
 * le logo du site, cartes, tableaux, pied paginé). La source est la réponse
 * de `POST /calcul` (`calcul`), gardée telle quelle dans le résultat de
 * l'écran : le PDF ne recalcule rien.
 *
 * Même règle que le moteur et l'écran : un montant que le moteur n'a pas pu
 * liquider s'écrit « à compléter », jamais 0. Un PDF circule sans l'écran,
 * les réserves voyagent donc avec lui (état du calcul, éléments manquants,
 * taux de change, simulation non opposable).
 */
import { estAnglais, montant, nombre } from './nombres';
import { reserveConversion } from '../components/calculator/unifiedCalculator';

const T = {
  fr: {
    module: 'MODULE CALCULATEUR',
    badge: 'SIMULATION DOUANIÈRE',
    title: (dest) => `Droits et taxes à l'importation — ${dest}`,
    subtitle: (o, d, code) => `Origine ${o} · destination ${d} · position ${code}`,
    prefName: 'régime préférentiel',
    cif: 'Valeur CIF',
    cifSub: 'base de calcul (USD)',
    npf: 'Droits et taxes NPF',
    pref: (r) => `Droits et taxes ${r}`,
    eff: (p) => `taux effectif ${p}`,
    economy: 'Économie',
    economySub: (p) => `${p} des droits NPF`,
    toPay: 'Total à payer NPF',
    toPaySub: 'CIF + droits et taxes',
    todo: 'à compléter',
    operation: 'Opération',
    origin: "Pays d'origine",
    destination: 'Pays de destination',
    code: 'Position tarifaire',
    level: { national: 'position nationale', hs6: 'sous-position SH6' },
    designation: 'Désignation',
    regime: 'Régime retenu',
    source: 'Source du tarif',
    collected: 'collecté le',
    legalBase: 'Base légale des assiettes',
    currency: 'Devise nationale',
    rate: (taux, dev, date) => `1 USD = ${taux} ${dev}${date ? ` (relevé le ${date})` : ''}`,
    state: 'État du calcul',
    states: {
      COMPLET: 'Complet : toutes les lignes de droits et taxes publiées pour cette position ont été liquidées.',
      INDICATIF: (codes) => `Indicatif : toutes les lignes sont liquidées, mais ${codes} repose sur une moyenne statistique SH6 (WITS/TRAINS), pas sur le tarif national.`,
      PARTIEL: "Partiel : une ou plusieurs lignes n'ont pas pu être liquidées (voir « Éléments manquants »). Le total est partiel ; aucun montant n'a été inventé.",
      INDISPONIBLE: "Indisponible : aucune ligne n'a pu être liquidée pour cette position (voir « Éléments manquants »).",
    },
    howTo: 'Comment lire ce calcul',
    howToText: () => [
      "Valeur CIF (coût, assurance, fret) : valeur de la marchandise rendue à la frontière du pays de destination. C'est la base habituelle du droit de douane.",
      `Chaque ligne s'applique à son assiette (colonne « Assiette ») : le droit de douane sur la valeur CIF ; les taxes intérieures, comme la TVA, sur une base qui comprend en général les droits déjà calculés (effet cascade), selon la base légale citée plus haut.`,
      "Régime NPF (nation la plus favorisée) : tarif de droit commun, appliqué à toute marchandise qui ne bénéficie d'aucun accord préférentiel.",
      "Régime préférentiel (ZLECAf, zone de libre-échange ou union douanière) : il ne s'applique que si la marchandise est originaire au sens des règles d'origine de l'accord, preuve d'origine à l'appui (certificat d'origine).",
      'Taux effectif : total des droits et taxes divisé par la valeur CIF. Il permet de comparer deux régimes ou deux pays.',
    ],
    regimeNote: 'Note sur le régime',
    linesNpf: 'Détail des droits et taxes — régime NPF',
    linesPref: (r) => `Détail des droits et taxes — ${r}`,
    cols: { code: 'Code', label: 'Libellé', base_expr: 'Assiette', base: 'Base', rate: 'Taux', amount: 'Montant', status: 'Statut' },
    calculated: 'calculé',
    totals: 'Totaux',
    totalDuties: 'Total des droits et taxes',
    totalToPay: 'Total à payer (CIF + droits et taxes)',
    effective: 'Taux effectif',
    missing: 'Éléments manquants',
    missingIntro: "Ces lignes n'ont pas été liquidées. Le total ne les comprend pas : il faut les compléter avant de s'y fier.",
    motif: 'Motif',
    motifs: {
      TAUX_INDISPONIBLE: "Taux non publié par la source pour cette position.",
      ASSIETTE_INDISPONIBLE: "Assiette (base de calcul) non déterminée par la source.",
      QUANTITE_REQUISE: 'Droit spécifique : saisir la quantité dans le calculateur.',
      QUANTITE_COMPLEMENTAIRE_REQUISE: 'Saisir la quantité complémentaire demandée par le tarif.',
      TAUX_DE_CHANGE_REQUIS: 'Montant en monnaie nationale : taux de change nécessaire.',
      ASSIETTE_INCOMPLETE: "Assiette incomplète : un de ses composants n'a pas pu être calculé.",
      VALEUR_FOB_REQUISE: 'Saisir la valeur FOB, base de cette ligne.',
      REGLE_COMPOSEE_NON_ETABLIE: "Droit composé dont la règle de départage n'est pas établie.",
      UNITES_DE_QUANTITE_MULTIPLES: 'Plusieurs unités de quantité possibles : préciser la quantité.',
      NON_TRACEE_A_LA_SOURCE: "Famille de taxes non tracée par la source : montant inconnu, pas nul.",
    },
    notes: 'Notes de la source par ligne',
    formalities: 'Formalités administratives',
    noFormality: "Aucune formalité administrative particulière n'est publiée pour cette position. Les obligations générales à l'importation demeurent.",
    formalitiesUnknown: "Formalités non établies pour cette position. Une absence d'information n'est pas une absence d'obligation : vérifier auprès de l'administration douanière de destination.",
    document: 'Document',
    regulation: "Réglementation à l'importation",
    authority: 'Autorité',
    legalRef: 'Référence',
    documents: 'Pièces',
    steps: 'Procédure',
    exchange: 'Taux de change',
    warning: 'Avertissement',
    warningText: [
      "Simulation informative, non opposable à l'administration douanière. Les taux proviennent de la source citée, à sa date de collecte : ils peuvent avoir changé depuis.",
      "Avant toute opération, faire confirmer la position tarifaire, l'origine et les montants par l'administration douanière du pays de destination ou par un commissionnaire en douane agréé.",
    ],
    filename: 'Calcul_droits',
  },
  en: {
    module: 'CALCULATOR MODULE',
    badge: 'CUSTOMS SIMULATION',
    title: (dest) => `Import duties and taxes — ${dest}`,
    subtitle: (o, d, code) => `Origin ${o} · destination ${d} · tariff line ${code}`,
    prefName: 'preferential regime',
    cif: 'CIF value',
    cifSub: 'calculation base (USD)',
    npf: 'MFN duties and taxes',
    pref: (r) => `${r} duties and taxes`,
    eff: (p) => `effective rate ${p}`,
    economy: 'Savings',
    economySub: (p) => `${p} of MFN duties`,
    toPay: 'MFN total to pay',
    toPaySub: 'CIF + duties and taxes',
    todo: 'to be completed',
    operation: 'Transaction',
    origin: 'Country of origin',
    destination: 'Destination country',
    code: 'Tariff line',
    level: { national: 'national tariff line', hs6: 'HS6 subheading' },
    designation: 'Description',
    regime: 'Regime applied',
    source: 'Tariff source',
    collected: 'collected on',
    legalBase: 'Legal basis of the tax bases',
    currency: 'National currency',
    rate: (taux, dev, date) => `1 USD = ${taux} ${dev}${date ? ` (retrieved ${date})` : ''}`,
    state: 'Calculation status',
    states: {
      COMPLET: 'Complete: every duty and tax published for this tariff line was liquidated.',
      INDICATIF: (codes) => `Indicative: every line is liquidated, but ${codes} rests on an HS6 statistical average (WITS/TRAINS), not on the national tariff.`,
      PARTIEL: 'Partial: one or more lines could not be liquidated (see "Missing items"). The total is partial; no amount was invented.',
      INDISPONIBLE: 'Unavailable: no line could be liquidated for this tariff line (see "Missing items").',
    },
    howTo: 'How to read this calculation',
    howToText: () => [
      'CIF value (cost, insurance, freight): value of the goods delivered to the border of the destination country. It is the usual base of the customs duty.',
      `Each line applies to its own base ("Base" column): the customs duty to the CIF value; domestic taxes such as VAT to a base that usually includes the duties already calculated (cascade effect), per the legal basis cited above.`,
      'MFN regime (most favoured nation): the standard tariff, applied to any goods that benefit from no preferential agreement.',
      'Preferential regime (AfCFTA, free trade area or customs union): it applies only if the goods are originating under the agreement\'s rules of origin, with proof of origin (certificate of origin).',
      'Effective rate: total duties and taxes divided by the CIF value. It lets you compare two regimes or two countries.',
    ],
    regimeNote: 'Note on the regime',
    linesNpf: 'Duties and taxes in detail — MFN regime',
    linesPref: (r) => `Duties and taxes in detail — ${r}`,
    cols: { code: 'Code', label: 'Label', base_expr: 'Base', base: 'Base value', rate: 'Rate', amount: 'Amount', status: 'Status' },
    calculated: 'calculated',
    totals: 'Totals',
    totalDuties: 'Total duties and taxes',
    totalToPay: 'Total to pay (CIF + duties and taxes)',
    effective: 'Effective rate',
    missing: 'Missing items',
    missingIntro: 'These lines were not liquidated. The total does not include them: complete them before relying on it.',
    motif: 'Reason',
    motifs: {
      TAUX_INDISPONIBLE: 'Rate not published by the source for this tariff line.',
      ASSIETTE_INDISPONIBLE: 'Tax base not determined by the source.',
      QUANTITE_REQUISE: 'Specific duty: enter the quantity in the calculator.',
      QUANTITE_COMPLEMENTAIRE_REQUISE: 'Enter the supplementary quantity required by the tariff.',
      TAUX_DE_CHANGE_REQUIS: 'Amount in national currency: an exchange rate is needed.',
      ASSIETTE_INCOMPLETE: 'Incomplete base: one of its components could not be calculated.',
      VALEUR_FOB_REQUISE: 'Enter the FOB value, base of this line.',
      REGLE_COMPOSEE_NON_ETABLIE: 'Compound duty whose selection rule is not established.',
      UNITES_DE_QUANTITE_MULTIPLES: 'Several possible quantity units: specify the quantity.',
      NON_TRACEE_A_LA_SOURCE: 'Tax family not traced by the source: amount unknown, not zero.',
    },
    notes: 'Source notes by line',
    formalities: 'Administrative formalities',
    noFormality: 'No specific administrative formality is published for this tariff line. General import obligations still apply.',
    formalitiesUnknown: 'Formalities not established for this tariff line. Missing information is not an absence of obligation: check with the destination customs administration.',
    document: 'Document',
    regulation: 'Import regulations',
    authority: 'Authority',
    legalRef: 'Reference',
    documents: 'Documents',
    steps: 'Procedure',
    exchange: 'Exchange rate',
    warning: 'Disclaimer',
    warningText: [
      'Informative simulation, not binding on the customs administration. Rates come from the cited source, as of its collection date: they may have changed since.',
      'Before any transaction, have the tariff line, the origin and the amounts confirmed by the customs administration of the destination country or by a licensed customs broker.',
    ],
    filename: 'Duty_calculation',
  },
  ar: {
    module: 'وحدة الحاسبة',
    badge: 'محاكاة جمركية',
    title: (dest) => `الرسوم والضرائب عند الاستيراد — ${dest}`,
    subtitle: (o, d, code) => `المنشأ ${o} · المقصد ${d} · البند ${code}`,
    prefName: 'النظام التفضيلي',
    cif: 'القيمة سيف (CIF)',
    cifSub: 'أساس الحساب (دولار أمريكي)',
    npf: 'رسوم وضرائب الدولة الأولى بالرعاية',
    pref: (r) => `رسوم وضرائب ${r}`,
    eff: (p) => `المعدل الفعلي ${p}`,
    economy: 'الوفر',
    economySub: (p) => `${p} من رسوم الدولة الأولى بالرعاية`,
    toPay: 'المجموع المستحق (الدولة الأولى بالرعاية)',
    toPaySub: 'سيف + الرسوم والضرائب',
    todo: 'يُستكمل',
    operation: 'العملية',
    origin: 'بلد المنشأ',
    destination: 'بلد المقصد',
    code: 'البند التعريفي',
    level: { national: 'بند وطني', hs6: 'بند فرعي SH6' },
    designation: 'التسمية',
    regime: 'النظام المعتمد',
    source: 'مصدر التعريفة',
    collected: 'تاريخ الجمع',
    legalBase: 'السند القانوني للأوعية',
    currency: 'العملة الوطنية',
    rate: (taux, dev, date) => `1 USD = ${taux} ${dev}${date ? ` (بتاريخ ${date})` : ''}`,
    state: 'حالة الحساب',
    states: {
      COMPLET: 'كامل: صُفّيت كل بنود الرسوم والضرائب المنشورة لهذا البند.',
      INDICATIF: (codes) => `إرشادي: صُفّيت كل البنود، لكن ${codes} يستند إلى متوسط إحصائي على مستوى SH6 (WITS/TRAINS)، لا إلى التعريفة الوطنية.`,
      PARTIEL: 'جزئي: تعذّرت تصفية بند أو أكثر (انظر «العناصر الناقصة»). المجموع جزئي، ولم يُختلق أي مبلغ.',
      INDISPONIBLE: 'غير متاح: لم تُصفَّ أي بند لهذا البند التعريفي (انظر «العناصر الناقصة»).',
    },
    howTo: 'كيف يُقرأ هذا الحساب',
    howToText: () => [
      'القيمة سيف (التكلفة والتأمين والشحن): قيمة البضاعة واصلةً إلى حدود بلد المقصد، وهي الأساس المعتاد للرسم الجمركي.',
      'يُطبَّق كل بند على وعائه (عمود «الوعاء»): الرسم الجمركي على القيمة سيف، والضرائب الداخلية كضريبة القيمة المضافة على أساس يشمل عادةً الرسوم المحسوبة قبلها (أثر التراكم)، وفق السند القانوني المذكور أعلاه.',
      'نظام الدولة الأولى بالرعاية: التعريفة العامة المطبقة على كل بضاعة لا تستفيد من أي اتفاق تفضيلي.',
      'النظام التفضيلي (زليكاف أو منطقة تجارة حرة أو اتحاد جمركي): لا يُطبَّق إلا إذا كانت البضاعة ناشئة وفق قواعد المنشأ في الاتفاق، مع إثبات المنشأ (شهادة المنشأ).',
      'المعدل الفعلي: مجموع الرسوم والضرائب مقسومًا على القيمة سيف، ويسمح بالمقارنة بين نظامين أو بلدين.',
    ],
    regimeNote: 'ملاحظة حول النظام',
    linesNpf: 'تفصيل الرسوم والضرائب — نظام الدولة الأولى بالرعاية',
    linesPref: (r) => `تفصيل الرسوم والضرائب — ${r}`,
    cols: { code: 'الرمز', label: 'التسمية', base_expr: 'الوعاء', base: 'الأساس', rate: 'المعدل', amount: 'المبلغ', status: 'الحالة' },
    calculated: 'محسوب',
    totals: 'المجاميع',
    totalDuties: 'مجموع الرسوم والضرائب',
    totalToPay: 'المجموع المستحق (سيف + الرسوم والضرائب)',
    effective: 'المعدل الفعلي',
    missing: 'العناصر الناقصة',
    missingIntro: 'لم تُصفَّ هذه البنود ولا يشملها المجموع: يجب استكمالها قبل الاعتماد عليه.',
    motif: 'السبب',
    motifs: {
      TAUX_INDISPONIBLE: 'معدل غير منشور في المصدر لهذا البند.',
      ASSIETTE_INDISPONIBLE: 'وعاء (أساس الحساب) غير محدد في المصدر.',
      QUANTITE_REQUISE: 'رسم نوعي: أدخل الكمية في الحاسبة.',
      QUANTITE_COMPLEMENTAIRE_REQUISE: 'أدخل الكمية التكميلية التي تطلبها التعريفة.',
      TAUX_DE_CHANGE_REQUIS: 'مبلغ بالعملة الوطنية: يلزم سعر صرف.',
      ASSIETTE_INCOMPLETE: 'وعاء ناقص: تعذّر حساب أحد مكوّناته.',
      VALEUR_FOB_REQUISE: 'أدخل القيمة فوب (FOB)، وهي أساس هذا البند.',
      REGLE_COMPOSEE_NON_ETABLIE: 'رسم مركّب لم تُحدَّد قاعدة الترجيح فيه.',
      UNITES_DE_QUANTITE_MULTIPLES: 'وحدات كمية متعددة ممكنة: حدّد الكمية.',
      NON_TRACEE_A_LA_SOURCE: 'فئة ضرائب لا يتتبعها المصدر: المبلغ مجهول وليس صفرًا.',
    },
    notes: 'ملاحظات المصدر حسب البند',
    formalities: 'الإجراءات الإدارية',
    noFormality: 'لا يُنشر أي إجراء إداري خاص لهذا البند. وتبقى الالتزامات العامة للاستيراد سارية.',
    formalitiesUnknown: 'الإجراءات غير محددة لهذا البند. وغياب المعلومة لا يعني غياب الالتزام: يُرجى التحقق لدى إدارة الجمارك في بلد المقصد.',
    document: 'الوثيقة',
    regulation: 'تنظيم الاستيراد',
    authority: 'الجهة',
    legalRef: 'المرجع',
    documents: 'الوثائق',
    steps: 'الإجراء',
    exchange: 'سعر الصرف',
    warning: 'تنبيه',
    warningText: [
      'محاكاة إرشادية لا يُحتج بها أمام إدارة الجمارك. المعدلات مأخوذة من المصدر المذكور في تاريخ جمعه، وقد تكون تغيّرت منذ ذلك الحين.',
      'قبل أي عملية، يجب تأكيد البند التعريفي والمنشأ والمبالغ لدى إدارة الجمارك في بلد المقصد أو لدى معشّر جمركي معتمد.',
    ],
    filename: 'Calcul_droits_ar',
  },
};

const estCalculee = (l) => l?.statut === 'CALCULE' && typeof l.montant === 'number';

// « 19 % » en français, « 19% » en anglais.
const pourcent = (v, langue) => (typeof v === 'number'
  ? `${nombre(v, langue, 2)}${estAnglais(langue) ? '' : ' '}%`
  : '—');

function libelleRegime(calcul, result) {
  const regime = calcul.regime_commercial || {};
  if (regime.regime === 'UNION_DOUANIERE' || regime.regime === 'GZALE') {
    return regime.code_bloc || regime.regime;
  }
  return result?.trade_regime === 'ZLECAF' ? 'ZLECAf' : null;
}

function tauxLigne(l, langue) {
  if (l.montant_unitaire != null && l.specifique) {
    return typeof l.specifique === 'object' ? String(l.specifique.brut || '') : String(l.specifique);
  }
  return pourcent(l.taux_pct, langue);
}

function tableLignes(lignes, t, langue) {
  const usd = (v) => (typeof v === 'number' ? montant(v, langue, 2) : t.todo);
  return {
    columns: [
      { key: 'code', label: t.cols.code, width: 0.8 },
      { key: 'libelle', label: t.cols.label, width: 2.2 },
      { key: 'assiette', label: t.cols.base_expr, width: 1.6 },
      { key: 'base', label: t.cols.base, width: 1.2, align: 'right', fmt: usd },
      { key: 'taux', label: t.cols.rate, width: 0.9, align: 'right' },
      { key: 'montant', label: t.cols.amount, width: 1.2, align: 'right', fmt: (v, row) => (row._calculee ? usd(v) : t.todo) },
      { key: 'statut', label: t.cols.status, width: 0.9 },
    ],
    rows: lignes.map((l) => ({
      code: l.code,
      libelle: l.libelle || l.code,
      assiette: l.assiette || '—',
      base: l.base,
      taux: tauxLigne(l, langue),
      montant: l.montant,
      statut: estCalculee(l) ? t.calculated : t.todo,
      _calculee: estCalculee(l),
    })),
  };
}

function totaux(bloc, t, langue) {
  const usd = (v) => (typeof v === 'number' ? montant(v, langue, 2) : t.todo);
  const complet = bloc.etat === 'COMPLET' || bloc.etat === 'INDICATIF';
  return [
    { label: t.totalDuties, value: usd(bloc.total_droits) + (complet ? '' : ` (${t.todo})`) },
    { label: t.totalToPay, value: usd(bloc.total_a_payer) },
    { label: t.effective, value: pourcent(bloc.taux_effectif_pct, langue) },
  ];
}

function etatCalcul(npf, t) {
  const etat = npf.etat || 'INDISPONIBLE';
  if (etat === 'INDICATIF') return t.states.INDICATIF((npf.lignes_base_statistique || []).join(', ') || '—');
  return t.states[etat] || etat;
}

/**
 * Spécification du rapport (voir buildOpportunityPdf).
 *
 * @param {object} p
 * @param {object} p.calcul      Réponse de `POST /calcul`.
 * @param {object} p.result      Résultat affiché (formalités, devise, régime).
 * @param {string} p.origine     Nom affiché du pays d'origine.
 * @param {string} p.destination Nom affiché du pays de destination.
 * @param {'fr'|'en'} p.langue
 */
export function specCalculPdf({ calcul, result, origine, destination, langue = 'fr' }) {
  const t = T[langue] || T.fr;
  const usd = (v) => (typeof v === 'number' ? montant(v, langue, 2) : t.todo);
  const pct = (v) => pourcent(v, langue);
  const npf = calcul.npf || { lignes: [], manques: [], etat: 'INDISPONIBLE' };
  const regime = libelleRegime(calcul, result);
  const pref = result?.preferential_regime_applied && calcul.preference ? calcul.preference : null;
  const prov = calcul.provenance || {};
  const source = prov.source || {};
  const code = prov.code_demande || result?.hs_code || '';
  const cif = calcul.valeur_cif;

  const kpis = [
    { label: t.cif, value: usd(cif), sub: t.cifSub, accent: 'gold' },
    { label: t.npf, value: usd(npf.total_droits), sub: t.eff(pct(npf.taux_effectif_pct)), accent: 'red' },
  ];
  if (pref) {
    kpis.push({ label: t.pref(regime || t.prefName), value: usd(pref.total_droits), sub: t.eff(pct(pref.taux_effectif_pct)), accent: 'green' });
    const economie = typeof calcul.economie === 'number' ? calcul.economie : null;
    const partEconomie = economie != null && npf.total_droits > 0 ? (economie / npf.total_droits) * 100 : null;
    kpis.push({ label: t.economy, value: usd(economie), sub: partEconomie != null ? t.economySub(pct(partEconomie)) : '', accent: 'green' });
  } else {
    kpis.push({ label: t.toPay, value: usd(npf.total_a_payer), sub: t.toPaySub, accent: 'terra' });
  }

  const operation = [
    { label: t.origin, value: origine || '—' },
    { label: t.destination, value: destination || '—' },
    { label: t.code, value: `${code}${prov.niveau ? ` (${t.level[prov.niveau] || prov.niveau})` : ''}` },
    { label: t.designation, value: (calcul.position?.designation || '—').replace(/\s*\n\s*/g, ' ') },
    { label: t.cif, value: usd(cif) },
    { label: t.regime, value: regime ? `${regime}${calcul.regime_commercial?.libelle_bloc ? ` — ${calcul.regime_commercial.libelle_bloc}` : ''}` : 'NPF' },
    { label: t.state, value: etatCalcul(npf, t) },
    { label: t.source, value: `${source.nom || '—'}${source.collecte ? `, ${t.collected} ${String(source.collecte).slice(0, 10)}` : ''}` },
  ];
  if (prov.assiettes?.reference_legale) operation.push({ label: t.legalBase, value: prov.assiettes.reference_legale });
  const devise = result?.currency;
  if (devise?.usd_to_local_rate) {
    operation.push({
      label: t.currency,
      value: t.rate(nombre(devise.usd_to_local_rate, langue, 4), devise.local_code || '', devise.rate_as_of ? String(devise.rate_as_of).slice(0, 10) : null),
    });
  }

  const sections = [
    { title: t.operation, keyValues: operation },
    { title: t.howTo, paragraphs: t.howToText() },
  ];

  const notesRegime = [calcul.regime_commercial?.note, calcul.preference_zlecaf?.note].filter(Boolean);
  if (notesRegime.length) sections.push({ title: t.regimeNote, paragraphs: [...new Set(notesRegime)] });

  sections.push({ title: t.linesNpf, table: tableLignes(npf.lignes || [], t, langue) });
  sections.push({ keyValues: totaux(npf, t, langue) });
  if (pref) {
    sections.push({ title: t.linesPref(regime || t.prefName), table: tableLignes(pref.lignes || [], t, langue) });
    sections.push({ keyValues: totaux(pref, t, langue) });
  }

  const manques = [...(npf.manques || []), ...((pref && pref.manques) || [])];
  if (manques.length) {
    const vus = new Set();
    sections.push({ title: t.missing, paragraphs: [t.missingIntro] });
    sections.push({
      table: {
        columns: [
          { key: 'code', label: t.cols.code, width: 1 },
          { key: 'motif', label: t.motif, width: 5 },
        ],
        rows: manques
          .filter((m) => {
            const cle = `${m.code}|${m.motif}`;
            if (vus.has(cle)) return false;
            vus.add(cle);
            return true;
          })
          .map((m) => ({ code: m.code, motif: t.motifs[m.motif] || String(m.motif || '—') })),
      },
    });
  }

  const notes = (npf.lignes || []).filter((l) => l.note).map((l) => `${l.code} : ${l.note}`);
  if (notes.length) sections.push({ title: t.notes, paragraphs: notes });

  const formalites = result?.administrative_formalities || [];
  if (formalites.length) {
    sections.push({
      title: t.formalities,
      table: {
        columns: [
          { key: 'code', label: t.cols.code, width: 1 },
          { key: 'document', label: t.document, width: 5 },
        ],
        rows: formalites.map((f) => ({
          code: f.code || '—',
          // En arabe, le texte officiel quand la source le publie en arabe (Égypte).
          document: langue === 'en' ? (f.document_en || f.document_fr || f.texte)
            : langue === 'ar' ? (f.texte || f.document_fr || f.document_en)
              : (f.document_fr || f.document_en || f.texte),
        })),
      },
    });
  } else {
    sections.push({
      title: t.formalities,
      notice: [result?.formalites_reserve
        || (result?.formalites_statut === 'AUCUNE_FORMALITE_PARTICULIERE' ? t.noFormality : t.formalitiesUnknown)],
    });
  }

  const mesures = calcul.regulatory_compliance?.measures || [];
  // Une fiche par mesure : le libellé et le texte de la source séparés, pour
  // qu'un libellé arabe ne se mêle pas à un texte publié en français.
  mesures.forEach((m, i) => {
    sections.push({
      title: `${i === 0 ? `${t.regulation} — ` : ''}${m.measure_name}`,
      keyValues: [
        m.authority && { label: t.authority, value: m.authority },
        m.legal_reference && { label: t.legalRef, value: m.legal_reference },
        m.documents?.length && { label: t.documents, value: m.documents.join(' ; ') },
        m.procedure?.steps?.length && { label: t.steps, value: m.procedure.steps.join(' > ') },
      ].filter(Boolean),
    });
  });

  const reserve = reserveConversion({ ...result, conversion_monetaire: calcul.conversion_monetaire }, langue);
  if (reserve) sections.push({ title: t.exchange, notice: [`${reserve.titre}. ${reserve.texte}`] });

  sections.push({ title: t.warning, notice: t.warningText });

  return {
    moduleLabel: t.module,
    badge: t.badge,
    title: t.title(destination || '—'),
    subtitle: t.subtitle(origine || '—', destination || '—', code),
    kpis,
    sections,
    source: `${source.nom || '—'}${source.collecte ? ` (${String(source.collecte).slice(0, 10)})` : ''}`,
    filename: [t.filename, code, new Date().toISOString().slice(0, 10)].filter(Boolean).join('_'),
  };
}
