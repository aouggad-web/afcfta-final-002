/**
 * Multi-Country Tariff Comparison Component
 * Compare tariffs for the same product across multiple African countries
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, Radar
} from 'recharts';
import { Search, Globe, TrendingDown, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const API = (process.env.REACT_APP_BACKEND_URL || '') + '/api';

// Country flag emoji helper
const getFlag = (iso2) => {
  if (!iso2 || iso2.length !== 2) return '🌍';
  const codePoints = iso2
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt());
  return String.fromCodePoint(...codePoints);
};

// ISO3 to ISO2 mapping
const ISO3_TO_ISO2 = {
  'DZA': 'DZ', 'AGO': 'AO', 'BEN': 'BJ', 'BWA': 'BW', 'BFA': 'BF', 'BDI': 'BI', 'CMR': 'CM', 'CPV': 'CV',
  'CAF': 'CF', 'TCD': 'TD', 'COM': 'KM', 'COG': 'CG', 'COD': 'CD', 'CIV': 'CI', 'DJI': 'DJ', 'EGY': 'EG',
  'GNQ': 'GQ', 'ERI': 'ER', 'SWZ': 'SZ', 'ETH': 'ET', 'GAB': 'GA', 'GMB': 'GM', 'GHA': 'GH', 'GIN': 'GN',
  'GNB': 'GW', 'KEN': 'KE', 'LSO': 'LS', 'LBR': 'LR', 'LBY': 'LY', 'MDG': 'MG', 'MWI': 'MW', 'MLI': 'ML',
  'MRT': 'MR', 'MUS': 'MU', 'MAR': 'MA', 'MOZ': 'MZ', 'NAM': 'NA', 'NER': 'NE', 'NGA': 'NG', 'RWA': 'RW',
  'STP': 'ST', 'SEN': 'SN', 'SYC': 'SC', 'SLE': 'SL', 'SOM': 'SO', 'ZAF': 'ZA', 'SSD': 'SS', 'SDN': 'SD',
  'TZA': 'TZ', 'TGO': 'TG', 'TUN': 'TN', 'UGA': 'UG', 'ZMB': 'ZM', 'ZWE': 'ZW'
};

// Country names
const COUNTRY_NAMES = {
  'DZA': { fr: 'Algérie', en: 'Algeria' },
  'AGO': { fr: 'Angola', en: 'Angola' },
  'BEN': { fr: 'Bénin', en: 'Benin' },
  'BWA': { fr: 'Botswana', en: 'Botswana' },
  'BFA': { fr: 'Burkina Faso', en: 'Burkina Faso' },
  'BDI': { fr: 'Burundi', en: 'Burundi' },
  'CMR': { fr: 'Cameroun', en: 'Cameroon' },
  'CPV': { fr: 'Cap-Vert', en: 'Cabo Verde' },
  'CAF': { fr: 'Centrafrique', en: 'Central African Rep.' },
  'TCD': { fr: 'Tchad', en: 'Chad' },
  'COM': { fr: 'Comores', en: 'Comoros' },
  'COG': { fr: 'Congo', en: 'Congo' },
  'COD': { fr: 'RD Congo', en: 'DR Congo' },
  'CIV': { fr: 'Côte d\'Ivoire', en: 'Côte d\'Ivoire' },
  'DJI': { fr: 'Djibouti', en: 'Djibouti' },
  'EGY': { fr: 'Égypte', en: 'Egypt' },
  'GNQ': { fr: 'Guinée Équat.', en: 'Equatorial Guinea' },
  'ERI': { fr: 'Érythrée', en: 'Eritrea' },
  'SWZ': { fr: 'Eswatini', en: 'Eswatini' },
  'ETH': { fr: 'Éthiopie', en: 'Ethiopia' },
  'GAB': { fr: 'Gabon', en: 'Gabon' },
  'GMB': { fr: 'Gambie', en: 'Gambia' },
  'GHA': { fr: 'Ghana', en: 'Ghana' },
  'GIN': { fr: 'Guinée', en: 'Guinea' },
  'GNB': { fr: 'Guinée-Bissau', en: 'Guinea-Bissau' },
  'KEN': { fr: 'Kenya', en: 'Kenya' },
  'LSO': { fr: 'Lesotho', en: 'Lesotho' },
  'LBR': { fr: 'Liberia', en: 'Liberia' },
  'LBY': { fr: 'Libye', en: 'Libya' },
  'MDG': { fr: 'Madagascar', en: 'Madagascar' },
  'MWI': { fr: 'Malawi', en: 'Malawi' },
  'MLI': { fr: 'Mali', en: 'Mali' },
  'MRT': { fr: 'Mauritanie', en: 'Mauritania' },
  'MUS': { fr: 'Maurice', en: 'Mauritius' },
  'MAR': { fr: 'Maroc', en: 'Morocco' },
  'MOZ': { fr: 'Mozambique', en: 'Mozambique' },
  'NAM': { fr: 'Namibie', en: 'Namibia' },
  'NER': { fr: 'Niger', en: 'Niger' },
  'NGA': { fr: 'Nigeria', en: 'Nigeria' },
  'RWA': { fr: 'Rwanda', en: 'Rwanda' },
  'STP': { fr: 'São Tomé', en: 'São Tomé' },
  'SEN': { fr: 'Sénégal', en: 'Senegal' },
  'SYC': { fr: 'Seychelles', en: 'Seychelles' },
  'SLE': { fr: 'Sierra Leone', en: 'Sierra Leone' },
  'SOM': { fr: 'Somalie', en: 'Somalia' },
  'ZAF': { fr: 'Afrique du Sud', en: 'South Africa' },
  'SSD': { fr: 'Soudan du Sud', en: 'South Sudan' },
  'SDN': { fr: 'Soudan', en: 'Sudan' },
  'TZA': { fr: 'Tanzanie', en: 'Tanzania' },
  'TGO': { fr: 'Togo', en: 'Togo' },
  'TUN': { fr: 'Tunisie', en: 'Tunisia' },
  'UGA': { fr: 'Ouganda', en: 'Uganda' },
  'ZMB': { fr: 'Zambie', en: 'Zambia' },
  'ZWE': { fr: 'Zimbabwe', en: 'Zimbabwe' }
};

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

// Regional groupings
const REGIONS = {
  'north': ['DZA', 'EGY', 'LBY', 'MAR', 'TUN', 'MRT', 'SDN'],
  'west': ['BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB', 'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO'],
  'cemac': ['CMR', 'CAF', 'TCD', 'COG', 'GNQ', 'GAB'],
  'central': ['COD', 'STP'],
  'east': ['BDI', 'COM', 'DJI', 'ERI', 'ETH', 'KEN', 'MDG', 'MUS', 'RWA', 'SYC', 'SOM', 'SSD', 'TZA', 'UGA'],
  'south': ['AGO', 'BWA', 'LSO', 'MWI', 'MOZ', 'NAM', 'ZAF', 'SWZ', 'ZMB', 'ZWE']
};

export default function MultiCountryComparison({ language = 'fr' }) {
  const [availableCountries, setAvailableCountries] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState(['MAR', 'DZA', 'TUN', 'EGY', 'NGA']);
  const [hsCode, setHsCode] = useState('180100');
  const [value, setValue] = useState(50000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [productDescription, setProductDescription] = useState('');
  
  const texts = {
    fr: {
      title: 'Comparaison Multi-Pays',
      subtitle: 'Comparez les tarifs douaniers pour un produit dans plusieurs pays',
      hsCode: 'Code HS (6-12 chiffres)',
      value: 'Valeur (USD)',
      selectCountries: 'Sélectionnez les pays à comparer',
      compare: 'Comparer',
      comparing: 'Comparaison en cours...',
      results: 'Résultats de la Comparaison',
      country: 'Pays',
      ddRate: 'DD%',
      vatRate: 'TVA%',
      totalTaxes: 'Total Taxes',
      npfTotal: 'Total NPF',
      zlecafTotal: 'Total ZLECAf',
      savings: 'Économies',
      bestChoice: 'Meilleur choix',
      allTaxes: 'Toutes les taxes',
      noResults: 'Aucun résultat',
      selectAtLeast2: 'Sélectionnez au moins 2 pays',
      regions: {
        north: 'Afrique du Nord',
        west: 'Afrique de l\'Ouest',
        cemac: 'CEMAC (Afrique Centrale)',
        central: 'Afrique Centrale (autres)',
        east: 'Afrique de l\'Est',
        south: 'Afrique Australe'
      }
    },
    en: {
      title: 'Multi-Country Comparison',
      subtitle: 'Compare customs tariffs for a product across multiple countries',
      hsCode: 'HS Code (6-12 digits)',
      value: 'Value (USD)',
      selectCountries: 'Select countries to compare',
      compare: 'Compare',
      comparing: 'Comparing...',
      results: 'Comparison Results',
      country: 'Country',
      ddRate: 'DD%',
      vatRate: 'VAT%',
      totalTaxes: 'Total Taxes',
      npfTotal: 'MFN Total',
      zlecafTotal: 'AfCFTA Total',
      savings: 'Savings',
      bestChoice: 'Best choice',
      allTaxes: 'All taxes',
      noResults: 'No results',
      selectAtLeast2: 'Select at least 2 countries',
      regions: {
        north: 'North Africa',
        west: 'West Africa',
        cemac: 'CEMAC (Central Africa)',
        central: 'Central Africa (other)',
        east: 'East Africa',
        south: 'Southern Africa'
      }
    }
  };
  
  const t = texts[language] || texts.fr;
  
  // Load available countries
  useEffect(() => {
    const loadCountries = async () => {
      try {
        const response = await axios.get(`${API}/authentic-tariffs/countries`);
        setAvailableCountries(response.data.countries.map(c => c.iso3));
      } catch (error) {
        console.error('Error loading countries:', error);
      }
    };
    loadCountries();
  }, []);
  
  // Toggle country selection
  const toggleCountry = (iso3) => {
    if (selectedCountries.includes(iso3)) {
      setSelectedCountries(prev => prev.filter(c => c !== iso3));
    } else {
      setSelectedCountries(prev => [...prev, iso3]);
    }
  };
  
  // Select/deselect region
  const toggleRegion = (regionKey) => {
    const regionCountries = REGIONS[regionKey].filter(c => availableCountries.includes(c));
    const allSelected = regionCountries.every(c => selectedCountries.includes(c));
    
    if (allSelected) {
      setSelectedCountries(prev => prev.filter(c => !regionCountries.includes(c)));
    } else {
      setSelectedCountries(prev => [...new Set([...prev, ...regionCountries])]);
    }
  };
  
  // Perform comparison
  const compareCountries = async () => {
    if (selectedCountries.length < 2) {
      alert(t.selectAtLeast2);
      return;
    }
    
    setLoading(true);
    setResults([]);
    
    try {
      const promises = selectedCountries.map(iso3 =>
        axios.get(`${API}/authentic-tariffs/calculate/${iso3}/${hsCode}?value=${value}&language=${language}`)
          .then(res => ({ iso3, ...res.data, success: true }))
          .catch(err => ({ iso3, success: false, error: err.message }))
      );
      
      const responses = await Promise.all(promises);
      const successfulResults = responses
        .filter(r => r.success)
        .map(r => {
          const npfTotal = r.npf_calculation?.total_to_pay || 0;
          const zlecafTotal = r.zlecaf_calculation?.total_to_pay || 0;
          const savings = npfTotal - zlecafTotal;
          
          return {
            iso3: r.iso3,
            iso2: ISO3_TO_ISO2[r.iso3],
            countryName: COUNTRY_NAMES[r.iso3]?.[language] || r.iso3,
            description: r.description,
            rates: r.rates || {},
            taxes: r.taxes_detail || [],
            npfTotal,
            zlecafTotal,
            savings,
            savingsPercent: npfTotal > 0 ? ((savings / npfTotal) * 100).toFixed(1) : 0
          };
        })
        .sort((a, b) => a.zlecafTotal - b.zlecafTotal);
      
      if (successfulResults.length > 0) {
        setProductDescription(successfulResults[0].description);
      }
      
      setResults(successfulResults);
    } catch (error) {
      console.error('Comparison error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Chart data
  const chartData = results.map(r => ({
    name: `${getFlag(r.iso2)} ${r.countryName}`,
    'NPF': r.npfTotal - value,
    'ZLECAf': r.zlecafTotal - value,
    savings: r.savings
  }));
  
  // Radar data for tax rates
  const radarData = results.length > 0 ? [
    { metric: 'DD%', ...Object.fromEntries(results.map(r => [r.countryName, r.rates.dd_rate_pct || 0])) },
    { metric: 'TVA%', ...Object.fromEntries(results.map(r => [r.countryName, r.rates.vat_rate_pct || 0])) },
    { metric: language === 'fr' ? 'Autres%' : 'Other%', ...Object.fromEntries(results.map(r => [r.countryName, r.rates.other_taxes_pct || 0])) }
  ] : [];
  
  // Best country
  const bestCountry = results.length > 0 ? results[0] : null;
  
  return (
    <div className="space-y-6" data-testid="multi-country-comparison">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <Globe className="h-8 w-8" />
            {t.title}
          </CardTitle>
          <CardDescription className="text-purple-100">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>
      
      {/* Search Form */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="hsCode">{t.hsCode}</Label>
              <Input
                id="hsCode"
                value={hsCode}
                onChange={(e) => setHsCode(e.target.value.replace(/\D/g, ''))}
                placeholder="180100"
                className="font-mono"
                data-testid="compare-hs-code"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="value">{t.value}</Label>
              <Input
                id="value"
                type="number"
                value={value}
                onChange={(e) => setValue(parseFloat(e.target.value) || 0)}
                placeholder="50000"
                data-testid="compare-value"
              />
            </div>
          </div>
          
          {/* Country Selection by Region */}
          <div className="space-y-3">
            <Label>{t.selectCountries}</Label>
            
            {Object.entries(REGIONS).map(([regionKey, countryCodes]) => {
              const regionCountries = countryCodes.filter(c => availableCountries.includes(c));
              if (regionCountries.length === 0) return null;
              
              const allSelected = regionCountries.every(c => selectedCountries.includes(c));
              
              return (
                <div key={regionKey} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleRegion(regionKey)}
                      className={allSelected ? 'bg-purple-100 border-purple-300' : ''}
                    >
                      {t.regions[regionKey]}
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 pl-4">
                    {regionCountries.map(iso3 => {
                      const isSelected = selectedCountries.includes(iso3);
                      return (
                        <Badge
                          key={iso3}
                          variant={isSelected ? 'default' : 'outline'}
                          className={`cursor-pointer transition-all ${
                            isSelected 
                              ? 'bg-purple-600 hover:bg-purple-700' 
                              : 'hover:bg-purple-100'
                          }`}
                          onClick={() => toggleCountry(iso3)}
                          data-testid={`country-badge-${iso3}`}
                        >
                          {getFlag(ISO3_TO_ISO2[iso3])} {COUNTRY_NAMES[iso3]?.[language] || iso3}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Compare Button */}
          <Button
            onClick={compareCountries}
            disabled={loading || selectedCountries.length < 2}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white"
            data-testid="compare-button"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.comparing}
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                {t.compare} ({selectedCountries.length} {language === 'fr' ? 'pays' : 'countries'})
              </>
            )}
          </Button>
        </CardContent>
      </Card>
      
      {/* Results */}
      {results.length > 0 && (
        <>
          {/* Product Info */}
          <Card className="bg-slate-50">
            <CardContent className="py-4">
              <div className="flex items-center gap-4 flex-wrap">
                <Badge variant="outline" className="text-lg px-4 py-2">
                  <span className="font-mono font-bold">{hsCode}</span>
                </Badge>
                <span className="text-lg font-medium text-slate-700">{productDescription}</span>
                <Badge className="bg-green-100 text-green-700">
                  {formatCurrency(value)} CIF
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          {/* Best Choice Highlight */}
          {bestCountry && (
            <Card className="bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-xl">
              <CardContent className="py-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <CheckCircle className="h-10 w-10" />
                    <div>
                      <p className="text-sm opacity-90">{t.bestChoice}</p>
                      <p className="text-3xl font-bold">
                        {getFlag(bestCountry.iso2)} {bestCountry.countryName}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm opacity-90">{t.zlecafTotal}</p>
                    <p className="text-3xl font-bold">{formatCurrency(bestCountry.zlecafTotal)}</p>
                    <Badge className="bg-white/20 mt-2">
                      {t.savings}: {formatCurrency(bestCountry.savings)} (-{bestCountry.savingsPercent}%)
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                📊 {t.results}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="text-left p-3">{t.country}</th>
                      <th className="text-center p-3">{t.ddRate}</th>
                      <th className="text-center p-3">{t.vatRate}</th>
                      <th className="text-left p-3">{t.allTaxes}</th>
                      <th className="text-right p-3">{t.npfTotal}</th>
                      <th className="text-right p-3">{t.zlecafTotal}</th>
                      <th className="text-right p-3">{t.savings}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r, idx) => (
                      <tr 
                        key={r.iso3} 
                        className={`border-b hover:bg-slate-50 ${idx === 0 ? 'bg-emerald-50' : ''}`}
                      >
                        <td className="p-3 font-medium">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{getFlag(r.iso2)}</span>
                            <span>{r.countryName}</span>
                            {idx === 0 && (
                              <Badge className="bg-emerald-500 text-white text-xs">
                                #1
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="text-center p-3 font-mono">
                          {r.rates.dd_rate_pct || 0}%
                        </td>
                        <td className="text-center p-3 font-mono">
                          {r.rates.vat_rate_pct || 0}%
                        </td>
                        <td className="p-3">
                          <div className="flex flex-wrap gap-1">
                            {r.taxes.slice(0, 4).map((tax, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {tax.tax}: {tax.rate}%
                              </Badge>
                            ))}
                            {r.taxes.length > 4 && (
                              <Badge variant="outline" className="text-xs bg-slate-100">
                                +{r.taxes.length - 4}
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="text-right p-3 font-mono text-slate-600">
                          {formatCurrency(r.npfTotal)}
                        </td>
                        <td className="text-right p-3 font-mono font-bold text-emerald-600">
                          {formatCurrency(r.zlecafTotal)}
                        </td>
                        <td className="text-right p-3">
                          <div className="text-green-600 font-bold">
                            {formatCurrency(r.savings)}
                          </div>
                          <div className="text-xs text-slate-500">
                            -{r.savingsPercent}%
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
          
          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {language === 'fr' ? '📊 Comparaison des Taxes' : '📊 Tax Comparison'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                    <Tooltip 
                      formatter={(v) => formatCurrency(v)}
                      labelFormatter={(label) => label}
                    />
                    <Legend />
                    <Bar dataKey="NPF" fill="#3b82f6" name={language === 'fr' ? 'Taxes NPF' : 'MFN Taxes'} />
                    <Bar dataKey="ZLECAf" fill="#10b981" name={language === 'fr' ? 'Taxes ZLECAf' : 'AfCFTA Taxes'} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            
            {/* Radar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {language === 'fr' ? '🎯 Taux Comparés' : '🎯 Rate Comparison'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" />
                    <PolarRadiusAxis angle={30} domain={[0, 'auto']} />
                    {results.slice(0, 5).map((r, idx) => (
                      <Radar
                        key={r.iso3}
                        name={r.countryName}
                        dataKey={r.countryName}
                        stroke={['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx]}
                        fill={['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx]}
                        fillOpacity={0.2}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
