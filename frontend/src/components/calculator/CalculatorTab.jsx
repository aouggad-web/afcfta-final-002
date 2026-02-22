import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Progress } from '../ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { toast } from '../../hooks/use-toast';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import SmartHSSearch from '../SmartHSSearch';
import { Package, ChevronDown, ChevronUp, Sparkles, AlertTriangle, Info, Calculator, Globe, FileText, CheckCircle, ClipboardList } from 'lucide-react';
import DetailedCalculationBreakdown from './DetailedCalculationBreakdown';
import { DetailedTaxTable, SavingsHighlight, TaxComparisonBarChart, TaxDistributionPieChart } from './TaxBreakdownChart';
import MultiCountryComparison from './MultiCountryComparison';
import './calculator.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Drapeaux par code ISO2
const countryFlagsISO2 = {
  'DZ': '🇩🇿', 'AO': '🇦🇴', 'BJ': '🇧🇯', 'BW': '🇧🇼', 'BF': '🇧🇫', 'BI': '🇧🇮', 'CM': '🇨🇲', 'CV': '🇨🇻',
  'CF': '🇨🇫', 'TD': '🇹🇩', 'KM': '🇰🇲', 'CG': '🇨🇬', 'CD': '🇨🇩', 'CI': '🇨🇮', 'DJ': '🇩🇯', 'EG': '🇪🇬',
  'GQ': '🇬🇶', 'ER': '🇪🇷', 'SZ': '🇸🇿', 'ET': '🇪🇹', 'GA': '🇬🇦', 'GM': '🇬🇲', 'GH': '🇬🇭', 'GN': '🇬🇳',
  'GW': '🇬🇼', 'KE': '🇰🇪', 'LS': '🇱🇸', 'LR': '🇱🇷', 'LY': '🇱🇾', 'MG': '🇲🇬', 'MW': '🇲🇼', 'ML': '🇲🇱',
  'MR': '🇲🇷', 'MU': '🇲🇺', 'MA': '🇲🇦', 'MZ': '🇲🇿', 'NA': '🇳🇦', 'NE': '🇳🇪', 'NG': '🇳🇬', 'RW': '🇷🇼',
  'ST': '🇸🇹', 'SN': '🇸🇳', 'SC': '🇸🇨', 'SL': '🇸🇱', 'SO': '🇸🇴', 'ZA': '🇿🇦', 'SS': '🇸🇸', 'SD': '🇸🇩',
  'TZ': '🇹🇿', 'TG': '🇹🇬', 'TN': '🇹🇳', 'UG': '🇺🇬', 'ZM': '🇿🇲', 'ZW': '🇿🇼'
};

// Fonction pour obtenir le drapeau (supporte ISO2 et ISO3)
const getFlag = (code) => {
  if (!code) return '🌍';
  // Si c'est ISO3, convertir en ISO2 pour le drapeau
  const ISO3_TO_ISO2 = {
    'DZA': 'DZ', 'AGO': 'AO', 'BEN': 'BJ', 'BWA': 'BW', 'BFA': 'BF', 'BDI': 'BI', 'CMR': 'CM', 'CPV': 'CV',
    'CAF': 'CF', 'TCD': 'TD', 'COM': 'KM', 'COG': 'CG', 'COD': 'CD', 'CIV': 'CI', 'DJI': 'DJ', 'EGY': 'EG',
    'GNQ': 'GQ', 'ERI': 'ER', 'SWZ': 'SZ', 'ETH': 'ET', 'GAB': 'GA', 'GMB': 'GM', 'GHA': 'GH', 'GIN': 'GN',
    'GNB': 'GW', 'KEN': 'KE', 'LSO': 'LS', 'LBR': 'LR', 'LBY': 'LY', 'MDG': 'MG', 'MWI': 'MW', 'MLI': 'ML',
    'MRT': 'MR', 'MUS': 'MU', 'MAR': 'MA', 'MOZ': 'MZ', 'NAM': 'NA', 'NER': 'NE', 'NGA': 'NG', 'RWA': 'RW',
    'STP': 'ST', 'SEN': 'SN', 'SYC': 'SC', 'SLE': 'SL', 'SOM': 'SO', 'ZAF': 'ZA', 'SSD': 'SS', 'SDN': 'SD',
    'TZA': 'TZ', 'TGO': 'TG', 'TUN': 'TN', 'UGA': 'UG', 'ZMB': 'ZM', 'ZWE': 'ZW'
  };
  const iso2 = code.length === 3 ? ISO3_TO_ISO2[code] : code;
  return countryFlagsISO2[iso2] || '🌍';
};

const countryFlags = countryFlagsISO2;

export default function CalculatorTab({ countries, language = 'fr' }) {
  const [originCountry, setOriginCountry] = useState('');
  const [destinationCountry, setDestinationCountry] = useState('');
  const [hsCode, setHsCode] = useState('');
  const [value, setValue] = useState('');
  const [result, setResult] = useState(null);
  const [detailedResult, setDetailedResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showHSBrowser, setShowHSBrowser] = useState(false);
  const [showDetailedBreakdown, setShowDetailedBreakdown] = useState(false);
  const [hs6TariffInfo, setHs6TariffInfo] = useState(null);
  const [subPositions, setSubPositions] = useState(null);
  const [useSmartSearch, setUseSmartSearch] = useState(true);
  const [ruleOfOrigin, setRuleOfOrigin] = useState(null);
  const [selectedSubPositionDesc, setSelectedSubPositionDesc] = useState(null);

  const texts = {
    fr: {
      originCountry: "Pays d'origine",
      partnerCountry: "Pays partenaire",
      hsCodeLabel: "Code HS (6-12 chiffres)",
      hsCodeHint: "6 chiffres = HS international | 8-12 chiffres = sous-position nationale",
      valueLabel: "Valeur de la marchandise (USD)",
      calculateBtn: "Calculer avec Données Officielles",
      calculatorTitle: "Calculateur ZLECAf Complet",
      calculatorDesc: "Calculs basés sur les données officielles des organismes internationaux",
      rulesOrigin: "Règles d'Origine ZLECAf",
      missingFields: "Champs manquants",
      fillAllFields: "Veuillez remplir tous les champs",
      invalidHsCode: "Code HS invalide",
      hsCodeMust6to12: "Le code HS doit contenir entre 6 et 12 chiffres",
      calculationSuccess: "Calcul réussi",
      potentialSavings: "Économie potentielle",
      calculationError: "Erreur de calcul",
      calculating: "Calcul en cours...",
      detailedResults: "Résultats Détaillés",
      completeComparison: "Comparaison Complète: Valeur + DD + TVA + Autres Taxes",
      merchandiseValue: "Valeur marchandise",
      customsDuties: "Droits douane",
      vat: "TVA",
      otherTaxes: "Autres taxes",
      nfpTariff: "Tarif NPF",
      zlecafTariff: "Tarif ZLECAf",
      totalSavings: "ÉCONOMIE TOTALE (avec toutes les taxes)",
      totalSavingsPercent: "d'économie totale",
      totalCostComparison: "Sur un coût total de",
      vs: "vs",
      calculationJournal: "Journal de Calcul Détaillé (Ordre Officiel)",
      step: "Étape",
      component: "Composant",
      base: "Base",
      rate: "Taux",
      amount: "Montant",
      cumulative: "Cumulatif",
      legalRef: "Référence Légale",
      ruleType: "Type",
      requirement: "Exigence",
      minRegionalContent: "Contenu régional minimum",
      african: "africain",
      sectorPrefix: "Secteur",
      hsCodeSelectorTitle: "Sélecteur de Code SH6",
      hsCodeSelectorDesc: "Recherchez ou parcourez les codes du Système Harmonisé",
      browseHS: "Parcourir les codes HS",
      hideHSBrowser: "Masquer le navigateur",
      // Nouvelles traductions SH6
      hs6TariffInfo: "Tarif SH6 Précis",
      hs6TariffApplied: "Tarif spécifique SH6 appliqué",
      chapterTariffApplied: "Tarif par chapitre appliqué",
      tariffPrecision: "Précision tarifaire",
      productDescription: "Description produit",
      normalRate: "Taux NPF",
      zlecafRate: "Taux ZLECAf",
      savingsRate: "Économie",
      hs6DataSource: "Source: OMC ITC, CNUCED TRAINS, WITS",
      // Sous-positions nationales
      subPositionApplied: "Sous-position nationale appliquée",
      subPositionInfo: "Tarif Sous-Position Nationale",
      subPositionCode: "Code national",
      subPositionsAvailable: "sous-positions disponibles",
      varyingRates: "Taux variables selon la sous-position",
      viewAllSubPositions: "Voir toutes les sous-positions",
      precisionHigh: "Haute précision",
      precisionMedium: "Précision moyenne"
    },
    en: {
      originCountry: "Origin Country",
      partnerCountry: "Partner Country",
      hsCodeLabel: "HS Code (6-12 digits)",
      hsCodeHint: "6 digits = international HS | 8-12 digits = national sub-position",
      valueLabel: "Merchandise Value (USD)",
      calculateBtn: "Calculate with Official Data",
      calculatorTitle: "Complete AfCFTA Calculator",
      calculatorDesc: "Calculations based on official data from international organizations",
      rulesOrigin: "AfCFTA Rules of Origin",
      missingFields: "Missing Fields",
      fillAllFields: "Please fill in all fields",
      invalidHsCode: "Invalid HS Code",
      hsCodeMust6to12: "HS code must contain between 6 and 12 digits",
      calculationSuccess: "Calculation Successful",
      potentialSavings: "Potential Savings",
      calculationError: "Calculation Error",
      calculating: "Calculating...",
      detailedResults: "Detailed Results",
      completeComparison: "Complete Comparison: Value + Duties + VAT + Other Taxes",
      merchandiseValue: "Merchandise Value",
      customsDuties: "Customs Duties",
      vat: "VAT",
      otherTaxes: "Other Taxes",
      nfpTariff: "MFN Tariff",
      zlecafTariff: "AfCFTA Tariff",
      totalSavings: "TOTAL SAVINGS (including all taxes)",
      totalSavingsPercent: "total savings",
      totalCostComparison: "On a total cost of",
      vs: "vs",
      calculationJournal: "Detailed Calculation Journal (Official Order)",
      step: "Step",
      component: "Component",
      base: "Base",
      rate: "Rate",
      amount: "Amount",
      cumulative: "Cumulative",
      legalRef: "Legal Reference",
      ruleType: "Type",
      requirement: "Requirement",
      minRegionalContent: "Minimum regional content",
      african: "African",
      sectorPrefix: "Sector",
      hsCodeSelectorTitle: "HS6 Code Selector",
      hsCodeSelectorDesc: "Search or browse Harmonized System codes",
      browseHS: "Browse HS codes",
      hideHSBrowser: "Hide browser",
      // HS6 translations
      hs6TariffInfo: "Precise HS6 Tariff",
      hs6TariffApplied: "Specific HS6 tariff applied",
      chapterTariffApplied: "Chapter tariff applied",
      tariffPrecision: "Tariff precision",
      productDescription: "Product description",
      normalRate: "MFN Rate",
      zlecafRate: "AfCFTA Rate",
      savingsRate: "Savings",
      hs6DataSource: "Source: WTO ITC, UNCTAD TRAINS, WITS",
      // National sub-positions
      subPositionApplied: "National sub-position applied",
      subPositionInfo: "National Sub-Position Tariff",
      subPositionCode: "National code",
      subPositionsAvailable: "sub-positions available",
      varyingRates: "Rates vary by sub-position",
      viewAllSubPositions: "View all sub-positions",
      precisionHigh: "High precision",
      precisionMedium: "Medium precision"
    }
  };

  const t = texts[language];

  const getSectorName = (hsCode) => {
    const sector = hsCode.substring(0, 2);
    const sectorNames = {
      fr: {
        '01': 'Animaux vivants', '02': 'Viandes', '03': 'Poissons', '04': 'Lait & Œufs',
        '05': 'Autres produits animaux', '06': 'Plantes', '07': 'Légumes', '08': 'Fruits',
        '09': 'Café/Thé', '10': 'Céréales', '27': 'Combustibles minéraux', '84': 'Machines',
        '85': 'Électrique', '87': 'Véhicules'
      },
      en: {
        '01': 'Live Animals', '02': 'Meat', '03': 'Fish', '04': 'Dairy & Eggs',
        '05': 'Other Animal Products', '06': 'Plants', '07': 'Vegetables', '08': 'Fruits',
        '09': 'Coffee/Tea', '10': 'Cereals', '27': 'Mineral Fuels', '84': 'Machinery',
        '85': 'Electrical', '87': 'Vehicles'
      }
    };
    return sectorNames[language][sector] || `${t.sectorPrefix} ${sector}`;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getCountryName = (code) => {
    const country = countries.find(c => c.code === code);
    return country ? country.name : code;
  };

  const calculateTariff = async () => {
    if (!originCountry || !destinationCountry || !hsCode || !value) {
      toast({
        title: t.missingFields,
        description: t.fillAllFields,
        variant: "destructive"
      });
      return;
    }

    // Validation: code HS entre 6 et 12 chiffres
    const cleanHsCode = hsCode.replace(/[.\s]/g, '');
    if (cleanHsCode.length < 6 || cleanHsCode.length > 12) {
      toast({
        title: t.invalidHsCode,
        description: t.hsCodeMust6to12,
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    
    // Mapping ISO2 -> ISO3 pour les pays
    const ISO2_TO_ISO3 = {
      'DZ': 'DZA', 'AO': 'AGO', 'BJ': 'BEN', 'BW': 'BWA', 'BF': 'BFA', 'BI': 'BDI', 'CM': 'CMR', 'CV': 'CPV',
      'CF': 'CAF', 'TD': 'TCD', 'KM': 'COM', 'CG': 'COG', 'CD': 'COD', 'CI': 'CIV', 'DJ': 'DJI', 'EG': 'EGY',
      'GQ': 'GNQ', 'ER': 'ERI', 'SZ': 'SWZ', 'ET': 'ETH', 'GA': 'GAB', 'GM': 'GMB', 'GH': 'GHA', 'GN': 'GIN',
      'GW': 'GNB', 'KE': 'KEN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY', 'MG': 'MDG', 'MW': 'MWI', 'ML': 'MLI',
      'MR': 'MRT', 'MU': 'MUS', 'MA': 'MAR', 'MZ': 'MOZ', 'NA': 'NAM', 'NE': 'NER', 'NG': 'NGA', 'RW': 'RWA',
      'ST': 'STP', 'SN': 'SEN', 'SC': 'SYC', 'SL': 'SLE', 'SO': 'SOM', 'ZA': 'ZAF', 'SS': 'SSD', 'SD': 'SDN',
      'TZ': 'TZA', 'TG': 'TGO', 'TN': 'TUN', 'UG': 'UGA', 'ZM': 'ZMB', 'ZW': 'ZWE'
    };
    
    // Convertir les codes pays en ISO3
    const destISO3 = destinationCountry.length === 2 ? ISO2_TO_ISO3[destinationCountry] || destinationCountry : destinationCountry;
    const originISO3 = originCountry.length === 2 ? ISO2_TO_ISO3[originCountry] || originCountry : originCountry;
    
    try {
      // PRIORITÉ 1: Essayer d'utiliser les données tarifaires AUTHENTIQUES
      let authenticResult = null;
      let useAuthenticData = false;
      
      try {
        const authenticResponse = await axios.get(
          `${API}/authentic-tariffs/calculate/${destISO3}/${cleanHsCode}?value=${parseFloat(value)}&language=${language}`
        );
        authenticResult = authenticResponse.data;
        useAuthenticData = true;
        console.log('✅ Using AUTHENTIC tariff data for', destISO3);
      } catch (authError) {
        console.log('ℹ️ Authentic tariff data not available for', destISO3, '- falling back to calculated data');
      }
      
      if (useAuthenticData && authenticResult) {
        // Transformer les données authentiques au format attendu par l'UI
        const npfCalc = authenticResult.npf_calculation || {};
        const zlecafCalc = authenticResult.zlecaf_calculation || {};
        const savings = authenticResult.savings || {};
        const rates = authenticResult.rates || {};
        
        // Construire le résultat au format compatible
        const transformedResult = {
          origin_country: originCountry,
          destination_country: destinationCountry,
          hs_code: cleanHsCode,
          hs6_code: authenticResult.hs6 || cleanHsCode.substring(0, 6),
          value: parseFloat(value),
          
          // Tarifs
          normal_tariff_rate: (rates.dd_rate_pct || 0) / 100,
          normal_tariff_amount: npfCalc.dd?.amount || 0,
          zlecaf_tariff_rate: 0, // DD exempt under ZLECAf
          zlecaf_tariff_amount: zlecafCalc.dd?.amount || 0,
          
          // TVA
          normal_vat_rate: (rates.vat_rate_pct || 0) / 100,
          normal_vat_amount: npfCalc.vat?.amount || 0,
          zlecaf_vat_rate: (rates.vat_rate_pct || 0) / 100,
          zlecaf_vat_amount: zlecafCalc.vat?.amount || 0,
          
          // Autres taxes
          normal_other_taxes_total: npfCalc.other_taxes?.amount || 0,
          zlecaf_other_taxes_total: zlecafCalc.other_taxes?.amount || 0,
          
          // Totaux
          normal_total_cost: npfCalc.total_to_pay || 0,
          zlecaf_total_cost: zlecafCalc.total_to_pay || 0,
          
          // Économies
          savings: savings.amount || 0,
          savings_percentage: savings.percentage || 0,
          total_savings_with_taxes: savings.amount || 0,
          total_savings_percentage: savings.percentage || 0,
          
          // Précision et source
          tariff_precision: 'authentic_data',
          data_source: 'authentic_tariff',
          
          // Détails des taxes
          taxes_detail: authenticResult.taxes_detail || [],
          
          // Avantages fiscaux
          fiscal_advantages: authenticResult.fiscal_advantages || [],
          
          // Formalités administratives
          administrative_formalities: authenticResult.administrative_formalities || [],
          
          // Sous-positions
          has_sub_positions: authenticResult.has_sub_positions || false,
          sub_position_count: authenticResult.sub_position_count || 0,
          sub_position: authenticResult.sub_position,
          
          // Règles d'origine (placeholder - à récupérer séparément si nécessaire)
          rules_of_origin: {
            rule: 'ZLECAf Rules of Origin',
            requirement: language === 'fr' ? 'Certificat d\'origine ZLECAf requis' : 'AfCFTA Certificate of Origin required',
            regional_content: 40
          },
          
          // Journal de calcul NPF
          normal_calculation_journal: [
            { step: 1, component: 'Valeur CIF', base: parseFloat(value), rate: '-', amount: parseFloat(value), cumulative: parseFloat(value), legal_ref: 'Incoterms 2020' },
            { step: 2, component: 'Droits de Douane (DD)', base: parseFloat(value), rate: `${rates.dd_rate_pct || 0}%`, amount: npfCalc.dd?.amount || 0, cumulative: parseFloat(value) + (npfCalc.dd?.amount || 0), legal_ref: `Tarif ${destISO3}` },
            { step: 3, component: 'TVA', base: npfCalc.vat?.base || parseFloat(value), rate: `${rates.vat_rate_pct || 0}%`, amount: npfCalc.vat?.amount || 0, cumulative: npfCalc.total_to_pay || 0, legal_ref: `CGI ${destISO3}` }
          ],
          
          // Journal de calcul ZLECAf
          zlecaf_calculation_journal: [
            { step: 1, component: 'Valeur CIF', base: parseFloat(value), rate: '-', amount: parseFloat(value), cumulative: parseFloat(value), legal_ref: 'Incoterms 2020' },
            { step: 2, component: 'Droits de Douane ZLECAf', base: parseFloat(value), rate: '0%', amount: 0, cumulative: parseFloat(value), legal_ref: 'AfCFTA Art. 8 - Exonération DD' },
            { step: 3, component: 'TVA', base: zlecafCalc.vat?.base || parseFloat(value), rate: `${rates.vat_rate_pct || 0}%`, amount: zlecafCalc.vat?.amount || 0, cumulative: zlecafCalc.total_to_pay || 0, legal_ref: `CGI ${destISO3}` }
          ],
          
          computation_order_ref: `Données tarifaires officielles ${destISO3} - Format enhanced_v2`,
          last_verified: authenticResult.generated_at ? new Date(authenticResult.generated_at).toISOString().split('T')[0] : '2025-02',
          confidence_level: 'very_high'
        };
        
        setResult(transformedResult);
        setDetailedResult(authenticResult);
        setShowDetailedBreakdown(true);
        
        // Récupérer les sous-positions authentiques
        const hs6 = cleanHsCode.substring(0, 6);
        try {
          const subPosResponse = await axios.get(`${API}/authentic-tariffs/country/${destISO3}/sub-positions/${hs6}?language=${language}`);
          setSubPositions(subPosResponse.data);
        } catch (subPosError) {
          setSubPositions(null);
        }
        
        // Info SH6 depuis les données authentiques
        setHs6TariffInfo({
          code: hs6,
          description: authenticResult.description,
          has_specific_tariff: true
        });
        
        toast({
          title: `✅ ${t.calculationSuccess}`,
          description: `${t.potentialSavings}: ${formatCurrency(savings.amount || 0)} (Données officielles ${destISO3})`,
        });
        
      } else {
        // FALLBACK: Utiliser l'ancien endpoint si pas de données authentiques
        const response = await axios.post(`${API}/calculate-tariff`, {
          origin_country: originCountry,
          destination_country: destinationCountry,
          hs_code: cleanHsCode,
          value: parseFloat(value)
        });
        
        setResult(response.data);
        
        // Récupérer le calcul détaillé NPF vs ZLECAf
        try {
          const detailedResponse = await axios.get(
            `${API}/calculate/detailed/${destinationCountry}/${cleanHsCode}?value=${parseFloat(value)}&language=${language}`
          );
          setDetailedResult(detailedResponse.data);
          setShowDetailedBreakdown(true);
        } catch (detailError) {
          console.warn('Detailed calculation not available:', detailError.message);
          setDetailedResult(null);
        }
        
        // Récupérer les sous-positions si disponibles pour le pays de destination
        const hs6 = cleanHsCode.substring(0, 6);
        try {
          const subPosResponse = await axios.get(`${API}/tariffs/sub-positions/${destinationCountry}/${hs6}?language=${language}`);
          setSubPositions(subPosResponse.data);
        } catch (subPosError) {
          setSubPositions(null);
        }
        
        // Récupérer les informations SH6 spécifiques si disponibles
        try {
          const hs6Response = await axios.get(`${API}/hs6-tariffs/code/${hs6}?language=${language}`);
          setHs6TariffInfo(hs6Response.data);
        } catch (hs6Error) {
          setHs6TariffInfo(null);
        }
        
        toast({
          title: t.calculationSuccess,
          description: `${t.potentialSavings}: ${formatCurrency(response.data.savings)}`,
        });
      }
    } catch (error) {
      console.error('Calculation error:', error);
      toast({
        title: t.calculationError,
        description: error.response?.data?.detail || t.calculationError,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Onglets Principal */}
      <Tabs defaultValue="calculator" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="calculator" className="flex items-center gap-2" data-testid="calculator-single-tab">
            <Calculator className="w-4 h-4" />
            {language === 'fr' ? 'Calculateur' : 'Calculator'}
          </TabsTrigger>
          <TabsTrigger value="compare" className="flex items-center gap-2" data-testid="calculator-compare-tab">
            <Globe className="w-4 h-4" />
            {language === 'fr' ? 'Comparaison Multi-Pays' : 'Multi-Country Comparison'}
          </TabsTrigger>
        </TabsList>
        
        {/* Onglet Calculateur Standard */}
        <TabsContent value="calculator">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" style={{ minHeight: '600px' }}>
            {/* Formulaire de calcul */}
            <Card className="shadow-2xl" style={{ minHeight: '400px', borderTop: '4px solid #D4AF37' }}>
              <CardHeader style={{ background: 'linear-gradient(135deg, rgba(193,122,43,0.2), rgba(212,175,55,0.1))' }}>
                <CardTitle className="flex items-center space-x-2 text-2xl" style={{ color: '#D4AF37' }}>
                  <span>📊</span>
                  <span>{t.calculatorTitle}</span>
                </CardTitle>
                <CardDescription style={{ color: '#A0AAB4' }} className="font-semibold">
                  {t.calculatorDesc}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="calculator-grid-2">
                  {/* Pays d'origine */}
                  <div className="calculator-form-group">
                    <label>{t.originCountry}</label>
                    <select
                      className="afcfta-select"
                      value={originCountry}
                      onChange={(e) => setOriginCountry(e.target.value)}
                      data-testid="origin-country-select"
                    >
                      <option value="">{t.originCountry}</option>
                      {countries && countries.map((country) => (
                        <option key={country.code} value={country.code}>
                          {getFlag(country.iso2 || country.code)} {country.name} ({country.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Pays partenaire */}
                  <div className="calculator-form-group">
                    <label>{t.partnerCountry}</label>
                    <select
                      className="afcfta-select"
                      value={destinationCountry}
                      onChange={(e) => setDestinationCountry(e.target.value)}
                      data-testid="destination-country-select"
                    >
                      <option value="">{t.partnerCountry}</option>
                      {countries && countries.map((country) => (
                        <option key={country.code} value={country.code}>
                          {getFlag(country.iso2 || country.code)} {country.name} ({country.code})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="hs-code" className="flex items-center gap-2">
                <Package className="w-4 h-4" />
                {t.hsCodeLabel}
              </Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setUseSmartSearch(!useSmartSearch)}
                className="text-xs text-purple-600 hover:text-purple-700"
              >
                <Sparkles className="w-3 h-3 mr-1" />
                {useSmartSearch ? 'Mode simple' : 'Recherche intelligente'}
              </Button>
            </div>
            
            {useSmartSearch ? (
              <SmartHSSearch
                value={hsCode}
                onChange={setHsCode}
                destinationCountry={destinationCountry}
                language={language}
                onSubPositionSelect={(code, desc) => {
                  setHsCode(code);
                  setSelectedSubPositionDesc(desc);
                }}
                onRuleOfOriginLoad={setRuleOfOrigin}
              />
            ) : (
              <div className="calculator-form-group">
                <input
                  type="text"
                  placeholder={language === 'fr' ? "Ex: 090111, 870323, 8517" : "Ex: 090111, 870323, 8517"}
                  value={hsCode}
                  onChange={(e) => setHsCode(e.target.value.replace(/[^0-9]/g, '').slice(0, 12))}
                  className="font-mono"
                  style={{ fontSize: '16px', letterSpacing: '1px' }}
                  data-testid="hs-code-simple-input"
                />
                <p style={{ color: '#A0AAB4', fontSize: '12px', marginTop: '4px', fontStyle: 'italic' }}>{t.hsCodeHint}</p>
              </div>
            )}
            
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowHSBrowser(!showHSBrowser)}
              className="w-full mt-2"
              style={{ 
                background: 'transparent', 
                border: '1px solid rgba(212,175,55,0.3)', 
                color: '#D4AF37',
                borderRadius: '10px'
              }}
              data-testid="toggle-hs-browser"
            >
              {showHSBrowser ? (
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

          {/* HS Code Browser Panel */}
          {showHSBrowser && (
            <div style={{ border: '1px solid rgba(212,175,55,0.2)', borderRadius: '10px', overflow: 'hidden' }}>
              <HSCodeBrowser
                onSelect={(code) => {
                  setHsCode(code.code);
                  setShowHSBrowser(false);
                }}
                language={language}
                showRulesOfOrigin={true}
              />
            </div>
          )}

          <div className="calculator-form-group">
            <label>{t.valueLabel}</label>
            <input
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="100000"
              min="0"
            />
          </div>

          <Button 
            onClick={calculateTariff}
            disabled={loading}
            data-testid="calculate-tariff-button"
            className="w-full bg-gradient-to-r from-red-600 via-yellow-500 to-green-600 text-white font-bold text-lg py-6 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all"
          >
            {loading ? `⏳ ${t.calculating}` : `🧮 ${t.calculateBtn}`}
          </Button>
        </CardContent>
      </Card>

      {/* Résultats complets avec visualisations */}
      {result && (
        <div className="space-y-4">
          <Card className="border-l-4 border-l-green-500 shadow-xl bg-gradient-to-br from-white to-green-50">
            <CardHeader className="bg-gradient-to-r from-green-600 to-yellow-500 text-white rounded-t-lg">
              <CardTitle className="flex items-center space-x-2 text-2xl">
                <span>💰</span>
                <span>{t.detailedResults}</span>
              </CardTitle>
              <CardDescription className="text-yellow-100 font-semibold">
                {countryFlags[result.origin_country]} {getCountryName(result.origin_country)} → {countryFlags[result.destination_country]} {getCountryName(result.destination_country)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 pt-6 results-container">
              {/* Information sur les DONNÉES AUTHENTIQUES */}
              {result.data_source === 'authentic_tariff' && (
                <div className="result-section bg-gradient-to-r from-emerald-50 via-green-50 to-teal-50 p-5 rounded-xl border-2 border-emerald-400 shadow-lg" data-testid="authentic-data-badge">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md">
                      <span className="text-2xl">✓</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold text-emerald-800 text-lg">
                          {language === 'fr' ? 'Données Tarifaires Officielles' : 'Official Tariff Data'}
                        </h4>
                        <Badge className="bg-emerald-600 text-white px-3 py-1">
                          {language === 'fr' ? 'Vérifié' : 'Verified'}
                        </Badge>
                      </div>
                      <p className="text-gray-700 text-sm mb-3">
                        {language === 'fr' 
                          ? `Calcul basé sur les tarifs douaniers officiels du ${getCountryName(destinationCountry)} avec ${result.sub_position_count || 0} sous-positions nationales.`
                          : `Calculation based on official customs tariffs of ${getCountryName(destinationCountry)} with ${result.sub_position_count || 0} national sub-headings.`}
                      </p>
                      
                      {/* Détail des taxes authentiques */}
                      {result.taxes_detail && result.taxes_detail.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {result.taxes_detail.map((tax, idx) => (
                            <Badge key={idx} variant="outline" className="bg-white border-emerald-300 text-emerald-700">
                              {tax.tax}: {tax.rate}%
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-xs text-gray-500 mb-1">
                        {language === 'fr' ? 'Confiance' : 'Confidence'}
                      </p>
                      <Badge className="bg-gradient-to-r from-emerald-500 to-green-600 text-white text-lg px-4 py-2">
                        {language === 'fr' ? 'Très élevée' : 'Very High'}
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Avantages fiscaux ZLECAf */}
                  {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
                    <div className="mt-4 p-3 bg-white/70 rounded-lg border border-emerald-200">
                      <p className="text-sm font-semibold text-emerald-800 mb-2">
                        {language === 'fr' ? '🎯 Avantages ZLECAf applicables:' : '🎯 Applicable AfCFTA advantages:'}
                      </p>
                      <ul className="space-y-1">
                        {result.fiscal_advantages.map((adv, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-emerald-500">✓</span>
                            <span>{language === 'fr' ? adv.condition_fr : adv.condition_en}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Formalités administratives */}
                  {result.administrative_formalities && result.administrative_formalities.length > 0 && (
                    <div className="mt-3 p-3 bg-amber-50/70 rounded-lg border border-amber-200">
                      <p className="text-sm font-semibold text-amber-800 mb-2">
                        {language === 'fr' ? '📋 Documents requis:' : '📋 Required documents:'}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {result.administrative_formalities.map((form, idx) => (
                          <Badge key={idx} variant="outline" className="bg-white border-amber-300 text-amber-700 text-xs">
                            {language === 'fr' ? form.document_fr : form.document_en}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TABLEAU DÉTAILLÉ DE TOUTES LES TAXES AVEC INTITULÉS */}
              {result.data_source === 'authentic_tariff' && result.taxes_detail && result.taxes_detail.length > 0 && (
                <div className="result-section bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden" data-testid="all-taxes-table">
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
                    <h4 className="font-bold text-lg text-blue-900 flex items-center gap-2">
                      <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">📋</span>
                      {language === 'fr' ? 'Détail Complet des Taxes' : 'Complete Tax Breakdown'}
                    </h4>
                    <p className="text-sm text-blue-700 mt-1">
                      {language === 'fr' 
                        ? `${result.taxes_detail.length} taxes applicables pour ${getCountryName(destinationCountry)}`
                        : `${result.taxes_detail.length} applicable taxes for ${getCountryName(destinationCountry)}`}
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-0">
                    {/* Colonne NPF */}
                    <div className="border-r border-gray-200">
                      <div className="p-3 bg-red-50 border-b border-red-100">
                        <h5 className="font-bold text-red-800 flex items-center gap-2">
                          <span>🚫</span>
                          {language === 'fr' ? 'Régime NPF (Sans préférence)' : 'MFN Regime (No preference)'}
                        </h5>
                      </div>
                      <div className="p-4">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 border-b">
                              <th className="pb-2">{language === 'fr' ? 'Taxe' : 'Tax'}</th>
                              <th className="pb-2 text-center">{language === 'fr' ? 'Taux' : 'Rate'}</th>
                              <th className="pb-2 text-right">{language === 'fr' ? 'Montant' : 'Amount'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b bg-gray-50">
                              <td className="py-2 font-medium">
                                <span className="font-mono">CIF</span>
                                <span className="text-xs text-gray-500 block">{language === 'fr' ? 'Valeur en douane' : 'Customs value'}</span>
                              </td>
                              <td className="py-2 text-center">-</td>
                              <td className="py-2 text-right font-mono font-bold">{formatCurrency(parseFloat(value))}</td>
                            </tr>
                            {result.taxes_detail.map((tax, idx) => {
                              const taxAmount = parseFloat(value) * (tax.rate / 100);
                              return (
                                <tr key={idx} className="border-b hover:bg-gray-50">
                                  <td className="py-2">
                                    <div className="flex items-center gap-2">
                                      <span 
                                        className="w-3 h-3 rounded-full flex-shrink-0"
                                        style={{ 
                                          backgroundColor: tax.tax.toLowerCase().includes('d.d') || tax.tax.toLowerCase().includes('douane') ? '#dc2626' :
                                            tax.tax.toLowerCase().includes('tva') || tax.tax.toLowerCase().includes('vat') ? '#f59e0b' :
                                            tax.tax.toLowerCase().includes('cedeao') ? '#10b981' :
                                            tax.tax.toLowerCase().includes('ciss') ? '#ec4899' :
                                            '#8b5cf6'
                                        }}
                                      />
                                      <div>
                                        <span className="font-mono font-medium">{tax.tax}</span>
                                        {tax.observation && tax.observation !== tax.tax && (
                                          <span className="text-xs text-gray-500 block">{tax.observation}</span>
                                        )}
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-2 text-center font-mono">{tax.rate}%</td>
                                  <td className="py-2 text-right font-mono">{formatCurrency(taxAmount)}</td>
                                </tr>
                              );
                            })}
                            <tr className="bg-red-50 font-bold">
                              <td className="py-3" colSpan={2}>
                                {language === 'fr' ? 'TOTAL À PAYER' : 'TOTAL TO PAY'}
                              </td>
                              <td className="py-3 text-right font-mono text-lg text-red-700">
                                {formatCurrency(result.normal_total_cost)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    
                    {/* Colonne ZLECAf */}
                    <div>
                      <div className="p-3 bg-emerald-50 border-b border-emerald-100">
                        <h5 className="font-bold text-emerald-800 flex items-center gap-2">
                          <span>✅</span>
                          {language === 'fr' ? 'Régime ZLECAf (Préférentiel)' : 'AfCFTA Regime (Preferential)'}
                        </h5>
                      </div>
                      <div className="p-4">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 border-b">
                              <th className="pb-2">{language === 'fr' ? 'Taxe' : 'Tax'}</th>
                              <th className="pb-2 text-center">{language === 'fr' ? 'Taux' : 'Rate'}</th>
                              <th className="pb-2 text-right">{language === 'fr' ? 'Montant' : 'Amount'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b bg-gray-50">
                              <td className="py-2 font-medium">
                                <span className="font-mono">CIF</span>
                                <span className="text-xs text-gray-500 block">{language === 'fr' ? 'Valeur en douane' : 'Customs value'}</span>
                              </td>
                              <td className="py-2 text-center">-</td>
                              <td className="py-2 text-right font-mono font-bold">{formatCurrency(parseFloat(value))}</td>
                            </tr>
                            {result.taxes_detail.map((tax, idx) => {
                              const isDD = tax.tax.toLowerCase().includes('d.d') || tax.tax.toLowerCase().includes('douane');
                              const effectiveRate = isDD ? 0 : tax.rate;
                              const taxAmount = parseFloat(value) * (effectiveRate / 100);
                              return (
                                <tr key={idx} className={`border-b hover:bg-gray-50 ${isDD ? 'bg-emerald-50' : ''}`}>
                                  <td className="py-2">
                                    <div className="flex items-center gap-2">
                                      <span 
                                        className="w-3 h-3 rounded-full flex-shrink-0"
                                        style={{ 
                                          backgroundColor: isDD ? '#10b981' :
                                            tax.tax.toLowerCase().includes('tva') || tax.tax.toLowerCase().includes('vat') ? '#f59e0b' :
                                            tax.tax.toLowerCase().includes('cedeao') ? '#10b981' :
                                            tax.tax.toLowerCase().includes('ciss') ? '#ec4899' :
                                            '#8b5cf6'
                                        }}
                                      />
                                      <div>
                                        <span className={`font-mono font-medium ${isDD ? 'text-emerald-700' : ''}`}>{tax.tax}</span>
                                        {tax.observation && tax.observation !== tax.tax && (
                                          <span className="text-xs text-gray-500 block">{tax.observation}</span>
                                        )}
                                        {isDD && (
                                          <Badge className="mt-1 bg-emerald-100 text-emerald-700 text-xs">
                                            {language === 'fr' ? 'Exonéré ZLECAf' : 'AfCFTA Exempt'}
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-2 text-center font-mono">
                                    {isDD ? (
                                      <span>
                                        <span className="line-through text-gray-400">{tax.rate}%</span>
                                        <span className="text-emerald-600 font-bold ml-1">0%</span>
                                      </span>
                                    ) : (
                                      <span>{tax.rate}%</span>
                                    )}
                                  </td>
                                  <td className={`py-2 text-right font-mono ${isDD ? 'text-emerald-600 font-bold' : ''}`}>
                                    {formatCurrency(taxAmount)}
                                  </td>
                                </tr>
                              );
                            })}
                            <tr className="bg-emerald-50 font-bold">
                              <td className="py-3" colSpan={2}>
                                {language === 'fr' ? 'TOTAL À PAYER' : 'TOTAL TO PAY'}
                              </td>
                              <td className="py-3 text-right font-mono text-lg text-emerald-700">
                                {formatCurrency(result.zlecaf_total_cost)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                  
                  {/* Économies */}
                  <div className="p-4 bg-gradient-to-r from-emerald-500 to-green-600 text-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">💰</span>
                        <div>
                          <p className="text-sm opacity-90">{language === 'fr' ? 'Économies grâce à la ZLECAf' : 'Savings thanks to AfCFTA'}</p>
                          <p className="text-2xl font-bold">{formatCurrency(result.savings || (result.normal_total_cost - result.zlecaf_total_cost))}</p>
                        </div>
                      </div>
                      <Badge className="bg-white/20 text-white text-lg px-4 py-2">
                        -{result.savings_percentage || ((result.normal_total_cost - result.zlecaf_total_cost) / result.normal_total_cost * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                </div>
              )}

              {/* GRAPHIQUES AVANCÉS - Répartition des taxes */}
              {result.data_source === 'authentic_tariff' && result.taxes_detail && result.taxes_detail.length > 0 && (
                <div className="result-section grid md:grid-cols-2 gap-4">
                  {/* Graphique en camembert NPF */}
                  <TaxDistributionPieChart 
                    taxes={result.taxes_detail} 
                    cifValue={parseFloat(value)} 
                    regime="npf" 
                    language={language}
                  />
                  
                  {/* Graphique en camembert ZLECAf */}
                  <TaxDistributionPieChart 
                    taxes={result.taxes_detail.map(t => ({
                      ...t,
                      rate: (t.tax.toLowerCase().includes('d.d') || t.tax.toLowerCase().includes('douane')) ? 0 : t.rate
                    }))} 
                    cifValue={parseFloat(value)} 
                    regime="zlecaf" 
                    language={language}
                  />
                </div>
              )}

              {/* SECTION FORMALITÉS ET DOCUMENTS NÉCESSAIRES */}
              {result.data_source === 'authentic_tariff' && (
                <div className="result-section bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden" data-testid="formalities-section">
                  <div className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 border-b">
                    <h4 className="font-bold text-lg text-amber-900 flex items-center gap-2">
                      <ClipboardList className="w-5 h-5" />
                      {language === 'fr' ? 'Formalités et Documents Nécessaires' : 'Required Formalities and Documents'}
                    </h4>
                    <p className="text-sm text-amber-700 mt-1">
                      {language === 'fr' 
                        ? `Documents requis pour l'importation vers ${getCountryName(destinationCountry)}`
                        : `Documents required for import to ${getCountryName(destinationCountry)}`}
                    </p>
                  </div>
                  
                  <div className="p-4 space-y-4">
                    {/* Documents obligatoires */}
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-amber-600" />
                        {language === 'fr' ? 'Documents Obligatoires' : 'Mandatory Documents'}
                      </h5>
                      <div className="grid md:grid-cols-2 gap-3">
                        {/* Documents standards toujours requis */}
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-amber-600 font-bold text-sm">1</span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">
                              {language === 'fr' ? 'Facture Commerciale' : 'Commercial Invoice'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {language === 'fr' ? 'Détail des marchandises, prix, conditions de vente' : 'Details of goods, prices, terms of sale'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-amber-600 font-bold text-sm">2</span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">
                              {language === 'fr' ? 'Liste de Colisage' : 'Packing List'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {language === 'fr' ? 'Poids, dimensions, nombre de colis' : 'Weight, dimensions, number of packages'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-amber-600 font-bold text-sm">3</span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">
                              {language === 'fr' ? 'Connaissement / LTA' : 'Bill of Lading / AWB'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {language === 'fr' ? 'Document de transport maritime ou aérien' : 'Sea or air transport document'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-amber-600 font-bold text-sm">4</span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">
                              {language === 'fr' ? 'Déclaration en Douane' : 'Customs Declaration'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {language === 'fr' ? 'Formulaire DAU ou équivalent national' : 'SAD form or national equivalent'}
                            </p>
                          </div>
                        </div>
                        
                        {/* Documents spécifiques du pays */}
                        {result.administrative_formalities && result.administrative_formalities.map((form, idx) => (
                          <div key={idx} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                            <div className="w-8 h-8 bg-amber-200 rounded-lg flex items-center justify-center flex-shrink-0">
                              <span className="text-amber-700 font-bold text-sm">{5 + idx}</span>
                            </div>
                            <div>
                              <p className="font-medium text-amber-900">
                                {language === 'fr' ? form.document_fr : form.document_en}
                              </p>
                              {form.code && (
                                <p className="text-xs text-amber-600">Code: {form.code}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {/* Documents ZLECAf */}
                    <div className="pt-4 border-t border-gray-200">
                      <h5 className="font-semibold text-emerald-800 mb-3 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        {language === 'fr' ? 'Documents pour Bénéficier du Tarif ZLECAf' : 'Documents to Benefit from AfCFTA Rate'}
                      </h5>
                      <div className="grid md:grid-cols-2 gap-3">
                        <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          </div>
                          <div>
                            <p className="font-medium text-emerald-900">
                              {language === 'fr' ? 'Certificat d\'Origine ZLECAf' : 'AfCFTA Certificate of Origin'}
                            </p>
                            <p className="text-xs text-emerald-600">
                              {language === 'fr' 
                                ? 'Délivré par l\'autorité compétente du pays exportateur'
                                : 'Issued by competent authority of exporting country'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          </div>
                          <div>
                            <p className="font-medium text-emerald-900">
                              {language === 'fr' ? 'Déclaration du Fournisseur' : 'Supplier Declaration'}
                            </p>
                            <p className="text-xs text-emerald-600">
                              {language === 'fr' 
                                ? 'Attestant l\'origine africaine du produit'
                                : 'Attesting African origin of the product'}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Avantages fiscaux */}
                      {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
                        <div className="mt-4 p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg border border-emerald-200">
                          <p className="font-semibold text-emerald-800 mb-2 flex items-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            {language === 'fr' ? 'Avantages obtenus avec ces documents:' : 'Benefits obtained with these documents:'}
                          </p>
                          <ul className="space-y-2">
                            {result.fiscal_advantages.map((adv, idx) => (
                              <li key={idx} className="flex items-center gap-2 text-sm">
                                <span className="w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs">✓</span>
                                <span className="text-gray-700">{language === 'fr' ? adv.condition_fr : adv.condition_en}</span>
                                {adv.rate !== undefined && adv.rate === 0 && (
                                  <Badge className="bg-emerald-100 text-emerald-700 text-xs ml-auto">
                                    {language === 'fr' ? 'Exonération totale' : 'Full exemption'}
                                  </Badge>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    
                    {/* Règles d'origine */}
                    {result.rules_of_origin && (
                      <div className="pt-4 border-t border-gray-200">
                        <h5 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                          <Info className="w-4 h-4 text-blue-600" />
                          {language === 'fr' ? 'Critères d\'Origine à Respecter' : 'Origin Criteria to Meet'}
                        </h5>
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <p className="text-sm text-blue-600 mb-1">{language === 'fr' ? 'Règle applicable:' : 'Applicable rule:'}</p>
                              <p className="font-semibold text-blue-900">{result.rules_of_origin.rule}</p>
                            </div>
                            <div>
                              <p className="text-sm text-blue-600 mb-1">{language === 'fr' ? 'Contenu régional minimum:' : 'Minimum regional content:'}</p>
                              <p className="font-semibold text-blue-900">{result.rules_of_origin.regional_content}% {language === 'fr' ? 'africain' : 'African'}</p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 mt-3 pt-3 border-t border-blue-200">
                            <span className="font-medium">{language === 'fr' ? 'Exigence:' : 'Requirement:'}</span> {result.rules_of_origin.requirement}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Note importante */}
                    <div className="mt-4 p-3 bg-gray-100 rounded-lg text-xs text-gray-600">
                      <p className="flex items-start gap-2">
                        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>
                          {language === 'fr' 
                            ? 'Ces documents doivent être présentés au moment du dédouanement. Des documents supplémentaires peuvent être requis selon la nature des produits (certificats sanitaires, licences, etc.).'
                            : 'These documents must be presented at customs clearance. Additional documents may be required depending on the nature of the products (sanitary certificates, licenses, etc.).'}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Information sur la sous-position nationale si utilisée */}
              {result.tariff_precision === 'sub_position' && (
                <div className="result-section tariff-info-section bg-gradient-to-r from-purple-50 to-indigo-50 p-5 rounded-xl border border-purple-200 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold text-purple-800">{t.subPositionInfo}</h4>
                        <Badge className="bg-purple-600 text-white text-xs">{t.precisionHigh}</Badge>
                      </div>
                      <p className="font-mono text-lg font-bold text-purple-900 mb-1">{result.sub_position_used}</p>
                      {result.sub_position_description && (
                        <p className="text-gray-600 text-sm">{result.sub_position_description}</p>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2 flex-shrink-0">
                      <div className="bg-red-50 p-3 rounded-lg text-center border border-red-100">
                        <p className="text-xs text-red-500 font-medium">{t.normalRate}</p>
                        <p className="font-bold text-red-600 text-lg">{(result.normal_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-center border border-green-100">
                        <p className="text-xs text-green-500 font-medium">{t.zlecafRate}</p>
                        <p className="font-bold text-green-600 text-lg">{(result.zlecaf_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Information sur le tarif SH6 précis */}
              {result.tariff_precision === 'hs6_country' && (
                <div className="result-section tariff-info-section bg-gradient-to-r from-blue-50 to-cyan-50 p-5 rounded-xl border border-blue-200 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold text-blue-800">{t.hs6TariffInfo}</h4>
                        <Badge className="bg-blue-600 text-white text-xs">{t.hs6TariffApplied}</Badge>
                      </div>
                      <p className="font-semibold text-gray-800">{hs6TariffInfo?.description || `Code ${result.hs6_code}`}</p>
                      <p className="text-blue-600 text-sm font-mono mt-1">Code: {result.hs6_code}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 flex-shrink-0">
                      <div className="bg-red-50 p-3 rounded-lg text-center border border-red-100">
                        <p className="text-xs text-red-500 font-medium">{t.normalRate}</p>
                        <p className="font-bold text-red-600 text-lg">{(result.normal_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-center border border-green-100">
                        <p className="text-xs text-green-500 font-medium">{t.zlecafRate}</p>
                        <p className="font-bold text-green-600 text-lg">{(result.zlecaf_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  {result.available_sub_positions_count > 0 && !result.rate_warning?.has_variation && (
                    <p className="text-xs text-blue-600 mt-3 pl-16">
                      {result.available_sub_positions_count} {t.subPositionsAvailable}
                    </p>
                  )}
                </div>
              )}

              {/* WARNING: Taux variables selon sous-positions nationales */}
              {result.rate_warning && result.rate_warning.has_variation && (
                <div 
                  className="rate-warning-box bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 p-5 rounded-xl border-l-4 border-amber-500 shadow-lg" 
                  data-testid="rate-warning-box"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-amber-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-lg text-amber-800 mb-2">
                        {language === 'fr' ? 'Attention: Taux de droits variables' : 'Warning: Variable duty rates'}
                      </h4>
                      <p className="text-gray-700 text-sm leading-relaxed mb-4">
                        {language === 'fr' 
                          ? `Ce code SH6 (${result.hs6_code}) comporte plusieurs sous-positions nationales avec des taux différents.`
                          : `This HS6 code (${result.hs6_code}) has multiple national sub-headings with different rates.`}
                      </p>
                      
                      {/* Visualisation des taux min/max/utilisé */}
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="rate-card bg-green-50 p-3 rounded-lg text-center border border-green-200 shadow-sm">
                          <p className="text-xs text-green-600 font-medium uppercase tracking-wide">{language === 'fr' ? 'Minimum' : 'Minimum'}</p>
                          <p className="text-2xl font-bold text-green-700 mt-1">{result.rate_warning.min_rate_pct}</p>
                        </div>
                        <div className="rate-card bg-blue-50 p-3 rounded-lg text-center border-2 border-blue-400 shadow-md relative">
                          <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                            <Badge className="bg-blue-600 text-white text-xs px-2">
                              {language === 'fr' ? 'Utilisé' : 'Used'}
                            </Badge>
                          </div>
                          <p className="text-xs text-blue-600 font-medium uppercase tracking-wide mt-2">{language === 'fr' ? 'Actuel' : 'Current'}</p>
                          <p className="text-2xl font-bold text-blue-700 mt-1">{result.rate_warning.rate_used_pct}</p>
                        </div>
                        <div className="rate-card bg-red-50 p-3 rounded-lg text-center border border-red-200 shadow-sm">
                          <p className="text-xs text-red-600 font-medium uppercase tracking-wide">{language === 'fr' ? 'Maximum' : 'Maximum'}</p>
                          <p className="text-2xl font-bold text-red-700 mt-1">{result.rate_warning.max_rate_pct}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2 bg-amber-100/50 p-3 rounded-lg">
                        <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-800">
                          {language === 'fr' 
                            ? 'Pour un calcul précis, sélectionnez la sous-position correspondant exactement à votre produit ci-dessous.'
                            : 'For an accurate calculation, select the sub-heading that exactly matches your product below.'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Sous-positions détaillées - Affiché uniquement si taux variables */}
              {result.sub_positions_details && result.sub_positions_details.length > 0 && result.rate_warning?.has_variation && (
                <div className="result-section bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  <div 
                    className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-purple-100 cursor-pointer"
                    onClick={() => document.getElementById('sub-positions-details')?.toggleAttribute('open')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                          <Package className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <h4 className="font-bold text-purple-800">
                            {language === 'fr' ? 'Sous-positions disponibles' : 'Available sub-headings'}
                          </h4>
                          <p className="text-sm text-purple-600">
                            {language === 'fr' ? 'Cliquez pour sélectionner le taux exact' : 'Click to select exact rate'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-purple-600 text-white">{result.sub_positions_details.length}</Badge>
                        <Badge className="bg-gradient-to-r from-green-500 to-red-500 text-white text-xs">
                          {result.rate_warning.min_rate_pct} → {result.rate_warning.max_rate_pct}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <details id="sub-positions-details" className="sub-positions-container" open>
                    <summary className="sr-only">Toggle sub-positions</summary>
                    <div className="p-4 space-y-2 max-h-80 overflow-y-auto">
                      {result.sub_positions_details.map((sp, idx) => {
                        const isMinRate = sp.dd_rate === result.rate_warning?.min_rate;
                        const isMaxRate = sp.dd_rate === result.rate_warning?.max_rate;
                        const isCurrentRate = sp.dd_rate === result.rate_warning?.rate_used;
                        
                        return (
                          <div 
                            key={idx} 
                            className={`sub-position-item p-3 rounded-lg cursor-pointer flex items-center justify-between border transition-all ${
                              isCurrentRate 
                                ? 'bg-blue-50 border-blue-300 shadow-sm' 
                                : 'bg-gray-50 border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                            }`}
                            onClick={() => {
                              setHsCode(sp.code);
                              toast({
                                title: language === 'fr' ? 'Sous-position sélectionnée' : 'Sub-heading selected',
                                description: sp.code,
                              });
                            }}
                          >
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                              <code className="font-mono font-bold text-purple-800 bg-purple-100 px-2 py-1 rounded text-sm">
                                {sp.code}
                              </code>
                              <span className="text-gray-700 text-sm truncate">
                                {language === 'fr' ? sp.description_fr : sp.description_en}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                              {isCurrentRate && (
                                <Badge className="bg-blue-100 text-blue-700 text-xs">
                                  {language === 'fr' ? 'Actuel' : 'Current'}
                                </Badge>
                              )}
                              <Badge className={`text-white font-bold px-3 ${
                                isMinRate ? 'bg-green-500' :
                                isMaxRate ? 'bg-red-500' :
                                isCurrentRate ? 'bg-blue-500' : 'bg-gray-500'
                              }`}>
                                {sp.dd_rate_pct}
                              </Badge>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </details>
                </div>
              )}
              
              {/* Badge tarif par chapitre si pas de SH6 spécifique */}
              {result.tariff_precision === 'chapter' && (
                <div className="result-section tariff-info-section bg-gray-50 p-4 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-gray-500" />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm text-gray-600">{t.chapterTariffApplied}</span>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-gray-600">{t.sectorPrefix} {result.hs_code?.substring(0, 2)}</Badge>
                      <Badge variant="outline" className="text-amber-600 border-amber-300">{t.precisionMedium}</Badge>
                    </div>
                  </div>
                </div>
              )}

              {/* Graphique comparaison complète avec TOUTES les taxes */}
              <div className="chart-container result-section bg-white p-5 rounded-xl shadow-md border border-gray-100">
                <h4 className="font-bold text-lg mb-4 text-gray-800 flex items-center gap-2">
                  <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">📊</span>
                  {t.completeComparison}
                </h4>
                <ResponsiveContainer width="100%" height={280} debounce={300}>
                  <BarChart data={[
                    { 
                      name: t.nfpTariff, 
                      [t.merchandiseValue]: result.value,
                      [t.customsDuties]: result.normal_tariff_amount,
                      [t.vat]: result.normal_vat_amount,
                      [t.otherTaxes]: result.normal_other_taxes_total
                    },
                    { 
                      name: t.zlecafTariff, 
                      [t.merchandiseValue]: result.value,
                      [t.customsDuties]: result.zlecaf_tariff_amount,
                      [t.vat]: result.zlecaf_vat_amount,
                      [t.otherTaxes]: result.zlecaf_other_taxes_total
                    }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Legend />
                    <Bar dataKey={t.merchandiseValue} stackId="a" fill="#60a5fa" />
                    <Bar dataKey={t.customsDuties} stackId="a" fill="#ef4444" />
                    <Bar dataKey={t.vat} stackId="a" fill="#f59e0b" />
                    <Bar dataKey={t.otherTaxes} stackId="a" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Économies TOTALES */}
              <div className="savings-section result-section text-center bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-6 rounded-xl shadow-lg border border-green-200">
                <p className="text-base font-semibold text-gray-600 mb-3">{t.totalSavings}</p>
                <p className="text-4xl md:text-5xl font-extrabold text-green-600 mb-4">
                  {formatCurrency(result.total_savings_with_taxes)}
                </p>
                <div className="inline-flex items-center gap-2 bg-green-600 text-white px-5 py-2 rounded-full shadow-md">
                  <Sparkles className="w-5 h-5" />
                  <span className="text-xl font-bold">{result.total_savings_percentage.toFixed(1)}%</span>
                  <span className="text-sm opacity-90">{t.totalSavingsPercent}</span>
                </div>
                <Progress value={result.total_savings_percentage} className="w-full mt-5 h-2 bg-green-100" />
                <p className="text-sm text-gray-500 mt-4">
                  {t.totalCostComparison} <span className="font-semibold text-red-600">{formatCurrency(result.normal_total_cost)}</span> (NPF) 
                  {' '}{t.vs}{' '}
                  <span className="font-semibold text-green-600">{formatCurrency(result.zlecaf_total_cost)}</span> (ZLECAf)
                </p>
              </div>

              {/* Journal de calcul détaillé */}
              {result.normal_calculation_journal && (
                <Card className="journal-container result-section shadow-md border-0 overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-100 py-4">
                    <CardTitle className="text-lg font-bold text-gray-800 flex items-center gap-3">
                      <div className="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center">
                        <Package className="w-5 h-5 text-purple-600" />
                      </div>
                      {t.calculationJournal}
                    </CardTitle>
                    <CardDescription className="text-gray-500 text-sm mt-1">
                      {result.computation_order_ref}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{t.step}</TableHead>
                            <TableHead>{t.component}</TableHead>
                            <TableHead>{t.base}</TableHead>
                            <TableHead>{t.rate}</TableHead>
                            <TableHead>{t.amount}</TableHead>
                            <TableHead>{t.cumulative}</TableHead>
                            <TableHead>{t.legalRef}</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.normal_calculation_journal.map((entry, index) => (
                            <TableRow key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                              <TableCell className="font-bold">{entry.step}</TableCell>
                              <TableCell className="font-semibold">{entry.component}</TableCell>
                              <TableCell>{formatCurrency(entry.base)}</TableCell>
                              <TableCell className="font-semibold text-red-600">{entry.rate}</TableCell>
                              <TableCell className="font-bold text-blue-600">{formatCurrency(entry.amount)}</TableCell>
                              <TableCell className="font-bold">{formatCurrency(entry.cumulative)}</TableCell>
                              <TableCell className="text-xs">
                                {entry.legal_ref_url ? (
                                  <a href={entry.legal_ref_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                    {entry.legal_ref}
                                  </a>
                                ) : (
                                  entry.legal_ref || '-'
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Règles d'origine avec style africain */}
              <div className="bg-gradient-to-r from-amber-100 to-orange-100 p-6 rounded-xl border-l-4 border-orange-500 shadow-lg">
                <h4 className="font-bold text-xl text-orange-800 mb-3 flex items-center gap-2">
                  <span>📜</span> {t.rulesOrigin}
                </h4>
                <div className="bg-white p-4 rounded-lg space-y-2">
                  <p className="text-sm text-amber-800 font-semibold">
                    <strong className="text-orange-600">{t.ruleType}:</strong> {result.rules_of_origin.rule}
                  </p>
                  <p className="text-sm text-amber-800 font-semibold">
                    <strong className="text-orange-600">{t.requirement}:</strong> {result.rules_of_origin.requirement}
                  </p>
                  <div className="mt-3">
                    <Progress 
                      value={result.rules_of_origin.regional_content} 
                      className="w-full h-3"
                    />
                    <p className="text-sm text-amber-700 mt-2 font-bold text-center">
                      🌍 {t.minRegionalContent}: {result.rules_of_origin.regional_content}% {t.african}
                    </p>
                  </div>
                </div>
              </div>

              {/* Bouton pour afficher/masquer le calcul détaillé - UNIQUEMENT pour données estimées (non authentiques) */}
              {detailedResult && detailedResult.data_source !== 'authentic_tariff' && (
                <div className="mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setShowDetailedBreakdown(!showDetailedBreakdown)}
                    className="w-full flex items-center justify-center gap-2 py-3 border-2 border-purple-200 hover:bg-purple-50"
                    data-testid="toggle-detailed-breakdown"
                  >
                    <Calculator className="h-5 w-5 text-purple-600" />
                    <span className="font-semibold text-purple-700">
                      {showDetailedBreakdown 
                        ? (language === 'fr' ? 'Masquer le Détail du Calcul' : 'Hide Calculation Details')
                        : (language === 'fr' ? 'Voir le Détail du Calcul NPF vs ZLECAf' : 'View NPF vs AfCFTA Calculation Details')}
                    </span>
                    {showDetailedBreakdown ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                  
                  {showDetailedBreakdown && (
                    <div className="mt-4 animate-in slide-in-from-top-2">
                      <DetailedCalculationBreakdown 
                        result={detailedResult} 
                        language={language} 
                      />
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
          </div>
        </TabsContent>
        
        {/* Onglet Comparaison Multi-Pays */}
        <TabsContent value="compare">
          <MultiCountryComparison language={language} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
