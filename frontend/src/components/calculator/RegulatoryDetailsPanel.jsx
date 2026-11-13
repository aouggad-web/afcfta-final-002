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
 * « à compléter », jamais 0 %.
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

const texts = {
  fr: {
    title: 'Détails Réglementaires',
    subtitle: 'Tarif de destination publié par le pays — mêmes données que le calculateur',
    productInfo: 'Informations Produit',
    nationalCode: 'Code national',
    hs6Code: 'Code HS6',
    chapter: 'Chapitre',
    unit: 'Unité',
    measures: 'Droits et Taxes',
    measuresDesc: 'Mesures publiées par le tarif, ligne à ligne',
    base: 'Assiette',
    rate: 'Taux publié',
    toComplete: 'À compléter',
    toCompleteHint: 'La source ne publie pas de taux pour cette ligne',
    vatMissing: "La source du tarif de ce pays ne publie pas la TVA : cette liste est incomplète. Le calculateur la complète quand une fiche officielle la documente.",
    preferenceNote: "Le taux préférentiel ZLECAf, les exonérations d'origine et le total à payer dépendent de l'origine : ils se calculent dans l'onglet Calculateur.",
    requirements: 'Formalités',
    requirementsDesc: "Documents et formalités à l'importation",
    formalitiesUnavailable: "Les formalités n'ont pas pu être consultées. Une absence d'information n'est pas une absence d'obligation : vérifier auprès de l'administration douanière de destination.",
    restrictions: 'Restrictions',
    restrictionsDesc: 'Interdictions et restrictions publiées avec la position, telles qu’écrites par la source',
    noData: 'Données non disponibles pour ce code',
    positionAbsent: 'Position introuvable dans les données servies pour ce pays',
    tariffUnavailable: 'Tarif de ce pays momentanément indisponible',
    chooseHint: 'Vérifiez le code HS ou essayez un autre pays',
    chooseNational: (n) => `Ce code SH6 couvre ${n} positions nationales : choisissez-en une dans la liste ci-dessus.`,
    loading: 'Chargement des données...'
  },
  en: {
    title: 'Regulatory Details',
    subtitle: "Destination tariff as published by the country — same data as the calculator",
    productInfo: 'Product Information',
    nationalCode: 'National code',
    hs6Code: 'HS6 code',
    chapter: 'Chapter',
    unit: 'Unit',
    measures: 'Duties and Taxes',
    measuresDesc: 'Measures published by the tariff, line by line',
    base: 'Base',
    rate: 'Published rate',
    toComplete: 'To be completed',
    toCompleteHint: 'The source does not publish a rate for this line',
    vatMissing: "This country's tariff source does not publish VAT: this list is incomplete. The calculator completes it when an official record documents it.",
    preferenceNote: 'The AfCFTA preferential rate, origin exemptions and the total payable depend on the origin: they are computed in the Calculator tab.',
    requirements: 'Formalities',
    requirementsDesc: 'Documents and formalities for import',
    formalitiesUnavailable: 'Formalities could not be retrieved. No information is not the same as no obligation: check with the destination customs administration.',
    restrictions: 'Restrictions',
    restrictionsDesc: 'Prohibitions and restrictions published with the position, as written by the source',
    noData: 'No data available for this code',
    positionAbsent: 'Position not found in the data served for this country',
    tariffUnavailable: "This country's tariff is temporarily unavailable",
    chooseHint: 'Check the HS code or try another country',
    chooseNational: (n) => `This HS6 code covers ${n} national positions: pick one in the list above.`,
    loading: 'Loading data...'
  },
  ar: {
    title: 'التفاصيل التنظيمية',
    subtitle: 'التعريفة المنشورة لبلد المقصد — نفس بيانات الحاسبة',
    productInfo: 'معلومات المنتج',
    nationalCode: 'الرمز الوطني',
    hs6Code: 'رمز SH6',
    chapter: 'الفصل',
    unit: 'الوحدة',
    measures: 'الرسوم والضرائب',
    measuresDesc: 'التدابير التي تنشرها التعريفة، سطرًا بسطر',
    base: 'الوعاء',
    rate: 'المعدل المنشور',
    toComplete: 'قيد الاستكمال',
    toCompleteHint: 'لا ينشر المصدر معدلًا لهذا السطر',
    vatMissing: 'لا ينشر مصدر تعريفة هذا البلد ضريبة القيمة المضافة: هذه القائمة ناقصة. تستكملها الحاسبة عندما توثّقها وثيقة رسمية.',
    preferenceNote: 'يتوقف معدل زليكاف التفضيلي والإعفاءات المرتبطة بالمنشأ والمجموع المستحق على بلد المنشأ، وتُحسب في تبويب الحاسبة.',
    requirements: 'الإجراءات',
    requirementsDesc: 'الوثائق والإجراءات عند الاستيراد',
    formalitiesUnavailable: 'تعذّر الاطلاع على الإجراءات. غياب المعلومة لا يعني غياب الالتزام: تحقق لدى إدارة الجمارك في بلد المقصد.',
    restrictions: 'القيود',
    restrictionsDesc: 'المنع والقيود المنشورة مع البند، كما كتبها المصدر',
    noData: 'لا توجد بيانات لهذا الرمز',
    positionAbsent: 'البند غير موجود في البيانات المتاحة لهذا البلد',
    tariffUnavailable: 'تعريفة هذا البلد غير متاحة مؤقتًا',
    chooseHint: 'تحقق من رمز SH أو جرّب بلدًا آخر',
    chooseNational: (n) => `يشمل رمز SH6 هذا ${n} بندًا وطنيًا: اختر أحدها من القائمة أعلاه.`,
    loading: 'جارٍ تحميل البيانات…'
  }
};

// Taux d'une ligne : le pourcentage, ou l'expression d'un droit spécifique ou
// composé (« 10% or 55c/kg less 90% »), ou rien. Jamais 0 % faute de taux.
const tauxAffiche = (droit) => {
  if (droit.taux !== null && droit.taux !== undefined) return `${droit.taux}%`;
  return droit.expression || null;
};

// Une erreur de la consultation, dite à l'opérateur : un SH6 à plusieurs
// positions n'est pas une panne, c'est un choix à faire.
const erreurLisible = (err, t) => {
  const statut = err.response?.status;
  const detail = err.response?.data?.detail;
  if (statut === 422 && detail?.code === 'POSITION_NATIONALE_REQUISE') {
    return { choix: true, message: t.chooseNational(detail.positions?.length ?? 0) };
  }
  if (statut === 404 || statut === 422) return { choix: false, message: t.positionAbsent };
  return { choix: false, message: t.tariffUnavailable };
};

export default function RegulatoryDetailsPanel({
  countryCode,
  hsCode,
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
    const cleanCode = (hsCode || '').replace(/[.\s]/g, '');
    if (!countryCode || cleanCode.length < 6) {
      setData(null);
      setFormalites(null);
      setError(null);
      setLoading(false);
      return undefined;
    }

    const iso3 = countryCode.length === 2 ? convertToISO3(countryCode) : countryCode;
    // Une réponse tardive d'un code déjà remplacé ne doit pas écraser la
    // réponse du code affiché : chaque nouvelle saisie annule la précédente.
    let annule = false;

    // Debounce the API call to prevent excessive requests
    const timeoutId = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const [fiche, reponseFormalites] = await Promise.all([
          axios.get(`${API}/consultation/${iso3}/position/${cleanCode}`),
          // Les formalités manquantes ne font pas tomber les droits et taxes :
          // elles se disent indisponibles, pas absentes.
          axios.get(`${API}/consultation/${iso3}/formalites/${cleanCode}`).catch(() => null)
        ]);
        if (annule) return;
        setData(fiche.data);
        setFormalites(reponseFormalites?.data || null);
      } catch (err) {
        if (annule) return;
        const lisible = erreurLisible(err, t);
        // Un SH6 à plusieurs positions est un choix à faire, pas une erreur.
        if (!lisible.choix) console.error('Error fetching regulatory data:', err);
        setData(null);
        setFormalites(null);
        setError(lisible);
      } finally {
        if (!annule) setLoading(false);
      }
    }, 500);

    return () => {
      annule = true;
      clearTimeout(timeoutId);
    };
  }, [countryCode, hsCode, t]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Loading state
  if (loading) {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden">
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
  if (error?.choix) {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]" data-testid="regulatory-details-choice">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
            <Info className="w-8 h-8 text-[var(--info)]" />
          </div>
          <p className="text-[var(--text)] text-lg">{error.message}</p>
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
          <p className="text-[var(--afcfta-muted)] text-lg">{error?.message || t.noData}</p>
          <p className="text-[var(--afcfta-muted)] text-sm mt-2">{t.chooseHint}</p>
        </CardContent>
      </Card>
    );
  }

  const { droits = [], restrictions = [], couverture = {} } = data;
  const description = pick(language, data.description_fr, data.description_en, data.description_fr);
  const listeFormalites = formalites?.formalities || [];

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
            <p className="text-[var(--text)] text-lg leading-relaxed whitespace-pre-line">{description}</p>
          </div>

          {/* Grille d'informations */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--overlay)] rounded-lg p-3">
              <p className="text-[var(--afcfta-muted)] text-xs mb-1">{t.nationalCode}</p>
              <p className="text-[var(--text)] font-mono text-lg font-semibold">{data.code}</p>
            </div>
            <div className="bg-[var(--overlay)] rounded-lg p-3">
              <p className="text-[var(--afcfta-muted)] text-xs mb-1">{t.hs6Code}</p>
              <p className="text-[var(--text)] font-mono text-lg">{data.hs6}</p>
            </div>
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
        </CardContent>
      </Card>

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
              <div className="space-y-2">
                {droits.map((droit, idx) => {
                  const famille = FAMILLES[droit.famille] || FAMILLES.autre;
                  const style = measureStyles[famille.style];
                  const Icon = style.icon;
                  const taux = tauxAffiche(droit);

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
                            <p className="text-[var(--afcfta-muted)] text-xs mt-1">
                              {t.base} : <span className="font-mono">{droit.assiette}</span>
                            </p>
                          )}
                          {droit.note && (
                            <p className="text-[var(--afcfta-muted)] text-xs mt-1">{droit.note}</p>
                          )}
                        </div>
                      </div>

                      <div className="sm:text-right sm:shrink-0 sm:max-w-[45%]">
                        <p className="text-[var(--afcfta-muted)] text-xs">{t.rate}</p>
                        {taux ? (
                          <p className="text-lg font-bold text-[var(--text)] break-words">{taux}</p>
                        ) : (
                          <p className="text-sm font-semibold text-[var(--afcfta-muted)]" title={t.toCompleteHint}>
                            {t.toComplete}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {couverture.tva === false && (
                <div className="flex items-start gap-2 mt-4 p-3 rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]" data-testid="regulatory-vat-missing">
                  <AlertCircle className="w-4 h-4 text-[var(--gold)] mt-0.5 shrink-0" />
                  <p className="text-[var(--text)] text-sm">{t.vatMissing}</p>
                </div>
              )}
              <div className="flex items-start gap-2 mt-3">
                <Info className="w-4 h-4 text-[var(--info)] mt-0.5 shrink-0" />
                <p className="text-[var(--afcfta-muted)] text-sm">{t.preferenceNote}</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* === RESTRICTIONS === */}
      {restrictions.length > 0 && (
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
              {expandedSections.restrictions ?
                <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> :
                <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
              }
            </div>
          </CardHeader>

          {expandedSections.restrictions && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {restrictions.map((restriction, idx) => (
                  <div
                    key={idx}
                    className="bg-[var(--overlay)] rounded-lg p-4 border border-[var(--afcfta-border)]"
                  >
                    {/* Texte tel qu'écrit par la source, souvent en arabe. */}
                    <p className="text-[var(--text)]" dir="auto">{restriction.text_verbatim}</p>
                    {restriction.source && (
                      <p className="text-[var(--afcfta-muted)] text-xs mt-2">{restriction.source}</p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

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
                        <p className="text-[var(--text)] font-medium text-base mt-1">
                          {pick(language, formalite.document_fr, formalite.document_en, formalite.document_fr) || formalite.texte}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {/* Le statut accompagne toujours la liste : une liste vide ne dit
                pas si la source n'a rien publié ou s'il n'y a rien à présenter. */}
            {formalites?.reserve && (
              <div className={`flex items-start gap-2 ${listeFormalites.length > 0 ? 'mt-4' : ''}`} data-testid="regulatory-formalities-status">
                <Info className="w-4 h-4 text-[var(--info)] mt-0.5 shrink-0" />
                <p className="text-[var(--afcfta-muted)] text-sm">{formalites.reserve}</p>
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
