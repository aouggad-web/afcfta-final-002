import React, { useState, useEffect, useCallback } from 'react';
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
import { Package, ChevronDown, ChevronUp, Sparkles, AlertTriangle, Info, Calculator, Globe, FileText, CheckCircle, ClipboardList, Scale } from 'lucide-react';
import DetailedCalculationBreakdown from './DetailedCalculationBreakdown';
import { DetailedTaxTable, SavingsHighlight, TaxComparisonBarChart, TaxDistributionPieChart } from './TaxBreakdownChart';
import MultiCountryComparison from './MultiCountryComparison';
import RegulatoryDetailsPanel from './RegulatoryDetailsPanel';
import TariffDownloads from '../tools/TariffDownloads';
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
  const [countryTariffProfile, setCountryTariffProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  const fetchCountryTariffProfile = useCallback(async (countryCode) => {
    if (!countryCode) {
      setCountryTariffProfile(null);
      return;
    }
    setLoadingProfile(true);
    try {
      const response = await axios.get(`${API}/tariff-data/${countryCode}?limit=1`);
      setCountryTariffProfile(response.data);
    } catch (error) {
      console.error('Error fetching country tariff profile:', error);
      setCountryTariffProfile(null);
    } finally {
      setLoadingProfile(false);
    }
  }, []);

  const handleDestinationChange = useCallback((value) => {
    setDestinationCountry(value);
    fetchCountryTariffProfile(value);
  }, [fetchCountryTariffProfile]);

  useEffect(() => {
    if (destinationCountry) {
      fetchCountryTariffProfile(destinationCountry);
    }
  }, [destinationCountry, fetchCountryTariffProfile]);

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

  const COUNTRIES_WITH_AUTHENTIC_DATA = new Set([
    'DZA','MAR','GHA','KEN','EGY','ETH','CIV','NGA','ZAF','SEN','CMR','TUN',
    'UGA','TZA','RWA','MUS','BEN','BFA','MLI','NER','TGO','GIN',
    'GAB','COG','TCD','CAF','BWA','SWZ','NAM','LSO','BDI','SSD','COD'
  ]);

  const TRADE_BLOCS = {
    'BEN': 'CEDEAO', 'BFA': 'AES', 'MLI': 'AES', 'NER': 'AES', 'TGO': 'CEDEAO', 'GIN': 'CEDEAO',
    'SEN': 'CEDEAO', 'CIV': 'CEDEAO', 'NGA': 'CEDEAO', 'GHA': 'CEDEAO',
    'CMR': 'CEMAC', 'GAB': 'CEMAC', 'COG': 'CEMAC', 'TCD': 'CEMAC', 'CAF': 'CEMAC',
    'KEN': 'EAC', 'TZA': 'EAC', 'UGA': 'EAC', 'RWA': 'EAC', 'BDI': 'EAC', 'SSD': 'EAC', 'COD': 'EAC',
    'ZAF': 'SACU', 'BWA': 'SACU', 'SWZ': 'SACU', 'NAM': 'SACU', 'LSO': 'SACU',
    'DZA': '', 'MAR': '', 'TUN': '', 'EGY': '', 'ETH': '', 'MUS': ''
  };

  const getBlocColor = (bloc) => {
    const colors = {
      'CEDEAO': 'bg-amber-100 text-amber-700 border-amber-300',
      'AES': 'bg-orange-100 text-orange-700 border-orange-300',
      'CEMAC': 'bg-blue-100 text-blue-700 border-blue-300',
      'EAC': 'bg-green-100 text-green-700 border-green-300',
      'SACU': 'bg-purple-100 text-purple-700 border-purple-300',
    };
    return colors[bloc] || 'bg-gray-100 text-gray-600 border-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Onglets Principal */}
      <Tabs defaultValue="calculator" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="calculator" className="flex items-center gap-2" data-testid="calculator-single-tab">
            <Calculator className="w-4 h-4" />
            {language === 'fr' ? 'Calculateur' : 'Calculator'}
          </TabsTrigger>
          <TabsTrigger value="regulatory" className="flex items-center gap-2" data-testid="calculator-regulatory-tab">
            <Scale className="w-4 h-4" />
            {language === 'fr' ? 'Réglementation' : 'Regulations'}
          </TabsTrigger>
          <TabsTrigger value="compare" className="flex items-center gap-2" data-testid="calculator-compare-tab">
            <Globe className="w-4 h-4" />
            {language === 'fr' ? 'Comparaison Multi-Pays' : 'Multi-Country Comparison'}
          </TabsTrigger>
        </TabsList>
        
        {/* Onglet Calculateur Standard */}
        <TabsContent value="calculator">
          <div className="space-y-6">
      
      {/* === FORMULAIRE DE CALCUL === */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl translate-x-1/2 -translate-y-1/2"></div>
        
        <CardHeader className="relative">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-amber-500/20">
              <Calculator className="w-8 h-8 text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-2xl text-white">{t.calculatorTitle}</CardTitle>
              <CardDescription className="text-slate-400 text-base mt-1">{t.calculatorDesc}</CardDescription>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="relative space-y-6">
          {/* Sélection des pays */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pays d'origine */}
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-xs text-blue-400">1</span>
                {t.originCountry}
              </Label>
              <Select value={originCountry} onValueChange={setOriginCountry}>
                <SelectTrigger 
                  data-testid="origin-country-select"
                  className="h-12 bg-slate-800/50 border-slate-600 hover:border-blue-500/50 transition-colors"
                >
                  <SelectValue placeholder={t.originCountry} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map((country) => {
                    const hasData = COUNTRIES_WITH_AUTHENTIC_DATA.has(country.code);
                    const bloc = TRADE_BLOCS[country.code];
                    return (
                      <SelectItem key={country.code} value={country.code}>
                        <span className="flex items-center gap-2">
                          <span className="text-lg">{getFlag(country.iso2 || country.code)}</span>
                          <span>{country.name}</span>
                          {hasData && <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>}
                          {bloc && <span className={`text-[10px] px-1.5 rounded border font-medium ${getBlocColor(bloc)}`}>{bloc}</span>}
                        </span>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Pays de destination */}
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-xs text-amber-400">2</span>
                {t.partnerCountry}
              </Label>
              <Select value={destinationCountry} onValueChange={handleDestinationChange}>
                <SelectTrigger 
                  data-testid="destination-country-select"
                  className="h-12 bg-slate-800/50 border-slate-600 hover:border-amber-500/50 transition-colors"
                >
                  <SelectValue placeholder={t.partnerCountry} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map((country) => {
                    const hasData = COUNTRIES_WITH_AUTHENTIC_DATA.has(country.code);
                    const bloc = TRADE_BLOCS[country.code];
                    return (
                      <SelectItem key={country.code} value={country.code}>
                        <span className="flex items-center gap-2">
                          <span className="text-lg">{getFlag(country.iso2 || country.code)}</span>
                          <span>{country.name}</span>
                          {hasData && <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>}
                          {bloc && <span className={`text-[10px] px-1.5 rounded border font-medium ${getBlocColor(bloc)}`}>{bloc}</span>}
                        </span>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Légende */}
          <div className="flex items-center gap-4 text-xs text-slate-500 bg-slate-800/30 rounded-lg px-4 py-2">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">{language === 'fr' ? 'Blocs:' : 'Blocs:'} CEDEAO · CEMAC · EAC · SACU · AES</span>
          </div>

          {/* Profil tarifaire du pays */}
          {loadingProfile && (
            <div className="flex items-center justify-center gap-3 py-4">
              <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-slate-400">{language === 'fr' ? 'Chargement du tarif national...' : 'Loading national tariff...'}</span>
            </div>
          )}

          {countryTariffProfile && countryTariffProfile.summary && !loadingProfile && (
            <div className="bg-slate-700/30 border border-slate-600/50 rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-slate-700/50 border-b border-slate-600/50 flex items-center justify-between flex-wrap gap-2">
                <span className="font-semibold text-white flex items-center gap-2">
                  <span className="text-lg">{getFlag(countries.find(c => c.code === destinationCountry)?.iso2 || destinationCountry)}</span>
                  {language === 'fr' ? 'Profil Tarifaire' : 'Tariff Profile'} - {getCountryName(destinationCountry)}
                </span>
                <div className="flex items-center gap-2">
                  {TRADE_BLOCS[destinationCountry] && (
                    <Badge variant="outline" className={`text-xs border ${getBlocColor(TRADE_BLOCS[destinationCountry])}`}>
                      {TRADE_BLOCS[destinationCountry]}
                    </Badge>
                  )}
                  <Badge className={`text-xs ${
                    COUNTRIES_WITH_AUTHENTIC_DATA.has(destinationCountry)
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                  } border`}>
                    {COUNTRIES_WITH_AUTHENTIC_DATA.has(destinationCountry)
                      ? (language === 'fr' ? 'Authentique' : 'Authentic')
                      : (language === 'fr' ? 'Estimé' : 'Estimated')
                    }
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-3 divide-x divide-slate-600/50">
                <div className="p-4 text-center">
                  <p className="text-slate-500 text-xs uppercase tracking-wide">{language === 'fr' ? 'DD moyen' : 'Avg. duty'}</p>
                  <p className="text-2xl font-bold text-blue-400 mt-1">{countryTariffProfile.summary.dd_rate_range?.avg?.toFixed(1) || '0'}%</p>
                  <p className="text-slate-500 text-xs">{countryTariffProfile.summary.dd_rate_range?.min?.toFixed(0) || '0'}% - {countryTariffProfile.summary.dd_rate_range?.max?.toFixed(0) || '0'}%</p>
                </div>
                <div className="p-4 text-center">
                  <p className="text-slate-500 text-xs uppercase tracking-wide">{language === 'fr' ? 'TVA' : 'VAT'}</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1">{countryTariffProfile.summary.vat_rate_pct || 0}%</p>
                  <p className="text-slate-500 text-xs">{countryTariffProfile.summary.vat_source || ''}</p>
                </div>
                <div className="p-4 text-center">
                  <p className="text-slate-500 text-xs uppercase tracking-wide">{language === 'fr' ? 'Autres' : 'Other'}</p>
                  <p className="text-2xl font-bold text-red-400 mt-1">{countryTariffProfile.summary.other_taxes_pct || 0}%</p>
                  <p className="text-slate-500 text-xs truncate">
                    {countryTariffProfile.summary.other_taxes_detail
                      ? Object.entries(countryTariffProfile.summary.other_taxes_detail).map(([k, v]) => `${k} ${v}%`).join(', ')
                      : '-'}
                  </p>
                </div>
              </div>
              <div className="px-4 py-2 bg-slate-800/50 border-t border-slate-600/50 flex justify-between text-xs text-slate-500">
                <span>{(countryTariffProfile.summary.total_positions || 0).toLocaleString()} {language === 'fr' ? 'positions' : 'positions'}</span>
                <span>{countryTariffProfile.summary.chapters_covered || 0} {language === 'fr' ? 'chapitres' : 'chapters'}</span>
              </div>
            </div>
          )}

          {/* Code HS */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-slate-300 font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-xs text-purple-400">3</span>
                <Package className="w-4 h-4 text-purple-400" />
                {t.hsCodeLabel}
              </Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setUseSmartSearch(!useSmartSearch)}
                className="text-xs text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
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
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder={language === 'fr' ? "Ex: 090111, 870323, 8517" : "Ex: 090111, 870323, 8517"}
                  value={hsCode}
                  onChange={(e) => setHsCode(e.target.value.replace(/[^0-9]/g, '').slice(0, 12))}
                  className="h-12 font-mono text-lg bg-slate-800/50 border-slate-600 hover:border-purple-500/50 focus:border-purple-500 transition-colors tracking-wider"
                  data-testid="hs-code-simple-input"
                />
                <p className="text-slate-500 text-xs">{t.hsCodeHint}</p>
              </div>
            )}
            
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowHSBrowser(!showHSBrowser)}
              className="w-full bg-slate-800/30 border-slate-600 hover:border-amber-500/50 hover:bg-slate-700/30 text-slate-300"
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
            <div className="border border-slate-700 rounded-xl overflow-hidden">
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

          {/* Valeur */}
          <div className="space-y-2">
            <Label className="text-slate-300 font-medium flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs text-emerald-400">4</span>
              {t.valueLabel}
            </Label>
            <Input
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="100000"
              min="0"
              className="h-12 font-mono text-lg bg-slate-800/50 border-slate-600 hover:border-emerald-500/50 focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Bouton Calculer */}
          <Button 
            onClick={calculateTariff}
            disabled={loading}
            data-testid="calculate-tariff-button"
            className="w-full h-14 text-lg font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-lg hover:shadow-xl transition-all"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                {t.calculating}
              </>
            ) : (
              <>
                <Calculator className="w-5 h-5 mr-2" />
                {t.calculateBtn}
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Résultats complets avec visualisations */}
      {result && (
        <div className="space-y-4">
          <Card className="shadow-xl" style={{ borderLeft: '4px solid #10b981', background: 'rgba(27,35,44,0.95)' }}>
            <CardHeader style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.25), rgba(212,175,55,0.15))', borderRadius: '12px 12px 0 0' }}>
              <CardTitle className="flex items-center space-x-2 text-2xl" style={{ color: '#10b981' }}>
                <span>💰</span>
                <span>{t.detailedResults}</span>
              </CardTitle>
              <CardDescription className="text-yellow-100 font-semibold flex items-center gap-2 flex-wrap">
                <span>{getFlag(result.origin_country)} {getCountryName(result.origin_country)} → {getFlag(result.destination_country)} {getCountryName(result.destination_country)}</span>
                {TRADE_BLOCS[result.destination_country] && (
                  <span className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full font-bold">
                    {TRADE_BLOCS[result.destination_country]}
                  </span>
                )}
                {COUNTRIES_WITH_AUTHENTIC_DATA.has(result.destination_country) && (
                  <span className="bg-green-400/30 text-green-100 text-xs px-2 py-0.5 rounded-full">
                    {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 pt-6 results-container">
              {/* Information sur les DONNÉES AUTHENTIQUES */}
              {result.data_source === 'authentic_tariff' && (
                <div className="result-section p-5 rounded-xl border-2 shadow-lg" style={{ background: 'rgba(16,185,129,0.1)', borderColor: 'rgba(16,185,129,0.4)' }} data-testid="authentic-data-badge">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
                      <span className="text-2xl text-white">✓</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold text-lg" style={{ color: '#10b981' }}>
                          {language === 'fr' ? 'Données Tarifaires Officielles' : 'Official Tariff Data'}
                        </h4>
                        <Badge className="px-3 py-1" style={{ background: '#10b981', color: '#fff' }}>
                          {language === 'fr' ? 'Vérifié' : 'Verified'}
                        </Badge>
                      </div>
                      <p className="text-sm mb-3" style={{ color: '#A0AAB4' }}>
                        {language === 'fr' 
                          ? `Calcul basé sur les tarifs douaniers officiels du ${getCountryName(destinationCountry)} avec ${result.sub_position_count || 0} sous-positions nationales.`
                          : `Calculation based on official customs tariffs of ${getCountryName(destinationCountry)} with ${result.sub_position_count || 0} national sub-headings.`}
                      </p>
                      
                      {/* Détail des taxes authentiques */}
                      {result.taxes_detail && result.taxes_detail.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {result.taxes_detail.map((tax, idx) => (
                            <Badge key={idx} variant="outline" style={{ background: 'rgba(16,185,129,0.15)', borderColor: 'rgba(16,185,129,0.4)', color: '#10b981' }}>
                              {tax.tax}: {tax.rate}%
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-xs mb-1" style={{ color: '#A0AAB4' }}>
                        {language === 'fr' ? 'Confiance' : 'Confidence'}
                      </p>
                      <Badge className="text-lg px-4 py-2" style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff' }}>
                        {language === 'fr' ? 'Très élevée' : 'Very High'}
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Avantages fiscaux ZLECAf */}
                  {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
                    <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
                      <p className="text-sm font-semibold mb-2" style={{ color: '#10b981' }}>
                        {language === 'fr' ? '🎯 Avantages ZLECAf applicables:' : '🎯 Applicable AfCFTA advantages:'}
                      </p>
                      <ul className="space-y-1">
                        {result.fiscal_advantages.map((adv, idx) => (
                          <li key={idx} className="text-sm flex items-start gap-2" style={{ color: '#F5F5F5' }}>
                            <span style={{ color: '#10b981' }}>✓</span>
                            <span>{language === 'fr' ? adv.condition_fr : adv.condition_en}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Formalités administratives */}
                  {result.administrative_formalities && result.administrative_formalities.length > 0 && (
                    <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(217,123,45,0.1)', border: '1px solid rgba(217,123,45,0.3)' }}>
                      <p className="text-sm font-semibold mb-2" style={{ color: '#D97B2D' }}>
                        {language === 'fr' ? '📋 Documents requis:' : '📋 Required documents:'}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {result.administrative_formalities.map((form, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs" style={{ background: 'rgba(217,123,45,0.15)', borderColor: 'rgba(217,123,45,0.4)', color: '#D97B2D' }}>
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
                <div className="result-section rounded-xl shadow-lg overflow-hidden" style={{ background: '#1B232C', border: '1px solid rgba(255,255,255,0.1)' }} data-testid="all-taxes-table">
                  <div className="p-4 border-b" style={{ background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.1))', borderColor: 'rgba(59,130,246,0.2)' }}>
                    <h4 className="font-bold text-lg flex items-center gap-2" style={{ color: '#3B82F6' }}>
                      <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.2)' }}>📋</span>
                      {language === 'fr' ? 'Détail Complet des Taxes' : 'Complete Tax Breakdown'}
                    </h4>
                    <p className="text-sm mt-1" style={{ color: '#93C5FD' }}>
                      {language === 'fr' 
                        ? `${result.taxes_detail.length} taxes applicables pour ${getCountryName(destinationCountry)}`
                        : `${result.taxes_detail.length} applicable taxes for ${getCountryName(destinationCountry)}`}
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-0">
                    {/* Colonne NPF */}
                    <div style={{ borderRight: '1px solid rgba(255,255,255,0.1)' }}>
                      <div className="p-3 border-b" style={{ background: 'rgba(239,68,68,0.15)', borderColor: 'rgba(239,68,68,0.2)' }}>
                        <h5 className="font-bold flex items-center gap-2" style={{ color: '#EF4444' }}>
                          <span>🚫</span>
                          {language === 'fr' ? 'Régime NPF (Sans préférence)' : 'MFN Regime (No preference)'}
                        </h5>
                      </div>
                      <div className="p-4">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b" style={{ color: '#A0AAB4', borderColor: 'rgba(255,255,255,0.1)' }}>
                              <th className="pb-2 text-left">{language === 'fr' ? 'Taxe' : 'Tax'}</th>
                              <th className="pb-2 text-center">{language === 'fr' ? 'Taux' : 'Rate'}</th>
                              <th className="pb-2 text-right">{language === 'fr' ? 'Montant' : 'Amount'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.1)' }}>
                              <td className="py-2 font-medium">
                                <span className="font-mono" style={{ color: '#F5F5F5' }}>CIF</span>
                                <span className="text-xs block" style={{ color: '#A0AAB4' }}>{language === 'fr' ? 'Valeur en douane' : 'Customs value'}</span>
                              </td>
                              <td className="py-2 text-center" style={{ color: '#A0AAB4' }}>-</td>
                              <td className="py-2 text-right font-mono font-bold" style={{ color: '#F5F5F5' }}>{formatCurrency(parseFloat(value))}</td>
                            </tr>
                            {result.taxes_detail.map((tax, idx) => {
                              const taxAmount = parseFloat(value) * (tax.rate / 100);
                              return (
                                <tr key={idx} className="border-b" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
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
                                        <span className="font-mono font-medium" style={{ color: '#F5F5F5' }}>{tax.tax}</span>
                                        {tax.observation && tax.observation !== tax.tax && (
                                          <span className="text-xs block" style={{ color: '#A0AAB4' }}>{tax.observation}</span>
                                        )}
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-2 text-center font-mono" style={{ color: '#F5F5F5' }}>{tax.rate}%</td>
                                  <td className="py-2 text-right font-mono" style={{ color: '#F5F5F5' }}>{formatCurrency(taxAmount)}</td>
                                </tr>
                              );
                            })}
                            <tr className="font-bold" style={{ background: 'rgba(239,68,68,0.15)' }}>
                              <td className="py-3" colSpan={2} style={{ color: '#F5F5F5' }}>
                                {language === 'fr' ? 'TOTAL À PAYER' : 'TOTAL TO PAY'}
                              </td>
                              <td className="py-3 text-right font-mono text-lg" style={{ color: '#EF4444' }}>
                                {formatCurrency(result.normal_total_cost)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    
                    {/* Colonne ZLECAf */}
                    <div>
                      <div className="p-3 border-b" style={{ background: 'rgba(16,185,129,0.15)', borderColor: 'rgba(16,185,129,0.2)' }}>
                        <h5 className="font-bold flex items-center gap-2" style={{ color: '#10b981' }}>
                          <span>✅</span>
                          {language === 'fr' ? 'Régime ZLECAf (Préférentiel)' : 'AfCFTA Regime (Preferential)'}
                        </h5>
                      </div>
                      <div className="p-4">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b" style={{ color: '#A0AAB4', borderColor: 'rgba(255,255,255,0.1)' }}>
                              <th className="pb-2 text-left">{language === 'fr' ? 'Taxe' : 'Tax'}</th>
                              <th className="pb-2 text-center">{language === 'fr' ? 'Taux' : 'Rate'}</th>
                              <th className="pb-2 text-right">{language === 'fr' ? 'Montant' : 'Amount'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b" style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.1)' }}>
                              <td className="py-2 font-medium">
                                <span className="font-mono" style={{ color: '#F5F5F5' }}>CIF</span>
                                <span className="text-xs block" style={{ color: '#A0AAB4' }}>{language === 'fr' ? 'Valeur en douane' : 'Customs value'}</span>
                              </td>
                              <td className="py-2 text-center" style={{ color: '#A0AAB4' }}>-</td>
                              <td className="py-2 text-right font-mono font-bold" style={{ color: '#F5F5F5' }}>{formatCurrency(parseFloat(value))}</td>
                            </tr>
                            {result.taxes_detail.map((tax, idx) => {
                              const isDD = tax.tax.toLowerCase().includes('d.d') || tax.tax.toLowerCase().includes('douane');
                              const effectiveRate = isDD ? 0 : tax.rate;
                              const taxAmount = parseFloat(value) * (effectiveRate / 100);
                              return (
                                <tr key={idx} className="border-b" style={{ borderColor: 'rgba(255,255,255,0.1)', background: isDD ? 'rgba(16,185,129,0.1)' : 'transparent' }}>
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
                                        <span className="font-mono font-medium" style={{ color: isDD ? '#10b981' : '#F5F5F5' }}>{tax.tax}</span>
                                        {tax.observation && tax.observation !== tax.tax && (
                                          <span className="text-xs block" style={{ color: '#A0AAB4' }}>{tax.observation}</span>
                                        )}
                                        {isDD && (
                                          <Badge className="mt-1 text-xs" style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>
                                            {language === 'fr' ? 'Exonéré ZLECAf' : 'AfCFTA Exempt'}
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-2 text-center font-mono">
                                    {isDD ? (
                                      <span>
                                        <span className="line-through" style={{ color: '#6B7280' }}>{tax.rate}%</span>
                                        <span className="font-bold ml-1" style={{ color: '#10b981' }}>0%</span>
                                      </span>
                                    ) : (
                                      <span style={{ color: '#F5F5F5' }}>{tax.rate}%</span>
                                    )}
                                  </td>
                                  <td className="py-2 text-right font-mono" style={{ color: isDD ? '#10b981' : '#F5F5F5', fontWeight: isDD ? 'bold' : 'normal' }}>
                                    {formatCurrency(taxAmount)}
                                  </td>
                                </tr>
                              );
                            })}
                            <tr className="font-bold" style={{ background: 'rgba(16,185,129,0.15)' }}>
                              <td className="py-3" colSpan={2} style={{ color: '#F5F5F5' }}>
                                {language === 'fr' ? 'TOTAL À PAYER' : 'TOTAL TO PAY'}
                              </td>
                              <td className="py-3 text-right font-mono text-lg" style={{ color: '#10b981' }}>
                                {formatCurrency(result.zlecaf_total_cost)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                  
                  {/* Économies */}
                  <div className="p-4" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">💰</span>
                        <div>
                          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.9)' }}>{language === 'fr' ? 'Économies grâce à la ZLECAf' : 'Savings thanks to AfCFTA'}</p>
                          <p className="text-2xl font-bold" style={{ color: '#fff' }}>{formatCurrency(result.savings || (result.normal_total_cost - result.zlecaf_total_cost))}</p>
                        </div>
                      </div>
                      <Badge className="text-lg px-4 py-2" style={{ background: 'rgba(255,255,255,0.2)', color: '#fff' }}>
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
                <div className="result-section rounded-xl shadow-lg overflow-hidden" style={{ background: '#1B232C', border: '1px solid rgba(255,255,255,0.1)' }} data-testid="formalities-section">
                  <div className="p-4 border-b" style={{ background: 'linear-gradient(135deg, rgba(217,123,45,0.15), rgba(249,115,22,0.1))', borderColor: 'rgba(217,123,45,0.2)' }}>
                    <h4 className="font-bold text-lg flex items-center gap-2" style={{ color: '#D97B2D' }}>
                      <ClipboardList className="w-5 h-5" />
                      {language === 'fr' ? 'Formalités et Documents Nécessaires' : 'Required Formalities and Documents'}
                    </h4>
                    <p className="text-sm mt-1" style={{ color: '#FBBF24' }}>
                      {language === 'fr' 
                        ? `Documents requis pour l'importation vers ${getCountryName(destinationCountry)}`
                        : `Documents required for import to ${getCountryName(destinationCountry)}`}
                    </p>
                  </div>
                  
                  <div className="p-4 space-y-4">
                    {/* Documents obligatoires */}
                    <div>
                      <h5 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#F5F5F5' }}>
                        <FileText className="w-4 h-4" style={{ color: '#D97B2D' }} />
                        {language === 'fr' ? 'Documents Obligatoires' : 'Mandatory Documents'}
                      </h5>
                      <div className="grid md:grid-cols-2 gap-3">
                        {/* Documents standards toujours requis */}
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(217,123,45,0.2)' }}>
                            <span className="font-bold text-sm" style={{ color: '#D97B2D' }}>1</span>
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#F5F5F5' }}>
                              {language === 'fr' ? 'Facture Commerciale' : 'Commercial Invoice'}
                            </p>
                            <p className="text-xs" style={{ color: '#A0AAB4' }}>
                              {language === 'fr' ? 'Détail des marchandises, prix, conditions de vente' : 'Details of goods, prices, terms of sale'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(217,123,45,0.2)' }}>
                            <span className="font-bold text-sm" style={{ color: '#D97B2D' }}>2</span>
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#F5F5F5' }}>
                              {language === 'fr' ? 'Liste de Colisage' : 'Packing List'}
                            </p>
                            <p className="text-xs" style={{ color: '#A0AAB4' }}>
                              {language === 'fr' ? 'Poids, dimensions, nombre de colis' : 'Weight, dimensions, number of packages'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(217,123,45,0.2)' }}>
                            <span className="font-bold text-sm" style={{ color: '#D97B2D' }}>3</span>
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#F5F5F5' }}>
                              {language === 'fr' ? 'Connaissement / LTA' : 'Bill of Lading / AWB'}
                            </p>
                            <p className="text-xs" style={{ color: '#A0AAB4' }}>
                              {language === 'fr' ? 'Document de transport maritime ou aérien' : 'Sea or air transport document'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(217,123,45,0.2)' }}>
                            <span className="font-bold text-sm" style={{ color: '#D97B2D' }}>4</span>
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#F5F5F5' }}>
                              {language === 'fr' ? 'Déclaration en Douane' : 'Customs Declaration'}
                            </p>
                            <p className="text-xs" style={{ color: '#A0AAB4' }}>
                              {language === 'fr' ? 'Formulaire DAU ou équivalent national' : 'SAD form or national equivalent'}
                            </p>
                          </div>
                        </div>
                        
                        {/* Documents spécifiques du pays */}
                        {result.administrative_formalities && result.administrative_formalities.map((form, idx) => (
                          <div key={idx} className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(217,123,45,0.1)', border: '1px solid rgba(217,123,45,0.3)' }}>
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(217,123,45,0.3)' }}>
                              <span className="font-bold text-sm" style={{ color: '#D97B2D' }}>{5 + idx}</span>
                            </div>
                            <div>
                              <p className="font-medium" style={{ color: '#FBBF24' }}>
                                {language === 'fr' ? form.document_fr : form.document_en}
                              </p>
                              {form.code && (
                                <p className="text-xs" style={{ color: '#D97B2D' }}>Code: {form.code}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {/* Documents ZLECAf */}
                    <div className="pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      <h5 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#10b981' }}>
                        <CheckCircle className="w-4 h-4" style={{ color: '#10b981' }} />
                        {language === 'fr' ? 'Documents pour Bénéficier du Tarif ZLECAf' : 'Documents to Benefit from AfCFTA Rate'}
                      </h5>
                      <div className="grid md:grid-cols-2 gap-3">
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(16,185,129,0.2)' }}>
                            <CheckCircle className="w-4 h-4" style={{ color: '#10b981' }} />
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#10b981' }}>
                              {language === 'fr' ? 'Certificat d\'Origine ZLECAf' : 'AfCFTA Certificate of Origin'}
                            </p>
                            <p className="text-xs" style={{ color: '#6EE7B7' }}>
                              {language === 'fr' 
                                ? 'Délivré par l\'autorité compétente du pays exportateur'
                                : 'Issued by competent authority of exporting country'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 rounded-lg" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(16,185,129,0.2)' }}>
                            <CheckCircle className="w-4 h-4" style={{ color: '#10b981' }} />
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: '#10b981' }}>
                              {language === 'fr' ? 'Déclaration du Fournisseur' : 'Supplier Declaration'}
                            </p>
                            <p className="text-xs" style={{ color: '#6EE7B7' }}>
                              {language === 'fr' 
                                ? 'Attestant l\'origine africaine du produit'
                                : 'Attesting African origin of the product'}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Avantages fiscaux */}
                      {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
                        <div className="mt-4 p-4 rounded-lg" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
                          <p className="font-semibold mb-2 flex items-center gap-2" style={{ color: '#10b981' }}>
                            <Sparkles className="w-4 h-4" />
                            {language === 'fr' ? 'Avantages obtenus avec ces documents:' : 'Benefits obtained with these documents:'}
                          </p>
                          <ul className="space-y-2">
                            {result.fiscal_advantages.map((adv, idx) => (
                              <li key={idx} className="flex items-center gap-2 text-sm">
                                <span className="w-5 h-5 rounded-full flex items-center justify-center text-white text-xs" style={{ background: '#10b981' }}>✓</span>
                                <span style={{ color: '#F5F5F5' }}>{language === 'fr' ? adv.condition_fr : adv.condition_en}</span>
                                {adv.rate !== undefined && adv.rate === 0 && (
                                  <Badge className="text-xs ml-auto" style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>
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
                      <div className="pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <h5 className="font-semibold mb-3 flex items-center gap-2" style={{ color: '#3B82F6' }}>
                          <Info className="w-4 h-4" style={{ color: '#3B82F6' }} />
                          {language === 'fr' ? 'Critères d\'Origine à Respecter' : 'Origin Criteria to Meet'}
                        </h5>
                        <div className="p-4 rounded-lg" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)' }}>
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <p className="text-sm mb-1" style={{ color: '#93C5FD' }}>{language === 'fr' ? 'Règle applicable:' : 'Applicable rule:'}</p>
                              <p className="font-semibold" style={{ color: '#3B82F6' }}>{result.rules_of_origin.rule}</p>
                            </div>
                            <div>
                              <p className="text-sm mb-1" style={{ color: '#93C5FD' }}>{language === 'fr' ? 'Contenu régional minimum:' : 'Minimum regional content:'}</p>
                              <p className="font-semibold" style={{ color: '#3B82F6' }}>{result.rules_of_origin.regional_content}% {language === 'fr' ? 'africain' : 'African'}</p>
                            </div>
                          </div>
                          <p className="text-sm mt-3 pt-3" style={{ color: '#F5F5F5', borderTop: '1px solid rgba(59,130,246,0.2)' }}>
                            <span className="font-medium">{language === 'fr' ? 'Exigence:' : 'Requirement:'}</span> {result.rules_of_origin.requirement}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* Note importante */}
                    <div className="mt-4 p-3 rounded-lg text-xs" style={{ background: 'rgba(255,255,255,0.05)', color: '#A0AAB4' }}>
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
                <div className="result-section tariff-info-section p-5 rounded-xl shadow-sm" style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)' }}>
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(139,92,246,0.2)' }}>
                      <Package className="w-6 h-6" style={{ color: '#8B5CF6' }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold" style={{ color: '#8B5CF6' }}>{t.subPositionInfo}</h4>
                        <Badge className="text-xs" style={{ background: '#8B5CF6', color: '#fff' }}>{t.precisionHigh}</Badge>
                      </div>
                      <p className="font-mono text-lg font-bold mb-1" style={{ color: '#A78BFA' }}>{result.sub_position_used}</p>
                      {result.sub_position_description && (
                        <p className="text-sm" style={{ color: '#A0AAB4' }}>{result.sub_position_description}</p>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2 flex-shrink-0">
                      <div className="p-3 rounded-lg text-center" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}>
                        <p className="text-xs font-medium" style={{ color: '#F87171' }}>{t.normalRate}</p>
                        <p className="font-bold text-lg" style={{ color: '#EF4444' }}>{(result.normal_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div className="p-3 rounded-lg text-center" style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}>
                        <p className="text-xs font-medium" style={{ color: '#34D399' }}>{t.zlecafRate}</p>
                        <p className="font-bold text-lg" style={{ color: '#10b981' }}>{(result.zlecaf_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Information sur la position tarifaire nationale (données crawlées authentiques) */}
              {result.tariff_precision === 'national_position' && (
                <div className="result-section tariff-info-section bg-gradient-to-r from-emerald-50 to-green-50 p-5 rounded-xl border border-emerald-200 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold text-emerald-800">
                          {language === 'fr' ? 'Position tarifaire nationale' : 'National tariff position'}
                        </h4>
                        <Badge className="bg-emerald-700 text-white text-xs">
                          {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
                        </Badge>
                        {result.data_source && (
                          <Badge variant="outline" className="text-xs text-emerald-600 border-emerald-300">
                            {result.data_source === 'crawled_authentic' ? (language === 'fr' ? 'Source officielle' : 'Official source') : result.data_source}
                          </Badge>
                        )}
                      </div>
                      <p className="font-mono text-lg font-bold text-emerald-900 mb-1">{result.sub_position_used}</p>
                      {result.sub_position_description && (
                        <p className="text-gray-700 text-sm">{result.sub_position_description}</p>
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
                  {result.taxes_detail && result.taxes_detail.length > 0 && (
                    <div className="mt-4 pl-16">
                      <h5 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                        {language === 'fr' ? 'Taxes applicables' : 'Applicable taxes'}
                      </h5>
                      <div className="flex flex-wrap gap-1.5">
                        {result.taxes_detail.map((tax, tIdx) => (
                          <span key={tIdx} className="text-xs bg-white border border-emerald-200 text-gray-700 px-2 py-1 rounded-md">
                            {tax.tax}: <strong>{tax.rate}%</strong>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.administrative_formalities && result.administrative_formalities.length > 0 && (
                    <div className="mt-3 pl-16">
                      <h5 className="text-xs font-semibold text-orange-600 mb-1">
                        {language === 'fr' ? 'Formalités administratives' : 'Administrative formalities'}
                      </h5>
                      {result.administrative_formalities.map((f, fIdx) => (
                        <p key={fIdx} className="text-xs text-orange-700">
                          {typeof f === 'string' ? f : f.description || ''}
                        </p>
                      ))}
                    </div>
                  )}
                  {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
                    <div className="mt-3 pl-16">
                      <h5 className="text-xs font-semibold text-blue-600 mb-1">
                        {language === 'fr' ? 'Avantages fiscaux' : 'Fiscal advantages'}
                      </h5>
                      {result.fiscal_advantages.map((a, aIdx) => (
                        <p key={aIdx} className="text-xs text-blue-700">
                          {typeof a === 'string' ? a : a.description || ''}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Information sur le tarif SH6 précis */}
              {result.tariff_precision === 'hs6_country' && (
                <div className="result-section tariff-info-section p-5 rounded-xl shadow-sm" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)' }}>
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(59,130,246,0.2)' }}>
                      <Package className="w-6 h-6" style={{ color: '#3B82F6' }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h4 className="font-bold" style={{ color: '#3B82F6' }}>{t.hs6TariffInfo}</h4>
                        <Badge className="text-xs" style={{ background: '#3B82F6', color: '#fff' }}>{t.hs6TariffApplied}</Badge>
                      </div>
                      <p className="font-semibold" style={{ color: '#F5F5F5' }}>{hs6TariffInfo?.description || `Code ${result.hs6_code}`}</p>
                      <p className="text-sm font-mono mt-1" style={{ color: '#60A5FA' }}>Code: {result.hs6_code}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 flex-shrink-0">
                      <div className="p-3 rounded-lg text-center" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}>
                        <p className="text-xs font-medium" style={{ color: '#F87171' }}>{t.normalRate}</p>
                        <p className="font-bold text-lg" style={{ color: '#EF4444' }}>{(result.normal_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div className="p-3 rounded-lg text-center" style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}>
                        <p className="text-xs font-medium" style={{ color: '#34D399' }}>{t.zlecafRate}</p>
                        <p className="font-bold text-lg" style={{ color: '#10b981' }}>{(result.zlecaf_tariff_rate * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  {result.available_sub_positions_count > 0 && !result.rate_warning?.has_variation && (
                    <p className="text-xs mt-3 pl-16" style={{ color: '#60A5FA' }}>
                      {result.available_sub_positions_count} {t.subPositionsAvailable}
                    </p>
                  )}
                </div>
              )}

              {/* WARNING: Taux variables selon sous-positions nationales */}
              {result.rate_warning && result.rate_warning.has_variation && (
                <div 
                  className="rate-warning-box p-5 rounded-xl shadow-lg" 
                  style={{ background: 'rgba(245,158,11,0.15)', borderLeft: '4px solid #F59E0B' }}
                  data-testid="rate-warning-box"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(245,158,11,0.2)' }}>
                      <AlertTriangle className="w-6 h-6" style={{ color: '#F59E0B' }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-lg mb-2" style={{ color: '#FBBF24' }}>
                        {language === 'fr' ? 'Attention: Taux de droits variables' : 'Warning: Variable duty rates'}
                      </h4>
                      <p className="text-sm leading-relaxed mb-4" style={{ color: '#F5F5F5' }}>
                        {language === 'fr' 
                          ? `Ce code SH6 (${result.hs6_code}) comporte plusieurs sous-positions nationales avec des taux différents.`
                          : `This HS6 code (${result.hs6_code}) has multiple national sub-headings with different rates.`}
                      </p>
                      
                      {/* Visualisation des taux min/max/utilisé */}
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="rate-card p-3 rounded-lg text-center shadow-sm" style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}>
                          <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#34D399' }}>{language === 'fr' ? 'Minimum' : 'Minimum'}</p>
                          <p className="text-2xl font-bold mt-1" style={{ color: '#10b981' }}>{result.rate_warning.min_rate_pct}</p>
                        </div>
                        <div className="rate-card p-3 rounded-lg text-center shadow-md relative" style={{ background: 'rgba(59,130,246,0.15)', border: '2px solid #3B82F6' }}>
                          <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                            <Badge className="text-xs px-2" style={{ background: '#3B82F6', color: '#fff' }}>
                              {language === 'fr' ? 'Utilisé' : 'Used'}
                            </Badge>
                          </div>
                          <p className="text-xs font-medium uppercase tracking-wide mt-2" style={{ color: '#60A5FA' }}>{language === 'fr' ? 'Actuel' : 'Current'}</p>
                          <p className="text-2xl font-bold mt-1" style={{ color: '#3B82F6' }}>{result.rate_warning.rate_used_pct}</p>
                        </div>
                        <div className="rate-card p-3 rounded-lg text-center shadow-sm" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}>
                          <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#F87171' }}>{language === 'fr' ? 'Maximum' : 'Maximum'}</p>
                          <p className="text-2xl font-bold mt-1" style={{ color: '#EF4444' }}>{result.rate_warning.max_rate_pct}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-2 p-3 rounded-lg" style={{ background: 'rgba(245,158,11,0.1)' }}>
                        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
                        <p className="text-sm" style={{ color: '#FBBF24' }}>
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
                <div className="result-section rounded-xl shadow-sm overflow-hidden" style={{ background: '#1B232C', border: '1px solid rgba(139,92,246,0.3)' }}>
                  <div 
                    className="p-4 cursor-pointer" 
                    style={{ background: 'rgba(139,92,246,0.15)', borderBottom: '1px solid rgba(139,92,246,0.2)' }}
                    onClick={() => document.getElementById('sub-positions-details')?.toggleAttribute('open')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(139,92,246,0.2)' }}>
                          <Package className="w-5 h-5" style={{ color: '#8B5CF6' }} />
                        </div>
                        <div>
                          <h4 className="font-bold" style={{ color: '#A78BFA' }}>
                            {language === 'fr' ? 'Sous-positions disponibles' : 'Available sub-headings'}
                          </h4>
                          <p className="text-sm" style={{ color: '#8B5CF6' }}>
                            {language === 'fr' ? 'Cliquez pour sélectionner le taux exact' : 'Click to select exact rate'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge style={{ background: '#8B5CF6', color: '#fff' }}>{result.sub_positions_details.length}</Badge>
                        <Badge className="text-xs" style={{ background: 'linear-gradient(90deg, #10b981, #EF4444)', color: '#fff' }}>
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
                            className="sub-position-item p-3 rounded-lg cursor-pointer flex items-center justify-between transition-all"
                            style={{ 
                              background: isCurrentRate ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.05)',
                              border: isCurrentRate ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.1)'
                            }}
                            onClick={() => {
                              setHsCode(sp.code);
                              toast({
                                title: language === 'fr' ? 'Sous-position sélectionnée' : 'Sub-heading selected',
                                description: sp.code,
                              });
                            }}
                          >
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                              <code className="font-mono font-bold px-2 py-1 rounded text-sm" style={{ background: 'rgba(139,92,246,0.2)', color: '#A78BFA' }}>
                                {sp.code}
                              </code>
                              <span className="text-sm truncate" style={{ color: '#F5F5F5' }}>
                                {language === 'fr' ? sp.description_fr : sp.description_en}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                              {isCurrentRate && (
                                <Badge className="text-xs" style={{ background: 'rgba(59,130,246,0.2)', color: '#60A5FA' }}>
                                  {language === 'fr' ? 'Actuel' : 'Current'}
                                </Badge>
                              )}
                              <Badge className="font-bold px-3" style={{ 
                                background: isMinRate ? '#10b981' : isMaxRate ? '#EF4444' : isCurrentRate ? '#3B82F6' : '#6B7280',
                                color: '#fff'
                              }}>
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
                <div className="result-section tariff-info-section p-4 rounded-xl shadow-sm" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.1)' }}>
                      <Package className="w-5 h-5" style={{ color: '#A0AAB4' }} />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm" style={{ color: '#A0AAB4' }}>{t.chapterTariffApplied}</span>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline" style={{ color: '#A0AAB4', borderColor: 'rgba(255,255,255,0.2)' }}>{t.sectorPrefix} {result.hs_code?.substring(0, 2)}</Badge>
                      <Badge variant="outline" style={{ color: '#F59E0B', borderColor: 'rgba(245,158,11,0.4)' }}>{t.precisionMedium}</Badge>
                    </div>
                  </div>
                </div>
              )}

              {/* Graphique comparaison complète avec TOUTES les taxes */}
              <div className="chart-container result-section p-5 rounded-xl shadow-md" style={{ background: '#1B232C', border: '1px solid rgba(255,255,255,0.1)' }}>
                <h4 className="font-bold text-lg mb-4 flex items-center gap-2" style={{ color: '#F5F5F5' }}>
                  <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.2)' }}>📊</span>
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
                    <XAxis dataKey="name" tick={{ fill: '#A0AAB4' }} />
                    <YAxis tick={{ fill: '#A0AAB4' }} />
                    <Tooltip formatter={(value) => formatCurrency(value)} contentStyle={{ background: '#1B232C', border: '1px solid rgba(212,175,55,0.3)', borderRadius: '8px' }} labelStyle={{ color: '#F5F5F5' }} />
                    <Legend wrapperStyle={{ color: '#F5F5F5' }} />
                    <Bar dataKey={t.merchandiseValue} stackId="a" fill="#60a5fa" />
                    <Bar dataKey={t.customsDuties} stackId="a" fill="#ef4444" />
                    <Bar dataKey={t.vat} stackId="a" fill="#f59e0b" />
                    <Bar dataKey={t.otherTaxes} stackId="a" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Économies TOTALES */}
              <div className="savings-section result-section text-center p-6 rounded-xl shadow-lg" style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.15))', border: '1px solid rgba(16,185,129,0.3)' }}>
                <p className="text-base font-semibold mb-3" style={{ color: '#A0AAB4' }}>{t.totalSavings}</p>
                <p className="text-4xl md:text-5xl font-extrabold mb-4" style={{ color: '#10b981' }}>
                  {formatCurrency(result.total_savings_with_taxes)}
                </p>
                <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full shadow-md" style={{ background: '#10b981', color: '#fff' }}>
                  <Sparkles className="w-5 h-5" />
                  <span className="text-xl font-bold">{result.total_savings_percentage.toFixed(1)}%</span>
                  <span className="text-sm opacity-90">{t.totalSavingsPercent}</span>
                </div>
                <Progress value={result.total_savings_percentage} className="w-full mt-5 h-2" style={{ background: 'rgba(16,185,129,0.2)' }} />
                <p className="text-sm mt-4" style={{ color: '#A0AAB4' }}>
                  {t.totalCostComparison} <span className="font-semibold" style={{ color: '#EF4444' }}>{formatCurrency(result.normal_total_cost)}</span> (NPF) 
                  {' '}{t.vs}{' '}
                  <span className="font-semibold" style={{ color: '#10b981' }}>{formatCurrency(result.zlecaf_total_cost)}</span> (ZLECAf)
                </p>
              </div>

              {/* Journal de calcul détaillé */}
              {result.normal_calculation_journal && (
                <Card className="journal-container result-section shadow-md border-0 overflow-hidden" style={{ background: '#1B232C' }}>
                  <CardHeader className="py-4" style={{ background: 'rgba(139,92,246,0.1)', borderBottom: '1px solid rgba(139,92,246,0.2)' }}>
                    <CardTitle className="text-lg font-bold flex items-center gap-3" style={{ color: '#F5F5F5' }}>
                      <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(139,92,246,0.2)' }}>
                        <Package className="w-5 h-5" style={{ color: '#8B5CF6' }} />
                      </div>
                      {t.calculationJournal}
                    </CardTitle>
                    <CardDescription className="text-sm mt-1" style={{ color: '#A0AAB4' }}>
                      {result.computation_order_ref}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow style={{ background: 'rgba(255,255,255,0.05)' }}>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.step}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.component}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.base}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.rate}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.amount}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.cumulative}</TableHead>
                            <TableHead style={{ color: '#A0AAB4' }}>{t.legalRef}</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.normal_calculation_journal.map((entry, index) => (
                            <TableRow key={index} style={{ background: index % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent' }}>
                              <TableCell className="font-bold" style={{ color: '#F5F5F5' }}>{entry.step}</TableCell>
                              <TableCell className="font-semibold" style={{ color: '#F5F5F5' }}>{entry.component}</TableCell>
                              <TableCell style={{ color: '#F5F5F5' }}>{formatCurrency(entry.base)}</TableCell>
                              <TableCell className="font-semibold" style={{ color: '#EF4444' }}>{entry.rate}</TableCell>
                              <TableCell className="font-bold" style={{ color: '#3B82F6' }}>{formatCurrency(entry.amount)}</TableCell>
                              <TableCell className="font-bold" style={{ color: '#F5F5F5' }}>{formatCurrency(entry.cumulative)}</TableCell>
                              <TableCell className="text-xs">
                                {entry.legal_ref_url ? (
                                  <a href={entry.legal_ref_url} target="_blank" rel="noopener noreferrer" style={{ color: '#60A5FA' }} className="hover:underline">
                                    {entry.legal_ref}
                                  </a>
                                ) : (
                                  <span style={{ color: '#A0AAB4' }}>{entry.legal_ref || '-'}</span>
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
              <div className="p-6 rounded-xl shadow-lg" style={{ background: 'rgba(217,123,45,0.15)', borderLeft: '4px solid #D97B2D' }}>
                <h4 className="font-bold text-xl mb-3 flex items-center gap-2" style={{ color: '#FBBF24' }}>
                  <span>📜</span> {t.rulesOrigin}
                </h4>
                <div className="p-4 rounded-lg space-y-2" style={{ background: 'rgba(0,0,0,0.2)' }}>
                  <p className="text-sm font-semibold" style={{ color: '#F5F5F5' }}>
                    <strong style={{ color: '#D97B2D' }}>{t.ruleType}:</strong> {result.rules_of_origin.rule}
                  </p>
                  <p className="text-sm font-semibold" style={{ color: '#F5F5F5' }}>
                    <strong style={{ color: '#D97B2D' }}>{t.requirement}:</strong> {result.rules_of_origin.requirement}
                  </p>
                  <div className="mt-3">
                    <Progress 
                      value={result.rules_of_origin.regional_content} 
                      className="w-full h-3"
                      style={{ background: 'rgba(217,123,45,0.2)' }}
                    />
                    <p className="text-sm mt-2 font-bold text-center" style={{ color: '#FBBF24' }}>
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
                    className="w-full flex items-center justify-center gap-2 py-3"
                    style={{ background: 'rgba(139,92,246,0.1)', border: '2px solid rgba(139,92,246,0.4)', color: '#A78BFA' }}
                    data-testid="toggle-detailed-breakdown"
                  >
                    <Calculator className="h-5 w-5" style={{ color: '#8B5CF6' }} />
                    <span className="font-semibold">
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
        
        {/* Onglet Réglementation - Moteur Réglementaire v3 */}
        <TabsContent value="regulatory">
          <div className="space-y-6">
            {/* Header avec recherche */}
            <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden">
              <div className="absolute top-0 left-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2"></div>
              
              <CardHeader className="relative">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-amber-500/20">
                    <Scale className="w-8 h-8 text-amber-400" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-white">
                      {language === 'fr' ? 'Moteur Réglementaire AfCFTA' : 'AfCFTA Regulatory Engine'}
                    </CardTitle>
                    <CardDescription className="text-slate-400 text-base mt-1">
                      {language === 'fr' 
                        ? 'Consultez les droits, taxes et formalités pour chaque code tarifaire'
                        : 'View duties, taxes and formalities for each tariff code'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="relative space-y-6">
                {/* Champs de recherche */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-slate-300 font-medium">
                      {language === 'fr' ? 'Pays de destination' : 'Destination Country'}
                    </Label>
                    <Select value={destinationCountry} onValueChange={handleDestinationChange}>
                      <SelectTrigger 
                        data-testid="regulatory-country-select"
                        className="h-12 bg-slate-800/50 border-slate-600 hover:border-amber-500/50 transition-colors"
                      >
                        <SelectValue placeholder={language === 'fr' ? 'Sélectionner un pays...' : 'Select a country...'} />
                      </SelectTrigger>
                      <SelectContent>
                        {countries.map((country) => (
                          <SelectItem key={country.code} value={country.code}>
                            <span className="flex items-center gap-2">
                              <span className="text-lg">{getFlag(country.iso2 || country.code)}</span>
                              <span>{country.name}</span>
                              {country.code === 'DZA' && (
                                <span className="ml-2 text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">
                                  {language === 'fr' ? 'Disponible' : 'Available'}
                                </span>
                              )}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300 font-medium">
                      {language === 'fr' ? 'Code HS (6 à 12 chiffres)' : 'HS Code (6 to 12 digits)'}
                    </Label>
                    <Input
                      value={hsCode}
                      onChange={(e) => setHsCode(e.target.value)}
                      placeholder={language === 'fr' ? 'Ex: 010110, 0101101000...' : 'E.g: 010110, 0101101000...'}
                      className="h-12 font-mono text-lg bg-slate-800/50 border-slate-600 hover:border-amber-500/50 focus:border-amber-500 transition-colors"
                      data-testid="regulatory-hs-input"
                    />
                  </div>
                </div>

                {/* Guide d'utilisation */}
                <div className="bg-slate-700/30 border border-slate-600/50 rounded-xl p-5">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20 shrink-0">
                      <Info className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white mb-2">
                        {language === 'fr' ? 'Guide d\'utilisation' : 'How to use'}
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold shrink-0">1</span>
                          <span className="text-slate-400">
                            {language === 'fr' ? 'Sélectionnez le pays de destination' : 'Select the destination country'}
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold shrink-0">2</span>
                          <span className="text-slate-400">
                            {language === 'fr' ? 'Entrez un code HS6 ou HS10' : 'Enter an HS6 or HS10 code'}
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold shrink-0">3</span>
                          <span className="text-slate-400">
                            {language === 'fr' ? 'Consultez droits, taxes et documents' : 'View duties, taxes and documents'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Panneau des détails réglementaires */}
            {destinationCountry && hsCode && hsCode.length >= 6 && (
              <RegulatoryDetailsPanel
                countryCode={destinationCountry}
                hsCode={hsCode}
                language={language}
              />
            )}

            {/* Message si pas de données sélectionnées */}
            {(!destinationCountry || !hsCode || hsCode.length < 6) && (
              <Card className="bg-slate-800/30 border-slate-700 border-dashed">
                <CardContent className="p-12 text-center">
                  <div className="w-20 h-20 mx-auto mb-6 bg-slate-700/30 rounded-2xl flex items-center justify-center">
                    <Scale className="w-10 h-10 text-slate-500" />
                  </div>
                  <p className="text-slate-400 text-lg mb-2">
                    {language === 'fr' 
                      ? 'Sélectionnez un pays et entrez un code HS'
                      : 'Select a country and enter an HS code'}
                  </p>
                  <p className="text-slate-500 text-sm">
                    {language === 'fr' 
                      ? 'Les détails réglementaires s\'afficheront automatiquement'
                      : 'Regulatory details will appear automatically'}
                  </p>
                </CardContent>
              </Card>
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
