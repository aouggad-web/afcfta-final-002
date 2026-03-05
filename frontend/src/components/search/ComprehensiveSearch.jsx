import React, { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { apiV2 } from '../../services/api-v2';

const AFRICAN_COUNTRIES = [
  'Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
  'Cameroon', 'Cape Verde', 'Chad', 'Comoros', 'Congo', 'Côte d\'Ivoire',
  'DR Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini',
  'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya',
  'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
  'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda',
  'São Tomé and Príncipe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia',
  'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia',
  'Uganda', 'Zambia', 'Zimbabwe',
];

const SECTORS = ['Agriculture', 'Manufacturing', 'Technology', 'Energy', 'Textiles', 'Finance', 'Infrastructure'];
const HS_CHAPTERS = ['01-05 Animals', '06-14 Vegetables', '25-27 Minerals', '28-38 Chemicals', '50-63 Textiles', '84-85 Machinery', '87-89 Transport'];

const TABS = ['products', 'countries', 'investments'];

function Spinner() {
  return (
    <div className="flex items-center justify-center py-10">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
    </div>
  );
}

function ProductCard({ item, language }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow">
      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-700 font-mono text-xs font-bold shrink-0">
        {item.hsCode?.substring(0, 4) || '—'}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-800 text-sm truncate">{item.name || item.description}</p>
        <p className="text-xs text-gray-500">{item.hsCode} · {item.chapter}</p>
      </div>
      {item.tariffRate != null && (
        <Badge variant="outline" className="text-xs shrink-0">{item.tariffRate}%</Badge>
      )}
    </div>
  );
}

function CountryCard({ item }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow">
      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-xl">
        {item.flag || '🌍'}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-800 text-sm">{item.name}</p>
        <p className="text-xs text-gray-500">{item.bloc} · {item.gdp}</p>
      </div>
      {item.tradeScore != null && (
        <Badge className="text-xs bg-green-100 text-green-700 border-0 shrink-0">
          Score: {item.tradeScore}
        </Badge>
      )}
    </div>
  );
}

function InvestmentCard({ item }) {
  return (
    <div className="p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow space-y-1">
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium text-gray-800 text-sm leading-tight">{item.title || item.name}</p>
        <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs shrink-0">{item.sector}</Badge>
      </div>
      <p className="text-xs text-gray-500">{item.country} · {item.size || item.investmentSize}</p>
      {item.roi && (
        <p className="text-xs text-green-600 font-medium">ROI: {item.roi}</p>
      )}
    </div>
  );
}

export default function ComprehensiveSearch({ language = 'fr' }) {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({ countries: [], sectors: [], hsChapters: [] });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('products');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const inputRef = useRef(null);

  const toggleFilter = (key, value) => {
    setFilters((f) => ({
      ...f,
      [key]: f[key].includes(value) ? f[key].filter((v) => v !== value) : [...f[key], value],
    }));
  };

  const handleSearch = useCallback(async (pageNum = 1) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setPage(pageNum);
    try {
      const data = await apiV2.comprehensiveSearch(query, filters, { page: pageNum, limit: 10 });
      setResults(data);
      setActiveTab('products');
    } catch {
      setError(language === 'fr' ? 'Erreur lors de la recherche.' : 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [query, filters, language]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch(1);
  };

  const tabLabel = (tab) => {
    const labels = {
      products: language === 'fr' ? 'Produits' : 'Products',
      countries: language === 'fr' ? 'Pays' : 'Countries',
      investments: language === 'fr' ? 'Investissements' : 'Investments',
    };
    return labels[tab];
  };

  const tabData = results ? {
    products: results.products || [],
    countries: results.countries || [],
    investments: results.investments || results.investmentOpportunities || [],
  } : {};

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            🔍 {language === 'fr' ? 'Recherche Intelligente AfCFTA' : 'AfCFTA Intelligent Search'}
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-4 space-y-3">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={language === 'fr'
                ? 'Rechercher produits, pays, opportunités...'
                : 'Search products, countries, opportunities...'}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <Button
              onClick={() => setShowFilters((v) => !v)}
              variant="outline"
              className="shrink-0 gap-1.5"
            >
              ⚙ {language === 'fr' ? 'Filtres' : 'Filters'}
              {(filters.countries.length + filters.sectors.length + filters.hsChapters.length) > 0 && (
                <Badge className="bg-blue-600 text-white border-0 text-xs ml-1">
                  {filters.countries.length + filters.sectors.length + filters.hsChapters.length}
                </Badge>
              )}
            </Button>
            <Button
              onClick={() => handleSearch(1)}
              disabled={loading || !query.trim()}
              className="bg-blue-700 hover:bg-blue-800 text-white shrink-0"
            >
              {loading ? '...' : (language === 'fr' ? 'Rechercher' : 'Search')}
            </Button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="border-t pt-3 space-y-3">
              {/* Countries */}
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">
                  {language === 'fr' ? 'Pays' : 'Countries'}
                </p>
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {AFRICAN_COUNTRIES.slice(0, 20).map((c) => (
                    <button
                      key={c}
                      onClick={() => toggleFilter('countries', c)}
                      className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                        filters.countries.includes(c)
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sectors */}
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">
                  {language === 'fr' ? 'Secteurs' : 'Sectors'}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {SECTORS.map((s) => (
                    <button
                      key={s}
                      onClick={() => toggleFilter('sectors', s)}
                      className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                        filters.sectors.includes(s)
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* HS Chapters */}
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1.5">
                  {language === 'fr' ? 'Chapitres SH' : 'HS Chapters'}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {HS_CHAPTERS.map((ch) => (
                    <button
                      key={ch}
                      onClick={() => toggleFilter('hsChapters', ch)}
                      className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                        filters.hsChapters.includes(ch)
                          ? 'bg-green-600 text-white border-green-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-green-400'
                      }`}
                    >
                      {ch}
                    </button>
                  ))}
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="text-gray-500 text-xs"
                onClick={() => setFilters({ countries: [], sectors: [], hsChapters: [] })}
              >
                {language === 'fr' ? 'Effacer les filtres' : 'Clear filters'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading */}
      {loading && <Spinner />}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
      )}

      {/* Results */}
      {results && !loading && (
        <Card>
          {/* Tabs */}
          <div className="border-b px-4 flex gap-0">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors -mb-px flex items-center gap-1.5 ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tabLabel(tab)}
                {tabData[tab]?.length > 0 && (
                  <Badge className="bg-gray-100 text-gray-600 border-0 text-xs">
                    {tabData[tab].length}
                  </Badge>
                )}
              </button>
            ))}
          </div>

          <CardContent className="pt-4 space-y-2">
            {tabData[activeTab]?.length === 0 && (
              <p className="text-center text-gray-400 py-8 text-sm">
                {language === 'fr' ? 'Aucun résultat.' : 'No results found.'}
              </p>
            )}

            {activeTab === 'products' && tabData.products.map((item, i) => (
              <ProductCard key={item.hsCode || i} item={item} language={language} />
            ))}

            {activeTab === 'countries' && tabData.countries.map((item, i) => (
              <CountryCard key={item.code || i} item={item} />
            ))}

            {activeTab === 'investments' && tabData.investments.map((item, i) => (
              <InvestmentCard key={item.id || i} item={item} />
            ))}

            {/* Pagination */}
            {results.totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => handleSearch(page - 1)}
                >
                  ← {language === 'fr' ? 'Précédent' : 'Previous'}
                </Button>
                <span className="text-sm text-gray-500">
                  {page} / {results.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= results.totalPages}
                  onClick={() => handleSearch(page + 1)}
                >
                  {language === 'fr' ? 'Suivant' : 'Next'} →
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
