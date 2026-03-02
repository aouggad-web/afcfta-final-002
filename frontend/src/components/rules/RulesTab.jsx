import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import { FileText, ChevronDown, ChevronUp, Globe, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
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
      loadingRules: "Chargement des règles..."
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
      loadingRules: "Loading rules..."
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
        <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50">
          <CardTitle className="text-2xl font-bold text-orange-700 flex items-center gap-2">
            <FileText className="w-6 h-6" />
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="font-semibold text-gray-700">
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
              className="w-full text-orange-600 border-orange-300 hover:bg-orange-50"
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
            <div className="border-2 border-orange-200 rounded-lg overflow-hidden">
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
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">{t.loadingRules}</p>
          </CardContent>
        </Card>
      )}

      {/* Rules of Origin Results */}
      {!loading && rulesOfOrigin && (
        <Card className="shadow-2xl border-l-4 border-l-amber-500">
          <CardHeader className="bg-gradient-to-r from-amber-100 to-yellow-100">
            <CardTitle className="text-xl font-bold text-amber-800 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              {t.rulesForCode} {rulesOfOrigin.hs_code}
            </CardTitle>
            <CardDescription className="font-semibold text-amber-700 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {t.sector}: {getSectorName(rulesOfOrigin.hs_code)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <h4 className="font-semibold mb-2 text-gray-700">{t.ruleType}</h4>
                <Badge variant="secondary" className="text-base px-4 py-2 bg-orange-100 text-orange-800">
                  {rulesOfOrigin.rules.rule}
                </Badge>
              </div>
              
              <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <h4 className="font-semibold mb-2 text-gray-700">{t.requirement}</h4>
                <p className="text-sm font-medium text-gray-800">{rulesOfOrigin.rules.requirement}</p>
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
              <h4 className="font-semibold mb-3 text-green-800">{t.minRegionalContent}</h4>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Progress value={rulesOfOrigin.rules.regional_content} className="w-full h-4" />
                </div>
                <span className="text-2xl font-bold text-green-700">
                  {rulesOfOrigin.rules.regional_content}%
                </span>
              </div>
              <p className="text-sm text-green-700 mt-2">
                {rulesOfOrigin.rules.regional_content}% {t.regionalContentRequired}
              </p>
            </div>

            <Separator />

            <div>
              <h4 className="font-semibold mb-3 text-gray-700">{t.requiredDocumentation}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {rulesOfOrigin.explanation.documentation_required.map((doc, index) => (
                  <Badge key={index} variant="outline" className="justify-start py-2 px-3">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                    {doc}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-2">{t.adminInfo}</h4>
              <div className="space-y-2 text-sm text-blue-700">
                <p className="flex items-center gap-2">
                  <span className="font-semibold">{t.validityPeriod}:</span> 
                  {rulesOfOrigin.explanation.validity_period}
                </p>
                <p className="flex items-center gap-2">
                  <span className="font-semibold">{t.issuingAuthority}:</span> 
                  {rulesOfOrigin.explanation.issuing_authority}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
