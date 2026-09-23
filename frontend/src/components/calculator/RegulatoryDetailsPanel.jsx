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

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Couleurs par type de mesure
const measureStyles = {
  'CUSTOMS_DUTY': { 
    icon: Banknote, 
    color: 'text-[var(--gold)]', 
    bg: 'bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))]', 
    border: 'border-[color-mix(in_srgb,var(--gold)_30%,transparent)]',
    label: 'Droit de Douane'
  },
  'VAT': { 
    icon: Percent, 
    color: 'text-[var(--info)]', 
    bg: 'bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))]', 
    border: 'border-[color-mix(in_srgb,var(--info)_30%,transparent)]',
    label: 'TVA'
  },
  'LEVY': { 
    icon: Building2, 
    color: 'text-[var(--violet)]', 
    bg: 'bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]', 
    border: 'border-[color-mix(in_srgb,var(--violet)_30%,transparent)]',
    label: 'Prélèvement'
  },
  'EXCISE': { 
    icon: AlertCircle, 
    color: 'text-[var(--danger)]', 
    bg: 'bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))]', 
    border: 'border-[color-mix(in_srgb,var(--danger)_30%,transparent)]',
    label: 'Accise'
  },
  'OTHER_TAX': { 
    icon: FileText, 
    color: 'text-[var(--afcfta-muted)]', 
    bg: 'bg-[var(--overlay)]', 
    border: 'border-[var(--afcfta-border)]',
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
          // Call onDataLoaded only if it's a function
          if (typeof onDataLoaded === 'function') {
            onDataLoaded(response.data);
          }
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

    // Debounce the API call to prevent excessive requests
    const timeoutId = setTimeout(() => {
      fetchData();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [countryCode, hsCode, t.noData]); // Remove onDataLoaded from dependencies to prevent re-render loops

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getSensitivityStyle = (sensitivity) => {
    switch (sensitivity) {
      case 'sensitive': return { bg: 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))]', text: 'text-[var(--terra)]', border: 'border-[color-mix(in_srgb,var(--terra)_30%,transparent)]' };
      case 'excluded': return { bg: 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))]', text: 'text-[var(--danger)]', border: 'border-[color-mix(in_srgb,var(--danger)_30%,transparent)]' };
      default: return { bg: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))]', text: 'text-[var(--success)]', border: 'border-[color-mix(in_srgb,var(--success)_30%,transparent)]' };
    }
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

  // Error state
  if (error || !data) {
    return (
      <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]">
        <CardContent className="p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-[var(--afcfta-muted)]" />
          </div>
          <p className="text-[var(--afcfta-muted)] text-lg">{error || t.noData}</p>
          <p className="text-[var(--afcfta-muted)] text-sm mt-2">
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
      <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[color-mix(in_srgb,var(--gold)_5%,transparent)] rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        
        <CardHeader className="relative pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                <Sparkles className="w-6 h-6 text-[var(--gold)]" />
              </div>
              <div>
                <CardTitle className="text-xl text-[var(--text)]">{t.title}</CardTitle>
                <CardDescription className="text-[var(--afcfta-muted)]">{t.subtitle}</CardDescription>
              </div>
            </div>
            {processing_time_ms && (
              <Badge variant="outline" className="bg-[var(--overlay)] text-[var(--text)] border-[var(--afcfta-border)] font-mono">
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
            <div className="relative bg-[var(--overlay)] rounded-xl p-5 border border-[var(--afcfta-border)] overflow-hidden group hover:border-[color-mix(in_srgb,var(--danger)_30%,transparent)] transition-colors">
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))]">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 to-red-400 transition-all duration-500"
                  style={{ width: `${Math.min(total_npf_pct || 0, 100)}%` }}
                ></div>
              </div>
              <p className="text-[var(--afcfta-muted)] text-sm font-medium uppercase tracking-wide">{t.totalNPF}</p>
              <p className="text-3xl font-bold text-[var(--danger)] mt-1">{(total_npf_pct || 0).toFixed(1)}%</p>
              <p className="text-[var(--afcfta-muted)] text-xs mt-1">{language === 'fr' ? 'Tarif Nation Plus Favorisée' : 'Most Favored Nation'}</p>
            </div>
            
            {/* Total ZLECAf */}
            <div className="relative bg-[var(--overlay)] rounded-xl p-5 border border-[var(--afcfta-border)] overflow-hidden group hover:border-[color-mix(in_srgb,var(--success)_30%,transparent)] transition-colors">
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))]">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${Math.min(total_zlecaf_pct || 0, 100)}%` }}
                ></div>
              </div>
              <p className="text-[var(--afcfta-muted)] text-sm font-medium uppercase tracking-wide">{t.totalZLECAf}</p>
              <p className="text-3xl font-bold text-[var(--success)] mt-1">{(total_zlecaf_pct || 0).toFixed(1)}%</p>
              <p className="text-[var(--afcfta-muted)] text-xs mt-1">{language === 'fr' ? 'Accord de Libre-Échange' : 'Free Trade Agreement'}</p>
            </div>
            
            {/* Économie */}
            <div className="relative bg-gradient-to-br from-amber-500/10 to-amber-600/5 rounded-xl p-5 border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] overflow-hidden">
              <div className="absolute top-3 right-3">
                <TrendingDown className="w-5 h-5 text-[var(--gold)]" />
              </div>
              <p className="text-[var(--gold)] text-sm font-medium uppercase tracking-wide">{t.savings}</p>
              <p className="text-3xl font-bold text-[var(--gold)] mt-1">-{(savings_pct || 0).toFixed(1)}%</p>
              <p className="text-[var(--gold)] text-xs mt-1">{language === 'fr' ? 'Avec Certificat d\'Origine' : 'With Certificate of Origin'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* === INFORMATIONS PRODUIT === */}
      {commodity && (
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
              <p className="text-[var(--text)] text-lg leading-relaxed">{commodity.description_fr}</p>
            </div>
            
            {/* Grille d'informations */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs uppercase tracking-wide mb-1">{t.nationalCode}</p>
                <p className="text-[var(--text)] font-mono text-lg font-semibold">{commodity.national_code}</p>
              </div>
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs uppercase tracking-wide mb-1">{t.hs6Code}</p>
                <p className="text-[var(--text)] font-mono text-lg">{commodity.hs6}</p>
              </div>
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs uppercase tracking-wide mb-1">{t.chapter}</p>
                <p className="text-[var(--text)] text-lg">{commodity.chapter}</p>
              </div>
              <div className="bg-[var(--overlay)] rounded-lg p-3">
                <p className="text-[var(--afcfta-muted)] text-xs uppercase tracking-wide mb-1">{t.sensitivity}</p>
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
                  {measures.length} {language === 'fr' ? 'taxes' : 'taxes'}
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
                        <div className={`p-2 rounded-lg bg-[var(--overlay)]`}>
                          <Icon className={`w-5 h-5 ${style.color}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[var(--text)] font-semibold">{measure.code}</span>
                            {hasReduction && (
                              <Badge className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)] border text-xs">
                                {t.exoneration}
                              </Badge>
                            )}
                          </div>
                          <p className="text-[var(--text)] text-sm">{measure.name_fr}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-[var(--afcfta-muted)] text-xs uppercase">{t.taxRate}</p>
                          <p className={`text-lg font-bold ${hasReduction ? 'text-[var(--danger)] line-through opacity-60' : 'text-[var(--text)]'}`}>
                            {measure.rate_pct}%
                          </p>
                        </div>
                        {measure.is_zlecaf_applicable && (
                          <div className="text-right">
                            <p className="text-[var(--afcfta-muted)] text-xs uppercase">{t.zlecafRate}</p>
                            <p className="text-lg font-bold text-[var(--success)]">
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
        <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden">
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
                <Badge className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)] border px-3">
                  {requirements.length} {language === 'fr' ? 'documents' : 'documents'}
                </Badge>
                {expandedSections.requirements ? 
                  <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> : 
                  <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
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
                    className="bg-[var(--overlay)] rounded-lg p-4 border border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--info)_30%,transparent)] transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2.5 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] shrink-0">
                        <FileCheck className="w-5 h-5 text-[var(--info)]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-[var(--info)] text-sm bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] px-2 py-0.5 rounded">
                            {req.code}
                          </span>
                          {req.is_mandatory && (
                            <Badge className="bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] text-[var(--danger)] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] border text-xs">
                              {t.mandatory}
                            </Badge>
                          )}
                        </div>
                        <p className="text-[var(--text)] font-medium text-base">{req.document_fr}</p>
                        {req.issuing_authority && (
                          <div className="flex items-center gap-2 mt-2 text-[var(--afcfta-muted)] text-sm">
                            <Landmark className="w-4 h-4 text-[var(--afcfta-muted)]" />
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
        <Card className="bg-gradient-to-br from-emerald-900/20 to-slate-800/50 border-[color-mix(in_srgb,var(--success)_30%,transparent)] overflow-hidden">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-[var(--overlay)] transition-colors"
            onClick={() => toggleSection('advantages')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                  <Award className="w-5 h-5 text-[var(--success)]" />
                </div>
                <div>
                  <CardTitle className="text-lg text-[var(--text)]">{t.fiscalAdvantages}</CardTitle>
                  <CardDescription className="text-[var(--success)]">{t.fiscalAdvantagesDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)] border px-3">
                  {fiscal_advantages.length}
                </Badge>
                {expandedSections.advantages ? 
                  <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> : 
                  <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />
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
                    className="bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] rounded-lg p-4 border border-[color-mix(in_srgb,var(--success)_30%,transparent)]"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)] border font-mono">
                        {adv.tax_code}
                      </Badge>
                      <span className="text-2xl font-bold text-[var(--success)]">
                        {adv.reduced_rate_pct}%
                      </span>
                    </div>
                    <p className="text-[var(--text)]">{adv.condition_fr}</p>
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
