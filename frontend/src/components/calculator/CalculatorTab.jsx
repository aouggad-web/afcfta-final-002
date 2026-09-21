import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { useHsLabel } from '../../hooks/useHsLabel';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import SmartHSSearch from '../SmartHSSearch';
import { Package, ChevronDown, ChevronUp, Sparkles, AlertTriangle, Info, Calculator, Globe, FileText, CheckCircle, ClipboardList, Scale, FileCheck, Shield, DollarSign, RotateCcw } from 'lucide-react';
import DetailedCalculationBreakdown from './DetailedCalculationBreakdown';
import TaxBreakdownDual from './TaxBreakdownDual';
import CalculationJournal from './CalculationJournal';
import CalculationMethodStatus from './CalculationMethodStatus';
import { DetailedTaxTable, SavingsHighlight, TaxComparisonBarChart, TaxDistributionPieChart } from './TaxBreakdownChart';
import MultiCountryComparison from './MultiCountryComparison';
import DataStatusBanner from '../common/DataStatusBanner';
import DismantlementSchedule from './DismantlementSchedule';
import RegulatoryDetailsPanel from './RegulatoryDetailsPanel';
import TariffDownloads from '../tools/TariffDownloads';
import NationalPositionsSelector from '../NationalPositionsSelector';
import ProductKeywordSearch from './ProductKeywordSearch';
import KenyaRemissionAuthorization from './KenyaRemissionAuthorization';
import TariffDocumentationPanel from './TariffDocumentationPanel';
import RegulatoryComplianceView, {
  hasActiveMandatedProvider,
  hasUnpricedActiveProviderFees,
} from '../regulatory/RegulatoryComplianceView';
import RegulatoryCostBreakdown from './RegulatoryCostBreakdown';
import RegulatoryReportedIndications from './RegulatoryReportedIndications';
import { normalizeTaxesDetail } from './taxesDetail';
import { buildCalculRequestBody, mapCalculToLegacyResult, moteurRendCompteDesMesures } from './unifiedCalculator';
import { trierAvantages } from './avantagesFiscaux';
import {
  effectiveTaxRateFromSteps,
  isCustomsDutyTax,
  isDisplayableZlecafResult,
  neutralizeZlecafBreakdown,
  neutralizeZlecafSummary,
  resolveZlecafAvailability,
  zlecafTotalTaxRatePct,
} from './zlecafAvailability';
import './calculator.css';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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
  const [selectedSubPositionFormalities, setSelectedSubPositionFormalities] = useState(null);
  // Repli en mode saisie directe (hors recherche intelligente) : celle-ci ne
  // remplit jamais selectedSubPositionDesc, donc sans ce hook le code SH
  // reste affiché nu tant qu'aucune sélection via recherche n'a été faite.
  const { label: hsCodeSimpleLabel } = useHsLabel(hsCode, language);
  const [countryTariffProfile, setCountryTariffProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [regulatorySelectedPos, setRegulatorySelectedPos] = useState(null);
  const [regulatorySelectedPosDesc, setRegulatorySelectedPosDesc] = useState(null);
  const [searchResetKey, setSearchResetKey] = useState(0);
  const [kenyaRemission, setKenyaRemission] = useState({
    answer: 'unknown',
    reference: '',
    validFrom: '',
    validTo: '',
    authorizedTariffLines: '',
    authorizedGoods: '',
  });
  // Quantité saisie pour les droits spécifiques (« 8c/kg »). Vide tant que
  // le moteur ne l'a pas réclamée : le champ n'apparaît que sur les positions
  // qui en portent un, et l'unité affichée est celle que la source publie.
  const [quantity, setQuantity] = useState('');
  // La quantité appartient à UNE position et à UNE destination. Sans ce
  // repère, un poids saisi pour une position serait renvoyé tel quel sur la
  // suivante — et liquiderait son droit spécifique sur une quantité qui n'est
  // pas la sienne. Le rapprochement est explicite plutôt que remis à un effet
  // de bord, qui s'exécuterait après l'appel qu'il doit protéger.
  const [quantityFor, setQuantityFor] = useState(null);
  const profileRequestRef = useRef(0);

  // Vider le champ quand la position ou la destination change. La justesse ne
  // dépend pas de cet effet — c'est `quantityFor` qui empêche une quantité de
  // servir sur une autre position, et il est évalué au moment de l'appel. Cet
  // effet évite seulement d'AFFICHER un poids qui n'est plus celui du calcul.
  useEffect(() => {
    setQuantity('');
    setQuantityFor(null);
  }, [hsCode, destinationCountry, originCountry]);

  const fetchCountryTariffProfile = useCallback(async (countryCode) => {
    if (!countryCode) {
      setCountryTariffProfile(null);
      return;
    }
    const requestId = ++profileRequestRef.current;
    setLoadingProfile(true);
    try {
      const response = await axios.get(`${API}/tariff-data/${countryCode}?limit=1`);
      // Ignore les réponses obsolètes (ex. après une réinitialisation ou un changement de pays)
      if (requestId !== profileRequestRef.current) return;
      setCountryTariffProfile(response.data);
    } catch (error) {
      console.error('Error fetching country tariff profile:', error);
      if (requestId !== profileRequestRef.current) return;
      setCountryTariffProfile(null);
    } finally {
      if (requestId === profileRequestRef.current) setLoadingProfile(false);
    }
  }, []);

  const handleDestinationChange = useCallback((value) => {
    setDestinationCountry(value);
    fetchCountryTariffProfile(value);
  }, [fetchCountryTariffProfile]);

  const handleRegulatoryHsCodeChange = useCallback((e) => {
    setHsCode(e.target.value);
    setRegulatorySelectedPos(null);
    setRegulatorySelectedPosDesc(null);
  }, []);

  // Remove redundant useEffect - handleDestinationChange already calls fetchCountryTariffProfile

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

  // Code SH6 « pur » : on n'affiche les positions nationales avoisinantes que
  // lorsque l'utilisateur a saisi exactement un code à 6 chiffres (pas 8/10).
  const hsCodeDigits = hsCode.replace(/\D/g, '');
  const isHs6Only = hsCodeDigits.length === 6;

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

  const resetSearch = () => {
    setOriginCountry('');
    setDestinationCountry('');
    setHsCode('');
    setValue('');
    setResult(null);
    setDetailedResult(null);
    setShowHSBrowser(false);
    setShowDetailedBreakdown(false);
    setHs6TariffInfo(null);
    setSubPositions(null);
    setRuleOfOrigin(null);
    setSelectedSubPositionDesc(null);
    setSelectedSubPositionFormalities(null);
    setCountryTariffProfile(null);
    setRegulatorySelectedPos(null);
    setRegulatorySelectedPosDesc(null);
    setLoadingProfile(false);
    profileRequestRef.current++;
    setSearchResetKey((k) => k + 1);
    setKenyaRemission({
      answer: 'unknown', reference: '', validFrom: '', validTo: '',
      authorizedTariffLines: '', authorizedGoods: '',
    });
  };

  const calculateTariff = async (overrideHsCode) => {
    // overrideHsCode : recalcul immédiat après sélection d'une position
    // nationale dans la liste (sinon l'état hsCode n'est pas encore à jour
    // au moment de cet appel, à cause du batching React setState/onClick).
    // Attention : le bouton « Calculer » câble `onClick={calculateTariff}`,
    // donc React passe l'événement de clic comme premier argument. On ne
    // retient donc `overrideHsCode` que si c'est réellement une chaîne de
    // code ; sinon (SyntheticEvent) `.replace` planterait et aucun résultat
    // ne s'afficherait.
    const hsCodeToUse =
      typeof overrideHsCode === 'string' && overrideHsCode ? overrideHsCode : hsCode;
    if (!originCountry || !destinationCountry || !hsCodeToUse || !value) {
      toast({
        title: t.missingFields,
        description: t.fillAllFields,
        variant: "destructive"
      });
      return;
    }

    // Validation: code HS entre 6 et 12 chiffres
    const cleanHsCode = hsCodeToUse.replace(/[.\s]/g, '');
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
      // LE MÊME APPEL AU SOCLE, DEMANDÉ À DEUX ENDROITS.
      //
      // Il sert AVANT le chemin historique pour les pays de
      // `SOCLE_EN_PREMIER`, et APRÈS lui pour tous les autres. Construit une
      // seule fois : deux corps de requête écrits séparément finiraient par
      // diverger, et l'un des deux liquiderait autre chose que l'autre.
      const demanderLeSocle = () => axios.post(`${API}/calcul`, buildCalculRequestBody({
        destinationISO3: destISO3,
        originISO3,
        hsCode: cleanHsCode,
        cifValue: parseFloat(value),
        // `parseFloat('')` rend NaN : `buildCalculRequestBody` l'écarte, et
        // le moteur continue de réclamer la quantité au lieu de liquider
        // le droit spécifique à zéro. Une quantité saisie pour une AUTRE
        // position est écartée de la même façon.
        quantite: quantityFor === `${destISO3}|${cleanHsCode}`
          ? parseFloat(quantity)
          : NaN,
      }));

      // PRIORITÉ 1 POUR CES PAYS SEULEMENT : LE SOCLE (`POST /calcul`).
      //
      // L'ordre était inverse, et il coûtait cher. Le chemin historique
      // `/authentic-tariffs` sert une quarantaine de pays ; tant qu'il passait
      // devant, tout ce que le socle vérifie ne parvenait qu'aux autres. La
      // colonne algérienne du tarif tunisien (13 362 positions) et les douze
      // régimes préférentiels mauriciens, établis sur source primaire et
      // scellés par empreinte, n'atteignaient jamais l'opérateur — leurs deux
      // pays étaient servis par l'autre porte.
      //
      // POURQUOI DEUX PAYS ET NON LES CINQUANTE-QUATRE. La bascule générale a
      // été écrite, puis restreinte : l'interface n'envoie au socle ni
      // `devise_cif`, ni `taux_de_change`, ni `valeur_fob`. Or la valeur en
      // douane de la SACU est la valeur FOB, jamais déduite du CIF. Mesuré sur
      // les 1 500 premières positions sud-africaines, 616 — 41 % — répondent
      // `VALEUR_FOB_REQUISE` : leur droit de douane devient indisponible. Le
      // chemin historique, lui, servait un montant. Basculer l'Afrique du Sud
      // aujourd'hui échangerait donc une préférence manquante contre un droit
      // manquant, ce qui n'est pas un progrès.
      //
      // Deux autres manques tiennent au même périmètre et justifient la même
      // prudence : les réponses du formulaire de remise kényane
      // (`remission_eligibility` et ses cinq champs d'autorisation) n'existent
      // que sur le chemin historique, et `moteurRendCompteDesMesures` ne peut
      // rien vérifier quand le chemin historique n'a pas été consulté — son
      // garde devient vide.
      //
      // Cette liste s'allonge PAYS PAR PAYS, quand le socle sert ce pays mieux
      // que l'autre porte et que rien de ce qui précède ne lui manque. Elle ne
      // se remplace pas par « tous ».
      const SOCLE_EN_PREMIER = new Set(['TUN', 'MUS']);

      let calculSocle = null;
      let erreurSocle = null;
      if (SOCLE_EN_PREMIER.has(destISO3)) {
        try {
          calculSocle = (await demanderLeSocle()).data;
        } catch (socleError) {
          // Deux refus seulement justifient le repli, et ce sont des ABSENCES,
          // pas des pannes : 404, la position n'est pas au socle ; 503, le socle
          // est absent ou périmé et refuse de servir. Tout le reste — 422 de
          // validation, 500, 401/403, réseau — remonte, comme avant, plutôt que
          // de dégrader en silence vers une source moins vérifiée.
          const statut = socleError.response?.status;
          if (statut !== 404 && statut !== 503) {
            throw socleError;
          }
          erreurSocle = socleError;
          console.log(`ℹ️ Position absente du socle pour ${destISO3} (${statut}) - repli sur le chemin historique`);
        }
      }

      // PRIORITÉ 2 : le chemin historique, quand le socle ne sert pas.
      let authenticResult = null;
      let useAuthenticData = false;
      // Renseignées seulement quand le chemin historique refuse la position
      // faute de savoir liquider une mesure : elles conditionnent l'acceptation
      // de la réponse du moteur.
      let mesuresReclamees = [];
      let erreurAuthentique = null;
      
      // Le chemin historique n'est CONSULTÉ que si le socle n'a pas servi.
      if (!calculSocle) {
        try {
          const remissionEligibility = kenyaRemission.answer === 'no'
            ? 'NOT_ELIGIBLE'
            : kenyaRemission.answer === 'yes'
              ? 'ELIGIBLE_VERIFIED'
              : 'ELIGIBILITY_UNKNOWN';
          const authenticResponse = await axios.get(
            `${API}/authentic-tariffs/calculate/${destISO3}/${cleanHsCode}`,
            {
              params: {
                value: parseFloat(value),
                language,
                origin: originISO3,
                remission_eligibility: remissionEligibility,
                authorization_reference: kenyaRemission.reference || undefined,
                authorization_valid_from: kenyaRemission.validFrom || undefined,
                authorization_valid_to: kenyaRemission.validTo || undefined,
                authorization_hs_codes: kenyaRemission.authorizedTariffLines || undefined,
                authorization_goods: kenyaRemission.authorizedGoods || undefined,
              },
            },
          );
          authenticResult = authenticResponse.data;
          useAuthenticData = true;
          console.log('✅ Using AUTHENTIC tariff data for', destISO3);
        } catch (authError) {
          // Un 404 — route absente ou pays/position sans donnée authentique —
          // est le seul signal qui justifie le repli vers le moteur unifié :
          // c'est une absence de donnée, pas une panne. Tout le reste (500,
          // délai dépassé, 401/403, erreur réseau) remonte au `catch` externe
          // et s'affiche à l'utilisateur, plutôt que de dégrader en silence
          // vers un calcul qui ignore les avantages fiscaux et les formalités.
          // Un 422 `CALCULATION_UNAVAILABLE` n'est pas une panne : c'est le
          // chemin historique qui dit ne pas savoir liquider cette position —
          // typiquement un droit spécifique (« 8c/kg »), qu'il ne sait pas
          // calculer faute de paramètre de quantité. Le moteur unique, lui,
          // le liquide dès qu'on lui donne la quantité. Laisser ce cas remonter
          // en erreur revenait à refuser un calcul que le dépôt sait faire.
          //
          // Le repli reste étroit à dessein : seul ce code d'erreur passe. Un
          // 422 de validation (valeur CIF invalide) et tout le reste (500,
          // délai, 401/403, réseau) remontent comme avant.
          const codeErreur = authError.response?.data?.detail?.code;
          const calculIndisponible =
            authError.response?.status === 422 && codeErreur === 'CALCULATION_UNAVAILABLE';
          if (authError.response?.status !== 404 && !calculIndisponible) {
            throw authError;
          }
          if (calculIndisponible) {
            // Ce que l'autre chemin a nommé comme manquant. Le moteur devra en
            // rendre compte, sinon son total est refusé et l'erreur d'origine
            // est rétablie — voir `moteurRendCompteDesMesures`.
            mesuresReclamees = authError.response?.data?.detail?.missing_or_non_ad_valorem_taxes || [];
            erreurAuthentique = authError;
          }
          console.log(
            calculIndisponible
              ? `ℹ️ Position non liquidable par le chemin authentique pour ${destISO3} (${(authError.response?.data?.detail?.missing_or_non_ad_valorem_taxes || []).join(', ')}) - passage au moteur unique`
              : `ℹ️ Authentic tariff data not available for ${destISO3} - falling back to calculated data`
          );
        }
      }
      
      if (useAuthenticData && authenticResult) {
        // Transformer les données authentiques au format attendu par l'UI
        const npfCalc = authenticResult.npf_calculation || {};
        const zlecafCalc = authenticResult.zlecaf_calculation || {};
        const savings = authenticResult.savings || {};
        const rates = authenticResult.rates || {};
        const cifValue = parseFloat(value);
        const zlecafAvailability = resolveZlecafAvailability(authenticResult);
        const hasZlecafRate = zlecafAvailability.available;
        const totalTaxesZlecaf = hasZlecafRate
          ? effectiveTaxRateFromSteps(authenticResult.calculation_steps_zlecaf, cifValue)
          : null;
        
        // Construire le résultat au format compatible
        const transformedResult = {
          origin_country: originCountry,
          // Code ISO3 de l'origine : la carte des colonnes préférentielles
          // doit savoir QUEL partenaire est concerné pour écarter celles qui
          // en nomment un autre.
          origin_country_iso3: originISO3,
          destination_country: destinationCountry,
          hs_code: cleanHsCode,
          hs6_code: authenticResult.hs6 || cleanHsCode.substring(0, 6),
          value: cifValue,
          
          // Tarifs
          normal_tariff_rate: (rates.dd_rate_pct || 0) / 100,
          // Droit NPF tel que la source le donne, SANS le `|| 0` ci-dessus :
          // un droit absent doit rester absent. Comparer une colonne
          // préférentielle à un zéro de repli ferait passer toute colonne non
          // nulle pour un désavantage.
          npf_dd_rate_pct:
            typeof rates.dd_rate_pct === 'number' && Number.isFinite(rates.dd_rate_pct)
              ? rates.dd_rate_pct
              : null,
          normal_tariff_amount: npfCalc.dd?.amount || 0,
          zlecaf_tariff_rate: hasZlecafRate
            ? zlecafAvailability.effectiveRatePct / 100
            : null,
          zlecaf_tariff_amount: hasZlecafRate ? (zlecafCalc.dd?.amount ?? 0) : null,
          
          // TVA
          normal_vat_rate: (rates.vat_rate_pct || 0) / 100,
          normal_vat_amount: npfCalc.vat?.amount || 0,
          zlecaf_vat_rate: hasZlecafRate ? (rates.vat_rate_pct || 0) / 100 : null,
          zlecaf_vat_amount: hasZlecafRate ? (zlecafCalc.vat?.amount ?? 0) : null,
          
          // Autres taxes
          normal_other_taxes_total: npfCalc.other_taxes?.amount || 0,
          zlecaf_other_taxes_total: hasZlecafRate ? (zlecafCalc.other_taxes?.amount ?? 0) : null,
          
          // Totaux
          normal_total_cost: npfCalc.total_to_pay || 0,
          zlecaf_total_cost: hasZlecafRate ? (zlecafCalc.total_to_pay ?? null) : null,
          
          // Taux effectif = total_taxes / CIF × 100 (cascade réelle, PAS somme de taux)
          total_taxes_npf: rates.effective_rate_pct || rates.total_rate_pct || 0,
          total_taxes_zlecaf: totalTaxesZlecaf,
          
          // Économies
          savings: hasZlecafRate ? (savings.amount ?? 0) : null,
          savings_percentage: hasZlecafRate ? (savings.percentage ?? 0) : null,
          total_savings_with_taxes: hasZlecafRate ? (savings.amount ?? 0) : null,
          total_savings_percentage: hasZlecafRate ? (savings.percentage ?? 0) : null,
          
          // Précision et source
          tariff_precision: 'authentic_data',
          data_source: 'authentic_tariff',

          // Régime commercial applicable (union douanière, ZLECAf, ZLE conditionnelle, NPF)
          trade_regime: authenticResult.trade_regime || null,
          trade_regime_code: authenticResult.trade_regime_code || null,
          trade_regime_note: authenticResult.trade_regime_note || null,
          preferential_regime_applied: authenticResult.preferential_regime_applied === true,
          // Éligibilité ZLECAf (réciprocité bilatérale + ratification continentale)
          zlecaf_eligible: authenticResult.zlecaf_eligible === true,
          zlecaf_preference_applied: authenticResult.zlecaf_preference_applied === true,
          zlecaf_note: authenticResult.zlecaf_note || null,
          // Renseigné uniquement quand le taux préférentiel dépassait le NPF
          // et a donc été écarté. Sans ce report, l'opérateur verrait un taux
          // qui ne correspond pas au barème sans savoir pourquoi.
          plancher_npf: authenticResult.plancher_npf || null,
          zlecaf_status: zlecafAvailability.status,
          zlecaf_rate_expression: authenticResult.zlecaf_rate_expression || null,
          zlecaf_rate_source: authenticResult.zlecaf_rate_source || null,
          zlecaf_rate_calculation_status:
            authenticResult.zlecaf_rate_calculation_status || null,
          // Taux publié au e-Tariff Book officiel de la ZLECAf mais non
          // vérifié comme applicable (OFFER_ONLY/PARTNER_NOTICE_REQUIRED) —
          // strictement informatif, jamais utilisé dans un calcul.
          zlecaf_offer_rate_pct: zlecafAvailability.offerRatePct,
          zlecaf_offer_rate_expression: zlecafAvailability.offerRateExpression,

          // Ventilation complète NPF vs ZLECAf + bi-devise (TaxBreakdownDual)
          taxes_breakdown: neutralizeZlecafBreakdown(
            authenticResult.taxes_breakdown,
            hasZlecafRate,
          ),
          taxes_summary: neutralizeZlecafSummary(
            authenticResult.taxes_summary,
            hasZlecafRate,
          ),
          currency: authenticResult.currency || null,
          calculation_profile_status: authenticResult.calculation_profile_status || 'default',
          cascade_legal_source: authenticResult.cascade_legal_source || null,
          
          // Détails des taxes — le chemin authentique renvoie un OBJET indexé
          // par code de taxe, l'affichage attend une liste : sans cette
          // normalisation, `taxes_detail.length` valait `undefined` et toute
          // la carte « Détail des Taxes » (donc la colonne ZLECAf par taxe)
          // disparaissait.
          taxes_detail: normalizeTaxesDetail(
            authenticResult.taxes_detail,
            authenticResult.taxes_breakdown,
          ),
          
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
          
          // Journal de calcul NPF — généré par le moteur cascade (vraies bases par pays)
          normal_calculation_journal: (() => {
            const cif = parseFloat(value);
            const steps = authenticResult.calculation_steps || [];
            const legalSource = authenticResult.cascade_legal_source || `Tarif officiel ${destISO3}`;
            const journal = [
              { step: 1, component: 'Valeur CIF', base: cif, rate: '-', amount: cif, cumulative: cif, legal_ref: 'Incoterms 2020' }
            ];
            steps.forEach((s, i) => {
              journal.push({
                step: i + 2,
                component: s.label || s.code,
                base: s.base_value,
                base_formula: s.base_formula,
                rate: `${s.rate_pct}%`,
                amount: s.amount,
                cumulative: s.cumulative,
                legal_ref: legalSource,
              });
            });
            return journal;
          })(),
          
          // Journal de calcul ZLECAf — moteur cascade avec DD préférentiel
          zlecaf_calculation_journal: hasZlecafRate ? (() => {
            const cif = parseFloat(value);
            const steps = authenticResult.calculation_steps_zlecaf || [];
            const legalSource = authenticResult.cascade_legal_source || `Tarif ZLECAf ${destISO3}`;
            const journal = [
              { step: 1, component: 'Valeur CIF', base: cif, rate: '-', amount: cif, cumulative: cif, legal_ref: 'Incoterms 2020' }
            ];
            steps.forEach((s, i) => {
              journal.push({
                step: i + 2,
                component: s.label || s.code,
                base: s.base_value,
                base_formula: s.base_formula,
                rate: `${s.rate_pct}%`,
                amount: s.amount,
                cumulative: s.cumulative,
                legal_ref: s.code === 'DD' ? `ZLECAf — ${legalSource}` : legalSource,
              });
            });
            return journal;
          })() : [],
          
          computation_order_ref: `Données tarifaires officielles ${destISO3} - Format enhanced_v2`,
          last_verified: authenticResult.generated_at ? new Date(authenticResult.generated_at).toISOString().split('T')[0] : '2025-02',
          confidence_level: 'very_high',
          kenya_legal_calculation: authenticResult.kenya_legal_calculation || null,

          // Formalités, prestataires mandatés et frais réglementaires — bloc
          // informatif strictement séparé des droits/taxes (voir
          // RegulatoryCostBreakdown / RegulatoryComplianceView / RegulatoryReportedIndications).
          // Sans ce report explicite, ces champs — présents dans la réponse API
          // authentique — étaient silencieusement perdus lors de la
          // reconstruction manuelle de `transformedResult`.
          regulatory_compliance: authenticResult.regulatory_compliance || null,
          regulatory_cost: authenticResult.regulatory_cost || null,
          regulatory_reported: authenticResult.regulatory_reported || null,
          national_legal_calculation: authenticResult.national_legal_calculation || null,
          generic_legal_calculation: authenticResult.generic_legal_calculation || authenticResult.legal_calculation || null
        };
        
        setResult(transformedResult);
        setDetailedResult(authenticResult);
        setShowDetailedBreakdown(true);
        
        // Récupérer les sous-positions authentiques depuis PostgreSQL
        const hs6 = cleanHsCode.substring(0, 6);
        try {
          // Try PostgreSQL API first (has real descriptions)
          let subPosResponse;
          try {
            subPosResponse = await axios.get(`${API}/postgres-tariffs/country/${destISO3}/sub-positions/${hs6}?language=${language}`);
          } catch (pgErr) {
            // Fallback to old API
            subPosResponse = await axios.get(`${API}/authentic-tariffs/country/${destISO3}/sub-positions/${hs6}?language=${language}`);
          }
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
          description: hasZlecafRate
            ? `${t.potentialSavings}: ${formatCurrency(savings.amount ?? 0)} (Données officielles ${destISO3})`
            : (authenticResult.zlecaf_status === 'OFFER_ONLY' || authenticResult.zlecaf_status === 'PARTNER_NOTICE_REQUIRED')
              ? (language === 'fr'
                ? `Offre tarifaire ZLECAf publiée pour ${destISO3}${zlecafAvailability.offerRateExpression ? ` (${zlecafAvailability.offerRateExpression})` : ''} — non vérifiée comme applicable, à confirmer avec les douanes locales (calcul NPF conservé)`
                : `Published AfCFTA tariff offer for ${destISO3}${zlecafAvailability.offerRateExpression ? ` (${zlecafAvailability.offerRateExpression})` : ''} — not verified as applicable, confirm with local customs (MFN calculation retained)`)
            : authenticResult.zlecaf_rate_expression
              ? (language === 'fr'
                ? `Taux officiel ZLECAf : ${authenticResult.zlecaf_rate_expression} — quantité requise, total non calculé (${destISO3})`
                : `Official AfCFTA rate: ${authenticResult.zlecaf_rate_expression} — quantity required, total not calculated (${destISO3})`)
            : (language === 'fr'
              ? `Taux ZLECAf non disponible pour cette ligne — calcul NPF conservé (${destISO3})`
              : `AfCFTA rate unavailable for this line — MFN calculation retained (${destISO3})`),
        });
        
      } else {
        // Pays sans chemin `/authentic-tariffs` : le calcul passe par la
        // route unique du moteur (chantier L3), plus par l'ancien
        // `/calculate-tariff` (`routes/calculator.py`) qui fabriquait des
        // montants sur un profil générique. Aucun repli supplémentaire —
        // une erreur ici remonte au `catch` externe et s'affiche, elle ne
        // bascule pas silencieusement vers une autre source.
        // DEUX CHEMINS ARRIVENT ICI, ET IL FAUT LES DISTINGUER.
        //
        // Pour un pays de `SOCLE_EN_PREMIER`, le socle a DÉJÀ été interrogé
        // plus haut : s'il n'a rien rendu, c'est que les deux portes ont
        // refusé, et l'erreur du socle reprend sa place plutôt qu'un écran
        // vide. Pour tous les autres pays, il n'a PAS encore été consulté —
        // c'est ici, après le refus du chemin historique, que sa réponse est
        // demandée, exactement comme avant ce lot. Aucun repli
        // supplémentaire : une erreur remonte au `catch` externe et s'affiche,
        // elle ne bascule pas en silence vers une autre source.
        if (!calculSocle) {
          if (erreurSocle) {
            throw erreurSocle;
          }
          calculSocle = (await demanderLeSocle()).data;
        }
        const calcul = calculSocle;
        // Un refus honnête ne se remplace pas par un total amputé. Si le
        // moteur ne dit rien d'une mesure que l'autre chemin réclamait, sa
        // réponse est écartée et l'erreur d'origine reprend sa place.
        if (!moteurRendCompteDesMesures(calcul, mesuresReclamees)) {
          throw erreurAuthentique;
        }
        const legacyResult = mapCalculToLegacyResult(calcul, {
          originCountry,
          destinationCountry,
          hsCode: cleanHsCode,
          cifValue: parseFloat(value),
        });

        setResult({
          ...legacyResult,
          taxes_detail: normalizeTaxesDetail(legacyResult.taxes_detail, legacyResult.taxes_breakdown),
          // La clé qui rattache une quantité à SA position. Construite ici, à
          // l'endroit exact où l'appel est fait, et relue telle quelle par le
          // champ de saisie : la reconstruire ailleurs à partir des champs
          // d'affichage (qui peuvent porter un code ISO2) la ferait diverger,
          // et la quantité saisie serait silencieusement écartée à chaque fois.
          _quantite_cle: `${destISO3}|${cleanHsCode}`,
        });
        setDetailedResult(null);
        setShowDetailedBreakdown(true);

        // Sous-positions et informations SH6 : données d'affichage annexes,
        // pas des montants — un manque y reste silencieux comme sur le
        // chemin authentique.
        const hs6 = cleanHsCode.substring(0, 6);
        try {
          let subPosResponse;
          try {
            subPosResponse = await axios.get(`${API}/postgres-tariffs/country/${destISO3}/sub-positions/${hs6}?language=${language}`);
          } catch (pgErr) {
            subPosResponse = await axios.get(`${API}/tariffs/sub-positions/${destISO3}/${hs6}?language=${language}`);
          }
          setSubPositions(subPosResponse.data);
        } catch (subPosError) {
          setSubPositions(null);
        }
        // LES FORMALITÉS SURVIVENT AU CHANGEMENT DE PRIORITÉ.
        //
        // Le socle porte des MONTANTS, pas les formalités administratives.
        // Basculer sur lui sans plus rien demander les aurait fait disparaître
        // pour les 40 pays que l'autre chemin servait — une régression de
        // produit déguisée en gain de rigueur. Elles sont donc redemandées
        // ici, en annexe, comme les sous-positions : un manque y reste
        // silencieux, parce qu'une formalité absente n'est pas un montant faux.
        //
        // Les « avantages fiscaux » du même chemin, eux, ne sont PAS repris :
        // voir le commentaire sur `fiscal_advantages` plus bas.
        try {
          const formalitesResponse = await axios.get(
            `${API}/authentic-tariffs/country/${destISO3}/formalities/${cleanHsCode}?language=${language}`
          );
          const formalites = formalitesResponse.data?.formalities || [];
          // Le STATUT accompagne la liste, et il est transmis même quand elle
          // est vide : c'est lui qui empêche l'écran de se taire, et le
          // silence de se lire « aucune obligation ».
          const statutFormalites = formalitesResponse.data?.statut || null;
          const reserveFormalites = formalitesResponse.data?.reserve || null;
          setResult((precedent) => (precedent
            ? {
              ...precedent,
              administrative_formalities: formalites.length > 0
                ? formalites
                : precedent.administrative_formalities,
              formalites_statut: statutFormalites,
              formalites_reserve: reserveFormalites,
            }
            : precedent));
        } catch (formalitesError) {
          // Silencieux : une formalité absente n'est pas un montant faux.
        }
        try {
          const hs6Response = await axios.get(`${API}/hs6-tariffs/code/${hs6}?language=${language}`);
          setHs6TariffInfo(hs6Response.data);
        } catch (hs6Error) {
          setHs6TariffInfo(null);
        }

        const npfEtat = calcul.npf?.etat;
        toast({
          title: npfEtat === 'COMPLET' ? t.calculationSuccess
            : (language === 'fr' ? 'Calcul incomplet' : 'Incomplete calculation'),
          description: npfEtat === 'COMPLET'
            ? (legacyResult.savings != null
              ? `${t.potentialSavings}: ${formatCurrency(legacyResult.savings)}`
              : `${destISO3} — ${language === 'fr' ? 'régime NPF' : 'MFN regime'}`)
            : (language === 'fr'
              ? `${destISO3} : un ou plusieurs droits n'ont pas pu être liquidés (${(calcul.npf?.manques || []).map((m) => m.code).join(', ') || '—'}) — total partiel, jamais un montant fabriqué`
              : `${destISO3}: one or more duties could not be liquidated (${(calcul.npf?.manques || []).map((m) => m.code).join(', ') || '—'}) — partial total, never a fabricated amount`),
          variant: npfEtat === 'COMPLET' ? 'default' : 'destructive',
        });
      }
    } catch (error) {
      console.error('Calculation error:', error);
      setResult(null);
      setDetailedResult(null);
      setShowDetailedBreakdown(false);
      const detail = error.response?.data?.detail;
      toast({
        title: t.calculationError,
        description: typeof detail === 'string' ? detail : (detail?.message || t.calculationError),
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
      {/* Bandeau statut des données — par pays importateur si sélectionné */}
      <DataStatusBanner countryIso3={destinationCountry || undefined} />

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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

            {/* ── Recherche par mot-clé ── */}
            <ProductKeywordSearch
              key={`pks-${searchResetKey}`}
              destinationCountry={destinationCountry}
              language={language}
              onSelect={(code, desc) => {
                if (code) {
                  setHsCode(code);
                  setSelectedSubPositionDesc(desc);
                }
              }}
            />

            {/* ── Séparateur ou code HS direct ── */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-px bg-slate-700" />
              <span className="text-xs text-slate-600 shrink-0">
                {language === 'fr' ? 'ou saisir directement' : 'or enter directly'}
              </span>
              <div className="flex-1 h-px bg-slate-700" />
            </div>

            {useSmartSearch ? (
              <SmartHSSearch
                key={`smart-${searchResetKey}`}
                value={hsCode}
                onChange={setHsCode}
                destinationCountry={destinationCountry}
                language={language}
                onSubPositionSelect={(code, desc, formalities) => {
                  setHsCode(code);
                  setSelectedSubPositionDesc(desc);
                  setSelectedSubPositionFormalities(formalities || null);
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
                {hsCodeSimpleLabel ? (
                  <p className="text-emerald-400 text-xs truncate" title={hsCodeSimpleLabel}>
                    {hsCodeSimpleLabel}
                  </p>
                ) : (
                  <p className="text-slate-500 text-xs">{t.hsCodeHint}</p>
                )}
              </div>
            )}

            {/* Code sélectionné via recherche */}
            {hsCode && selectedSubPositionDesc && (
              <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 rounded-lg px-3 py-2">
                <span className="font-mono text-purple-300 text-sm font-bold shrink-0">{hsCode}</span>
                <span className="text-slate-400 text-xs line-clamp-1">{selectedSubPositionDesc}</span>
              </div>
            )}

            {/* Règle d'origine ZLECAf applicable au code sélectionné.
                hs_code is matched against the current input so a rule loaded
                for a previous code (e.g. via Smart Search) never lingers
                after the user switches to simple input or types a new code. */}
            {ruleOfOrigin && ruleOfOrigin.rule && ruleOfOrigin.rules && ruleOfOrigin.hs_code === hsCode && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-amber-300 text-xs font-semibold uppercase tracking-wide">
                    {language === 'fr' ? "Règle d'origine ZLECAf" : 'AfCFTA Rule of Origin'}
                  </span>
                  <Badge className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs">
                    {ruleOfOrigin.rules.primary_rule?.name || ruleOfOrigin.rules.primary_rule?.code}
                  </Badge>
                  {ruleOfOrigin.rules.regional_content != null && (
                    <Badge className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs">
                      {language === 'fr' ? 'Contenu régional' : 'Regional content'}: {ruleOfOrigin.rules.regional_content}%
                    </Badge>
                  )}
                  {ruleOfOrigin.status === 'YTB' && (
                    <Badge className="bg-orange-500/20 text-orange-300 border border-orange-500/30 text-xs">
                      {language === 'fr' ? 'En négociation' : 'Under negotiation'}
                    </Badge>
                  )}
                </div>
                {ruleOfOrigin.rules.primary_rule?.explanation && (
                  <p className="text-slate-300 text-xs leading-relaxed">
                    {ruleOfOrigin.rules.primary_rule.explanation}
                  </p>
                )}
                {ruleOfOrigin.rules.alternative_rule && (
                  <p className="text-slate-500 text-xs">
                    {language === 'fr' ? 'Règle alternative' : 'Alternative rule'}: {ruleOfOrigin.rules.alternative_rule.name}
                  </p>
                )}
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
              data-testid="cif-value-input"
            />
          </div>

          {/* Sélecteur de Positions Nationales — uniquement pour un code SH6 (6 chiffres) */}
          {destinationCountry && isHs6Only && (
            <NationalPositionsSelector
              countryCode={destinationCountry}
              hs6Code={hsCodeDigits}
              language={language}
              selectedPosition={hsCode}
              onPositionSelect={(code, description) => {
                setHsCode(code);
                setSelectedSubPositionDesc(description);
              }}
            />
          )}

          {['KEN', 'KE'].includes(destinationCountry) && (
            <KenyaRemissionAuthorization
              value={kenyaRemission}
              onChange={setKenyaRemission}
            />
          )}

          {/* Boutons Calculer / Réinitialiser */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              onClick={() => calculateTariff()}
              disabled={loading}
              data-testid="calculate-tariff-button"
              className="flex-1 h-14 text-lg font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-lg hover:shadow-xl transition-all"
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
            <Button
              type="button"
              variant="outline"
              onClick={resetSearch}
              disabled={loading}
              data-testid="reset-search-button"
              title={language === 'fr' ? 'Réinitialiser la recherche' : 'Reset search'}
              className="h-14 px-5 border-slate-600 text-slate-300 hover:border-red-500/50 hover:text-red-400 hover:bg-red-500/10 transition-all"
            >
              <RotateCcw className="w-5 h-5 mr-2" />
              {language === 'fr' ? 'Réinitialiser' : 'Reset'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* === RÉSULTATS === */}
      {result && (
        <div className="space-y-4 animate-in fade-in duration-300">
          {/* En-tête des résultats avec synthèse */}
          <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden transition-all duration-300">
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
              {/* Bandeau régime commercial applicable :
                  - CUSTOMS_UNION  → libre circulation intra-union (positif, vert)
                  - FTA_CONDITIONAL → régime du bloc possible sous conditions (ambre)
                  - NPF             → aucune préférence (avertissement, ambre)
                  - ZLECAF          → pas de bandeau EN GÉNÉRAL (la colonne
                                      préférentielle suffit), SAUF si le
                                      plancher NPF a écarté le taux du barème :
                                      l'opérateur verrait sinon un taux qui ne
                                      correspond à aucune source lisible. */}
              {result.trade_regime === 'CUSTOMS_UNION' && (
                <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-start gap-3">
                  <Shield className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-emerald-300 font-semibold text-sm">
                      {language === 'fr'
                        ? `Union douanière ${result.trade_regime_code || ''} — libre circulation`
                        : `${result.trade_regime_code || ''} customs union — free circulation`}
                    </p>
                    <p className="text-emerald-200/80 text-sm mt-1">{result.trade_regime_note}</p>
                  </div>
                </div>
              )}

              {result.trade_regime === 'FTA_CONDITIONAL' && (
                <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3">
                  <Info className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-amber-300 font-semibold text-sm">
                      {language === 'fr'
                        ? `Régime ${result.trade_regime_code || 'du bloc'} applicable sous conditions`
                        : `${result.trade_regime_code || 'Bloc'} regime applies under conditions`}
                    </p>
                    <p className="text-amber-200/80 text-sm mt-1">{result.trade_regime_note}</p>
                  </div>
                </div>
              )}

              {result.trade_regime === 'NPF' && result.zlecaf_note && (
                <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-amber-300 font-semibold text-sm">
                      {language === 'fr' ? 'Préférence ZLECAf non appliquée' : 'AfCFTA preference not applied'}
                    </p>
                    <p className="text-amber-200/80 text-sm mt-1">{result.zlecaf_note}</p>
                  </div>
                </div>
              )}

              {/* Simulations régionales — ce que le tarif de DESTINATION publie
                  pour ce couloir sous un autre régime, chiffré par le moteur
                  et JAMAIS appliqué. Le total facturé plus haut ne bouge pas.

                  Sur le couloir Mozambique → Afrique du Sud, position 020110,
                  la colonne SADC publie 0 % quand la ZLECAf reste à 40 % :
                  l'opérateur voyait 161 000 sans qu'aucun champ ne lui signale
                  les 115 000 que son tarif de destination publie pourtant.

                  L'ordre est celui que le backend rend — alphabétique, pas
                  classé par avantage. Trier par montant mettrait en tête le
                  régime dont les règles d'origine sont précisément ce que le
                  moteur ne vérifie pas. */}
              {/* Droit spécifique : la quantité, demandée seulement là où elle sert.

                  Un droit publié « 8c/kg » ne se liquide pas sur la valeur. Le
                  moteur rend alors QUANTITE_REQUISE et nomme l'unité que la
                  source publie ; ce champ la reprend telle quelle. Trois cas,
                  et ils ne se confondent pas :

                  - unité publiée → on demande la quantité dans CETTE unité ;
                  - unité non publiée (droit sanitaire vétérinaire tunisien,
                    « 0.1 dinars » sans unité) → on ne demande RIEN et on dit
                    pourquoi : demander « un poids » produirait un montant faux ;
                  - deux unités divergentes sur la même position → une quantité
                    unique en servirait une pour l'autre ; on refuse de même.

                  0,9 % des positions sont concernées (3 260 sur 358 752) : le
                  champ reste absent partout ailleurs. */}
              {result.quantite_requise?.requise && (
                <div
                  className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl"
                  data-testid="quantite-requise"
                >
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-amber-300 font-semibold text-sm">
                        {language === 'fr'
                          ? 'Droit spécifique : quantité nécessaire'
                          : 'Specific duty: quantity required'}
                      </p>

                      <div className="mt-2 space-y-1">
                        {result.quantite_requise.lignes.map((l) => (
                          <p key={l.code} className="text-amber-200/80 text-xs">
                            <span className="font-mono">{l.code}</span> — {l.libelle}
                            {l.specifique ? ` : ${l.specifique}` : ''}
                          </p>
                        ))}
                      </div>

                      {result.quantite_requise.unite ? (
                        <div className="mt-3 flex flex-wrap items-end gap-2">
                          <div>
                            <label
                              className="block text-amber-200/70 text-xs mb-1"
                              htmlFor="quantite-droit-specifique"
                            >
                              {language === 'fr'
                                ? `Quantité importée (${result.quantite_requise.unite})`
                                : `Imported quantity (${result.quantite_requise.unite})`}
                            </label>
                            <input
                              id="quantite-droit-specifique"
                              data-testid="quantite-saisie"
                              type="number"
                              min="0"
                              step="any"
                              value={quantity}
                              onChange={(e) => {
                                setQuantity(e.target.value);
                                setQuantityFor(result._quantite_cle);
                              }}
                              className="w-40 px-3 py-2 bg-slate-900/60 border border-amber-500/40 rounded-lg text-white text-sm"
                              placeholder={result.quantite_requise.unite}
                            />
                          </div>
                          <Button
                            type="button"
                            data-testid="quantite-recalculer"
                            onClick={() => calculateTariff()}
                            disabled={loading || !(parseFloat(quantity) > 0)}
                            className="bg-amber-600 hover:bg-amber-700"
                          >
                            {language === 'fr' ? 'Recalculer' : 'Recalculate'}
                          </Button>
                        </div>
                      ) : (
                        <p className="text-amber-200/70 text-xs mt-3">
                          {result.quantite_requise.uniteAmbigue
                            ? (language === 'fr'
                              ? "Cette position porte deux droits spécifiques exprimés dans des unités différentes : une quantité unique en liquiderait un dans la mauvaise unité. Le total reste incomplet."
                              : 'This line carries two specific duties expressed in different units: a single quantity would settle one of them in the wrong unit. The total remains incomplete.')
                            : (language === 'fr'
                              ? "La source ne publie pas l'unité de quantité de ce droit. Demander un poids ici produirait un montant faux : le total reste incomplet tant que l'unité n'est pas établie."
                              : 'The source does not publish this duty\u2019s unit of quantity. Asking for a weight here would produce a wrong amount: the total remains incomplete until the unit is established.')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {Array.isArray(result.regional_simulations) && result.regional_simulations.length > 0 && (
                <div className="mb-6 p-4 bg-sky-500/10 border border-sky-500/30 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-sky-400 mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-sky-300 font-semibold text-sm">
                        {language === 'fr'
                          ? 'Autres régimes publiés par le tarif de destination'
                          : 'Other regimes published by the destination tariff'}
                      </p>
                      <p className="text-sky-200/70 text-xs mt-1">
                        {language === 'fr'
                          ? "Simulations, non appliquées au total ci-dessus."
                          : 'Simulations, not applied to the total above.'}
                      </p>

                      <div className="mt-3 space-y-2">
                        {result.regional_simulations.map((sim) => (
                          <div
                            key={sim.regime}
                            className="p-3 bg-slate-900/40 border border-slate-700/60 rounded-lg"
                            data-testid={`regional-simulation-${sim.regime}`}
                          >
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                              <span className="text-slate-200 text-sm font-medium">{sim.libelle}</span>
                              <span className="font-mono text-sm text-sky-300">
                                {sim.taux_publie_pct} % · {sim.prelevement}
                              </span>
                            </div>
                            {sim.total_simule !== null && sim.total_simule !== undefined && (
                              <div className="flex flex-wrap items-baseline justify-between gap-2 mt-1">
                                <span className="text-slate-400 text-xs">
                                  {language === 'fr' ? 'Total simulé' : 'Simulated total'}
                                </span>
                                <span className="font-mono text-base text-slate-100">
                                  {sim.total_simule.toLocaleString('fr-FR')}
                                  {sim.ecart_vs_total_servi !== null &&
                                    sim.ecart_vs_total_servi !== undefined && (
                                      <span className="text-slate-400 text-xs ml-2">
                                        {language === 'fr' ? 'écart ' : 'gap '}
                                        {sim.ecart_vs_total_servi.toLocaleString('fr-FR')}
                                      </span>
                                    )}
                                </span>
                              </div>
                            )}
                            <p className="text-slate-400 text-xs mt-2">{sim.reserve}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {result.plancher_npf && (
                <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3">
                  <Info className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-amber-300 font-semibold text-sm">
                      {language === 'fr'
                        ? `Taux NPF servi (${result.plancher_npf.taux_retenu_pct} %) : le barème préférentiel est plus cher`
                        : `MFN rate applied (${result.plancher_npf.taux_retenu_pct}%): the preferential schedule costs more`}
                    </p>
                    <p className="text-amber-200/80 text-sm mt-1">
                      {language === 'fr'
                        ? `Le barème préférentiel de cette position affiche ${result.plancher_npf.taux_preferentiel_ecarte_pct} %, soit davantage que le droit commun. Une préférence est une faculté, pas une obligation : c'est le NPF qui est servi.`
                        : `The preferential schedule for this line shows ${result.plancher_npf.taux_preferentiel_ecarte_pct}%, more than the ordinary duty. A preference is an option, not an obligation: the MFN rate is applied.`}
                    </p>
                  </div>
                </div>
              )}

              <TariffDocumentationPanel result={result} language={language} />

              {/* Bandeau Valeur CIF + Code HS sélectionné */}
              <div className="mb-6 p-4 bg-gradient-to-r from-slate-700/50 to-slate-800/50 rounded-xl border border-slate-600/50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Valeur CIF */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/10 rounded-lg">
                      <DollarSign className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-slate-500 text-xs uppercase">{language === 'fr' ? 'Valeur CIF' : 'CIF Value'}</p>
                      <p className="text-xl font-bold text-emerald-400">
                        {formatCurrency(parseFloat(value) || 0)}
                      </p>
                    </div>
                  </div>
                  
                  {/* Code HS utilisé */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/10 rounded-lg">
                      <Package className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-slate-500 text-xs uppercase">{language === 'fr' ? 'Code Tarifaire' : 'Tariff Code'}</p>
                      <p className="font-mono text-lg font-bold text-purple-400">{result.hs_code || hsCode}</p>
                    </div>
                  </div>
                  
                  {/* Description produit */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-500/10 rounded-lg">
                      <FileText className="w-5 h-5 text-amber-400" />
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-500 text-xs uppercase">{language === 'fr' ? 'Produit' : 'Product'}</p>
                      <p className="text-sm text-slate-300 truncate">
                        {selectedSubPositionDesc || detailedResult?.description || result.description || (language === 'fr' ? 'Position sélectionnée' : 'Selected position')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Grille de synthèse économique */}
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {/* Total NPF */}
                <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/20">
                  <p className="text-red-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Total NPF' : 'Total MFN'}</p>
                  <p className="text-3xl font-bold text-red-400 mt-1">{(result.total_taxes_npf || 0).toFixed(1)}%</p>
                  <p className="text-red-400/60 text-xs mt-1">{language === 'fr' ? 'Sans accord' : 'No agreement'}</p>
                </div>
                
                {/* Total ZLECAf */}
                <div className="bg-emerald-500/10 rounded-xl p-4 border border-emerald-500/20">
                  <p className="text-emerald-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Total ZLECAf' : 'Total AfCFTA'}</p>
                  <p className="text-3xl font-bold text-emerald-400 mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? `${zlecafTotalTaxRatePct(result).toFixed(1)}%`
                      : '—'}
                  </p>
                  <p className="text-emerald-400/60 text-xs mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? (language === 'fr' ? 'Avec accord' : 'With agreement')
                      : (result.zlecaf_status === 'OFFER_ONLY' || result.zlecaf_status === 'PARTNER_NOTICE_REQUIRED')
                        ? (language === 'fr'
                          ? `Offre publiée ZLECAf${result.zlecaf_offer_rate_expression ? ` : ${result.zlecaf_offer_rate_expression}` : ''} — à vérifier avec les douanes locales`
                          : `Published AfCFTA offer${result.zlecaf_offer_rate_expression ? `: ${result.zlecaf_offer_rate_expression}` : ''} — verify with local customs`)
                        : result.zlecaf_rate_expression
                          ? (language === 'fr'
                            ? `Taux ligne ${result.zlecaf_rate_expression} — quantité requise`
                            : `Line rate ${result.zlecaf_rate_expression} — quantity required`)
                          : (language === 'fr' ? 'Taux non disponible' : 'Rate unavailable')}
                  </p>
                </div>

                {/* Économie */}
                <div className="bg-amber-500/10 rounded-xl p-4 border border-amber-500/20">
                  <p className="text-amber-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Économie' : 'Savings'}</p>
                  <p className="text-3xl font-bold text-amber-400 mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? `-${((result.total_taxes_npf || 0) - zlecafTotalTaxRatePct(result)).toFixed(1)}%`
                      : '—'}
                  </p>
                  <p className="text-amber-400/60 text-xs mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? (language === 'fr' ? 'Certificat Origine' : 'Origin Certificate')
                      : (result.zlecaf_status === 'OFFER_ONLY' || result.zlecaf_status === 'PARTNER_NOTICE_REQUIRED')
                        ? (language === 'fr' ? 'À vérifier' : 'To verify')
                        : (language === 'fr' ? 'Non disponible' : 'Unavailable')}
                  </p>
                </div>
                
                {/* Montant économisé */}
                <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
                  <p className="text-blue-400/80 text-xs uppercase tracking-wide font-medium">{language === 'fr' ? 'Montant Économisé' : 'Amount Saved'}</p>
                  <p className="text-2xl font-bold text-blue-400 mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? `${((parseFloat(value) || 0) * ((result.total_taxes_npf || 0) - zlecafTotalTaxRatePct(result)) / 100).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} USD`
                      : '—'}
                  </p>
                  <p className="text-blue-400/60 text-xs mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? (language === 'fr' ? 'Sur votre valeur' : 'On your value')
                      : (language === 'fr' ? 'Non calculé' : 'Not calculated')}
                  </p>
                </div>
              </div>
              <p className="mt-4 text-center text-xs font-medium text-amber-300">
                Simulation informative — non opposable à l’administration douanière.
              </p>

              {/* Point 4 — signalement d'incomplétude : le total ci-dessus couvre les
                  droits et taxes exigibles, mais un prestataire mandaté actif facture
                  des frais dont le montant n'est pas chiffré dans les sources. Le coût
                  total réel de dédouanement est donc INCOMPLET — signalé, jamais estimé. */}
              {hasUnpricedActiveProviderFees(result.regulatory_compliance) && (
                <div className="mt-4 flex items-start gap-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-200/90">
                    {language === 'fr'
                      ? "Calcul incomplet : ces totaux couvrent les droits et taxes exigibles, mais un prestataire mandaté actif perçoit des frais dont le montant n'est pas publié dans les sources (NOT_AVAILABLE). Le coût total de dédouanement est donc supérieur — voir le bloc « Frais des prestataires mandatés » ci-dessous. Aucun montant n'est estimé."
                      : 'Incomplete calculation: these totals cover payable duties and taxes, but an active mandated provider charges fees whose amount is not published in the sources (NOT_AVAILABLE). The total clearance cost is therefore higher — see the “Mandated-provider fees” block below. No amount is estimated.'}
                  </p>
                </div>
              )}
              <p className="mt-4 text-center text-xs font-medium text-amber-300">
                Simulation informative — non opposable à l’administration douanière.
              </p>
            </CardContent>
          </Card>

          {/* Schéma de démantèlement ZLECAf */}
          {result && destinationCountry && hsCode && isDisplayableZlecafResult(result) && (
            <DismantlementSchedule
              countryIso3={destinationCountry}
              hs6={hsCode.replace(/[.\s]/g, '').slice(0, 6)}
              npfRate={result.customs_duty_rate ?? result.dd_rate_pct ?? result.tariff_rate ?? 0}
              language={language}
            />
          )}

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
                            {isDisplayableZlecafResult(result)
                              ? (typeof tax.rate_zlecaf_pct === 'number'
                                ? `${tax.rate_zlecaf_pct.toFixed(2)}%`
                                : isCustomsDutyTax(tax)
                                  ? `${(result.zlecaf_tariff_rate * 100).toFixed(2)}%`
                                  : `${tax.rate}%`)
                              : (isCustomsDutyTax(tax)
                                && result.zlecaf_rate_expression
                                ? result.zlecaf_rate_expression
                                : '—')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Détail complet NPF vs ZLECAf, base par base + bi-devise */}
          <CalculationMethodStatus
            status={result.calculation_profile_status}
            legalSource={result.cascade_legal_source}
            language={language}
          />

          {result.taxes_breakdown && result.taxes_breakdown.length > 0 && (
            <TaxBreakdownDual
              breakdown={result.taxes_breakdown}
              summary={result.taxes_summary}
              currency={result.currency}
              zlecafAvailable={isDisplayableZlecafResult(result)}
              language={language}
            />
          )}

          {/* Journal de calcul pas-à-pas (NPF / ZLECAf) avec références légales */}
          {((result.normal_calculation_journal && result.normal_calculation_journal.length > 0) ||
            (result.zlecaf_calculation_journal && result.zlecaf_calculation_journal.length > 0)) && (
            <CalculationJournal
              normalJournal={result.normal_calculation_journal}
              zlecafJournal={result.zlecaf_calculation_journal}
              language={language}
            />
          )}

          {/* Sous-positions nationales disponibles — uniquement pour un code SH6 (6 chiffres) */}
          {isHs6Only && subPositions && subPositions.sub_positions && subPositions.sub_positions.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                      <Scale className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <CardTitle className="text-lg text-white">
                        {language === 'fr' ? 'Positions Nationales' : 'National Positions'}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        {subPositions.sub_positions.length} {language === 'fr' ? 'positions (10 chiffres)' : 'positions (10 digits)'}
                        {subPositions.note && <span className="ml-2 text-purple-400/70 text-xs">— {subPositions.note}</span>}
                      </CardDescription>
                    </div>
                  </div>
                  {selectedSubPositionDesc && (
                    <Badge className="bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs">
                      {hsCode.replace(/[.\s]/g, '').slice(0, 10)} {language === 'fr' ? 'sélectionnée' : 'selected'}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {subPositions.sub_positions.map((sp, idx) => {
                    const code = sp.code || sp.national_code || '';
                    const isSelected = hsCode.replace(/[.\s]/g, '').startsWith(code.slice(0, 10));
                    const desc = language === 'fr' ? (sp.description_fr || sp.description_en) : (sp.description_en || sp.description_fr);
                    const spFormalities = sp.administrative_formalities || null;
                    return (
                      <div
                        key={idx}
                        onClick={() => {
                          setHsCode(code);
                          setSelectedSubPositionDesc(desc);
                          setSelectedSubPositionFormalities(spFormalities);
                          calculateTariff(code);
                        }}
                        data-testid={`sub-position-${code}`}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-purple-500/20 border-purple-500/50'
                            : 'bg-slate-700/30 border-slate-700 hover:border-purple-500/30 hover:bg-slate-700/50'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="font-mono text-sm font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded shrink-0">
                            {code}
                          </span>
                          <p className="text-slate-300 text-sm truncate">{desc}</p>
                        </div>
                        <div className="flex items-center gap-3 shrink-0 ml-3">
                          {spFormalities && spFormalities.length > 0 && (
                            <Badge className="bg-slate-600/50 text-slate-300 border border-slate-600 text-xs">
                              {spFormalities.length} {language === 'fr' ? 'docs' : 'docs'}
                            </Badge>
                          )}
                          {isSelected && <CheckCircle className="w-4 h-4 text-purple-400" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-500 mt-3 border-t border-slate-700 pt-2">
                  {language === 'fr'
                    ? 'Cliquez sur une position pour appliquer son taux et ses formalités spécifiques.'
                    : 'Click a position to apply its specific rate and formalities.'}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Documents requis — niveau position nationale si sélectionnée, sinon HS6 */}
          {(() => {
            // La position nationale est celle réellement utilisée pour le calcul
            // (result.hs_code, résolu par le backend), pas seulement celle dont
            // les formalités ont été transmises par tel ou tel chemin de
            // sélection — sinon une saisie directe du code à 10 chiffres, ou une
            // position sans formalité propre, retombe à tort sur le message HS6.
            const resolvedCode = (result.hs_code || hsCode || '').replace(/[.\s]/g, '');
            const isPositionLevel = resolvedCode.length >= 10;
            const formalities = (isPositionLevel && selectedSubPositionFormalities)
              || result.administrative_formalities;
            const positionCode = isPositionLevel ? resolvedCode : null;

            // LA CARTE NE DISPARAÎT PLUS QUAND LA LISTE EST VIDE.
            //
            // Elle rendait `null`, et l'opérateur voyait un résultat complet —
            // taxes, avantages, coût réglementaire — sans le moindre signe que
            // les formalités n'avaient jamais été établies. Mesuré sur les
            // crawls du 21/09/2026 : 315 185 positions sur 350 022 (90 %) n'en
            // portent aucune, et 46 pays sur 54 n'en portent aucune du tout.
            // Le silence était la règle, et il se lisait « rien à faire ».
            //
            // Une absence d'information n'est pas une absence d'obligation :
            // la carte reste, et dit laquelle des deux elle constate.
            const aucuneFormalite = !formalities || formalities.length === 0;
            // Deux silences très différents, et l'opérateur doit les distinguer.
            //
            // Quand la source publie ses formalités de façon EXHAUSTIVE — c'est
            // établi pour l'Algérie, échantillon à l'appui — une liste vide est
            // un CONSTAT : la marchandise n'est soumise à aucune formalité
            // particulière. Dire « non établies » sous-estimerait ce que l'on
            // sait, et ferait passer une information solide pour une lacune.
            // Partout ailleurs, le silence reste une lacune, et se dit comme tel.
            const constatSource = result.formalites_statut === 'AUCUNE_FORMALITE_PARTICULIERE';
            const reserve = result.formalites_reserve
              || (constatSource
                ? (language === 'fr'
                  ? "Aucune formalité administrative particulière n'est publiée pour cette position. Les obligations générales à l'importation demeurent."
                  : 'No specific administrative formality is published for this position. General import obligations still apply.')
                : (language === 'fr'
                  ? "Formalités non établies pour cette position. Une absence d'information n'est pas une absence d'obligation : vérifier auprès de l'administration douanière de destination."
                  : 'Formalities not established for this position. Missing information is not an absence of obligation: check with the destination customs administration.'));
            return (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                        <FileCheck className="w-5 h-5 text-amber-400" />
                      </div>
                      <div>
                        <CardTitle className="text-lg text-white">
                          {language === 'fr' ? 'Documents Requis' : 'Required Documents'}
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                          {aucuneFormalite
                            ? (constatSource
                              ? (language === 'fr' ? 'Aucune formalité particulière' : 'No specific formality')
                              : (language === 'fr' ? 'Non établies' : 'Not established'))
                            : `${formalities.length} ${language === 'fr' ? 'formalités' : 'formalities'}`}
                          {isPositionLevel && (
                            <span className="ml-2 text-amber-400 text-xs font-mono">
                              — position {positionCode}
                            </span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                    {isPositionLevel && (
                      <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs">
                        {language === 'fr' ? 'Position nationale' : 'National position'}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {aucuneFormalite && (
                    <div className={`flex items-start gap-3 p-3 rounded-lg border ${constatSource ? 'bg-slate-900/40 border-slate-700' : 'bg-amber-500/10 border-amber-500/20'}`}>
                      {constatSource
                        ? <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                        : <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />}
                      <p className="text-slate-300 text-sm">{reserve}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(formalities || []).map((form, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${form.is_mandatory === false ? 'bg-slate-700/20 border-slate-700' : 'bg-slate-700/30 border-slate-700'}`}
                      >
                        <div className="flex items-start gap-2">
                          <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 border font-mono shrink-0 text-xs">
                            {form.code}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            <p className="text-slate-300 text-sm">
                              {language === 'fr' ? (form.document_fr || form.document_en) : (form.document_en || form.document_fr)}
                            </p>
                            {(form.authority_fr || form.authority_en) && (
                              <p className="text-slate-500 text-xs mt-1">
                                {language === 'fr' ? form.authority_fr : form.authority_en}
                              </p>
                            )}
                            {form.is_mandatory === false && (
                              <span className="text-xs text-slate-500 italic">
                                {language === 'fr' ? 'Optionnel' : 'Optional'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {!isPositionLevel && (
                    <p className="text-xs text-slate-500 mt-3 border-t border-slate-700 pt-2">
                      {language === 'fr'
                        ? 'Formalités au niveau HS6. Sélectionnez une sous-position nationale pour les formalités spécifiques à la position (10 chiffres).'
                        : 'Formalities at HS6 level. Select a national sub-position for position-specific formalities (10 digits).'}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })()}

          {/* ── COLONNES PRÉFÉRENTIELLES PUBLIÉES PAR LE TARIF DE DESTINATION ──
              `fiscal_advantages` porte TOUTES les colonnes que le tarif de
              destination publie, quel que soit le partenaire : pour la
              Tunisie, le Koweït, la Palestine, l'Union européenne, la
              Turquie... Les afficher toutes sous un titre « Avantages ZLECAf »,
              avec un coche vert et sans le taux, disait trois choses fausses —
              le partenaire, le régime, et le sens de la colonne (sur
              TUN/27101981100, droit NPF 0 %, les colonnes nommées valent 50 %).
              On ne retient donc que celles qui nomment l'origine choisie ; les
              autres sont comptées et déclarées, jamais nommées ni affichées. */}
          {(() => {
            const tri = trierAvantages(
              result.fiscal_advantages,
              result.origin_country_iso3 || result.origin_country || originCountry,
              result.npf_dd_rate_pct ?? null,
            );
            const retenus = [...tri.pourLOrigine, ...tri.generaux];
            if (retenus.length === 0 && tri.autresPartenaires === 0) return null;
            const origineNom = getCountryName(
              result.origin_country_iso3 || result.origin_country || originCountry,
            );
            return (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-700/40 rounded-lg border border-slate-600">
                      <Shield className="w-5 h-5 text-slate-300" />
                    </div>
                    <div>
                      <CardTitle className="text-lg text-white">
                        {language === 'fr'
                          ? 'Colonnes préférentielles publiées'
                          : 'Published preferential columns'}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        {language === 'fr'
                          ? `Tarif de destination, colonnes au nom de ${origineNom} — montrées, jamais appliquées`
                          : `Destination tariff, columns named for ${origineNom} — shown, never applied`}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {retenus.map((entree, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-3 p-3 bg-slate-900/40 rounded-lg border border-slate-700"
                      >
                        {entree.reduitLeDroit === true ? (
                          <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                        ) : (
                          <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                        )}
                        <div className="min-w-0">
                          <div className="text-slate-200">
                            {entree.libelle}
                            {entree.taux !== null && (
                              <span className="ml-2 font-mono text-white">
                                {entree.taux} %
                              </span>
                            )}
                          </div>
                          {entree.reduitLeDroit === false && (
                            <div className="text-xs text-amber-400/80 mt-1">
                              {language === 'fr'
                                ? `Cette colonne ne réduit pas le droit NPF de la position (${result.npf_dd_rate_pct} %).`
                                : `This column does not reduce the position's MFN duty (${result.npf_dd_rate_pct}%).`}
                            </div>
                          )}
                          {entree.taux === null && (
                            <div className="text-xs text-slate-500 mt-1">
                              {language === 'fr'
                                ? 'Taux non donné par la source.'
                                : 'Rate not given by the source.'}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {retenus.length === 0 && (
                    <p className="text-sm text-slate-400">
                      {language === 'fr'
                        ? `Le tarif de destination ne publie aucune colonne au nom de ${origineNom} sur cette position.`
                        : `The destination tariff publishes no column named for ${origineNom} on this position.`}
                    </p>
                  )}
                  {tri.autresPartenaires > 0 && (
                    <p className="text-xs text-slate-500 mt-3 border-t border-slate-700 pt-2">
                      {language === 'fr'
                        ? `${tri.autresPartenaires} autre(s) colonne(s) préférentielle(s) publiée(s) sur cette position concernent d'autres partenaires : elles ne s'appliquent pas à une importation en provenance de ${origineNom} et ne sont pas affichées.`
                        : `${tri.autresPartenaires} other preferential column(s) published on this position concern other partners: they do not apply to an import from ${origineNom} and are not shown.`}
                    </p>
                  )}
                  <p className="text-xs text-slate-500 mt-2">
                    {language === 'fr'
                      ? "Colonnes telles que le tarif de destination les publie. La franchise reste subordonnée aux règles d'origine de l'accord, que ce moteur ne vérifie pas : le certificat d'origine reste à produire."
                      : 'Columns as published by the destination tariff. Relief remains subject to the agreement\'s rules of origin, which this engine does not verify: the certificate of origin is still required.'}
                  </p>
                </CardContent>
              </Card>
            );
          })()}

          {/* Composition du coût réglementaire : droits & taxes publics + frais de
              formalité et de prestataire (lignes séparées). Les frais documentés
              chiffrés entrent dans le coût total ; les frais existants non chiffrés
              sont signalés « montant à confirmer », jamais valués à zéro. */}
          <RegulatoryCostBreakdown result={result} language={language} />

          {/* ── BLOC DÉTAILLÉ — Formalités & prestataires mandatés (registre conforme) ──
              Détail sourcé et daté (mission, mandat, preuves). Affiché UNIQUEMENT
              pour les pays utilisant réellement un prestataire mandaté actif (jamais
              pour une formalité opérée directement par l'administration ni un mandat
              expiré). Distinct des droits et taxes. */}
          {hasActiveMandatedProvider(result.regulatory_compliance) && (
            <Card className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-amber-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                    <ClipboardList className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-white">
                      {language === 'fr'
                        ? 'Détail des formalités & prestataires mandatés'
                        : 'Formalities & mandated providers — detail'}
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      {language === 'fr'
                        ? `${getCountryName(result.destination_country)} — mission, mandat, preuves datées et sources officielles`
                        : `${getCountryName(result.destination_country)} — mission, mandate, dated evidence and official sources`}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-200/90">
                    {language === 'fr'
                      ? "Les frais du prestataire mandaté sont séparés des droits et taxes publics (voir « Composition du coût réglementaire » ci-dessus). Un montant n'est chiffré et intégré que lorsqu'il est prouvé et sourcé ; sinon il reste à confirmer (jamais fabriqué, jamais valué à zéro)."
                      : 'Mandated-provider fees are separate from public duties and taxes (see “Regulatory cost composition” above). An amount is quantified and included only when proven and sourced; otherwise it stays to be confirmed (never fabricated, never valued at zero).'}
                  </p>
                </div>
                <RegulatoryComplianceView
                  compliance={result.regulatory_compliance}
                  language={language}
                  showFilters={false}
                />
              </CardContent>
            </Card>
          )}

          {/* Couche « indications secondaires » (non vérifiée) — pays hors registre
              conforme. Rendu distinct, jamais sommé, tout « à confirmer ». */}
          <RegulatoryReportedIndications result={result} language={language} />
        </div>
      )}
          </div>
      </TabsContent>

        {/* Onglet Réglementation - Moteur Réglementaire v3 */}
        <TabsContent value="regulatory">
          <div className="space-y-6">
            {/* Formalités & prestataires mandatés — registre CONFORME fail-closed
                (source-bound, daté). Affiché en priorité sur le Moteur v3 ci-dessous,
                et UNIQUEMENT pour un pays de destination utilisant réellement un
                prestataire mandaté actif. */}
            {hasActiveMandatedProvider(result?.regulatory_compliance) && (
              <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border border-amber-500/30">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                      <ClipboardList className="w-6 h-6 text-amber-400" />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-white">
                        {language === 'fr'
                          ? 'Formalités particulières & prestataires mandatés'
                          : 'Special formalities & mandated providers'}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        {language === 'fr'
                          ? `${getCountryName(result.destination_country)} — registre sourcé et daté, distinct du calcul de droits et taxes`
                          : `${getCountryName(result.destination_country)} — source-bound dated registry, distinct from the duties/taxes computation`}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <RegulatoryComplianceView
                    compliance={result.regulatory_compliance}
                    language={language}
                    showFilters
                  />
                </CardContent>
              </Card>
            )}

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
                      onChange={handleRegulatoryHsCodeChange}
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

            {/* Sélecteur de Positions Nationales — uniquement pour un code SH6 (6 chiffres) */}
            {destinationCountry && isHs6Only && (
              <>
                {!regulatorySelectedPos && (
                  <NationalPositionsSelector
                    countryCode={destinationCountry}
                    hs6Code={hsCodeDigits}
                    language={language}
                    selectedPosition={regulatorySelectedPos}
                    onPositionSelect={(code, description) => {
                      setRegulatorySelectedPos(code);
                      setRegulatorySelectedPosDesc(description);
                    }}
                  />
                )}
                {regulatorySelectedPosDesc && (
                  <div className="flex items-start justify-between gap-3 p-4 bg-amber-500/10 rounded-xl border border-amber-500/30">
                    <div className="flex items-start gap-3 min-w-0">
                      <FileText className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-amber-400/70 uppercase tracking-wide font-medium mb-1">
                          {language === 'fr' ? 'Intitulé exact de la position nationale' : 'Exact title of national position'}
                        </p>
                        <p className="text-white font-medium">{regulatorySelectedPosDesc}</p>
                        <p className="text-amber-400/60 font-mono text-sm mt-1">{regulatorySelectedPos}</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="shrink-0 border-amber-500/40 text-amber-300 hover:bg-amber-500/10"
                      onClick={() => {
                        setRegulatorySelectedPos(null);
                        setRegulatorySelectedPosDesc(null);
                      }}
                    >
                      {language === 'fr' ? 'Changer' : 'Change'}
                    </Button>
                  </div>
                )}
              </>
            )}

            {/* Panneau des détails réglementaires */}
            {destinationCountry && hsCode && hsCode.length >= 6 && (
              <RegulatoryDetailsPanel
                countryCode={destinationCountry}
                hsCode={regulatorySelectedPos || hsCode}
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
