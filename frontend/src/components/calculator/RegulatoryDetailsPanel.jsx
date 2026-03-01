/**
 * RegulatoryDetailsPanel - Panneau des Détails Réglementaires (Version Améliorée)
 * 
 * Affiche les données du Moteur Réglementaire v3 avec une UX optimisée :
 * - Design moderne et épuré
 * - Visualisation claire des économies ZLECAf
 * - Sections collapsibles
 * - Indicateurs visuels colorés
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { 
  FileText, 
  Shield, 
  Percent, 
  Building2, 
  CheckCircle2, 
  AlertCircle,
  Package,
  FileCheck,
  Banknote,
  Clock,
  ChevronDown,
  ChevronUp,
  Sparkles,
  TrendingDown,
  Info,
  Landmark,
  ScrollText,
  Award
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Couleurs par type de mesure
const measureStyles = {
  'CUSTOMS_DUTY': { 
    icon: Banknote, 
    color: 'text-amber-400', 
    bg: 'bg-amber-500/10', 
    border: 'border-amber-500/30',
    label: 'Droit de Douane'
  },
  'VAT': { 
    icon: Percent, 
    color: 'text-blue-400', 
    bg: 'bg-blue-500/10', 
    border: 'border-blue-500/30',
    label: 'TVA'
  },
  'LEVY': { 
    icon: Building2, 
    color: 'text-purple-400', 
    bg: 'bg-purple-500/10', 
    border: 'border-purple-500/30',
    label: 'Prélèvement'
  },
  'EXCISE': { 
    icon: AlertCircle, 
    color: 'text-red-400', 
    bg: 'bg-red-500/10', 
    border: 'border-red-500/30',
    label: 'Accise'
  },
  'OTHER_TAX': { 
    icon: FileText, 
    color: 'text-slate-400', 
    bg: 'bg-slate-500/10', 
    border: 'border-slate-500/30',
    label: 'Autre taxe'
  }
};

const texts = {
  fr: {
    title: 'Détails Réglementaires',
    subtitle: 'Moteur Réglementaire AfCFTA v3',
    productInfo: 'Informations Produit',
    nationalCode: 'Code national',
    hs6Code: 'Code HS6',
    chapter: 'Chapitre',
    category: 'Catégorie',
    unit: 'Unité',
    sensitivity: 'Sensibilité ZLECAf',
    measures: 'Droits et Taxes',
    measuresDesc: 'Détail des mesures tarifaires applicables',
    taxCode: 'Code',
    taxName: 'Intitulé',
    taxRate: 'Taux NPF',
    zlecafRate: 'Taux ZLECAf',
    requirements: 'Documents Requis',
    requirementsDesc: 'Formalités administratives à l\'importation',
    document: 'Document',
    authority: 'Autorité émettrice',
    mandatory: 'Obligatoire',
    fiscalAdvantages: 'Avantages ZLECAf',
    fiscalAdvantagesDesc: 'Exonérations et réductions tarifaires',
    condition: 'Condition',
    reduction: 'Réduction',
    totalNPF: 'Total NPF',
    totalZLECAf: 'Total ZLECAf',
    savings: 'Économie',
    noData: 'Données non disponibles pour ce code',
    loading: 'Chargement des données...',
    notAvailable: 'Pays non disponible dans le moteur réglementaire',
    normal: 'Normal',
    sensitive: 'Sensible',
    excluded: 'Exclu',
    exoneration: 'Exonération'
  },
  en: {
    title: 'Regulatory Details',
    subtitle: 'AfCFTA Regulatory Engine v3',
    productInfo: 'Product Information',
    nationalCode: 'National code',
    hs6Code: 'HS6 Code',
    chapter: 'Chapter',
    category: 'Category',
    unit: 'Unit',
    sensitivity: 'AfCFTA Sensitivity',
    measures: 'Duties and Taxes',
    measuresDesc: 'Applicable tariff measures breakdown',
    taxCode: 'Code',
    taxName: 'Name',
    taxRate: 'MFN Rate',
    zlecafRate: 'AfCFTA Rate',
    requirements: 'Required Documents',
    requirementsDesc: 'Administrative formalities for import',
    document: 'Document',
    authority: 'Issuing authority',
    mandatory: 'Mandatory',
    fiscalAdvantages: 'AfCFTA Advantages',
    fiscalAdvantagesDesc: 'Tariff exemptions and reductions',
    condition: 'Condition',
    reduction: 'Reduction',
    totalNPF: 'Total MFN',
    totalZLECAf: 'Total AfCFTA',
    savings: 'Savings',
    noData: 'No data available for this code',
    loading: 'Loading data...',
    notAvailable: 'Country not available in regulatory engine',
    normal: 'Normal',
    sensitive: 'Sensitive',
    excluded: 'Excluded',
    exoneration: 'Exemption'
  }
};

export default function RegulatoryDetailsPanel({ 
  countryCode, 
  hsCode, 
  language = 'fr',
  onDataLoaded = () => {}
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    measures: true,
    requirements: true,
    advantages: true
  });

  const t = texts[language];

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
    const fetchData = async () => {
      if (!countryCode || !hsCode || hsCode.length < 6) {
        setData(null);
        setError(null);
        return;
      }

      const iso3 = countryCode.length === 2 ? convertToISO3(countryCode) : countryCode;

      setLoading(true);
      setError(null);

      try {
        const cleanCode = hsCode.replace(/[.\s]/g, '');
        const searchType = cleanCode.length > 6 ? 'national' : 'hs6';
        
        const response = await axios.get(
          `${API}/regulatory-engine/details?country=${iso3}&code=${cleanCode}&search_type=${searchType}`
        );

        if (response.data.success) {
          setData(response.data);
          onDataLoaded(response.data);
        } else {
          setError(response.data.error || t.noData);
          setData(null);
        }
      } catch (err) {
        console.error('Error fetching regulatory data:', err);
        setError(err.response?.data?.error || t.noData);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    const timeoutId = setTimeout(() => {
      fetchData();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [countryCode, hsCode, t.noData, onDataLoaded]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getSensitivityStyle = (sensitivity) => {
    switch (sensitivity) {
      case 'sensitive': return { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' };
      case 'excluded': return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' };
      default: return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
        <CardContent className="p-12 text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 border-4 border-amber-500/30 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-slate-400 text-lg">{t.loading}</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-slate-700/50 rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-slate-500" />
          </div>
          <p className="text-slate-400 text-lg">{error || t.noData}</p>
          <p className="text-slate-500 text-sm mt-2">
            {language === 'fr' ? 'Vérifiez le code HS ou essayez un autre pays' : 'Check the HS code or try another country'}
          </p>
        </CardContent>
      </Card>
    );
  }

  const { commodity, measures, requirements, fiscal_advantages, total_npf_pct, total_zlecaf_pct, savings_pct, processing_time_ms } = data;
  const sensStyle = getSensitivityStyle(commodity?.sensitivity);

  return (
    <div className="space-y-4" data-testid="regulatory-details-panel">
      
      {/* === HEADER - Synthèse Économique === */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        
        <CardHeader className="relative pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-amber-500/20">
                <Sparkles className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <CardTitle className="text-xl text-white">{t.title}</CardTitle>
                <CardDescription className="text-slate-400">{t.subtitle}</CardDescription>
              </div>
            </div>
            {processing_time_ms && (
              <Badge variant="outline" className="bg-slate-800/80 text-slate-300 border-slate-600 font-mono">
                <Clock className="w-3 h-3 mr-1.5" />
                {processing_time_ms.toFixed(1)}ms
              </Badge>
            )}
          </div>
        </CardHeader>
        
        <CardContent className="relative pt-4">
          {/* Barres de comparaison visuelles */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Total NPF */}
            <div className="relative bg-slate-800/60 rounded-xl p-5 border border-slate-700/50 overflow-hidden group hover:border-red-500/30 transition-colors">
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-red-500/20">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 to-red-400 transition-all duration-500"
                  style={{ width: `${Math.min(total_npf_pct || 0, 100)}%` }}
                ></div>
              </div>
              <p className="text-slate-400 text-sm font-medium uppercase tracking-wide">{t.totalNPF}</p>
              <p className="text-3xl font-bold text-red-400 mt-1">{(total_npf_pct || 0).toFixed(1)}%</p>
              <p className="text-slate-500 text-xs mt-1">{language === 'fr' ? 'Tarif Nation Plus Favorisée' : 'Most Favored Nation'}</p>
            </div>
            
            {/* Total ZLECAf */}
            <div className="relative bg-slate-800/60 rounded-xl p-5 border border-slate-700/50 overflow-hidden group hover:border-emerald-500/30 transition-colors">
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-emerald-500/20">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${Math.min(total_zlecaf_pct || 0, 100)}%` }}
                ></div>
              </div>
              <p className="text-slate-400 text-sm font-medium uppercase tracking-wide">{t.totalZLECAf}</p>
              <p className="text-3xl font-bold text-emerald-400 mt-1">{(total_zlecaf_pct || 0).toFixed(1)}%</p>
              <p className="text-slate-500 text-xs mt-1">{language === 'fr' ? 'Accord de Libre-Échange' : 'Free Trade Agreement'}</p>
            </div>
            
            {/* Économie */}
            <div className="relative bg-gradient-to-br from-amber-500/10 to-amber-600/5 rounded-xl p-5 border border-amber-500/30 overflow-hidden">
              <div className="absolute top-3 right-3">
                <TrendingDown className="w-5 h-5 text-amber-400/50" />
              </div>
              <p className="text-amber-400/80 text-sm font-medium uppercase tracking-wide">{t.savings}</p>
              <p className="text-3xl font-bold text-amber-400 mt-1">-{(savings_pct || 0).toFixed(1)}%</p>
              <p className="text-amber-500/60 text-xs mt-1">{language === 'fr' ? 'Avec Certificat d\'Origine' : 'With Certificate of Origin'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* === INFORMATIONS PRODUIT === */}
      {commodity && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <Package className="w-5 h-5 text-blue-400" />
              </div>
              <CardTitle className="text-lg text-white">{t.productInfo}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {/* Description du produit */}
            <div className="bg-slate-700/30 rounded-lg p-4 mb-4 border-l-4 border-blue-500">
              <p className="text-white text-lg leading-relaxed">{commodity.description_fr}</p>
            </div>
            
            {/* Grille d'informations */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-700/20 rounded-lg p-3">
                <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">{t.nationalCode}</p>
                <p className="text-white font-mono text-lg font-semibold">{commodity.national_code}</p>
              </div>
              <div className="bg-slate-700/20 rounded-lg p-3">
                <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">{t.hs6Code}</p>
                <p className="text-white font-mono text-lg">{commodity.hs6}</p>
              </div>
              <div className="bg-slate-700/20 rounded-lg p-3">
                <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">{t.chapter}</p>
                <p className="text-white text-lg">{commodity.chapter}</p>
              </div>
              <div className="bg-slate-700/20 rounded-lg p-3">
                <p className="text-slate-500 text-xs uppercase tracking-wide mb-1">{t.sensitivity}</p>
                <Badge className={`${sensStyle.bg} ${sensStyle.text} ${sensStyle.border} border`}>
                  {t[commodity.sensitivity] || commodity.sensitivity}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* === DROITS ET TAXES === */}
      {measures && measures.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/20 transition-colors"
            onClick={() => toggleSection('measures')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                  <Banknote className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white">{t.measures}</CardTitle>
                  <CardDescription className="text-slate-400">{t.measuresDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 border px-3">
                  {measures.length} {language === 'fr' ? 'taxes' : 'taxes'}
                </Badge>
                {expandedSections.measures ? 
                  <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                }
              </div>
            </div>
          </CardHeader>
          
          {expandedSections.measures && (
            <CardContent className="pt-0">
              <div className="space-y-2">
                {measures.map((measure, idx) => {
                  const style = measureStyles[measure.measure_type] || measureStyles.OTHER_TAX;
                  const Icon = style.icon;
                  const hasReduction = measure.is_zlecaf_applicable && measure.zlecaf_rate_pct !== null && measure.zlecaf_rate_pct < measure.rate_pct;
                  
                  return (
                    <div 
                      key={idx} 
                      className={`flex items-center justify-between p-4 rounded-lg ${style.bg} border ${style.border} transition-all hover:scale-[1.01]`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg bg-slate-900/50`}>
                          <Icon className={`w-5 h-5 ${style.color}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-white font-semibold">{measure.code}</span>
                            {hasReduction && (
                              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 border text-xs">
                                {t.exoneration}
                              </Badge>
                            )}
                          </div>
                          <p className="text-slate-300 text-sm">{measure.name_fr}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-slate-500 text-xs uppercase">{t.taxRate}</p>
                          <p className={`text-lg font-bold ${hasReduction ? 'text-red-400 line-through opacity-60' : 'text-white'}`}>
                            {measure.rate_pct}%
                          </p>
                        </div>
                        {measure.is_zlecaf_applicable && (
                          <div className="text-right">
                            <p className="text-slate-500 text-xs uppercase">{t.zlecafRate}</p>
                            <p className="text-lg font-bold text-emerald-400">
                              {measure.zlecaf_rate_pct ?? measure.rate_pct}%
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* === DOCUMENTS REQUIS === */}
      {requirements && requirements.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/20 transition-colors"
            onClick={() => toggleSection('requirements')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <ScrollText className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white">{t.requirements}</CardTitle>
                  <CardDescription className="text-slate-400">{t.requirementsDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 border px-3">
                  {requirements.length} {language === 'fr' ? 'documents' : 'documents'}
                </Badge>
                {expandedSections.requirements ? 
                  <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                }
              </div>
            </div>
          </CardHeader>
          
          {expandedSections.requirements && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {requirements.map((req, idx) => (
                  <div 
                    key={idx} 
                    className="bg-slate-700/30 rounded-lg p-4 border border-slate-700 hover:border-blue-500/30 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2.5 bg-blue-500/10 rounded-lg border border-blue-500/20 shrink-0">
                        <FileCheck className="w-5 h-5 text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-blue-400 text-sm bg-blue-500/10 px-2 py-0.5 rounded">
                            {req.code}
                          </span>
                          {req.is_mandatory && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 border text-xs">
                              {t.mandatory}
                            </Badge>
                          )}
                        </div>
                        <p className="text-white font-medium text-base">{req.document_fr}</p>
                        {req.issuing_authority && (
                          <div className="flex items-center gap-2 mt-2 text-slate-400 text-sm">
                            <Landmark className="w-4 h-4 text-slate-500" />
                            <span>{req.issuing_authority}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* === AVANTAGES ZLECAf === */}
      {fiscal_advantages && fiscal_advantages.length > 0 && (
        <Card className="bg-gradient-to-br from-emerald-900/20 to-slate-800/50 border-emerald-500/30 overflow-hidden">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/20 transition-colors"
            onClick={() => toggleSection('advantages')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <Award className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white">{t.fiscalAdvantages}</CardTitle>
                  <CardDescription className="text-emerald-400/60">{t.fiscalAdvantagesDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 border px-3">
                  {fiscal_advantages.length}
                </Badge>
                {expandedSections.advantages ? 
                  <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                }
              </div>
            </div>
          </CardHeader>
          
          {expandedSections.advantages && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {fiscal_advantages.map((adv, idx) => (
                  <div 
                    key={idx} 
                    className="bg-emerald-500/10 rounded-lg p-4 border border-emerald-500/20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 border font-mono">
                        {adv.tax_code}
                      </Badge>
                      <span className="text-2xl font-bold text-emerald-400">
                        {adv.reduced_rate_pct}%
                      </span>
                    </div>
                    <p className="text-slate-300">{adv.condition_fr}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
