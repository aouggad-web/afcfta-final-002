/**
 * RegulatoryDetailsPanel - Panneau des Détails Réglementaires
 *
 * Ce que le tarif du pays de destination publie pour une position : droits et
 * taxes ligne à ligne, restrictions, formalités. Tout est lu au socle — la
 * source de POST /calcul — par GET /consultation/{iso3}/position/{code} et
 * GET /consultation/{iso3}/formalites/{code}.
 *
 * Le panneau ne totalise rien et n'affiche aucun taux ZLECAf : le total des
 * droits et taxes est celui du calcul, et la préférence dépend d'une origine
 * que cet onglet ne connaît pas. Un taux que la source ne porte pas s'affiche
 * « à compléter », jamais 0 % ; un taux qui est une moyenne statistique
 * (WITS/TRAINS) le dit, comme le calcul le déclare indicatif.
 *
 * Il lisait auparavant /regulatory-engine/details, dont les fichiers de lignes
 * ne sont pas livrés : il répondait « Pays … non disponible » pour tous les pays.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  FileText,
  Percent,
  Building2,
  AlertCircle,
  Package,
  FileCheck,
  Banknote,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Info,
  ScrollText,
  Ban
} from 'lucide-react';
import { pick } from '../../i18n/lang';
import { refusAcces, PRICING_URL } from '../acces/AccesModules';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Couleurs par type de mesure
const measureStyles = {
  'CUSTOMS_DUTY': {
    icon: Banknote,
    color: 'text-[var(--gold)]',
    bg: 'bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))]',
    border: 'border-[color-mix(in_srgb,var(--gold)_30%,transparent)]'
  },
  'VAT': {
    icon: Percent,
    color: 'text-[var(--info)]',
    bg: 'bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))]',
    border: 'border-[color-mix(in_srgb,var(--info)_30%,transparent)]'
  },
  'LEVY': {
    icon: Building2,
    color: 'text-[var(--violet)]',
    bg: 'bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]',
    border: 'border-[color-mix(in_srgb,var(--violet)_30%,transparent)]'
  },
  'EXCISE': {
    icon: AlertCircle,
    color: 'text-[var(--danger)]',
    bg: 'bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))]',
    border: 'border-[color-mix(in_srgb,var(--danger)_30%,transparent)]'
  },
  'OTHER_TAX': {
    icon: FileText,
    color: 'text-[var(--afcfta-muted)]',
    bg: 'bg-[var(--overlay)]',
    border: 'border-[var(--afcfta-border)]'
  }
};

// Famille d'un droit du socle → style, et libellé dans les trois langues.
const FAMILLES = {
  droit: { style: 'CUSTOMS_DUTY', label: ['Droit de douane', 'Customs duty', 'رسم جمركي'] },
  tva: { style: 'VAT', label: ['TVA', 'VAT', 'ضريبة القيمة المضافة'] },
  post_tva: { style: 'VAT', label: ['Après TVA', 'After VAT', 'بعد ضريبة القيمة المضافة'] },
  accise: { style: 'EXCISE', label: ['Accise', 'Excise', 'ضريبة استهلاك'] },
  communautaire: { style: 'LEVY', label: ['Prélèvement communautaire', 'Community levy', 'مقتطع مجموعة إقليمية'] },
  redevance: { style: 'LEVY', label: ['Redevance', 'Fee', 'إتاوة'] },
  fonds: { style: 'LEVY', label: ['Fonds', 'Fund', 'صندوق'] },
  autre: { style: 'OTHER_TAX', label: ['Autre taxe', 'Other tax', 'ضريبة أخرى'] }
};

// Types de restriction que la source nomme, dans les trois langues. Un type
// inconnu garde le libellé de la source.
const TYPES_RESTRICTION = {
  IMPORTATION_INTERDITE: ['Importation interdite', 'Import prohibited', 'الاستيراد ممنوع']
};

const texts = {
  fr: {
    title: 'Détails Réglementaires',
    subtitle: 'Tarif de destination tel que le pays le publie',
    productInfo: 'Informations Produit',
    nationalCode: 'Code national',
    hs6Line: 'Ligne SH6',
    hs6Code: 'Code HS6',
    chapter: 'Chapitre',
    unit: 'Unité',
    noDescription: 'Désignation non publiée',
    codeSubstituted: (saisi, servi, hs6) => (hs6
      ? `Le code ${saisi} n'existe pas au tarif de ce pays : la ligne affichée est celle du SH6 ${servi}.`
      : `Le code ${saisi} n'existe pas au tarif de ce pays : la ligne affichée est celle de la position ${servi}.`),
    measures: 'Droits et Taxes',
    measuresDesc: 'Mesures publiées par le tarif, ligne à ligne',
    base: 'Assiette',
    rate: 'Taux publié',
    statisticalRate: 'Moyenne statistique SH6',
    statisticalBadge: 'Indicatif',
    statisticalNote: "Les lignes marquées « Indicatif » sont des moyennes statistiques au niveau SH6 (WITS/UNCTAD-TRAINS, Banque mondiale), pas le tarif national du pays.",
    toComplete: 'À compléter',
    toCompleteHint: 'La source ne publie pas de taux pour cette ligne',
    conditional: "Selon l'origine ou le produit",
    conditionalHint: "Mesure de défense commerciale : le taux dépend de l'origine, du producteur ou du produit. Il se calcule dans l'onglet Calculateur.",
    vatMissing: "La source du tarif de ce pays ne publie pas la TVA : cette liste est incomplète. Le calculateur la complète quand une fiche officielle la documente.",
    usagesTitle: "Régime selon l'usage déclaré",
    usagesHint: "Les droits ci-dessus sont ceux du régime courant ; le calculateur applique l'usage que vous déclarez.",
    preferenceNote: "Le taux préférentiel ZLECAf, les exonérations d'origine, les mesures temporaires et le total à payer dépendent de l'origine et de la date : ils se calculent dans l'onglet Calculateur.",
    preferenceNoteOrigin: "Le taux préférentiel suppose que l'origine du produit est justifiée (règles d'origine). Les mesures temporaires et le total à payer dépendent de la date : ils se calculent dans l'onglet Calculateur.",
    originRegime: (origine, regime) => `Origine ${origine} : régime ${regime}`,
    originNoPreference: (origine) => `Origine ${origine} : aucune préférence applicable, le taux publié (NPF) s'applique.`,
    originSameCountry: (origine) => `Origine ${origine} : c'est le pays de destination, aucune préférence n'est à chercher.`,
    preferentialRate: (origine) => `Taux préférentiel (origine ${origine})`,
    preferentialSpecific: 'Droit spécifique : voir le Calculateur',
    preferentialFloor: (taux) => `La préférence (${taux}) dépasserait le taux publié : le taux publié s'applique.`,
    requirements: 'Formalités',
    requirementsDesc: "Documents et formalités à l'importation",
    unofficialTranslation: ' — traduction non officielle',
    formalitiesUnavailable: "Les formalités n'ont pas pu être consultées. Une absence d'information n'est pas une absence d'obligation : vérifier auprès de l'administration douanière de destination.",
    restrictions: 'Restrictions',
    restrictionsDesc: 'Interdictions et restrictions publiées avec la position, telles qu’écrites par la source',
    scope: 'Portée',
    noData: 'Données non disponibles pour ce code',
    positionAbsent: 'Position introuvable dans les données servies pour ce pays',
    tariffUnavailable: 'Tarif de ce pays indisponible',
    chooseHint: 'Vérifiez le code HS ou essayez un autre pays',
    access: {
      connexion: "Connectez-vous pour consulter la réglementation d'une position.",
      quota: 'Vos recherches gratuites du mois sont utilisées. Abonnez-vous pour continuer sans limite.',
      abonnes: 'Cette consultation est réservée aux abonnés.'
    },
    seePlans: 'Voir les formules',
    chooseNational: (n) => `Ce code SH6 couvre ${n} positions nationales : choisissez-en une dans la liste ci-dessus.`,
    loading: 'Chargement des données...'
  },
  en: {
    title: 'Regulatory Details',
    subtitle: 'Destination tariff as published by the country',
    productInfo: 'Product Information',
    nationalCode: 'National code',
    hs6Line: 'HS6 line',
    hs6Code: 'HS6 code',
    chapter: 'Chapter',
    unit: 'Unit',
    noDescription: 'Designation not published',
    codeSubstituted: (saisi, servi, hs6) => (hs6
      ? `Code ${saisi} is not in this country's tariff: the line shown is the one for HS6 ${servi}.`
      : `Code ${saisi} is not in this country's tariff: the line shown is the one for position ${servi}.`),
    measures: 'Duties and Taxes',
    measuresDesc: 'Measures published by the tariff, line by line',
    base: 'Base',
    rate: 'Published rate',
    statisticalRate: 'HS6 statistical average',
    statisticalBadge: 'Indicative',
    statisticalNote: "Lines marked “Indicative” are HS6-level statistical averages (WITS/UNCTAD-TRAINS, World Bank), not the country's national tariff.",
    toComplete: 'To be completed',
    toCompleteHint: 'The source does not publish a rate for this line',
    conditional: 'Depends on origin or product',
    conditionalHint: 'Trade remedy: the rate depends on the origin, the producer or the product. It is computed in the Calculator tab.',
    vatMissing: "This country's tariff source does not publish VAT: this list is incomplete. The calculator completes it when an official record documents it.",
    usagesTitle: 'Regime depending on the declared use',
    usagesHint: 'The duties above are those of the current regime; the calculator applies the use you declare.',
    preferenceNote: 'The AfCFTA preferential rate, origin exemptions, temporary measures and the total payable depend on the origin and the date: they are computed in the Calculator tab.',
    preferenceNoteOrigin: 'The preferential rate assumes the origin of the product is justified (rules of origin). Temporary measures and the total payable depend on the date: they are computed in the Calculator tab.',
    originRegime: (origine, regime) => `Origin ${origine}: ${regime} regime`,
    originNoPreference: (origine) => `Origin ${origine}: no preference applies, the published rate (MFN) applies.`,
    originSameCountry: (origine) => `Origin ${origine}: this is the destination country, there is no preference to look for.`,
    preferentialRate: (origine) => `Preferential rate (origin ${origine})`,
    preferentialSpecific: 'Specific duty: see the Calculator',
    preferentialFloor: (taux) => `The preference (${taux}) would exceed the published rate: the published rate applies.`,
    requirements: 'Formalities',
    requirementsDesc: 'Documents and formalities for import',
    unofficialTranslation: ' — unofficial translation',
    formalitiesUnavailable: 'Formalities could not be retrieved. No information is not the same as no obligation: check with the destination customs administration.',
    // Statuts des formalités : le français est celui du serveur (reserve).
    formalityStatus: {
      AUCUNE_FORMALITE_PARTICULIERE: 'No particular administrative formality is published for this position. General import obligations still apply.',
      NON_ETABLIES: 'Formalities not established for this position. No information is not the same as no obligation: check with the destination customs administration.',
      POSITION_INTROUVABLE: 'Position not found in the data served for this country: no formality could be looked up.'
    },
    restrictions: 'Restrictions',
    restrictionsDesc: 'Prohibitions and restrictions published with the position, as written by the source',
    scope: 'Scope',
    noData: 'No data available for this code',
    positionAbsent: 'Position not found in the data served for this country',
    tariffUnavailable: "This country's tariff is unavailable",
    chooseHint: 'Check the HS code or try another country',
    access: {
      connexion: "Sign in to look up a position's regulation.",
      quota: 'Your free searches for this month are used up. Subscribe to continue without limits.',
      abonnes: 'This lookup is reserved for subscribers.'
    },
    seePlans: 'See plans',
    chooseNational: (n) => `This HS6 code covers ${n} national positions: pick one in the list above.`,
    loading: 'Loading data...'
  },
  ar: {
    title: 'التفاصيل التنظيمية',
    subtitle: 'التعريفة المنشورة لبلد المقصد كما ينشرها البلد',
    productInfo: 'معلومات المنتج',
    nationalCode: 'الرمز الوطني',
    hs6Line: 'سطر SH6',
    hs6Code: 'رمز SH6',
    chapter: 'الفصل',
    unit: 'الوحدة',
    noDescription: 'التسمية غير منشورة',
    codeSubstituted: (saisi, servi, hs6) => (hs6
      ? `الرمز ${saisi} غير موجود في تعريفة هذا البلد: السطر المعروض هو سطر SH6 ${servi}.`
      : `الرمز ${saisi} غير موجود في تعريفة هذا البلد: السطر المعروض هو سطر البند ${servi}.`),
    measures: 'الرسوم والضرائب',
    measuresDesc: 'التدابير التي تنشرها التعريفة، سطرًا بسطر',
    base: 'الوعاء',
    rate: 'المعدل المنشور',
    statisticalRate: 'متوسط إحصائي على مستوى SH6',
    statisticalBadge: 'إرشادي',
    statisticalNote: 'الأسطر المشار إليها بعبارة «إرشادي» هي متوسطات إحصائية على مستوى SH6 (WITS/UNCTAD-TRAINS، البنك الدولي) وليست التعريفة الوطنية للبلد.',
    toComplete: 'قيد الاستكمال',
    toCompleteHint: 'لا ينشر المصدر معدلًا لهذا السطر',
    conditional: 'بحسب المنشأ أو المنتج',
    conditionalHint: 'إجراء دفاع تجاري: يتوقف المعدل على المنشأ أو المنتِج أو المنتج، ويُحسب في تبويب الحاسبة.',
    vatMissing: 'لا ينشر مصدر تعريفة هذا البلد ضريبة القيمة المضافة: هذه القائمة ناقصة. تستكملها الحاسبة عندما توثّقها وثيقة رسمية.',
    usagesTitle: 'النظام بحسب الاستخدام المصرَّح به',
    usagesHint: 'الرسوم أعلاه هي رسوم النظام الجاري؛ وتطبّق الحاسبة الاستخدام الذي تصرّح به.',
    preferenceNote: 'يتوقف معدل زليكاف التفضيلي والإعفاءات المرتبطة بالمنشأ والتدابير المؤقتة والمجموع المستحق على بلد المنشأ وعلى التاريخ، وتُحسب في تبويب الحاسبة.',
    preferenceNoteOrigin: 'يفترض المعدل التفضيلي إثبات منشأ المنتج (قواعد المنشأ). وتتوقف التدابير المؤقتة والمجموع المستحق على التاريخ، وتُحسب في تبويب الحاسبة.',
    originRegime: (origine, regime) => `المنشأ ${origine}: نظام ${regime}`,
    originNoPreference: (origine) => `المنشأ ${origine}: لا يوجد تفضيل منطبق، ويسري المعدل المنشور (الدولة الأولى بالرعاية).`,
    originSameCountry: (origine) => `المنشأ ${origine}: هو بلد المقصد نفسه، فلا تفضيل يُطلب.`,
    preferentialRate: (origine) => `المعدل التفضيلي (المنشأ ${origine})`,
    preferentialSpecific: 'رسم نوعي: انظر الحاسبة',
    preferentialFloor: (taux) => `التفضيل (${taux}) يتجاوز المعدل المنشور: يسري المعدل المنشور.`,
    requirements: 'الإجراءات',
    requirementsDesc: 'الوثائق والإجراءات عند الاستيراد',
    unofficialTranslation: ' — ترجمة غير رسمية',
    formalitiesUnavailable: 'تعذّر الاطلاع على الإجراءات. غياب المعلومة لا يعني غياب الالتزام: تحقق لدى إدارة الجمارك في بلد المقصد.',
    formalityStatus: {
      AUCUNE_FORMALITE_PARTICULIERE: 'لا تُنشر أي إجراءات إدارية خاصة بهذا البند. وتبقى الالتزامات العامة عند الاستيراد سارية.',
      NON_ETABLIES: 'لم تُحدَّد الإجراءات الخاصة بهذا البند. غياب المعلومة لا يعني غياب الالتزام: تحقق لدى إدارة الجمارك في بلد المقصد.',
      POSITION_INTROUVABLE: 'البند غير موجود في البيانات المتاحة لهذا البلد: تعذّر البحث عن أي إجراءات.'
    },
    restrictions: 'القيود',
    restrictionsDesc: 'المنع والقيود المنشورة مع البند، كما كتبها المصدر',
    scope: 'النطاق',
    noData: 'لا توجد بيانات لهذا الرمز',
    positionAbsent: 'البند غير موجود في البيانات المتاحة لهذا البلد',
    tariffUnavailable: 'تعريفة هذا البلد غير متاحة',
    chooseHint: 'تحقق من رمز SH أو جرّب بلدًا آخر',
    access: {
      connexion: 'سجّل الدخول للاطلاع على التنظيم المتعلق بالبند.',
      quota: 'استُنفدت عمليات بحثك المجانية لهذا الشهر. اشترك للمتابعة دون حدود.',
      abonnes: 'هذه الخدمة مخصصة للمشتركين.'
    },
    seePlans: 'عرض الاشتراكات',
    chooseNational: (n) => `يشمل رمز SH6 هذا ${n} بندًا وطنيًا: اختر أحدها من القائمة أعلاه.`,
    loading: 'جارٍ تحميل البيانات…'
  }
};

// Certaines sources (WITS) portent des flottants simples : 16.6666660308838.
// Quatre décimales au plus ; 0 reste 0.
const arrondi = (taux) => (typeof taux === 'number' ? Number(taux.toFixed(4)) : taux);

// Taux d'une ligne : le pourcentage, ou l'expression d'un droit spécifique ou
// composé (« 10% or 55c/kg less 90% »), ou rien. Jamais 0 % faute de taux.
const tauxAffiche = (droit) => {
  if (droit.taux !== null && droit.taux !== undefined) return `${arrondi(droit.taux)}%`;
  return droit.expression || null;
};

// Le régime d'une préférence, tel que le serveur le nomme : la ZLECAf n'a pas de
// libellé de bloc, les unions et zones de libre-échange en ont un.
const libelleRegime = (preference) => (preference.regime === 'ZLECAF' ? 'ZLECAf' : (preference.libelle_bloc || preference.regime));

// Une désignation qui ne dit rien du produit : vide, ou réduite à un code
// (Libye : le « verbatim » français et anglais de la source est le code).
const aDesLettres = (texte) => /\p{L}/u.test(texte || '');

// La nature d'une erreur de la consultation. Un SH6 à plusieurs positions n'est
// pas une panne, c'est un choix à faire. Le message se construit au rendu, dans
// la langue du moment : le stocker figerait celle de la requête.
const erreurLisible = (err) => {
  // Connexion, quota de recherches ou formule : la décision d'accès, pas une panne.
  const refus = refusAcces(err);
  if (refus) return { kind: 'acces', genre: refus.genre };
  const statut = err.response?.status;
  const detail = err.response?.data?.detail;
  if (statut === 422 && detail?.code === 'POSITION_NATIONALE_REQUISE') {
    return { kind: 'choix', total: detail.positions?.length ?? 0 };
  }
  if (statut === 404 || statut === 422) return { kind: 'absente' };
  return { kind: 'indisponible' };
};

const messageErreur = (erreur, t) => {
  if (erreur.kind === 'acces') return t.access[erreur.genre] || t.access.abonnes;
  if (erreur.kind === 'choix') return t.chooseNational(erreur.total);
  if (erreur.kind === 'absente') return t.positionAbsent;
  return t.tariffUnavailable;
};

export default function RegulatoryDetailsPanel({
  countryCode,
  hsCode,
  originCode,
  language = 'fr'
}) {
  const [data, setData] = useState(null);
  const [formalites, setFormalites] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    measures: true,
    requirements: true,
    restrictions: true
  });

  const t = texts[language] || texts.fr;

  const convertToISO3 = (iso2) => {
    const map = {
      'DZ': 'DZA', 'AO': 'AGO', 'BJ': 'BEN', 'BW': 'BWA', 'BF': 'BFA', 'BI': 'BDI', 'CM': 'CMR', 'CV': 'CPV',
      'CF': 'CAF', 'TD': 'TCD', 'KM': 'COM', 'CG': 'COG', 'CD': 'COD', 'CI': 'CIV', 'DJ': 'DJI', 'EG': 'EGY',
      'GQ': 'GNQ', 'ER': 'ERI', 'SZ': 'SWZ', 'ET': 'ETH', 'GA': 'GAB', 'GM': 'GMB', 'GH': 'GHA', 'GN': 'GIN',
      'GW': 'GNB', 'KE': 'KEN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY', 'MG': 'MDG', 'MW': 'MWI', 'ML': 'MLI',
      'MR': 'MRT', 'MU': 'MUS', 'MA': 'MAR', 'MZ': 'MOZ', 'NA': 'NAM', 'NE': 'NER', 'NG': 'NGA', 'RW': 'RWA',
      'ST': 'STP', 'SN': 'SEN', 'SC': 'SYC', 'SL': 'SLE', 'SO': 'SOM', 'ZA': 'ZAF', 'SS': 'SSD', 'SD': 'SDN',
      'TZ': 'TZA', 'TG': 'TGO', 'TN': 'TUN', 'UG': 'UGA', 'ZM': 'ZMB', 'ZW': 'ZWE'
    };
    return map[iso2] || iso2;
  };

  useEffect(() => {
    const cleanCode = (hsCode || '').replace(/\D/g, '');
    if (!countryCode || cleanCode.length < 6) {
      setData(null);
      setFormalites(null);
      setError(null);
      setLoading(false);
      return undefined;
    }

    const iso3 = countryCode.length === 2 ? convertToISO3(countryCode) : countryCode;
    // Le pays d'origine est facultatif : sans lui, la fiche est celle du tarif seul.
    const origine = originCode ? (originCode.length === 2 ? convertToISO3(originCode) : originCode) : null;
    // Une réponse tardive d'un code déjà remplacé ne doit pas écraser la
    // réponse du code affiché : chaque nouvelle saisie annule la précédente.
    let annule = false;

    // L'écran attend dès que la saisie est valide, pas seulement quand la
    // requête part : pendant l'antirebond, il montrait l'ancien contenu — ou
    // « données non disponibles », avant même d'avoir demandé quoi que ce soit.
    setLoading(true);
    setError(null);

    // Debounce the API call to prevent excessive requests
    const timeoutId = setTimeout(async () => {
      try {
        const [fiche, reponseFormalites] = await Promise.all([
          origine
            ? axios.get(`${API}/consultation/${iso3}/position/${cleanCode}`, { params: { origine } })
            : axios.get(`${API}/consultation/${iso3}/position/${cleanCode}`),
          // Les formalités manquantes ne font pas tomber les droits et taxes :
          // elles se disent indisponibles, pas absentes.
          axios.get(`${API}/consultation/${iso3}/formalites/${cleanCode}`).catch(() => null)
        ]);
        if (annule) return;
        setData(fiche.data);
        setFormalites(reponseFormalites?.data || null);
      } catch (err) {
        if (annule) return;
        const erreur = erreurLisible(err);
        // Un SH6 à plusieurs positions est un choix à faire, un refus d'accès une
        // décision : ni l'un ni l'autre n'est une erreur.
        if (erreur.kind !== 'choix' && erreur.kind !== 'acces') console.error('Error fetching regulatory data:', err);
        setData(null);
        setFormalites(null);
        setError(erreur);
      } finally {
        if (!annule) setLoading(false);
      }
    }, 500);

    return () => {
      annule = true;
      clearTimeout(timeoutId);
    };
  }, [countryCode, hsCode, originCode]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Loading state
  if (loading) {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden" data-testid="regulatory-details-loading">
        <CardContent className="p-12 text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 border-4 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-full"></div>
            <div className="absolute inset-0 border-4 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-[var(--afcfta-muted)] text-lg">{t.loading}</p>
        </CardContent>
      </Card>
    );
  }

  // Un SH6 à plusieurs positions : un choix à faire, pas une panne.
  if (error?.kind === 'choix') {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]" data-testid="regulatory-details-choice">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
            <Info className="w-8 h-8 text-[var(--info)]" />
          </div>
          <p className="text-[var(--text)] text-lg">{messageErreur(error, t)}</p>
        </CardContent>
      </Card>
    );
  }

  // Refus d'accès : la fenêtre d'abonnement s'ouvre déjà (intercepteur global) ;
  // la carte dit la même chose et reste lisible une fois la fenêtre fermée.
  if (error?.kind === 'acces') {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]" data-testid="regulatory-details-access">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
            <Info className="w-8 h-8 text-[var(--gold)]" />
          </div>
          <p className="text-[var(--text)] text-lg">{messageErreur(error, t)}</p>
          {error.genre !== 'connexion' && (
            <a href={PRICING_URL} className="inline-block mt-4 text-[var(--gold)] font-semibold underline">
              {t.seePlans}
            </a>
          )}
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]" data-testid="regulatory-details-error">
        <CardContent className="p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-[var(--afcfta-muted)]" />
          </div>
          <p className="text-[var(--afcfta-muted)] text-lg">{error ? messageErreur(error, t) : t.noData}</p>
          <p className="text-[var(--afcfta-muted)] text-sm mt-2">{t.chooseHint}</p>
        </CardContent>
      </Card>
    );
  }

  const { droits = [], restrictions = [], usages = [], couverture = {}, preference = null } = data;
  // La désignation dans la langue de l'écran ; à défaut, la première qui dise
  // quelque chose du produit.
  const description = [
    pick(language, data.description_fr, data.description_en, data.description_ar),
    data.description_ar,
    data.description_en,
    data.description_fr
  ].find(aDesLettres);
  const listeFormalites = formalites?.formalities || [];
  // Le français du statut est celui du serveur ; les autres langues le traduisent.
  const reserveFormalites = (language !== 'fr' && t.formalityStatus?.[formalites?.statut]) || formalites?.reserve;
  const saisi = (hsCode || '').replace(/\D/g, '');
  // Le code saisi n'est pas une ligne du tarif : la ligne du SH6, ou une autre
  // position, a répondu. Un code saisi avec sa clé de contrôle (TUN) ou plus
  // court que la position servie en est le préfixe : rien à signaler.
  const codeSubstitue = saisi.length > 6 && (
    data.niveau === 'hs6'
    || (!saisi.startsWith(data.code) && !data.code.startsWith(saisi))
  );
  const aBaseStatistique = droits.some((droit) => droit.base_statistique);

  // Une interdiction d'importation est la première chose à lire. Une restriction
  // ordinaire (Égypte : les instructions de la position, longues et nombreuses)
  // vient après les taux, qu'elle ne doit pas enfouir.
  const interdit = restrictions.some((restriction) => TYPES_RESTRICTION[restriction.type]);
  // L'état replié survit d'une recherche à l'autre : il ne doit jamais masquer une interdiction.
  const restrictionsOuvertes = interdit || expandedSections.restrictions;
  const carteRestrictions = restrictions.length > 0 && (
    <Card className="bg-[var(--overlay)] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] overflow-hidden" data-testid="regulatory-restrictions">
      <CardHeader
        className="pb-3 cursor-pointer hover:bg-[var(--overlay)] transition-colors"
        onClick={() => toggleSection('restrictions')}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--danger)_30%,transparent)]">
              <Ban className="w-5 h-5 text-[var(--danger)]" />
            </div>
            <div>
              <CardTitle className="text-lg text-[var(--text)]">{t.restrictions}</CardTitle>
              <CardDescription className="text-[var(--afcfta-muted)]">{t.restrictionsDesc}</CardDescription>
            </div>
          </div>
          {restrictionsOuvertes ?
            <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> :
            <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
          }
        </div>
      </CardHeader>

      {restrictionsOuvertes && (
        <CardContent className="pt-0">
          <div className="space-y-3">
            {restrictions.map((restriction, idx) => {
              const libelle = TYPES_RESTRICTION[restriction.type]
                ? pick(language, ...TYPES_RESTRICTION[restriction.type])
                : restriction.libelle;
              return (
                <div
                  key={idx}
                  className="bg-[var(--overlay)] rounded-lg p-4 border border-[var(--afcfta-border)]"
                  data-testid="regulatory-restriction"
                >
                  {libelle && (
                    <p className="text-[var(--danger)] font-semibold">{libelle}</p>
                  )}
                  {/* Texte tel qu'écrit par la source, souvent en arabe. */}
                  <p className="text-[var(--text)] break-words" dir="auto">{restriction.texte}</p>
                  {restriction.portee && (
                    <p className="text-[var(--afcfta-muted)] text-xs mt-2 break-words">{t.scope} : {restriction.portee}</p>
                  )}
                  {restriction.source && (
                    <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words">{restriction.source}</p>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );

  return (
    <div className="space-y-4" data-testid="regulatory-details-panel">

      {/* === EN-TÊTE === */}
      <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] overflow-hidden">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <Sparkles className="w-6 h-6 text-[var(--gold)]" />
            </div>
            <div>
              <CardTitle className="text-xl text-[var(--text)]">{t.title}</CardTitle>
              <CardDescription className="text-[var(--afcfta-muted)]">{t.subtitle}</CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* === INFORMATIONS PRODUIT === */}
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
              <Package className="w-5 h-5 text-[var(--info)]" />
            </div>
            <CardTitle className="text-lg text-[var(--text)]">{t.productInfo}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {/* Description du produit */}
          <div className="bg-[var(--overlay)] rounded-lg p-4 mb-4 border-l-4 border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
            {description ? (
              <p className="text-[var(--text)] text-lg leading-relaxed whitespace-pre-line break-words" dir="auto">{description}</p>
            ) : (
              <p className="text-[var(--afcfta-muted)] text-lg italic" data-testid="regulatory-no-description">{t.noDescription}</p>
            )}
          </div>

          {/* Grille d'informations */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--overlay)] rounded-lg p-3">
              <p className="text-[var(--afcfta-muted)] text-xs mb-1">{data.niveau === 'hs6' ? t.hs6Line : t.nationalCode}</p>
              <p className="text-[var(--text)] font-mono text-lg font-semibold break-words">{data.code}</p>
            </div>
            {data.niveau !== 'hs6' && (
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs mb-1">{t.hs6Code}</p>
                <p className="text-[var(--text)] font-mono text-lg break-words">{data.hs6}</p>
              </div>
            )}
            <div className="bg-[var(--overlay)] rounded-lg p-3">
              <p className="text-[var(--afcfta-muted)] text-xs mb-1">{t.chapter}</p>
              <p className="text-[var(--text)] text-lg">{data.chapitre}</p>
            </div>
            {data.unite && (
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs mb-1">{t.unit}</p>
                <p className="text-[var(--text)] text-lg">{data.unite}</p>
              </div>
            )}
          </div>
          {codeSubstitue && (
            <div className="flex items-start gap-2 mt-4" data-testid="regulatory-code-substituted">
              <Info className="w-4 h-4 text-[var(--gold)] mt-0.5 shrink-0" />
              <p className="text-[var(--text)] text-sm">{t.codeSubstituted(saisi, data.code, data.niveau === 'hs6')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {interdit && carteRestrictions}

      {/* === DROITS ET TAXES === */}
      {droits.length > 0 && (
        <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden">
          <CardHeader
            className="pb-3 cursor-pointer hover:bg-[var(--overlay)] transition-colors"
            onClick={() => toggleSection('measures')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                  <Banknote className="w-5 h-5 text-[var(--gold)]" />
                </div>
                <div>
                  <CardTitle className="text-lg text-[var(--text)]">{t.measures}</CardTitle>
                  <CardDescription className="text-[var(--afcfta-muted)]">{t.measuresDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] border px-3">
                  {droits.length} {droits.length > 1 ? pick(language, 'lignes', 'lines', 'سطور') : pick(language, 'ligne', 'line', 'سطر')}
                </Badge>
                {expandedSections.measures ?
                  <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> :
                  <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
                }
              </div>
            </div>
          </CardHeader>

          {expandedSections.measures && (
            <CardContent className="pt-0">
              {preference && (
                <div className="flex items-start gap-2 mb-4 p-3 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]" data-testid="regulatory-preference">
                  <Info className="w-4 h-4 text-[var(--info)] mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[var(--text)] text-sm font-semibold break-words">
                      {preference.statut === 'MEME_PAYS'
                        ? t.originSameCountry(preference.origine)
                        : preference.applique
                          ? t.originRegime(preference.origine, libelleRegime(preference))
                          : t.originNoPreference(preference.origine)}
                    </p>
                    {preference.statut !== 'MEME_PAYS' && preference.note && (
                      <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words" dir="auto">{preference.note}</p>
                    )}
                  </div>
                </div>
              )}
              <div className="space-y-2">
                {droits.map((droit, idx) => {
                  const famille = FAMILLES[droit.famille] || FAMILLES.autre;
                  const style = measureStyles[famille.style];
                  const Icon = style.icon;
                  const taux = tauxAffiche(droit);
                  const pref = droit.preference;

                  return (
                    <div
                      key={`${droit.code}-${idx}`}
                      className={`flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 p-4 rounded-lg ${style.bg} border ${style.border}`}
                      data-testid="regulatory-measure"
                    >
                      <div className="flex items-start gap-4 min-w-0">
                        <div className="p-2 rounded-lg bg-[var(--overlay)] shrink-0">
                          <Icon className={`w-5 h-5 ${style.color}`} />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-[var(--text)] font-semibold">{droit.code}</span>
                            <Badge variant="outline" className="text-xs border-[var(--afcfta-border)] text-[var(--afcfta-muted)]">
                              {pick(language, ...famille.label)}
                            </Badge>
                          </div>
                          {droit.libelle && droit.libelle !== droit.code && (
                            <p className="text-[var(--text)] text-sm">{droit.libelle}</p>
                          )}
                          {droit.assiette && (
                            <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words">
                              {t.base} : <span className="font-mono">{droit.assiette}</span>
                            </p>
                          )}
                          {droit.note && (
                            <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words">{droit.note}</p>
                          )}
                        </div>
                      </div>

                      <div className="sm:text-right sm:shrink-0 sm:max-w-[45%]">
                        <p className="text-[var(--afcfta-muted)] text-xs">
                          {droit.base_statistique ? t.statisticalRate : t.rate}
                        </p>
                        {taux ? (
                          <p className="text-lg font-bold text-[var(--text)] break-words">{taux}</p>
                        ) : droit.conditionnel ? (
                          <p className="text-sm font-semibold text-[var(--afcfta-muted)]" title={t.conditionalHint}>
                            {t.conditional}
                          </p>
                        ) : (
                          <p className="text-sm font-semibold text-[var(--afcfta-muted)]" title={t.toCompleteHint}>
                            {t.toComplete}
                          </p>
                        )}
                        {droit.base_statistique && (
                          <Badge variant="outline" className="mt-1 text-xs border-[color-mix(in_srgb,var(--gold)_40%,transparent)] text-[var(--gold)]">
                            {t.statisticalBadge}
                          </Badge>
                        )}
                        {pref?.regime === 'preference' && (
                          <div className="mt-2 pt-2 border-t border-[var(--afcfta-border)]" data-testid="regulatory-preferential-rate">
                            <p className="text-[var(--afcfta-muted)] text-xs">{t.preferentialRate(preference.origine)}</p>
                            {pref.taux !== null && pref.taux !== undefined ? (
                              <p className="text-lg font-bold text-[var(--success)] break-words">{`${arrondi(pref.taux)}%`}</p>
                            ) : (
                              <p className="text-sm font-semibold text-[var(--afcfta-muted)]">{t.preferentialSpecific}</p>
                            )}
                          </div>
                        )}
                        {pref?.regime === 'npf_plancher' && pref.taux_ecarte !== null && pref.taux_ecarte !== undefined && (
                          <p className="text-[var(--afcfta-muted)] text-xs mt-2" data-testid="regulatory-preferential-floor">
                            {t.preferentialFloor(`${arrondi(pref.taux_ecarte)}%`)}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {aBaseStatistique && (
                <div className="flex items-start gap-2 mt-4 p-3 rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]" data-testid="regulatory-statistical-note">
                  <AlertCircle className="w-4 h-4 text-[var(--gold)] mt-0.5 shrink-0" />
                  <p className="text-[var(--text)] text-sm">{t.statisticalNote}</p>
                </div>
              )}
              {couverture.tva === false && (
                <div className="flex items-start gap-2 mt-4 p-3 rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]" data-testid="regulatory-vat-missing">
                  <AlertCircle className="w-4 h-4 text-[var(--gold)] mt-0.5 shrink-0" />
                  <p className="text-[var(--text)] text-sm">{t.vatMissing}</p>
                </div>
              )}
              {usages.length > 0 && (
                <div className="mt-4 p-3 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]" data-testid="regulatory-usages">
                  <p className="text-[var(--text)] text-sm font-semibold">{t.usagesTitle}</p>
                  <p className="text-[var(--afcfta-muted)] text-xs mt-1">{t.usagesHint}</p>
                  <ul className="mt-2 space-y-2">
                    {usages.map((usage, idx) => (
                      <li key={`${usage.code}-${idx}`} className="text-sm">
                        <span className="text-[var(--text)] font-medium">{usage.libelle || usage.code}</span>
                        {usage.texte && (
                          <p className="text-[var(--afcfta-muted)] text-xs mt-0.5 break-words" dir="auto">{usage.texte}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex items-start gap-2 mt-3">
                <Info className="w-4 h-4 text-[var(--info)] mt-0.5 shrink-0" />
                <p className="text-[var(--afcfta-muted)] text-sm">{preference ? t.preferenceNoteOrigin : t.preferenceNote}</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {!interdit && carteRestrictions}

      {/* === FORMALITÉS === */}
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden" data-testid="regulatory-formalities">
        <CardHeader
          className="pb-3 cursor-pointer hover:bg-[var(--overlay)] transition-colors"
          onClick={() => toggleSection('requirements')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                <ScrollText className="w-5 h-5 text-[var(--info)]" />
              </div>
              <div>
                <CardTitle className="text-lg text-[var(--text)]">{t.requirements}</CardTitle>
                <CardDescription className="text-[var(--afcfta-muted)]">{t.requirementsDesc}</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {listeFormalites.length > 0 && (
                <Badge className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)] border px-3">
                  {listeFormalites.length} {listeFormalites.length > 1 ? pick(language, 'documents', 'documents', 'وثائق') : pick(language, 'document', 'document', 'وثيقة')}
                </Badge>
              )}
              {expandedSections.requirements ?
                <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> :
                <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
              }
            </div>
          </div>
        </CardHeader>

        {expandedSections.requirements && (
          <CardContent className="pt-0">
            {listeFormalites.length > 0 && (
              <div className="space-y-3">
                {listeFormalites.map((formalite, idx) => (
                  <div
                    key={`${formalite.code}-${idx}`}
                    className="bg-[var(--overlay)] rounded-lg p-4 border border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--info)_30%,transparent)] transition-colors"
                    data-testid="regulatory-formality"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2.5 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] shrink-0">
                        <FileCheck className="w-5 h-5 text-[var(--info)]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        {formalite.code && (
                          <span className="font-mono text-[var(--info)] text-sm bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] px-2 py-0.5 rounded">
                            {formalite.code}
                          </span>
                        )}
                        {/* Égypte : le texte officiel est l'arabe ; la traduction,
                            reprise d'un autre fichier, se dit non officielle. */}
                        {formalite.traduction_non_officielle && (
                          <p className="text-[var(--text)] font-medium text-base mt-1 break-words" dir="auto">{formalite.texte}</p>
                        )}
                        <p className={formalite.traduction_non_officielle
                          ? 'text-[var(--afcfta-muted)] text-xs mt-1 break-words'
                          : 'text-[var(--text)] font-medium text-base mt-1 break-words'}
                        >
                          {pick(
                            language,
                            formalite.document_fr || formalite.document_en,
                            formalite.document_en || formalite.document_fr,
                            formalite.document_fr || formalite.document_en
                          ) || formalite.texte}
                          {formalite.traduction_non_officielle && (
                            <span className="italic">{t.unofficialTranslation}</span>
                          )}
                        </p>
                        {formalite.base_legale && (
                          <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words">{formalite.base_legale}</p>
                        )}
                        {formalite.issuing_authority && (
                          <p className="text-[var(--afcfta-muted)] text-xs mt-1 break-words">{formalite.issuing_authority}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {/* Le statut accompagne toujours la liste : une liste vide ne dit
                pas si la source n'a rien publié ou s'il n'y a rien à présenter. */}
            {reserveFormalites && (
              <div className={`flex items-start gap-2 ${listeFormalites.length > 0 ? 'mt-4' : ''}`} data-testid="regulatory-formalities-status">
                <Info className="w-4 h-4 text-[var(--info)] mt-0.5 shrink-0" />
                <p className="text-[var(--afcfta-muted)] text-sm break-words">{reserveFormalites}</p>
              </div>
            )}
            {!formalites && (
              <div className="flex items-start gap-2" data-testid="regulatory-formalities-unavailable">
                <AlertCircle className="w-4 h-4 text-[var(--gold)] mt-0.5 shrink-0" />
                <p className="text-[var(--afcfta-muted)] text-sm">{t.formalitiesUnavailable}</p>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
