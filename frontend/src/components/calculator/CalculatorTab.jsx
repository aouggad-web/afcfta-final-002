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
import { Package, ChevronDown, ChevronUp, Sparkles, AlertTriangle, Info, Calculator, Globe, FileText, CheckCircle, ClipboardList, Scale, FileCheck, Shield } from 'lucide-react';
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
          
          // Totaux en pourcentage (pour l'affichage)
          total_taxes_npf: rates.total_rate_pct || (rates.dd_rate_pct || 0) + (rates.vat_rate_pct || 0) + (rates.other_taxes_pct || 0),
          total_taxes_zlecaf: (rates.vat_rate_pct || 0) + (rates.other_taxes_pct || 0), // DD exonéré sous ZLECAf
          
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

      {/* === RÉSULTATS === */}
      {result && (
        <div className="space-y-4">
          {/* En-tête des résultats avec synthèse */}
          <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden">
            <div className="absolute top-0 left-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2"></div>
            
            <CardHeader className="relative">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl border border-emerald-500/20">
                    <CheckCircle className="w-8 h-8 text-emerald-400" />
                  </div>
                  <div>
                    <CardTitle className="text-xl text-white flex items-center gap-2">
                      {t.detailedResults}
                      {result.data_source === 'authentic_tariff' && (
                        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 border text-xs">
                          {language === 'fr' ? 'Données Officielles' : 'Official Data'}
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="text-slate-400 flex items-center gap-2 mt-1">
                      <span className="text-lg">{getFlag(result.origin_country)}</span>
                      <span>{getCountryName(result.origin_country)}</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-lg">{getFlag(result.destination_country)}</span>
                      <span>{getCountryName(result.destination_country)}</span>
                      {TRADE_BLOCS[result.destination_country] && (
                        <Badge variant="outline" className={`text-xs ml-2 ${getBlocColor(TRADE_BLOCS[result.destination_country])}`}>
                          {TRADE_BLOCS[result.destination_country]}
                        </Badge>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="relative">
              {/* Grille de synthèse économique */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Total NPF */}
                <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/20">
                  <p className="text-red-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Total NPF' : 'Total MFN'}</p>
                  <p className="text-3xl font-bold text-red-400 mt-1">{(result.total_taxes_npf || 0).toFixed(1)}%</p>
                  <p className="text-red-400/60 text-xs mt-1">{language === 'fr' ? 'Sans accord' : 'No agreement'}</p>
                </div>
                
                {/* Total ZLECAf */}
                <div className="bg-emerald-500/10 rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-emerald-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Total ZLECAf' : 'Total AfCFTA'}</p>
                  <p className="text-3xl font-bold text-emerald-400 mt-1">{(result.total_taxes_zlecaf || 0).toFixed(1)}%</p>
                  <p className="text-emerald-400/60 text-xs mt-1">{language === 'fr' ? 'Avec accord' : 'With agreement'}</p>
                </div>
                
                {/* Économie */}
                <div className="bg-amber-500/10 rounded-xl p-4 border border-amber-500/20">
                  <p className="text-amber-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Économie' : 'Savings'}</p>
                  <p className="text-3xl font-bold text-amber-400 mt-1">
                    -{((result.total_taxes_npf || 0) - (result.total_taxes_zlecaf || 0)).toFixed(1)}%
                  </p>
                  <p className="text-amber-400/60 text-xs mt-1">{language === 'fr' ? 'Certificat Origine' : 'Origin Certificate'}</p>
                </div>
                
                {/* Montant économisé */}
                <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
                  <p className="text-blue-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Montant Économisé' : 'Amount Saved'}</p>
                  <p className="text-2xl font-bold text-blue-400 mt-1">
                    {((parseFloat(value) || 0) * ((result.total_taxes_npf || 0) - (result.total_taxes_zlecaf || 0)) / 100).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €
                  </p>
                  <p className="text-blue-400/60 text-xs mt-1">{language === 'fr' ? 'Sur votre valeur' : 'On your value'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Détail des taxes */}
          {result.taxes_detail && result.taxes_detail.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <ClipboardList className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-white">{language === 'fr' ? 'Détail des Taxes' : 'Tax Breakdown'}</CardTitle>
                    <CardDescription className="text-slate-400">
                      {result.taxes_detail.length} {language === 'fr' ? 'taxes applicables' : 'applicable taxes'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.taxes_detail.map((tax, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-700 hover:border-blue-500/30 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                          <FileText className="w-4 h-4 text-blue-400" />
                        </div>
                        <div>
                          <span className="font-mono text-white font-semibold">{tax.tax}</span>
                          {tax.observation && (
                            <p className="text-slate-400 text-sm">{tax.observation}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-slate-500 text-xs">{language === 'fr' ? 'NPF' : 'MFN'}</p>
                          <p className="text-white font-bold">{tax.rate}%</p>
                        </div>
                        <div className="text-right">
                          <p className="text-slate-500 text-xs">{language === 'fr' ? 'ZLECAf' : 'AfCFTA'}</p>
                          <p className="text-emerald-400 font-bold">
                            {tax.tax === 'D.D' || tax.tax === 'DD' ? '0%' : `${tax.rate}%`}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Documents requis */}
          {result.administrative_formalities && result.administrative_formalities.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                    <FileCheck className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-white">{language === 'fr' ? 'Documents Requis' : 'Required Documents'}</CardTitle>
                    <CardDescription className="text-slate-400">
                      {result.administrative_formalities.length} {language === 'fr' ? 'formalités' : 'formalities'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.administrative_formalities.map((form, idx) => (
                    <div 
                      key={idx}
                      className="p-3 bg-slate-700/30 rounded-lg border border-slate-700"
                    >
                      <div className="flex items-start gap-2">
                        <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 border font-mono shrink-0">
                          {form.code}
                        </Badge>
                        <p className="text-slate-300 text-sm">{form.document_fr || form.document_en}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Avantages ZLECAf */}
          {result.fiscal_advantages && result.fiscal_advantages.length > 0 && (
            <Card className="bg-gradient-to-br from-emerald-900/20 to-slate-800/50 border-emerald-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                    <Shield className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-white">{language === 'fr' ? 'Avantages ZLECAf' : 'AfCFTA Advantages'}</CardTitle>
                    <CardDescription className="text-emerald-400/60">
                      {language === 'fr' ? 'Exonérations applicables' : 'Applicable exemptions'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.fiscal_advantages.map((adv, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center gap-3 p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20"
                    >
                      <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
                      <span className="text-slate-300">{adv.condition_fr || adv.condition_en}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
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
                        {countries.map((country) => {
                          // Tous les 54 pays AfCFTA avec données canoniques du Moteur Réglementaire v3
                          const REGULATORY_ENGINE_COUNTRIES = [
                            'AGO', 'BDI', 'BEN', 'BFA', 'BWA', 'CAF', 'CIV', 'CMR', 'COD', 'COG',
                            'COM', 'CPV', 'DJI', 'DZA', 'EGY', 'ERI', 'ETH', 'GAB', 'GHA', 'GIN',
                            'GMB', 'GNB', 'GNQ', 'KEN', 'LBR', 'LBY', 'LSO', 'MAR', 'MDG', 'MLI',
                            'MOZ', 'MRT', 'MUS', 'MWI', 'NAM', 'NER', 'NGA', 'RWA', 'SDN', 'SEN',
                            'SLE', 'SOM', 'SSD', 'STP', 'SWZ', 'SYC', 'TCD', 'TGO', 'TUN', 'TZA',
                            'UGA', 'ZAF', 'ZMB', 'ZWE'
                          ];
                          const hasRegulatoryData = REGULATORY_ENGINE_COUNTRIES.includes(country.code);
                          return (
                            <SelectItem key={country.code} value={country.code}>
                              <span className="flex items-center gap-2">
                                <span className="text-lg">{getFlag(country.iso2 || country.code)}</span>
                                <span>{country.name}</span>
                                {hasRegulatoryData && (
                                  <span className="ml-2 text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">
                                    {language === 'fr' ? 'Disponible' : 'Available'}
                                  </span>
                                )}
                              </span>
                            </SelectItem>
                          );
                        })}
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
