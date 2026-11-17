import React, { useRef, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import OriginLegalReference from './OriginLegalReference';
import AppendixIvNotes from './AppendixIvNotes';
import { FileText, ChevronDown, ChevronUp, Globe, CheckCircle, AlertTriangle, Info } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function RulesTab({ language = 'fr' }) {
  const [hsCode, setHsCode] = useState('');
  const [rulesOfOrigin, setRulesOfOrigin] = useState(null);
  const [showBrowser, setShowBrowser] = useState(false);
  const [loading, setLoading] = useState(false);
  const requestId = useRef(0);

  const texts = {
    fr: {
      title: "Règles d'Origine ZLECAf",
      description: "Entrez un code SH6 pour consulter les règles d'origine spécifiques",
      placeholder: "Code SH6 (ex: 010121)",
      consult: "Consulter",
      rulesForCode: "Règles pour le Code SH",
      sector: "Secteur",
      ruleType: "Type de Règle",
      requirement: "Exigence",
      productDescription: "Désignation du produit",
      note25Threshold: "Seuil applicable : 55 % depuis le 1er janvier 2026 (note 2.5)",
      minRegionalContent: "Contenu Régional Minimum",
      regionalContentRequired: "de contenu africain requis",
      originCriterion: "Critère d'origine",
      criteria: {
        CTH: "Changement de position tarifaire",
        CTSH: "Changement de sous-position tarifaire",
        CC: "Changement de chapitre",
        WO: "Produit entièrement obtenu",
        SP: "Ouvraison spécifique",
        YARN: "Fabrication à partir de fils",
        NONE: "Pas de règle d'origine",
        YTB: "Règle en négociation",
        SPECIFIC: "Règle propre à cette ligne de l'Appendice IV : voir l'exigence"
      },
      ruleTextPrevails: "Seul le texte de la règle fait foi.",
      requiredDocumentation: "Documentation Requise",
      validityPeriod: "Période de validité",
      issuingAuthority: "Autorité émettrice",
      errorLoading: "Erreur lors du chargement des règles d'origine",
      browseHS: "Parcourir les codes HS",
      hideHSBrowser: "Masquer le navigateur",
      searchOrBrowse: "Recherchez ou parcourez les codes SH6 pour voir les règles d'origine applicables",
      loadingRules: "Chargement des règles...",
      explanation: "Ce que cela implique",
      alternativeRule: "Règle alternative",
      ytbWarning: "Cette règle est encore en cours de négociation (statut À Déterminer) entre les États membres"
    },
    en: {
      title: "AfCFTA Rules of Origin",
      description: "Enter an HS6 code to consult specific rules of origin",
      placeholder: "HS6 Code (e.g., 010121)",
      consult: "Consult",
      rulesForCode: "Rules for HS Code",
      sector: "Sector",
      ruleType: "Rule Type",
      requirement: "Requirement",
      productDescription: "Product description",
      note25Threshold: "Applicable threshold: 55% since 1 January 2026 (note 2.5)",
      minRegionalContent: "Minimum Regional Content",
      regionalContentRequired: "African content required",
      originCriterion: "Origin criterion",
      criteria: {
        CTH: "Change of tariff heading",
        CTSH: "Change of tariff subheading",
        CC: "Change of chapter",
        WO: "Wholly obtained product",
        SP: "Specific process",
        YARN: "Manufacture from yarn",
        NONE: "No rule of origin",
        YTB: "Rule under negotiation",
        SPECIFIC: "Rule specific to this Appendix IV row: see the requirement"
      },
      ruleTextPrevails: "Only the rule text is authoritative.",
      requiredDocumentation: "Required Documentation",
      validityPeriod: "Validity period",
      issuingAuthority: "Issuing authority",
      errorLoading: "Error loading rules of origin",
      browseHS: "Browse HS codes",
      hideHSBrowser: "Hide browser",
      searchOrBrowse: "Search or browse HS6 codes to view applicable rules of origin",
      loadingRules: "Loading rules...",
      explanation: "What this means",
      alternativeRule: "Alternative rule",
      ytbWarning: "This rule is still under negotiation (Yet To Be agreed) between member states"
    },
    ar: {
      title: "قواعد المنشأ في منطقة التجارة الحرة القارية الأفريقية",
      description: "أدخل رمز SH6 للاطلاع على قواعد المنشأ الخاصة به",
      placeholder: "رمز SH6 (مثال: 010121)",
      consult: "عرض",
      rulesForCode: "القواعد الخاصة برمز SH",
      sector: "القطاع",
      ruleType: "نوع القاعدة",
      requirement: "الشرط",
      productDescription: "وصف المنتج",
      note25Threshold: "الحد المطبق: 55% منذ 1 يناير 2026 (الملاحظة 2.5)",
      minRegionalContent: "الحد الأدنى للمحتوى الإقليمي",
      regionalContentRequired: "من المحتوى الأفريقي مطلوب",
      originCriterion: "معيار المنشأ",
      criteria: {
        CTH: "تغيير البند التعريفي",
        CTSH: "تغيير البند الفرعي التعريفي",
        CC: "تغيير الفصل",
        WO: "منتج تم الحصول عليه بالكامل",
        SP: "عملية تصنيع محددة",
        YARN: "التصنيع انطلاقًا من الخيوط",
        NONE: "لا توجد قاعدة منشأ",
        YTB: "قاعدة قيد التفاوض",
        SPECIFIC: "قاعدة خاصة بهذا السطر من التذييل الرابع: انظر الشرط"
      },
      ruleTextPrevails: "نص القاعدة وحده هو المرجع المعتمد.",
      requiredDocumentation: "الوثائق المطلوبة",
      validityPeriod: "فترة الصلاحية",
      issuingAuthority: "الجهة المُصدِرة",
      errorLoading: "خطأ أثناء تحميل قواعد المنشأ",
      browseHS: "تصفّح رموز SH",
      hideHSBrowser: "إخفاء المتصفّح",
      searchOrBrowse: "ابحث عن رموز SH6 أو تصفّحها للاطلاع على قواعد المنشأ المطبّقة",
      loadingRules: "جارٍ تحميل القواعد…",
      explanation: "ما يعنيه ذلك",
      alternativeRule: "قاعدة بديلة",
      ytbWarning: "لا تزال هذه القاعدة قيد التفاوض (لم يُتفق عليها بعد) بين الدول الأعضاء"
    }
  };

  const t = texts[language] || texts.fr;

  const fetchRulesOfOrigin = async (code) => {
    if (!code || code.length < 2) return;
    
    const id = ++requestId.current;
    setLoading(true);
    setRulesOfOrigin(null);
    try {
      const response = await axios.get(`${API}/rules-of-origin/${code}?lang=${language}`);
      if (id === requestId.current) setRulesOfOrigin(response.data);
    } catch (error) {
      if (id !== requestId.current) return;
      console.error(t.errorLoading, error);
      setRulesOfOrigin(null);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  };

  const handleCodeChange = (code) => {
    setHsCode(code);
    if (code && code.length >= 2) {
      fetchRulesOfOrigin(code);
    } else {
      requestId.current += 1;
      setLoading(false);
      setRulesOfOrigin(null);
    }
  };

  const handleBrowserSelect = (codeObj) => {
    setHsCode(codeObj.code);
    fetchRulesOfOrigin(codeObj.code);
    setShowBrowser(false);
  };

  const getSectorName = (code) => {
    const sector = code.substring(0, 2);
    return `${t.sector} ${sector}`; 
  };

  // Real criterion of a rule without a value threshold. A rule still under
  // negotiation shows as such whatever its code (chapter 60 is YARN/YTB); a row
  // whose text does not state its code's criterion (e.g. a "WO" row that only
  // requires certain materials to be originating) gets the row-specific label;
  // a code with no label here falls back to the source rule text.
  const getCriterion = (roo) => {
    const code = roo.rules?.primary_rule?.code;
    const key = roo.status === 'YTB' ? 'YTB'
      : roo.rules?.primary_rule?.matches_text === false && code !== 'NONE' ? 'SPECIFIC' : code;
    return t.criteria[key] || roo.rules?.rule_text_fr;
  };

  return (
    <div className="space-y-6">
      <Card className="shadow-xl border-t-4 border-t-orange-500">
        <CardHeader className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))]">
          <CardTitle className="text-2xl font-bold text-[var(--terra)] flex items-center gap-2">
            <FileText className="w-6 h-6" />
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="font-semibold text-[var(--text)]">
            {t.searchOrBrowse}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          {/* HS Code Search */}
          <div className="space-y-3">
            <HSCodeSearch
              value={hsCode}
              onChange={handleCodeChange}
              language={language}
              placeholder={t.placeholder}
            />
            
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowBrowser(!showBrowser)}
              className="w-full text-[var(--terra)] border-[color-mix(in_srgb,var(--terra)_30%,transparent)] hover:bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))]"
              data-testid="toggle-rules-hs-browser"
            >
              {showBrowser ? (
                <>
                  <ChevronUp className="w-4 h-4 mr-2" />
                  {t.hideHSBrowser}
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4 mr-2" />
                  {t.browseHS}
                </>
              )}
            </Button>
          </div>

          {/* HS Browser Panel */}
          {showBrowser && (
            <div className="border-2 border-[color-mix(in_srgb,var(--terra)_30%,transparent)] rounded-lg overflow-hidden">
              <HSCodeBrowser
                onSelect={handleBrowserSelect}
                language={language}
                showRulesOfOrigin={false}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card className="shadow-lg border-l-4 border-l-blue-500">
          <CardContent className="py-8 text-center">
            <div className="animate-spin w-8 h-8 border-4 border-[color-mix(in_srgb,var(--info)_30%,transparent)] border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-[var(--afcfta-muted)]">{t.loadingRules}</p>
          </CardContent>
        </Card>
      )}

      {/* Rules of Origin Results */}
      {!loading && rulesOfOrigin && rulesOfOrigin.rule && (
        <Card className="shadow-2xl border-l-4 border-l-amber-500">
          <CardHeader className="bg-gradient-to-r from-amber-100 to-yellow-100">
            <CardTitle className="text-xl font-bold text-[var(--gold)] flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-[var(--success)]" />
              {t.rulesForCode} {rulesOfOrigin.hs_code}
            </CardTitle>
            <CardDescription className="font-semibold text-[var(--gold)] flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {t.sector}: {getSectorName(rulesOfOrigin.hs_code)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {rulesOfOrigin.warning && (
              <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-lg p-3 text-sm text-[var(--gold)]">
                ⚠️ {rulesOfOrigin.warning}
              </div>
            )}

            {rulesOfOrigin.status === 'YTB' && (
              <div className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--terra)_30%,transparent)] rounded-lg p-3 flex items-start gap-2 text-sm text-[var(--terra)]">
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{t.ytbWarning}</span>
              </div>
            )}

            {rulesOfOrigin.product_description_fr && (
              <div>
                <h4 className="font-semibold text-[var(--text)]">{t.productDescription}</h4>
                <p className="text-sm"><bdi lang="fr" dir="ltr">{rulesOfOrigin.product_description_fr}</bdi></p>
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.ruleType}</h4>
                <Badge variant="secondary" className="text-base px-4 py-2 bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]">
                  {rulesOfOrigin.status === 'YTB' ? t.criteria.YTB :
                    rulesOfOrigin.rules?.primary_rule?.name || rulesOfOrigin.rule.category || rulesOfOrigin.match_type}
                </Badge>
              </div>

              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.requirement}</h4>
                <p className="text-sm font-medium text-[var(--text)]">
                  {rulesOfOrigin.status === 'YTB' ? t.criteria.YTB :
                    <bdi lang="fr" dir="ltr">{rulesOfOrigin.rule.psr}</bdi>}
                </p>
              </div>
            </div>

            {rulesOfOrigin.rules?.primary_rule?.explanation && (
              <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] flex items-start gap-2">
                <Info className="w-4 h-4 mt-0.5 text-[var(--gold)] shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1 text-[var(--gold)]">{t.explanation}</h4>
                  <p className="text-sm text-[var(--gold)]">
                    <bdi lang={language === 'en' ? 'en' : 'fr'} dir="ltr">{rulesOfOrigin.rules.primary_rule.explanation}</bdi>
                  </p>
                  {/* Règle non encore adoptée : aucun texte ne fait foi. */}
                  {rulesOfOrigin.status !== 'YTB' && (
                    <p className="text-xs italic text-[var(--afcfta-muted)] mt-1">{t.ruleTextPrevails}</p>
                  )}
                </div>
              </div>
            )}

            {rulesOfOrigin.rules?.alternative_rule && (
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.alternativeRule}</h4>
                <Badge variant="outline" className="text-sm px-3 py-1">
                  {rulesOfOrigin.rules.alternative_rule.name}
                </Badge>
                {rulesOfOrigin.rules.alternative_rule.explanation && (
                  <p className="text-sm text-[var(--afcfta-muted)] mt-2">
                    <bdi lang={language === 'en' ? 'en' : 'fr'} dir="ltr">{rulesOfOrigin.rules.alternative_rule.explanation}</bdi>
                  </p>
                )}
              </div>
            )}

            {rulesOfOrigin.rules?.threshold_note_fr && (
              <div className="text-sm text-[var(--text)]" data-testid="note-25-threshold">
                <h4 className="font-semibold">{t.note25Threshold}</h4>
                <p><bdi lang="fr" dir="ltr">{rulesOfOrigin.rules.threshold_note_fr}</bdi></p>
              </div>
            )}

            {rulesOfOrigin.status !== 'YTB' && rulesOfOrigin.rule.value_added_threshold != null ? (
              <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                <h4 className="font-semibold mb-3 text-[var(--success)]">{t.minRegionalContent}</h4>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Progress value={rulesOfOrigin.rule.value_added_threshold} className="w-full h-4" />
                  </div>
                  <span className="text-2xl font-bold text-[var(--success)]">
                    {rulesOfOrigin.rule.value_added_threshold}%
                  </span>
                </div>
                <p className="text-sm text-[var(--success)] mt-2">
                  {rulesOfOrigin.rule.value_added_threshold}% {t.regionalContentRequired}
                </p>
              </div>
            ) : (
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.originCriterion}</h4>
                <p className="text-sm font-medium text-[var(--text)]">{getCriterion(rulesOfOrigin)}</p>
              </div>
            )}

            <AppendixIvNotes
              roo={rulesOfOrigin}
              language={language}
              className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] text-sm text-[var(--text)]"
            />

            <OriginLegalReference
              roo={rulesOfOrigin}
              language={language}
              className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] text-sm text-[var(--afcfta-muted)]"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
