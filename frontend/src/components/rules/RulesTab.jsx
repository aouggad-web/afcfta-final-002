import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import { FileText, ChevronDown, ChevronUp, Globe, CheckCircle, AlertTriangle, Info } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function RulesTab({ language = 'fr' }) {
  const [hsCode, setHsCode] = useState('');
  const [rulesOfOrigin, setRulesOfOrigin] = useState(null);
  const [showBrowser, setShowBrowser] = useState(false);
  const [loading, setLoading] = useState(false);

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
      minRegionalContent: "Contenu Régional Minimum",
      regionalContentRequired: "de contenu africain requis",
      requiredDocumentation: "Documentation Requise",
      adminInfo: "Informations Administratives",
      validityPeriod: "Période de validité",
      issuingAuthority: "Autorité émettrice",
      errorLoading: "Erreur lors du chargement des règles d'origine",
      browseHS: "Parcourir les codes HS",
      hideHSBrowser: "Masquer le navigateur",
      searchOrBrowse: "Recherchez ou parcourez les codes SH6 pour voir les règles d'origine applicables",
      loadingRules: "Chargement des règles...",
      explanation: "Ce que cela implique",
      alternativeRule: "Règle alternative",
      ytbWarning: "Cette règle est encore en cours de négociation (statut À Déterminer) entre les États membres",
      source: "Source"
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
      minRegionalContent: "Minimum Regional Content",
      regionalContentRequired: "African content required",
      requiredDocumentation: "Required Documentation",
      adminInfo: "Administrative Information",
      validityPeriod: "Validity period",
      issuingAuthority: "Issuing authority",
      errorLoading: "Error loading rules of origin",
      browseHS: "Browse HS codes",
      hideHSBrowser: "Hide browser",
      searchOrBrowse: "Search or browse HS6 codes to view applicable rules of origin",
      loadingRules: "Loading rules...",
      explanation: "What this means",
      alternativeRule: "Alternative rule",
      ytbWarning: "This rule is still under negotiation (Yet To Be agreed) between member states",
      source: "Source"
    }
  };

  const t = texts[language];

  const fetchRulesOfOrigin = async (code) => {
    if (!code || code.length < 2) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rules-of-origin/${code}?lang=${language}`);
      setRulesOfOrigin(response.data);
    } catch (error) {
      console.error(t.errorLoading, error);
      setRulesOfOrigin(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (code) => {
    setHsCode(code);
    if (code && code.length >= 2) {
      fetchRulesOfOrigin(code);
    } else {
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.ruleType}</h4>
                <Badge variant="secondary" className="text-base px-4 py-2 bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]">
                  {rulesOfOrigin.rules?.primary_rule?.name || rulesOfOrigin.rule.category || rulesOfOrigin.match_type}
                </Badge>
              </div>

              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border border-[var(--afcfta-border)] shadow-sm">
                <h4 className="font-semibold mb-2 text-[var(--text)]">{t.requirement}</h4>
                <p className="text-sm font-medium text-[var(--text)]">{rulesOfOrigin.rule.psr}</p>
              </div>
            </div>

            {rulesOfOrigin.rules?.primary_rule?.explanation && (
              <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] flex items-start gap-2">
                <Info className="w-4 h-4 mt-0.5 text-[var(--gold)] shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1 text-[var(--gold)]">{t.explanation}</h4>
                  <p className="text-sm text-[var(--gold)]">{rulesOfOrigin.rules.primary_rule.explanation}</p>
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
                  <p className="text-sm text-[var(--afcfta-muted)] mt-2">{rulesOfOrigin.rules.alternative_rule.explanation}</p>
                )}
              </div>
            )}

            <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
              <h4 className="font-semibold mb-3 text-[var(--success)]">{t.minRegionalContent}</h4>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Progress value={rulesOfOrigin.rule.value_added_threshold || 30} className="w-full h-4" />
                </div>
                <span className="text-2xl font-bold text-[var(--success)]">
                  {rulesOfOrigin.rule.value_added_threshold || 30}%
                </span>
              </div>
              <p className="text-sm text-[var(--success)] mt-2">
                {rulesOfOrigin.rule.value_added_threshold || 30}% {t.regionalContentRequired}
              </p>
            </div>

            {rulesOfOrigin.rule.notes && (
              <>
                <Separator />
                <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                  <h4 className="font-semibold text-[var(--info)] mb-2">{t.adminInfo}</h4>
                  <p className="text-sm text-[var(--info)]">{rulesOfOrigin.rule.notes}</p>
                </div>
              </>
            )}

            {rulesOfOrigin.source && (
              <p className="text-xs text-[var(--afcfta-muted)] text-right">{t.source}: {rulesOfOrigin.source}</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
