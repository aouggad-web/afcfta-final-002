/**
 * RegulatoryDetailsPanel - Panneau des Détails Réglementaires
 * 
 * Affiche les données du Moteur Réglementaire v3 de manière claire et structurée :
 * - Informations sur le produit
 * - Détail des mesures (droits et taxes)
 * - Formalités administratives requises
 * - Avantages fiscaux ZLECAf
 * - Comparaison NPF vs ZLECAf
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Progress } from '../ui/progress';
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
  Sparkles
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icônes par type de mesure
const measureIcons = {
  'CUSTOMS_DUTY': Banknote,
  'VAT': Percent,
  'LEVY': Building2,
  'EXCISE': AlertCircle,
  'OTHER_TAX': FileText
};

// Couleurs par type de mesure
const measureColors = {
  'CUSTOMS_DUTY': 'text-amber-400 bg-amber-400/10 border-amber-400/30',
  'VAT': 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  'LEVY': 'text-purple-400 bg-purple-400/10 border-purple-400/30',
  'EXCISE': 'text-red-400 bg-red-400/10 border-red-400/30',
  'OTHER_TAX': 'text-gray-400 bg-gray-400/10 border-gray-400/30'
};

// Icônes par type de formalité
const requirementIcons = {
  'IMPORT_DECLARATION': FileText,
  'CERTIFICATE': FileCheck,
  'LICENSE': Shield,
  'PERMIT': FileCheck,
  'INSPECTION': AlertCircle,
  'AUTHORIZATION': CheckCircle2
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
    sensitivity: 'Sensibilité',
    measures: 'Mesures Tarifaires',
    measuresDesc: 'Droits et taxes applicables',
    taxCode: 'Code',
    taxName: 'Intitulé',
    taxRate: 'Taux',
    zlecafRate: 'Taux ZLECAf',
    requirements: 'Formalités Administratives',
    requirementsDesc: 'Documents et autorisations requis',
    document: 'Document',
    authority: 'Autorité émettrice',
    mandatory: 'Obligatoire',
    fiscalAdvantages: 'Avantages Fiscaux ZLECAf',
    fiscalAdvantagesDesc: 'Réductions tarifaires sous l\'AfCFTA',
    condition: 'Condition',
    reduction: 'Réduction',
    summary: 'Synthèse',
    totalNPF: 'Total NPF',
    totalZLECAf: 'Total ZLECAf',
    savings: 'Économie',
    processingTime: 'Temps de réponse',
    noData: 'Données non disponibles',
    loading: 'Chargement...',
    notAvailable: 'Le moteur réglementaire n\'est pas disponible pour ce pays',
    viewMore: 'Voir plus',
    viewLess: 'Voir moins',
    normal: 'normal',
    sensitive: 'sensible',
    excluded: 'exclu'
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
    sensitivity: 'Sensitivity',
    measures: 'Tariff Measures',
    measuresDesc: 'Applicable duties and taxes',
    taxCode: 'Code',
    taxName: 'Name',
    taxRate: 'Rate',
    zlecafRate: 'AfCFTA Rate',
    requirements: 'Administrative Formalities',
    requirementsDesc: 'Required documents and authorizations',
    document: 'Document',
    authority: 'Issuing authority',
    mandatory: 'Mandatory',
    fiscalAdvantages: 'AfCFTA Fiscal Advantages',
    fiscalAdvantagesDesc: 'Tariff reductions under AfCFTA',
    condition: 'Condition',
    reduction: 'Reduction',
    summary: 'Summary',
    totalNPF: 'Total MFN',
    totalZLECAf: 'Total AfCFTA',
    savings: 'Savings',
    processingTime: 'Response time',
    noData: 'Data not available',
    loading: 'Loading...',
    notAvailable: 'Regulatory engine not available for this country',
    viewMore: 'View more',
    viewLess: 'View less',
    normal: 'normal',
    sensitive: 'sensitive',
    excluded: 'excluded'
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
  const [availableCountries, setAvailableCountries] = useState([]);
  const [expandedSections, setExpandedSections] = useState({
    measures: true,
    requirements: true,
    advantages: true
  });

  const t = texts[language];

  // Charger la liste des pays disponibles
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await axios.get(`${API}/regulatory-engine/countries`);
        setAvailableCountries(response.data.countries || []);
      } catch (err) {
        console.warn('Could not fetch regulatory engine countries:', err);
        setAvailableCountries([]);
      }
    };
    fetchCountries();
  }, []);

  // Charger les données quand le pays ou le code change
  useEffect(() => {
    const fetchData = async () => {
      if (!countryCode || !hsCode || hsCode.length < 6) {
        setData(null);
        setError(null);
        return;
      }

      // Convertir en ISO3 si nécessaire
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

    if (availableCountries.length > 0 || countryCode) {
      fetchData();
    }
  }, [countryCode, hsCode, availableCountries, t.noData, t.notAvailable, onDataLoaded]);

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

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getSensitivityColor = (sensitivity) => {
    switch (sensitivity) {
      case 'sensitive': return 'bg-orange-500/20 text-orange-400 border-orange-400/30';
      case 'excluded': return 'bg-red-500/20 text-red-400 border-red-400/30';
      default: return 'bg-green-500/20 text-green-400 border-green-400/30';
    }
  };

  if (loading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-8 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-400">{t.loading}</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-8 text-center">
          <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400">{error || t.noData}</p>
          {availableCountries.length > 0 && (
            <p className="text-slate-500 text-sm mt-2">
              {language === 'fr' ? 'Pays disponibles : ' : 'Available countries: '}
              {availableCountries.join(', ')}
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  const { commodity, measures, requirements, fiscal_advantages, total_npf_pct, total_zlecaf_pct, savings_pct, processing_time_ms } = data;

  return (
    <div className="space-y-4" data-testid="regulatory-details-panel">
      {/* En-tête avec synthèse */}
      <Card className="bg-gradient-to-r from-amber-900/30 to-slate-800/50 border-amber-500/30">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Sparkles className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <CardTitle className="text-xl text-amber-400">{t.title}</CardTitle>
                <CardDescription className="text-slate-400">{t.subtitle}</CardDescription>
              </div>
            </div>
            {processing_time_ms && (
              <Badge variant="outline" className="bg-slate-700/50 text-slate-300 border-slate-600">
                <Clock className="w-3 h-3 mr-1" />
                {processing_time_ms.toFixed(1)}ms
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Synthèse visuelle */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/20">
              <p className="text-red-400 text-sm font-medium">{t.totalNPF}</p>
              <p className="text-2xl font-bold text-red-300">{total_npf_pct?.toFixed(1) || 0}%</p>
            </div>
            <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/20">
              <p className="text-green-400 text-sm font-medium">{t.totalZLECAf}</p>
              <p className="text-2xl font-bold text-green-300">{total_zlecaf_pct?.toFixed(1) || 0}%</p>
            </div>
            <div className="bg-amber-500/10 rounded-lg p-4 border border-amber-500/20">
              <p className="text-amber-400 text-sm font-medium">{t.savings}</p>
              <p className="text-2xl font-bold text-amber-300">-{savings_pct?.toFixed(1) || 0}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Informations Produit */}
      {commodity && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-400" />
              <CardTitle className="text-lg text-white">{t.productInfo}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-slate-500 text-xs uppercase">{t.nationalCode}</p>
                <p className="text-white font-mono text-lg">{commodity.national_code}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs uppercase">{t.hs6Code}</p>
                <p className="text-white font-mono">{commodity.hs6}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs uppercase">{t.chapter}</p>
                <p className="text-white">{commodity.chapter}</p>
              </div>
              {commodity.category && (
                <div>
                  <p className="text-slate-500 text-xs uppercase">{t.category}</p>
                  <p className="text-white capitalize">{commodity.category}</p>
                </div>
              )}
              {commodity.unit && (
                <div>
                  <p className="text-slate-500 text-xs uppercase">{t.unit}</p>
                  <p className="text-white">{commodity.unit}</p>
                </div>
              )}
              <div>
                <p className="text-slate-500 text-xs uppercase">{t.sensitivity}</p>
                <Badge className={getSensitivityColor(commodity.sensitivity)}>
                  {t[commodity.sensitivity] || commodity.sensitivity}
                </Badge>
              </div>
            </div>
            <Separator className="my-4 bg-slate-700" />
            <p className="text-slate-300">{commodity.description_fr}</p>
            {commodity.description_en && language === 'en' && (
              <p className="text-slate-400 text-sm mt-1">{commodity.description_en}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Mesures Tarifaires */}
      {measures && measures.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
            onClick={() => toggleSection('measures')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Banknote className="w-5 h-5 text-amber-400" />
                <div>
                  <CardTitle className="text-lg text-white">{t.measures}</CardTitle>
                  <CardDescription className="text-slate-400">{t.measuresDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                  {measures.length}
                </Badge>
                {expandedSections.measures ? 
                  <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                }
              </div>
            </div>
          </CardHeader>
          {expandedSections.measures && (
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700 hover:bg-slate-700/30">
                    <TableHead className="text-slate-400">{t.taxCode}</TableHead>
                    <TableHead className="text-slate-400">{t.taxName}</TableHead>
                    <TableHead className="text-slate-400 text-right">{t.taxRate}</TableHead>
                    <TableHead className="text-slate-400 text-right">{t.zlecafRate}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {measures.map((measure, idx) => {
                    const Icon = measureIcons[measure.measure_type] || FileText;
                    const colorClass = measureColors[measure.measure_type] || measureColors.OTHER_TAX;
                    return (
                      <TableRow key={idx} className="border-slate-700 hover:bg-slate-700/30">
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={`p-1.5 rounded ${colorClass}`}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <span className="font-mono text-white">{measure.code}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-300">{measure.name_fr}</TableCell>
                        <TableCell className="text-right">
                          <span className="text-red-400 font-medium">{measure.rate_pct}%</span>
                        </TableCell>
                        <TableCell className="text-right">
                          {measure.is_zlecaf_applicable ? (
                            <span className="text-green-400 font-medium">{measure.zlecaf_rate_pct ?? measure.rate_pct}%</span>
                          ) : (
                            <span className="text-slate-500">{measure.rate_pct}%</span>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          )}
        </Card>
      )}

      {/* Formalités Administratives */}
      {requirements && requirements.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
            onClick={() => toggleSection('requirements')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-blue-400" />
                <div>
                  <CardTitle className="text-lg text-white">{t.requirements}</CardTitle>
                  <CardDescription className="text-slate-400">{t.requirementsDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                  {requirements.length}
                </Badge>
                {expandedSections.requirements ? 
                  <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                }
              </div>
            </div>
          </CardHeader>
          {expandedSections.requirements && (
            <CardContent>
              <div className="space-y-3">
                {requirements.map((req, idx) => {
                  const Icon = requirementIcons[req.requirement_type] || FileText;
                  return (
                    <div 
                      key={idx} 
                      className="flex items-start gap-4 p-4 bg-slate-700/30 rounded-lg border border-slate-700"
                    >
                      <div className="p-2 bg-blue-500/20 rounded-lg shrink-0">
                        <Icon className="w-5 h-5 text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-slate-400 text-sm">{req.code}</span>
                          {req.is_mandatory && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                              {t.mandatory}
                            </Badge>
                          )}
                        </div>
                        <p className="text-white font-medium">{req.document_fr}</p>
                        {req.issuing_authority && (
                          <p className="text-slate-400 text-sm mt-1">
                            <Building2 className="w-3 h-3 inline mr-1" />
                            {req.issuing_authority}
                          </p>
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

      {/* Avantages Fiscaux ZLECAf */}
      {fiscal_advantages && fiscal_advantages.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader 
            className="pb-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
            onClick={() => toggleSection('advantages')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-400" />
                <div>
                  <CardTitle className="text-lg text-white">{t.fiscalAdvantages}</CardTitle>
                  <CardDescription className="text-slate-400">{t.fiscalAdvantagesDesc}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
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
            <CardContent>
              <div className="space-y-3">
                {fiscal_advantages.map((adv, idx) => (
                  <div 
                    key={idx} 
                    className="p-4 bg-gradient-to-r from-green-500/10 to-slate-700/30 rounded-lg border border-green-500/20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                        {adv.tax_code}
                      </Badge>
                      <span className="text-green-400 font-bold text-lg">
                        {adv.reduced_rate_pct}%
                      </span>
                    </div>
                    <p className="text-slate-300">{adv.condition_fr}</p>
                    {adv.condition_en && language === 'en' && (
                      <p className="text-slate-400 text-sm mt-1">{adv.condition_en}</p>
                    )}
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
