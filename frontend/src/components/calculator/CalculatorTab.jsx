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
import { useHsLabel } from '../../hooks/useHsLabel';
import { HSCodeSearch, HSCodeBrowser } from '../HSCodeSelector';
import SmartHSSearch from '../SmartHSSearch';
import { Package, ChevronDown, ChevronUp, Sparkles, AlertTriangle, Info, Calculator, Globe, FileText, CheckCircle, ClipboardList, Scale, FileCheck, Shield, DollarSign, RotateCcw } from 'lucide-react';
import TaxBreakdownDual from './TaxBreakdownDual';
import CalculationJournal from './CalculationJournal';
import CalculationMethodStatus from './CalculationMethodStatus';
import { DetailedTaxTable, SavingsHighlight, TaxComparisonBarChart, TaxDistributionPieChart } from './TaxBreakdownChart';
import DataStatusBanner from '../common/DataStatusBanner';
import RegulatoryDetailsPanel from './RegulatoryDetailsPanel';
import TariffDownloads from '../tools/TariffDownloads';
import NationalPositionsSelector from '../NationalPositionsSelector';
import MultiCountryComparison from './MultiCountryComparison';
import ProductKeywordSearch from './ProductKeywordSearch';
import KenyaRemissionAuthorization from './KenyaRemissionAuthorization';
import RegulatoryComplianceView, {
  hasActiveMandatedProvider,
  hasUnpricedActiveProviderFees,
} from '../regulatory/RegulatoryComplianceView';
import RegulatoryCostBreakdown from './RegulatoryCostBreakdown';
import RegulatoryReportedIndications from './RegulatoryReportedIndications';
import { normalizeTaxesDetail } from './taxesDetail';
import {
  buildCalculRequestBody,
  expeditionSacuRequise,
  mapCalculToLegacyResult,
  localiserResultat,
  paysExpeditionPour,
  reserveConversion,
  tauxDeChangePour,
} from './unifiedCalculator';
import ExpeditionSacuQuestion from './ExpeditionSacuQuestion';
import {
  isCustomsDutyTax,
  isDisplayableZlecafResult,
  zlecafTotalTaxRatePct,
} from './zlecafAvailability';
import { montant } from '../../utils/nombres';
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
  const [loading, setLoading] = useState(false);
  const [showHSBrowser, setShowHSBrowser] = useState(false);
  const [showDetailedBreakdown, setShowDetailedBreakdown] = useState(false);
  const [subPositions, setSubPositions] = useState(null);
  const [useSmartSearch, setUseSmartSearch] = useState(true);
  const [ruleOfOrigin, setRuleOfOrigin] = useState(null);
  const [selectedSubPositionDesc, setSelectedSubPositionDesc] = useState(null);
  // Nombre de positions nationales servies sous le SH6 saisi, et pour quel pays.
  const [positionsSh6, setPositionsSh6] = useState(null);
  const [selectedSubPositionFormalities, setSelectedSubPositionFormalities] = useState(null);
  // Repli en mode saisie directe (hors recherche intelligente) : celle-ci ne
  // remplit jamais selectedSubPositionDesc, donc sans ce hook le code SH
  // reste affiché nu tant qu'aucune sélection via recherche n'a été faite.
  const { label: hsCodeSimpleLabel } = useHsLabel(hsCode, language);
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
  // Afrique du Sud, VAT Act s.13(2)(b) : pour une origine BWA/LSO/NAM/SWZ,
  // la majoration de 10 % de la TVA dépend du pays d'expédition.
  const [expeditionSacu, setExpeditionSacu] = useState('unknown');
  // Valeur FOB (assiette SACU), sur le même modèle : demandée seulement quand
  // un moteur la réclame, et rattachée à la position pour laquelle elle a été
  // saisie.
  const [fobValue, setFobValue] = useState('');
  const [fobFor, setFobFor] = useState(null);
  // Usage de la marchandise, quand le tarif y subordonne un prélèvement
  // (Égypte : Taxe de Table d'un pesticide agricole, d'un engrais…). Même
  // règle que la quantité : rattaché à la position pour laquelle il est déclaré.
  const [usage, setUsage] = useState('');
  const [usageFor, setUsageFor] = useState(null);
  // Facultatifs : chiffrent les frais par tonne et par conteneur ou véhicule
  // du bloc réglementaire (péage, scanner…), jamais les droits et taxes.
  const [poidsBrut, setPoidsBrut] = useState('');
  const [moyenTransport, setMoyenTransport] = useState('');
  const [nombreUnites, setNombreUnites] = useState('1');
  const [modeAcheminement, setModeAcheminement] = useState('');

  // Vider le champ quand la position ou la destination change. La justesse ne
  // dépend pas de cet effet — c'est `quantityFor` qui empêche une quantité de
  // servir sur une autre position, et il est évalué au moment de l'appel. Cet
  // effet évite seulement d'AFFICHER un poids qui n'est plus celui du calcul.
  useEffect(() => {
    setQuantity('');
    setQuantityFor(null);
    setFobValue('');
    setFobFor(null);
    setUsage('');
    setUsageFor(null);
  }, [hsCode, destinationCountry, originCountry]);

  useEffect(() => {
    setExpeditionSacu('unknown');
  }, [destinationCountry, originCountry]);

  const handleDestinationChange = useCallback((value) => {
    setDestinationCountry(value);
  }, []);

  const handleRegulatoryHsCodeChange = useCallback((e) => {
    setHsCode(e.target.value);
    setRegulatorySelectedPos(null);
    setRegulatorySelectedPosDesc(null);
  }, []);

  const texts = {
    fr: {
      originCountry: "Pays d'origine",
      partnerCountry: "Pays partenaire",
      hsCodeLabel: "Code HS (6-12 chiffres)",
      hsCodeHint: "6 chiffres = HS international | 8-12 chiffres = sous-position nationale",
      valueLabel: "Valeur de la marchandise (USD)",
      logisticsLabel: "Poids et transport (facultatif)",
      logisticsHint: "Chiffrent les frais par tonne, par conteneur ou véhicule (péage, scanner…) et écartent ceux d'un autre mode d'acheminement (port pour une importation par route), à part des droits et taxes.",
      grossWeightPlaceholder: "Poids brut (kg)",
      transportPlaceholder: "Moyen de transport",
      transportContainer: "Conteneur",
      transportCar: "Voiture",
      transportTruck: "Camion",
      transportCountPlaceholder: "Nombre",
      routingPlaceholder: "Acheminement",
      routingUnspecified: "Non précisé",
      routingSea: "Mer",
      routingRoad: "Route",
      routingAir: "Air",
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
      choosePosition: "Choisissez une position nationale",
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
      logisticsLabel: "Weight and transport (optional)",
      logisticsHint: "Used to price per-tonne and per-container or per-vehicle fees (tolls, scanner…) and to leave out fees of another routing (port fees for road imports), shown apart from duties and taxes.",
      grossWeightPlaceholder: "Gross weight (kg)",
      transportPlaceholder: "Means of transport",
      transportContainer: "Container",
      transportCar: "Car",
      transportTruck: "Truck",
      transportCountPlaceholder: "Number",
      routingPlaceholder: "Routing",
      routingUnspecified: "Not specified",
      routingSea: "Sea",
      routingRoad: "Road",
      routingAir: "Air",
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
      choosePosition: "Choose a national position",
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
  // Plusieurs positions nationales sous le SH6 saisi : le calcul attend que
  // l'opérateur choisisse la sienne. Le compte vaut pour le pays et le SH6
  // pour lesquels la liste a été chargée, et pour eux seuls.
  const positionRequise = isHs6Only
    && positionsSh6?.cle === `${destinationCountry}|${hsCodeDigits}`
    && positionsSh6.total > 1;

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

  // « 12 345 $ » en français ; forme anglaise inchangée.
  const formatCurrency = (amount) => {
    if (language !== 'en') return montant(amount, language, 2);
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
    setPoidsBrut('');
    setMoyenTransport('');
    setNombreUnites('1');
    setModeAcheminement('');
    setResult(null);
    setShowHSBrowser(false);
    setShowDetailedBreakdown(false);
    setSubPositions(null);
    setRuleOfOrigin(null);
    setSelectedSubPositionDesc(null);
    setSelectedSubPositionFormalities(null);
    setRegulatorySelectedPos(null);
    setRegulatorySelectedPosDesc(null);
    setSearchResetKey((k) => k + 1);
    setKenyaRemission({
      answer: 'unknown', reference: '', validFrom: '', validTo: '',
      authorizedTariffLines: '', authorizedGoods: '',
    });
    setExpeditionSacu('unknown');
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
    const paysExpedition = paysExpeditionPour(destISO3, originISO3, expeditionSacu);
    
    // Une valeur FOB saisie pour une AUTRE position est écartée, comme la
    // quantité : elle serait l'assiette d'une marchandise qui n'est pas celle-ci.
    const valeurFob = fobFor === `${destISO3}|${cleanHsCode}` ? parseFloat(fobValue) : NaN;
    const transport = {
      poidsBrutKg: parseFloat(poidsBrut),
      moyenTransport,
      // Number, pas parseInt : « 1.5 » doit être refusé, pas lu comme 1.
      nombreUnitesTransport: Number(nombreUnites),
      modeAcheminement,
    };

    // LE TAUX DE CHANGE DU MODULE BANQUE, demandé une seule fois et seulement
    // si le socle est interrogé : le moteur en a besoin pour les plafonds et
    // les droits spécifiques publiés en monnaie nationale, et l'écran pour
    // les montants locaux. Sans taux, ces lignes restent à compléter et
    // l'écran en USD seul. Une panne du change ne fait jamais échouer le
    // calcul : elle se lirait, plus bas, comme un refus du socle.
    let conversionDemandee = null;
    const demanderConversion = () => {
      if (!conversionDemandee) {
        conversionDemandee = axios.get(`${API}/banking/forex/convert`, {
          params: { country_code: destISO3, amount: parseFloat(value), from_currency: 'USD' },
        }).then((reponse) => reponse.data, () => null);
      }
      return conversionDemandee;
    };

    try {
      // UN SEUL CALCUL : le socle (`POST /calcul`), pour tous les pays. Une
      // position absente ou un socle indisponible s'affichent en erreur, avec
      // le message du socle : aucune autre source ne prend le relais.
      const calcul = (await axios.post(`${API}/calcul`, buildCalculRequestBody({
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
        paysExpedition,
        valeurFob,
        tauxDeChange: tauxDeChangePour(destISO3, await demanderConversion()),
        ...transport,
        remise: destISO3 === 'KEN' ? kenyaRemission : null,
        usage: usageFor === `${destISO3}|${cleanHsCode}` ? usage : null,
      }))).data;
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
      setShowDetailedBreakdown(true);

      // Sous-positions : données d'affichage annexes, pas des montants — un
      // manque y reste silencieux.
      const hs6 = cleanHsCode.substring(0, 6);
      try {
        const subPosResponse = await axios.get(`${API}/consultation/${destISO3}/sous-positions/${hs6}`);
        setSubPositions(subPosResponse.data);
      } catch (subPosError) {
        setSubPositions(null);
      }
      // LES FORMALITÉS, lues au socle comme les sous-positions. Un manque y
      // reste silencieux, parce qu'une formalité absente n'est pas un montant
      // faux.
      try {
        const formalitesResponse = await axios.get(
          `${API}/consultation/${destISO3}/formalites/${cleanHsCode}`
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
            // La liste se remplace À CHAQUE RÉPONSE, y compris vide. La
            // garder quand la nouvelle est vide ferait afficher les
            // documents de la position PRÉCÉDENTE sous le statut de la
            // nouvelle — et, la liste n'étant plus vide, supprimerait
            // justement l'avertissement que ce lot installe.
            administrative_formalities: formalites,
            formalites_statut: statutFormalites,
            formalites_reserve: reserveFormalites,
          }
          : precedent));
      } catch (formalitesError) {
        // Silencieux : une formalité absente n'est pas un montant faux.
      }
      // LA CONVERSION EN MONNAIE LOCALE, au taux déjà envoyé au moteur.
      // Deux calculs peuvent se chevaucher : la conversion ne s'applique qu'au
      // résultat de SA demande (même pays et position, même valeur CIF).
      const conversion = await demanderConversion();
      if (conversion) {
        setResult((precedent) => (
          precedent?._quantite_cle === `${destISO3}|${cleanHsCode}` && precedent.value === parseFloat(value)
            ? localiserResultat(precedent, conversion)
            : precedent));
      }

      const npfEtat = calcul.npf?.etat;
      // INDICATIF n'est pas un échec : toutes les lignes sont liquidées. La
      // réserve porte sur la nature d'un taux — une moyenne statistique, pas
      // un tarif — et doit se lire, sans faire passer le calcul pour cassé.
      const codesStatistiques = calcul.npf?.lignes_base_statistique || [];
      // Complet, mais des montants dépendent du taux de marché du module
      // Banque : le total se lit comme indicatif tant que le taux douanier
      // n'est pas vérifié.
      const lignesConverties = calcul.conversion_monetaire?.lignes || [];
      let titreToast;
      let descriptionToast;
      if (npfEtat === 'COMPLET' && lignesConverties.length) {
        titreToast = language === 'fr' ? 'Calcul indicatif' : 'Indicative calculation';
        descriptionToast = (language === 'fr'
          ? `${destISO3} : ${lignesConverties.join(', ')} au taux de marché du module Banque — taux douanier à vérifier`
          : `${destISO3}: ${lignesConverties.join(', ')} at the Banking module's market rate — customs rate to be checked`)
          + (legacyResult.savings != null ? ` · ${t.potentialSavings}: ${formatCurrency(legacyResult.savings)}` : '');
      } else if (npfEtat === 'COMPLET') {
        titreToast = t.calculationSuccess;
        descriptionToast = legacyResult.savings != null
          ? `${t.potentialSavings}: ${formatCurrency(legacyResult.savings)}`
          : `${destISO3} — ${language === 'fr' ? 'régime NPF' : 'MFN regime'}`;
      } else if (npfEtat === 'INDICATIF') {
        titreToast = language === 'fr' ? 'Calcul indicatif' : 'Indicative calculation';
        descriptionToast = language === 'fr'
          ? `${destISO3} : ${codesStatistiques.join(', ') || '—'} repose sur une moyenne statistique SH6 (WITS/TRAINS), pas sur un tarif national — montant indicatif`
          : `${destISO3}: ${codesStatistiques.join(', ') || '—'} rests on an HS6 statistical average (WITS/TRAINS), not a national tariff — indicative amount`;
      } else {
        titreToast = language === 'fr' ? 'Calcul incomplet' : 'Incomplete calculation';
        descriptionToast = language === 'fr'
          ? `${destISO3} : un ou plusieurs droits n'ont pas pu être liquidés (${(calcul.npf?.manques || []).map((m) => m.code).join(', ') || '—'}) — total partiel, jamais un montant fabriqué`
          : `${destISO3}: one or more duties could not be liquidated (${(calcul.npf?.manques || []).map((m) => m.code).join(', ') || '—'}) — partial total, never a fabricated amount`;
      }
      toast({
        title: titreToast,
        description: descriptionToast,
        variant: npfEtat === 'COMPLET' || npfEtat === 'INDICATIF' ? 'default' : 'destructive',
      });
    } catch (error) {
      console.error('Calculation error:', error);
      setResult(null);
      setShowDetailedBreakdown(false);
      const detail = error.response?.data?.detail;
      // Un SH6 sous lequel le tarif publie plusieurs positions nationales :
      // le calcul ne choisit pas à la place de l'opérateur. Ce n'est pas une
      // panne — la position se choisit dans « Positions Tarifaires
      // Nationales », affiché sous le code SH6.
      if (detail?.code === 'POSITION_NATIONALE_REQUISE') {
        toast({
          title: language === 'fr' ? 'Position nationale requise' : 'National position required',
          description: language === 'fr'
            ? `${detail.positions?.length || 'Plusieurs'} positions nationales sous ce code SH6 : choisissez la vôtre dans la liste « Positions Tarifaires Nationales », puis relancez le calcul.`
            : `${detail.positions?.length || 'Several'} national positions under this HS6 code: choose yours in the "National Tariff Positions" list, then calculate again.`,
        });
        return;
      }
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
      'CEDEAO': 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]',
      'AES': 'bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)] border-[color-mix(in_srgb,var(--terra)_30%,transparent)]',
      'CEMAC': 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]',
      'EAC': 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]',
      'SACU': 'bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]',
    };
    return colors[bloc] || 'bg-[var(--afcfta-card2)] text-[var(--afcfta-muted)] border-[var(--afcfta-border)]';
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
      <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[color-mix(in_srgb,var(--gold)_5%,transparent)] rounded-full blur-3xl translate-x-1/2 -translate-y-1/2"></div>
        
        <CardHeader className="relative">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <Calculator className="w-8 h-8 text-[var(--gold)]" />
            </div>
            <div>
              <CardTitle className="text-2xl text-[var(--text)]">{t.calculatorTitle}</CardTitle>
              <CardDescription className="text-[var(--afcfta-muted)] text-base mt-1">{t.calculatorDesc}</CardDescription>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="relative space-y-6">
          {/* Sélection des pays */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pays d'origine */}
            <div className="space-y-2">
              <Label className="text-[var(--text)] font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] flex items-center justify-center text-xs text-[var(--info)]">1</span>
                {t.originCountry}
              </Label>
              <Select value={originCountry} onValueChange={setOriginCountry}>
                <SelectTrigger 
                  data-testid="origin-country-select"
                  className="h-12 bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--info)_30%,transparent)] transition-colors"
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
                          {bloc && <span className={`text-[11px] px-1.5 rounded border font-medium ${getBlocColor(bloc)}`}>{bloc}</span>}
                        </span>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Pays de destination */}
            <div className="space-y-2">
              <Label className="text-[var(--text)] font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] flex items-center justify-center text-xs text-[var(--gold)]">2</span>
                {t.partnerCountry}
              </Label>
              <Select value={destinationCountry} onValueChange={handleDestinationChange}>
                <SelectTrigger 
                  data-testid="destination-country-select"
                  className="h-12 bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--gold)_30%,transparent)] transition-colors"
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
                          {bloc && <span className={`text-[11px] px-1.5 rounded border font-medium ${getBlocColor(bloc)}`}>{bloc}</span>}
                        </span>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Légende */}
          <div className="flex items-center gap-4 text-xs text-[var(--afcfta-muted)] bg-[var(--overlay)] rounded-lg px-4 py-2">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
            </span>
            <span className="text-[var(--afcfta-muted)]">|</span>
            <span className="text-[var(--afcfta-muted)]">{language === 'fr' ? 'Blocs:' : 'Blocs:'} CEDEAO · CEMAC · EAC · SACU · AES</span>
          </div>

          {/* Code HS */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-[var(--text)] font-medium flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] flex items-center justify-center text-xs text-[var(--violet)]">3</span>
                <Package className="w-4 h-4 text-[var(--violet)]" />
                {t.hsCodeLabel}
              </Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setUseSmartSearch(!useSmartSearch)}
                className="text-xs text-[var(--violet)] hover:text-[var(--violet)] hover:bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]"
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
              <div className="flex-1 h-px bg-[var(--overlay)]" />
              <span className="text-xs text-[var(--afcfta-muted)] shrink-0">
                {language === 'fr' ? 'ou saisir directement' : 'or enter directly'}
              </span>
              <div className="flex-1 h-px bg-[var(--overlay)]" />
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
                  className="h-12 font-mono text-lg bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--violet)_30%,transparent)] focus:border-[color-mix(in_srgb,var(--violet)_30%,transparent)] transition-colors tracking-wider"
                  data-testid="hs-code-simple-input"
                />
                {hsCodeSimpleLabel ? (
                  <p className="text-[var(--success)] text-xs truncate" title={hsCodeSimpleLabel}>
                    {hsCodeSimpleLabel}
                  </p>
                ) : (
                  <p className="text-[var(--afcfta-muted)] text-xs">{t.hsCodeHint}</p>
                )}
              </div>
            )}

            {/* Code sélectionné via recherche */}
            {hsCode && selectedSubPositionDesc && (
              <div className="flex items-center gap-2 bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--violet)_30%,transparent)] rounded-lg px-3 py-2">
                <span className="font-mono text-[var(--violet)] text-sm font-bold shrink-0">{hsCode}</span>
                <span className="text-[var(--afcfta-muted)] text-xs line-clamp-1">{selectedSubPositionDesc}</span>
              </div>
            )}

            {/* Règle d'origine ZLECAf applicable au code sélectionné.
                hs_code is matched against the current input so a rule loaded
                for a previous code (e.g. via Smart Search) never lingers
                after the user switches to simple input or types a new code. */}
            {ruleOfOrigin && ruleOfOrigin.rule && ruleOfOrigin.rules && ruleOfOrigin.hs_code === hsCode && (
              <div className="bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-[var(--gold)] text-xs font-semibold">
                    {language === 'fr' ? "Règle d'origine ZLECAf" : 'AfCFTA Rule of Origin'}
                  </span>
                  <Badge className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] text-xs">
                    {ruleOfOrigin.rules.primary_rule?.name || ruleOfOrigin.rules.primary_rule?.code}
                  </Badge>
                  {ruleOfOrigin.rules.regional_content != null && (
                    <Badge className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-xs">
                      {language === 'fr' ? 'Contenu régional' : 'Regional content'}: {ruleOfOrigin.rules.regional_content}%
                    </Badge>
                  )}
                  {ruleOfOrigin.status === 'YTB' && (
                    <Badge className="bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] text-[var(--terra)] border border-[color-mix(in_srgb,var(--terra)_30%,transparent)] text-xs">
                      {language === 'fr' ? 'En négociation' : 'Under negotiation'}
                    </Badge>
                  )}
                </div>
                {ruleOfOrigin.rules.primary_rule?.explanation && (
                  <p className="text-[var(--text)] text-xs leading-relaxed">
                    {ruleOfOrigin.rules.primary_rule.explanation}
                  </p>
                )}
                {ruleOfOrigin.rules.alternative_rule && (
                  <p className="text-[var(--afcfta-muted)] text-xs">
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
              className="w-full bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--gold)_30%,transparent)] hover:bg-[var(--overlay)] text-[var(--text)]"
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
            <div className="border border-[var(--afcfta-border)] rounded-xl overflow-hidden">
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
            <Label className="text-[var(--text)] font-medium flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] flex items-center justify-center text-xs text-[var(--success)]">4</span>
              {t.valueLabel}
            </Label>
            <Input
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="100000"
              min="0"
              className="h-12 font-mono text-lg bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--success)_30%,transparent)] focus:border-[color-mix(in_srgb,var(--success)_30%,transparent)] transition-colors"
              data-testid="cif-value-input"
            />
          </div>

          {/* Poids et transport — facultatifs, bloc réglementaire seulement */}
          <div className="space-y-2">
            <Label className="text-[var(--text)] font-medium">{t.logisticsLabel}</Label>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <Select
                value={modeAcheminement || undefined}
                onValueChange={(v) => setModeAcheminement(v === 'NON_PRECISE' ? '' : v)}
              >
                <SelectTrigger
                  className="bg-[var(--overlay)] border-[var(--afcfta-border)]"
                  data-testid="routing-select"
                  aria-label={t.routingPlaceholder}
                >
                  <SelectValue placeholder={t.routingPlaceholder} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NON_PRECISE">{t.routingUnspecified}</SelectItem>
                  <SelectItem value="MER">{t.routingSea}</SelectItem>
                  <SelectItem value="ROUTE">{t.routingRoad}</SelectItem>
                  <SelectItem value="AIR">{t.routingAir}</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="number"
                value={poidsBrut}
                onChange={(e) => setPoidsBrut(e.target.value)}
                placeholder={t.grossWeightPlaceholder}
                aria-label={t.grossWeightPlaceholder}
                min="0"
                className="bg-[var(--overlay)] border-[var(--afcfta-border)]"
                data-testid="gross-weight-input"
              />
              <Select value={moyenTransport} onValueChange={setMoyenTransport}>
                <SelectTrigger
                  className="bg-[var(--overlay)] border-[var(--afcfta-border)]"
                  data-testid="transport-select"
                  aria-label={t.transportPlaceholder}
                >
                  <SelectValue placeholder={t.transportPlaceholder} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CONTENEUR">{t.transportContainer}</SelectItem>
                  <SelectItem value="VOITURE">{t.transportCar}</SelectItem>
                  <SelectItem value="CAMION">{t.transportTruck}</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="number"
                value={nombreUnites}
                onChange={(e) => setNombreUnites(e.target.value)}
                placeholder={t.transportCountPlaceholder}
                aria-label={t.transportCountPlaceholder}
                min="1"
                step="1"
                disabled={!moyenTransport}
                className="bg-[var(--overlay)] border-[var(--afcfta-border)]"
                data-testid="transport-count-input"
              />
            </div>
            <p className="text-xs text-[var(--afcfta-muted)]">{t.logisticsHint}</p>
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
              onPositionsLoaded={({ countryCode, hs6, total }) => setPositionsSh6({ cle: `${countryCode}|${hs6}`, total })}
            />
          )}

          {['KEN', 'KE'].includes(destinationCountry) && (
            <KenyaRemissionAuthorization
              value={kenyaRemission}
              onChange={setKenyaRemission}
            />
          )}

          {expeditionSacuRequise(
            destinationCountry.length === 2 ? ISO2_TO_ISO3[destinationCountry] || destinationCountry : destinationCountry,
            originCountry.length === 2 ? ISO2_TO_ISO3[originCountry] || originCountry : originCountry,
          ) && (
            <ExpeditionSacuQuestion
              value={expeditionSacu}
              onChange={setExpeditionSacu}
              language={language}
            />
          )}

          {/* Boutons Calculer / Réinitialiser */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              onClick={() => calculateTariff()}
              disabled={loading || positionRequise}
              data-testid="calculate-tariff-button"
              className="flex-1 h-14 text-lg font-bold bg-[image:var(--active-fill)] hover:opacity-90 text-[#F7F1E6] shadow-lg hover:shadow-xl transition-all"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-[var(--overlay-border)] border-t-white rounded-full animate-spin mr-2"></div>
                  {t.calculating}
                </>
              ) : positionRequise ? (
                <>
                  <Calculator className="w-5 h-5 mr-2" />
                  {t.choosePosition}
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
              className="h-14 px-5 border-[var(--afcfta-border)] text-[var(--text)] hover:border-[color-mix(in_srgb,var(--danger)_30%,transparent)] hover:text-[var(--danger)] hover:bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))] transition-all"
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
          <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] overflow-hidden transition-all duration-300">
            <div className="absolute top-0 left-0 w-64 h-64 bg-[color-mix(in_srgb,var(--success)_5%,transparent)] rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2"></div>
            
            <CardHeader className="relative">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl border border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                    <CheckCircle className="w-8 h-8 text-[var(--success)]" />
                  </div>
                  <div>
                    <CardTitle className="text-xl text-[var(--text)] flex items-center gap-2">
                      {t.detailedResults}
                    </CardTitle>
                    <CardDescription className="text-[var(--afcfta-muted)] flex items-center gap-2 mt-1">
                      <span className="text-lg">{getFlag(result.origin_country)}</span>
                      <span>{getCountryName(result.origin_country)}</span>
                      <span className="text-[var(--afcfta-muted)]">→</span>
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
                                      correspond à aucune source lisible ; ou
                                      si une réserve accompagne la préférence
                                      (règle d'origine non arrêtée). */}
              {result.trade_regime === 'CUSTOMS_UNION' && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--success)_30%,transparent)] rounded-xl flex items-start gap-3">
                  <Shield className="w-5 h-5 text-[var(--success)] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-[var(--success)] font-semibold text-sm">
                      {language === 'fr'
                        ? `Union douanière ${result.trade_regime_code || ''} — libre circulation`
                        : `${result.trade_regime_code || ''} customs union — free circulation`}
                    </p>
                    <p className="text-[var(--success)] text-sm mt-1">{result.trade_regime_note}</p>
                  </div>
                </div>
              )}

              {result.trade_regime === 'FTA_CONDITIONAL' && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl flex items-start gap-3">
                  <Info className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-[var(--gold)] font-semibold text-sm">
                      {language === 'fr'
                        ? `Régime ${result.trade_regime_code || 'du bloc'} applicable sous conditions`
                        : `${result.trade_regime_code || 'Bloc'} regime applies under conditions`}
                    </p>
                    <p className="text-[var(--gold)] text-sm mt-1">{result.trade_regime_note}</p>
                  </div>
                </div>
              )}

              {result.trade_regime === 'ZLECAF' && result.zlecaf_reserve && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-[var(--gold)] font-semibold text-sm">
                      {language === 'fr'
                        ? 'Préférence ZLECAf servie sous réserve'
                        : 'AfCFTA preference shown with a reservation'}
                    </p>
                    <p className="text-[var(--gold)] text-sm mt-1">{result.zlecaf_reserve}</p>
                  </div>
                </div>
              )}

              {(() => {
                const reserve = reserveConversion(result, language);
                return reserve && (
                  <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-[var(--gold)] font-semibold text-sm">{reserve.titre}</p>
                      <p className="text-[var(--gold)] text-sm mt-1">{reserve.texte}</p>
                    </div>
                  </div>
                );
              })()}

              {result.trade_regime === 'NPF' && result.zlecaf_note && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-[var(--gold)] font-semibold text-sm">
                      {language === 'fr' ? 'Préférence ZLECAf non appliquée' : 'AfCFTA preference not applied'}
                    </p>
                    <p className="text-[var(--gold)] text-sm mt-1">{result.zlecaf_note}</p>
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
                  className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl"
                  data-testid="quantite-requise"
                >
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-[var(--gold)] font-semibold text-sm">
                        {language === 'fr'
                          ? 'Droit spécifique : quantité nécessaire'
                          : 'Specific duty: quantity required'}
                      </p>

                      <div className="mt-2 space-y-1">
                        {result.quantite_requise.lignes.map((l) => (
                          <p key={l.code} className="text-[var(--gold)] text-xs">
                            <span className="font-mono">{l.code}</span> — {l.libelle}
                            {l.specifique ? ` : ${l.specifique}` : ''}
                          </p>
                        ))}
                      </div>

                      {result.quantite_requise.unite ? (
                        <div className="mt-3 flex flex-wrap items-end gap-2">
                          <div>
                            <label
                              className="block text-[var(--gold)] text-xs mb-1"
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
                              className="w-40 px-3 py-2 bg-[var(--field)] border border-[var(--field-border)] rounded-lg text-[var(--text)] text-sm"
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
                        <p className="text-[var(--gold)] text-xs mt-3">
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

              {/* USAGE DE LA MARCHANDISE — ouvert seulement quand le tarif y
                  subordonne un prélèvement (Égypte : instructions ر7009,
                  ر7018, ر7027, ر7100). Sans déclaration, le régime courant est
                  liquidé ; l'usage déclaré, lui, l'est avec son prélèvement. */}
              {result.usages?.possibles?.length > 0 && (
                <div
                  className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl"
                  data-testid="usage-declare"
                >
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-[var(--gold)] font-semibold text-sm">
                        {language === 'fr'
                          ? 'Prélèvement selon l\'usage de la marchandise'
                          : 'Levy depending on the use of the goods'}
                      </p>
                      <p className="text-[var(--gold)] text-xs mt-1">
                        {result.usages.applique
                          ? (language === 'fr' ? 'Usage déclaré appliqué : ' : 'Declared use applied: ')
                            + (result.usages.possibles.find((u) => u.code === result.usages.applique)?.libelle || result.usages.applique)
                          : (language === 'fr'
                            ? 'Aucun usage déclaré : le régime courant est calculé.'
                            : 'No use declared: the standard regime is calculated.')}
                      </p>
                      <div className="mt-2 space-y-1">
                        {result.usages.possibles.map((u) => (
                          <p key={u.code} className="text-[var(--gold)] text-xs" dir="auto">
                            <span className="font-semibold">{u.libelle}</span> — {u.texte}
                          </p>
                        ))}
                      </div>
                      <div className="mt-3 flex flex-wrap items-end gap-2">
                        <select
                          data-testid="usage-saisi"
                          value={usageFor === result._quantite_cle ? usage : (result.usages.applique || '')}
                          onChange={(e) => {
                            setUsage(e.target.value);
                            setUsageFor(result._quantite_cle);
                          }}
                          className="px-3 py-2 bg-[var(--field)] border border-[var(--field-border)] rounded-lg text-[var(--text)] text-sm"
                        >
                          <option value="">{language === 'fr' ? 'Aucun de ces usages' : 'None of these uses'}</option>
                          {result.usages.possibles.map((u) => (
                            <option key={u.code} value={u.code}>{u.libelle}</option>
                          ))}
                        </select>
                        <Button
                          type="button"
                          data-testid="usage-recalculer"
                          onClick={() => calculateTariff()}
                          disabled={loading}
                          className="bg-amber-600 hover:bg-amber-700"
                        >
                          {language === 'fr' ? 'Recalculer' : 'Recalculate'}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* VALEUR FOB — ouverte seulement quand un moteur la réclame
                  (assiette SACU). Elle ne se déduit jamais du CIF : le fret et
                  l'assurance n'y sont pas connus. Au plus égale au CIF, que
                  fret et assurance complètent. */}
              {result.valeur_fob_requise?.requise && (
                <div
                  className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl"
                  data-testid="valeur-fob-requise"
                >
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-[var(--gold)] font-semibold text-sm">
                        {language === 'fr'
                          ? 'Valeur en douane FOB nécessaire'
                          : 'FOB customs value required'}
                      </p>
                      <p className="text-[var(--gold)] text-xs mt-1">
                        {language === 'fr'
                          ? "Ce pays liquide le droit de douane sur la valeur FOB (fret et assurance internationaux exclus). Elle ne se déduit pas de la valeur CIF."
                          : 'This country assesses customs duty on the FOB value (international freight and insurance excluded). It cannot be derived from the CIF value.'}
                      </p>

                      <div className="mt-2 space-y-1">
                        {result.valeur_fob_requise.lignes.map((l) => (
                          <p key={l.code} className="text-[var(--gold)] text-xs">
                            <span className="font-mono">{l.code}</span> — {l.libelle}
                          </p>
                        ))}
                      </div>

                      <div className="mt-3 flex flex-wrap items-end gap-2">
                        <div>
                          <label
                            className="block text-[var(--gold)] text-xs mb-1"
                            htmlFor="valeur-fob"
                          >
                            {language === 'fr'
                              ? 'Valeur FOB (USD, au plus la valeur CIF)'
                              : 'FOB value (USD, at most the CIF value)'}
                          </label>
                          <input
                            id="valeur-fob"
                            data-testid="valeur-fob-saisie"
                            type="number"
                            min="0"
                            step="any"
                            value={fobValue}
                            onChange={(e) => {
                              setFobValue(e.target.value);
                              setFobFor(result._quantite_cle);
                            }}
                            className="w-40 px-3 py-2 bg-[var(--field)] border border-[var(--field-border)] rounded-lg text-[var(--text)] text-sm"
                            placeholder="FOB"
                          />
                        </div>
                        <Button
                          type="button"
                          data-testid="valeur-fob-recalculer"
                          onClick={() => calculateTariff()}
                          disabled={
                            loading
                            || !(parseFloat(fobValue) > 0)
                            || parseFloat(fobValue) > parseFloat(value)
                          }
                          className="bg-amber-600 hover:bg-amber-700"
                        >
                          {language === 'fr' ? 'Recalculer' : 'Recalculate'}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {Array.isArray(result.regional_simulations) && result.regional_simulations.length > 0 && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--info)_30%,transparent)] rounded-xl">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-[var(--info)] mt-0.5 flex-shrink-0" />
                    <div className="w-full">
                      <p className="text-[var(--info)] font-semibold text-sm">
                        {language === 'fr'
                          ? 'Autres régimes publiés par le tarif de destination'
                          : 'Other regimes published by the destination tariff'}
                      </p>
                      <p className="text-[var(--info)] text-xs mt-1">
                        {language === 'fr'
                          ? "Simulations, non appliquées au total ci-dessus."
                          : 'Simulations, not applied to the total above.'}
                      </p>

                      <div className="mt-3 space-y-2">
                        {result.regional_simulations.map((sim) => (
                          <div
                            key={sim.regime}
                            className="p-3 bg-[var(--overlay)] border border-[var(--afcfta-border)] rounded-lg"
                            data-testid={`regional-simulation-${sim.regime}`}
                          >
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                              <span className="text-[var(--text)] text-sm font-medium">{sim.libelle}</span>
                              <span className="font-mono text-sm text-[var(--info)]">
                                {sim.taux_publie_pct} % · {sim.prelevement}
                              </span>
                            </div>
                            {sim.total_simule !== null && sim.total_simule !== undefined && (
                              <div className="flex flex-wrap items-baseline justify-between gap-2 mt-1">
                                <span className="text-[var(--afcfta-muted)] text-xs">
                                  {language === 'fr' ? 'Total simulé' : 'Simulated total'}
                                </span>
                                <span className="font-mono text-base text-[var(--text)]">
                                  {sim.total_simule.toLocaleString('fr-FR')}
                                  {sim.ecart_vs_total_servi !== null &&
                                    sim.ecart_vs_total_servi !== undefined && (
                                      <span className="text-[var(--afcfta-muted)] text-xs ml-2">
                                        {language === 'fr' ? 'écart ' : 'gap '}
                                        {sim.ecart_vs_total_servi.toLocaleString('fr-FR')}
                                      </span>
                                    )}
                                </span>
                              </div>
                            )}
                            <p className="text-[var(--afcfta-muted)] text-xs mt-2">{sim.reserve}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {result.plancher_npf && (
                <div className="mb-6 p-4 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-xl flex items-start gap-3">
                  <Info className="w-5 h-5 text-[var(--gold)] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-[var(--gold)] font-semibold text-sm">
                      {language === 'fr'
                        ? `Taux NPF servi (${result.plancher_npf.taux_retenu_pct} %) : le barème préférentiel est plus cher`
                        : `MFN rate applied (${result.plancher_npf.taux_retenu_pct}%): the preferential schedule costs more`}
                    </p>
                    <p className="text-[var(--gold)] text-sm mt-1">
                      {language === 'fr'
                        ? `Le barème préférentiel de cette position affiche ${result.plancher_npf.taux_preferentiel_ecarte_pct} %, soit davantage que le droit commun. Une préférence est une faculté, pas une obligation : c'est le NPF qui est servi.`
                        : `The preferential schedule for this line shows ${result.plancher_npf.taux_preferentiel_ecarte_pct}%, more than the ordinary duty. A preference is an option, not an obligation: the MFN rate is applied.`}
                    </p>
                  </div>
                </div>
              )}

              {/* Bandeau Valeur CIF + Code HS sélectionné */}
              <div className="mb-6 p-4 bg-[image:var(--lift)] rounded-xl border border-[var(--afcfta-border)]">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Valeur CIF */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] rounded-lg">
                      <DollarSign className="w-5 h-5 text-[var(--success)]" />
                    </div>
                    <div>
                      <p className="text-[var(--afcfta-muted)] text-xs">{language === 'fr' ? 'Valeur CIF' : 'CIF value'}</p>
                      <p className="text-xl font-bold text-[var(--success)]">
                        {formatCurrency(parseFloat(value) || 0)}
                      </p>
                    </div>
                  </div>
                  
                  {/* Code HS utilisé */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))] rounded-lg">
                      <Package className="w-5 h-5 text-[var(--violet)]" />
                    </div>
                    <div>
                      <p className="text-[var(--afcfta-muted)] text-xs">{language === 'fr' ? 'Code tarifaire' : 'Tariff code'}</p>
                      <p className="font-mono text-lg font-bold text-[var(--violet)]">{result.hs_code || hsCode}</p>
                    </div>
                  </div>
                  
                  {/* Description produit */}
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg">
                      <FileText className="w-5 h-5 text-[var(--gold)]" />
                    </div>
                    <div className="flex-1">
                      <p className="text-[var(--afcfta-muted)] text-xs">{language === 'fr' ? 'Produit' : 'Product'}</p>
                      <p className="text-sm text-[var(--text)] truncate">
                        {selectedSubPositionDesc || result.description || (language === 'fr' ? 'Position sélectionnée' : 'Selected position')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Grille de synthèse économique */}
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {/* Total NPF */}
                <div className="bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))] rounded-xl p-4 border border-[color-mix(in_srgb,var(--danger)_30%,transparent)]">
                  <p className="text-[var(--danger)] text-xs font-medium">{language === 'fr' ? 'Total NPF' : 'Total MFN'}</p>
                  <p className="text-3xl font-bold text-[var(--danger)] mt-1">{(result.total_taxes_npf || 0).toFixed(1)}%</p>
                  <p className="text-[var(--danger)] text-xs mt-1">{language === 'fr' ? 'Sans accord' : 'No agreement'}</p>
                </div>
                
                {/* Total ZLECAf */}
                <div className="bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] rounded-xl p-4 border border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                  <p className="text-[var(--success)] text-xs font-medium">{language === 'fr' ? 'Total ZLECAf' : 'Total AfCFTA'}</p>
                  <p className="text-3xl font-bold text-[var(--success)] mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? `${zlecafTotalTaxRatePct(result).toFixed(1)}%`
                      : '—'}
                  </p>
                  <p className="text-[var(--success)] text-xs mt-1">
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
                <div className="bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-xl p-4 border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                  <p className="text-[var(--gold)] text-xs font-medium">{language === 'fr' ? 'Économie' : 'Savings'}</p>
                  <p className="text-3xl font-bold text-[var(--gold)] mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? `-${((result.total_taxes_npf || 0) - zlecafTotalTaxRatePct(result)).toFixed(1)}%`
                      : '—'}
                  </p>
                  <p className="text-[var(--gold)] text-xs mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? (language === 'fr' ? 'Certificat Origine' : 'Origin Certificate')
                      : (result.zlecaf_status === 'OFFER_ONLY' || result.zlecaf_status === 'PARTNER_NOTICE_REQUIRED')
                        ? (language === 'fr' ? 'À vérifier' : 'To verify')
                        : (language === 'fr' ? 'Non disponible' : 'Unavailable')}
                  </p>
                </div>
                
                {/* Montant économisé */}
                <div className="bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-xl p-4 border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                  <p className="text-[var(--info)] text-xs font-medium">{language === 'fr' ? 'Montant économisé' : 'Amount saved'}</p>
                  <p className="text-2xl font-bold text-[var(--info)] mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? montant((parseFloat(value) || 0) * ((result.total_taxes_npf || 0) - zlecafTotalTaxRatePct(result)) / 100, language)
                      : '—'}
                  </p>
                  <p className="text-[var(--info)] text-xs mt-1">
                    {zlecafTotalTaxRatePct(result) !== null
                      ? (language === 'fr' ? 'Sur votre valeur' : 'On your value')
                      : (language === 'fr' ? 'Non calculé' : 'Not calculated')}
                  </p>
                </div>
              </div>
              <p className="mt-4 text-center text-xs font-medium text-[var(--gold)]">
                Simulation informative — non opposable à l’administration douanière.
              </p>

              {/* Point 4 — signalement d'incomplétude : le total ci-dessus couvre les
                  droits et taxes exigibles, mais un prestataire mandaté actif facture
                  des frais dont le montant n'est pas chiffré dans les sources. Le coût
                  total réel de dédouanement est donc INCOMPLET — signalé, jamais estimé. */}
              {hasUnpricedActiveProviderFees(result.regulatory_compliance) && (
                <div className="mt-4 flex items-start gap-3 p-3 rounded-xl bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                  <AlertTriangle className="w-5 h-5 text-[var(--gold)] shrink-0 mt-0.5" />
                  <p className="text-sm text-[var(--gold)]">
                    {language === 'fr'
                      ? "Calcul incomplet : ces totaux couvrent les droits et taxes exigibles, mais un prestataire mandaté actif perçoit des frais dont le montant n'est pas publié dans les sources (NOT_AVAILABLE). Le coût total de dédouanement est donc supérieur — voir le bloc « Frais des prestataires mandatés » ci-dessous. Aucun montant n'est estimé."
                      : 'Incomplete calculation: these totals cover payable duties and taxes, but an active mandated provider charges fees whose amount is not published in the sources (NOT_AVAILABLE). The total clearance cost is therefore higher — see the “Mandated-provider fees” block below. No amount is estimated.'}
                  </p>
                </div>
              )}
              <p className="mt-4 text-center text-xs font-medium text-[var(--gold)]">
                Simulation informative — non opposable à l’administration douanière.
              </p>
            </CardContent>
          </Card>

          {/* Détail des taxes */}
          {result.taxes_detail && result.taxes_detail.length > 0 && (
            <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <ClipboardList className="w-5 h-5 text-[var(--info)]" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-[var(--text)]">{language === 'fr' ? 'Détail des Taxes' : 'Tax Breakdown'}</CardTitle>
                    <CardDescription className="text-[var(--afcfta-muted)]">
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
                      className="flex items-center justify-between p-3 bg-[var(--overlay)] rounded-lg border border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--info)_30%,transparent)] transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg">
                          <FileText className="w-4 h-4 text-[var(--info)]" />
                        </div>
                        <div>
                          <span className="font-mono text-[var(--text)] font-semibold">{tax.tax}</span>
                          {tax.observation && (
                            <p className="text-[var(--afcfta-muted)] text-sm">{tax.observation}</p>
                          )}
                          {tax.note && (
                            <p className="text-[var(--afcfta-muted)] text-xs">{tax.note}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-[var(--afcfta-muted)] text-xs">{language === 'fr' ? 'NPF' : 'MFN'}</p>
                          <p className="text-[var(--text)] font-bold">{tax.rate}%</p>
                        </div>
                        <div className="text-right">
                          <p className="text-[var(--afcfta-muted)] text-xs">{language === 'fr' ? 'ZLECAf' : 'AfCFTA'}</p>
                          <p className="text-[var(--success)] font-bold">
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
            <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                      <Scale className="w-5 h-5 text-[var(--violet)]" />
                    </div>
                    <div>
                      <CardTitle className="text-lg text-[var(--text)]">
                        {language === 'fr' ? 'Positions Nationales' : 'National Positions'}
                      </CardTitle>
                      <CardDescription className="text-[var(--afcfta-muted)]">
                        {subPositions.sub_positions.length} {language === 'fr' ? 'positions (10 chiffres)' : 'positions (10 digits)'}
                        {subPositions.note && <span className="ml-2 text-[var(--violet)]/70 text-xs">— {subPositions.note}</span>}
                      </CardDescription>
                    </div>
                  </div>
                  {selectedSubPositionDesc && (
                    <Badge className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] border border-[color-mix(in_srgb,var(--violet)_30%,transparent)] text-xs">
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
                            ? 'bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]'
                            : 'bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--violet)_30%,transparent)] hover:bg-[var(--overlay)]'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="font-mono text-sm font-bold text-[var(--violet)] bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))] px-2 py-0.5 rounded shrink-0">
                            {code}
                          </span>
                          <p className="text-[var(--text)] text-sm truncate">{desc}</p>
                        </div>
                        <div className="flex items-center gap-3 shrink-0 ml-3">
                          {spFormalities && spFormalities.length > 0 && (
                            <Badge className="bg-[var(--overlay)] text-[var(--text)] border border-[var(--afcfta-border)] text-xs">
                              {spFormalities.length} {language === 'fr' ? 'docs' : 'docs'}
                            </Badge>
                          )}
                          {isSelected && <CheckCircle className="w-4 h-4 text-[var(--violet)]" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-[var(--afcfta-muted)] mt-3 border-t border-[var(--afcfta-border)] pt-2">
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
            // établi pour l'Algérie, fiche DGD à l'appui — une liste vide est
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
              <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)]">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                        <FileCheck className="w-5 h-5 text-[var(--gold)]" />
                      </div>
                      <div>
                        <CardTitle className="text-lg text-[var(--text)]">
                          {language === 'fr' ? 'Documents Requis' : 'Required Documents'}
                        </CardTitle>
                        <CardDescription className="text-[var(--afcfta-muted)]">
                          {aucuneFormalite
                            ? (constatSource
                              ? (language === 'fr' ? 'Aucune formalité particulière' : 'No specific formality')
                              : (language === 'fr' ? 'Non établies' : 'Not established'))
                            : `${formalities.length} ${language === 'fr' ? 'formalités' : 'formalities'}`}
                          {isPositionLevel && (
                            <span className="ml-2 text-[var(--violet)] text-xs font-mono">
                              — position {positionCode}
                            </span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                    {isPositionLevel && (
                      <Badge className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] border border-[color-mix(in_srgb,var(--violet)_30%,transparent)] text-xs">
                        {language === 'fr' ? 'Position nationale' : 'National position'}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {aucuneFormalite && (
                    <div className={`flex items-start gap-3 p-3 rounded-lg border ${constatSource ? 'bg-[var(--overlay)] border-[var(--afcfta-border)]' : 'bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]'}`}>
                      {constatSource
                        ? <Info className="w-5 h-5 text-[var(--afcfta-muted)] shrink-0 mt-0.5" />
                        : <AlertTriangle className="w-5 h-5 text-[var(--gold)] shrink-0 mt-0.5" />}
                      <p className="text-[var(--text)] text-sm">{reserve}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(formalities || []).map((form, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${form.is_mandatory === false ? 'bg-[var(--overlay)] border-[var(--afcfta-border)]' : 'bg-[var(--overlay)] border-[var(--afcfta-border)]'}`}
                      >
                        <div className="flex items-start gap-2">
                          <Badge className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] border font-mono shrink-0 text-xs">
                            {form.code}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            {/* Égypte : le texte officiel est l'arabe ; la
                                traduction, reprise d'un autre fichier, se dit
                                non officielle. */}
                            {form.traduction_non_officielle && (
                              <p dir="auto" className="text-[var(--text)] text-sm">{form.texte}</p>
                            )}
                            <p className={form.traduction_non_officielle ? 'text-[var(--afcfta-muted)] text-xs mt-1' : 'text-[var(--text)] text-sm'}>
                              {language === 'fr' ? (form.document_fr || form.document_en) : (form.document_en || form.document_fr)}
                              {form.traduction_non_officielle && (
                                <span className="italic">
                                  {language === 'fr' ? ' — traduction non officielle' : ' — unofficial translation'}
                                </span>
                              )}
                            </p>
                            {form.base_legale && (
                              <p className="text-[var(--afcfta-muted)] text-xs mt-1">{form.base_legale}</p>
                            )}
                            {(form.authority_fr || form.authority_en) && (
                              <p className="text-[var(--afcfta-muted)] text-xs mt-1">
                                {language === 'fr' ? form.authority_fr : form.authority_en}
                              </p>
                            )}
                            {form.is_mandatory === false && (
                              <span className="text-xs text-[var(--afcfta-muted)] italic">
                                {language === 'fr' ? 'Optionnel' : 'Optional'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {!isPositionLevel && (
                    <p className="text-xs text-[var(--afcfta-muted)] mt-3 border-t border-[var(--afcfta-border)] pt-2">
                      {language === 'fr'
                        ? 'Formalités au niveau HS6. Sélectionnez une sous-position nationale pour les formalités spécifiques à la position (10 chiffres).'
                        : 'Formalities at HS6 level. Select a national sub-position for position-specific formalities (10 digits).'}
                    </p>
                  )}
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
            <Card className="bg-[image:var(--card-grad)] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                    <ClipboardList className="w-5 h-5 text-[var(--gold)]" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-[var(--text)]">
                      {language === 'fr'
                        ? 'Détail des formalités & prestataires mandatés'
                        : 'Formalities & mandated providers — detail'}
                    </CardTitle>
                    <CardDescription className="text-[var(--afcfta-muted)]">
                      {language === 'fr'
                        ? `${getCountryName(result.destination_country)} — mission, mandat, preuves datées et sources officielles`
                        : `${getCountryName(result.destination_country)} — mission, mandate, dated evidence and official sources`}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                  <AlertTriangle className="w-5 h-5 text-[var(--gold)] shrink-0 mt-0.5" />
                  <p className="text-sm text-[var(--gold)]">
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
              <Card className="bg-[image:var(--card-grad)] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                      <ClipboardList className="w-6 h-6 text-[var(--gold)]" />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-[var(--text)]">
                        {language === 'fr'
                          ? 'Formalités particulières & prestataires mandatés'
                          : 'Special formalities & mandated providers'}
                      </CardTitle>
                      <CardDescription className="text-[var(--afcfta-muted)]">
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
            <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] overflow-hidden">
              <div className="absolute top-0 left-0 w-96 h-96 bg-[color-mix(in_srgb,var(--gold)_5%,transparent)] rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2"></div>
              
              <CardHeader className="relative">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                    <Scale className="w-8 h-8 text-[var(--gold)]" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-[var(--text)]">
                      {language === 'fr' ? 'Moteur Réglementaire AfCFTA' : 'AfCFTA Regulatory Engine'}
                    </CardTitle>
                    <CardDescription className="text-[var(--afcfta-muted)] text-base mt-1">
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
                    <Label className="text-[var(--text)] font-medium">
                      {language === 'fr' ? 'Pays de destination' : 'Destination Country'}
                    </Label>
                    <Select value={destinationCountry} onValueChange={handleDestinationChange}>
                      <SelectTrigger 
                        data-testid="regulatory-country-select"
                        className="h-12 bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--gold)_30%,transparent)] transition-colors"
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
                                  <span className="ml-2 text-xs bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] px-2 py-0.5 rounded">
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
                    <Label className="text-[var(--text)] font-medium">
                      {language === 'fr' ? 'Code HS (6 à 12 chiffres)' : 'HS Code (6 to 12 digits)'}
                    </Label>
                    <Input
                      value={hsCode}
                      onChange={handleRegulatoryHsCodeChange}
                      placeholder={language === 'fr' ? 'Ex: 010110, 0101101000...' : 'E.g: 010110, 0101101000...'}
                      className="h-12 font-mono text-lg bg-[var(--overlay)] border-[var(--afcfta-border)] hover:border-[color-mix(in_srgb,var(--gold)_30%,transparent)] focus:border-[color-mix(in_srgb,var(--gold)_30%,transparent)] transition-colors"
                      data-testid="regulatory-hs-input"
                    />
                  </div>
                </div>

                {/* Guide d'utilisation */}
                <div className="bg-[var(--overlay)] border border-[var(--afcfta-border)] rounded-xl p-5">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] shrink-0">
                      <Info className="w-5 h-5 text-[var(--info)]" />
                    </div>
                    <div>
                      <p className="font-semibold text-[var(--text)] mb-2">
                        {language === 'fr' ? 'Guide d\'utilisation' : 'How to use'}
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] text-xs font-bold shrink-0">1</span>
                          <span className="text-[var(--afcfta-muted)]">
                            {language === 'fr' ? 'Sélectionnez le pays de destination' : 'Select the destination country'}
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] text-xs font-bold shrink-0">2</span>
                          <span className="text-[var(--afcfta-muted)]">
                            {language === 'fr' ? 'Entrez un code HS6 ou HS10' : 'Enter an HS6 or HS10 code'}
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] text-xs font-bold shrink-0">3</span>
                          <span className="text-[var(--afcfta-muted)]">
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
                  <div className="flex items-start justify-between gap-3 p-4 bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))] rounded-xl border border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                    <div className="flex items-start gap-3 min-w-0">
                      <FileText className="w-5 h-5 text-[var(--violet)] mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-[var(--violet)] font-medium mb-1">
                          {language === 'fr' ? 'Intitulé exact de la position nationale' : 'Exact title of national position'}
                        </p>
                        <p className="text-[var(--text)] font-medium">{regulatorySelectedPosDesc}</p>
                        <p className="text-[var(--violet)] font-mono text-sm mt-1">{regulatorySelectedPos}</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="shrink-0 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] text-[var(--violet)] hover:bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]"
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
              <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] border-dashed">
                <CardContent className="p-12 text-center">
                  <div className="w-20 h-20 mx-auto mb-6 bg-[var(--overlay)] rounded-2xl flex items-center justify-center">
                    <Scale className="w-10 h-10 text-[var(--afcfta-muted)]" />
                  </div>
                  <p className="text-[var(--afcfta-muted)] text-lg mb-2">
                    {language === 'fr' 
                      ? 'Sélectionnez un pays et entrez un code HS'
                      : 'Select a country and enter an HS code'}
                  </p>
                  <p className="text-[var(--afcfta-muted)] text-sm">
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
