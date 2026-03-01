import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Separator } from './ui/separator';
import { ChevronDown, ChevronUp, Search, Info, AlertTriangle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Composant de recherche intelligente HS6 avec suggestions de sous-positions
 */
export default function SmartHSSearch({ 
  value, 
  onChange, 
  destinationCountry,
  language = 'fr',
  onSubPositionSelect,
  onRuleOfOriginLoad
}) {
  const [searchQuery, setSearchQuery] = useState(value || '');
  const [searchResults, setSearchResults] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
  const [ruleOfOrigin, setRuleOfOrigin] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [selectedCode, setSelectedCode] = useState(null);

  const texts = {
    fr: {
      searchPlaceholder: "Rechercher par code ou mot-clé (ex: voiture, 870323, café)",
      noResults: "Aucun résultat trouvé",
      subPositionSuggestions: "Suggestions de sous-positions",
      countrySpecificRates: "Taux spécifiques au pays",
      ruleOfOrigin: "Règle d'origine ZLECAf",
      selectSubPosition: "Sélectionner cette sous-position",
      genericSuggestions: "Types de distinctions possibles",
      noSuggestions: "Pas de sous-positions pour ce code",
      sensitivity: "Sensibilité",
      category: "Catégorie",
      sensitive: "Sensible",
      normal: "Normal",
      excluded: "Exclu",
      regionalContent: "Contenu régional",
      useCode: "Utiliser ce code",
      viewDetails: "Voir les détails"
    },
    en: {
      searchPlaceholder: "Search by code or keyword (e.g.: car, 870323, coffee)",
      noResults: "No results found",
      subPositionSuggestions: "Sub-position suggestions",
      countrySpecificRates: "Country-specific rates",
      ruleOfOrigin: "AfCFTA Rule of Origin",
      selectSubPosition: "Select this sub-position",
      genericSuggestions: "Possible distinction types",
      noSuggestions: "No sub-positions for this code",
      sensitivity: "Sensitivity",
      category: "Category",
      sensitive: "Sensitive",
      normal: "Normal",
      excluded: "Excluded",
      regionalContent: "Regional content",
      useCode: "Use this code",
      viewDetails: "View details"
    }
  };

  const t = texts[language] || texts.fr;

  // Debounce search
  const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  };

  // Search HS6 codes
  const searchHS6 = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setSearchResults([]);
        return;
      }

      setLoading(true);
      try {
        const response = await axios.get(`${API}/hs6/smart-search`, {
          params: {
            q: query,
            country_code: destinationCountry || undefined,
            language,
            include_sub_positions: true
          }
        });
        setSearchResults(response.data.results || []);
        setShowResults(true);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    [destinationCountry, language]
  );

  // Load suggestions for a specific code
  const loadSuggestions = async (hsCode) => {
    if (!hsCode || hsCode.length < 6) return;

    try {
      const response = await axios.get(`${API}/hs6/suggestions/${hsCode}`, {
        params: {
          country_code: destinationCountry || undefined,
          language
        }
      });
      setSuggestions(response.data);
      
      // Also load rule of origin
      const ruleResponse = await axios.get(`${API}/hs6/rule-of-origin/${hsCode}`, {
        params: { language }
      });
      setRuleOfOrigin(ruleResponse.data);
      if (onRuleOfOriginLoad) {
        onRuleOfOriginLoad(ruleResponse.data);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  // Handle search input change
  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    searchHS6(query);
  };

  // Handle code selection
  const handleCodeSelect = (code, description) => {
    setSearchQuery(code);
    setSelectedCode(code);
    setShowResults(false);
    onChange(code);
    loadSuggestions(code);
  };

  // Handle sub-position selection
  const handleSubPositionSelect = (fullCode, description) => {
    setSearchQuery(fullCode);
    onChange(fullCode);
    if (onSubPositionSelect) {
      onSubPositionSelect(fullCode, description);
    }
  };

  // Update when value prop changes
  useEffect(() => {
    if (value && value !== searchQuery) {
      setSearchQuery(value);
      if (value.length >= 6) {
        loadSuggestions(value);
      }
    }
  }, [value]);

  // Reload suggestions when destination country changes
  useEffect(() => {
    if (selectedCode && destinationCountry) {
      loadSuggestions(selectedCode);
    }
  }, [destinationCountry]);

  const getSensitivityColor = (sensitivity) => {
    switch (sensitivity) {
      case 'sensitive': return 'bg-orange-500';
      case 'excluded': return 'bg-red-500';
      default: return 'bg-green-500';
    }
  };

  const getSensitivityLabel = (sensitivity) => {
    switch (sensitivity) {
      case 'sensitive': return t.sensitive;
      case 'excluded': return t.excluded;
      default: return t.normal;
    }
  };

  return (
    <div className="space-y-4" data-testid="smart-hs-search">
      {/* Search Input */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => searchQuery.length >= 2 && setShowResults(true)}
            placeholder={t.searchPlaceholder}
            className="pl-10 pr-4"
            data-testid="hs-search-input"
          />
        </div>

        {/* Search Results Dropdown */}
        {showResults && searchResults.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-[#1B232C] border border-[rgba(212,175,55,0.2)] rounded-lg shadow-2xl max-h-96 overflow-y-auto">
            {/* Chapter header if code search */}
            {searchResults[0]?.chapter_name && (
              <div className="sticky top-0 bg-gradient-to-r from-[#C17A2B] to-[#D4AF37] text-[#0b0f14] px-4 py-2 text-sm font-bold">
                📦 {searchResults[0].full_position}
              </div>
            )}
            
            {searchResults.map((result, idx) => (
              <div key={idx} className="border-b border-[rgba(255,255,255,0.08)] last:border-b-0">
                {/* Main HS6 code */}
                <div
                  className="p-3 hover:bg-[rgba(212,175,55,0.1)] cursor-pointer transition-colors"
                  onClick={() => handleCodeSelect(result.code, result.description)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-[#D4AF37] bg-[rgba(212,175,55,0.15)] px-2 py-0.5 rounded text-base">{result.code}</span>
                        <span className="text-xs text-[#A0AAB4]">HS6</span>
                        {result.category && (
                          <Badge variant="outline" className="text-xs border-[rgba(255,255,255,0.15)] text-[#A0AAB4]">{result.category}</Badge>
                        )}
                      </div>
                      <p className="text-[#F5F5F5] mt-1 text-sm">{result.description}</p>
                    </div>
                    <Button size="sm" variant="ghost" className="shrink-0 text-[#D4AF37] hover:bg-[rgba(212,175,55,0.15)]">
                      {t.useCode}
                    </Button>
                  </div>
                </div>
                
                {/* Sub-positions nationales (HS8-HS12) */}
                {result.sub_positions && result.sub_positions.length > 0 && (
                  <div className="bg-[rgba(139,92,246,0.08)] px-3 py-2 border-t border-[rgba(139,92,246,0.2)]">
                    <p className="text-xs font-semibold text-[#A78BFA] mb-2 flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      {language === 'fr' ? 'Sous-positions nationales disponibles:' : 'National sub-positions available:'}
                    </p>
                    <div className="space-y-1">
                      {result.sub_positions.slice(0, 5).map((sp, spIdx) => (
                        <div 
                          key={spIdx}
                          className="flex items-center justify-between bg-[#15202A] p-2 rounded border border-[rgba(139,92,246,0.25)] hover:border-[#A78BFA] cursor-pointer transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSubPositionSelect(sp.code, sp.description_fr || sp.description_en);
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm font-bold text-[#A78BFA] bg-[rgba(139,92,246,0.15)] px-2 py-0.5 rounded">{sp.code}</span>
                            <span className="text-xs text-[#A0AAB4]">HS{sp.digits}</span>
                          </div>
                          <div className="flex-1 px-2">
                            <span className="text-sm text-[#F5F5F5]">{language === 'fr' ? sp.description_fr : sp.description_en}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-[rgba(212,175,55,0.15)] text-[#D4AF37] text-xs border border-[rgba(212,175,55,0.3)]">DD: {sp.dd}%</Badge>
                            <Button size="sm" variant="outline" className="text-xs h-6 text-[#A78BFA] border-[rgba(139,92,246,0.4)] hover:bg-[rgba(139,92,246,0.15)]">
                              {language === 'fr' ? 'Utiliser' : 'Use'}
                            </Button>
                          </div>
                        </div>
                      ))}
                      {result.sub_positions.length > 5 && (
                        <p className="text-xs text-[#A78BFA] text-center pt-1">
                          +{result.sub_positions.length - 5} {language === 'fr' ? 'autres sous-positions' : 'more sub-positions'}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {showResults && searchResults.length === 0 && searchQuery.length >= 2 && !loading && (
          <div className="absolute z-50 w-full mt-1 bg-[#1B232C] border border-[rgba(255,255,255,0.1)] rounded-lg shadow-lg p-4 text-center text-[#A0AAB4]">
            {t.noResults}
          </div>
        )}
      </div>

      {/* Suggestions Panel */}
      {suggestions && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader className="py-3 cursor-pointer" onClick={() => setShowSuggestions(!showSuggestions)}>
            <CardTitle className="text-sm flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="text-purple-700">{t.subPositionSuggestions}</span>
                {suggestions.description && (
                  <Badge variant="outline" className="text-xs">
                    {suggestions.hs6_code}: {suggestions.description}
                  </Badge>
                )}
              </span>
              {showSuggestions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </CardTitle>
          </CardHeader>
          
          {showSuggestions && (
            <CardContent className="pt-0 space-y-4">
              {/* Generic Suggestions */}
              {suggestions.generic_suggestions && suggestions.generic_suggestions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 mb-2">{t.genericSuggestions}</h4>
                  <div className="space-y-2">
                    {suggestions.generic_suggestions.map((sg, idx) => (
                      <div key={idx} className="bg-white p-2 rounded border">
                        <div className="font-medium text-sm text-purple-700 mb-1">{sg.label}</div>
                        <div className="flex flex-wrap gap-1">
                          {sg.options.map((opt, optIdx) => (
                            <Button
                              key={optIdx}
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 hover:bg-purple-100"
                              onClick={() => handleSubPositionSelect(opt.full_code, opt.label)}
                            >
                              <span className="font-mono mr-1">{opt.full_code}</span>
                              <span className="text-gray-500">{opt.label}</span>
                            </Button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Country-specific Sub-positions */}
              {suggestions.country_sub_positions && suggestions.country_sub_positions.length > 0 && (
                <div>
                  <Separator className="my-3" />
                  <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
                    {suggestions.authentic_data 
                      ? (language === 'fr' ? 'Positions tarifaires nationales (source officielle)' : 'National tariff positions (official source)')
                      : t.countrySpecificRates}
                    <Badge className="bg-green-600 text-white text-xs">{suggestions.country_code}</Badge>
                    {suggestions.authentic_data && (
                      <Badge className="bg-emerald-700 text-white text-xs">
                        {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
                      </Badge>
                    )}
                  </h4>
                  <div className="text-xs text-gray-500 mb-2">
                    {suggestions.country_sub_positions.length} {language === 'fr' ? 'positions trouvées' : 'positions found'}
                    {suggestions.country_sub_positions[0]?.source && (
                      <span> — {language === 'fr' ? 'Source' : 'Source'}: {suggestions.country_sub_positions[0].source}</span>
                    )}
                  </div>
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {suggestions.country_sub_positions.map((sp, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-2 rounded border hover:bg-green-50 cursor-pointer"
                        onClick={() => handleSubPositionSelect(sp.code_clean || sp.code, sp.description_fr || sp.description)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <span className="font-mono font-bold text-green-700">{sp.code}</span>
                            <span className="mx-2 text-gray-400">—</span>
                            <span className="text-sm text-gray-700">{sp.description_fr || sp.description}</span>
                          </div>
                          {sp.dd_rate_pct && (
                            <Badge className="bg-blue-600 text-white ml-2 shrink-0">
                              DD {sp.dd_rate_pct}
                            </Badge>
                          )}
                        </div>
                        {sp.taxes_display && sp.taxes_display.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {sp.taxes_display.map((tax, tIdx) => (
                              <span key={tIdx} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                {tax}
                              </span>
                            ))}
                          </div>
                        )}
                        {sp.administrative_formalities && sp.administrative_formalities.length > 0 && (
                          <div className="mt-1">
                            {sp.administrative_formalities.slice(0, 2).map((f, fIdx) => (
                              <span key={fIdx} className="text-xs text-orange-600 mr-2">
                                ⚠ {typeof f === 'string' ? f : f.text || f.description || ''}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Rule of Origin */}
              {ruleOfOrigin && (
                <div>
                  <Separator className="my-3" />
                  <h4 className="text-xs font-semibold text-gray-600 mb-2">{t.ruleOfOrigin}</h4>
                  <div className="bg-white p-3 rounded border">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className="text-xs">
                        {ruleOfOrigin.type === 'wholly_obtained' ? 'Entièrement obtenu' : 
                         ruleOfOrigin.type === 'double_transformation' ? 'Double transformation' :
                         'Transformation substantielle'}
                      </Badge>
                      <Badge className="bg-yellow-500 text-white">
                        {t.regionalContent}: {ruleOfOrigin.regional_content}%
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700">{ruleOfOrigin.requirement}</p>
                  </div>
                </div>
              )}

              {/* No suggestions message */}
              {(!suggestions.generic_suggestions || suggestions.generic_suggestions.length === 0) &&
               (!suggestions.country_sub_positions || suggestions.country_sub_positions.length === 0) && (
                <div className="text-center text-gray-500 py-2">
                  <AlertTriangle className="h-5 w-5 mx-auto mb-1" />
                  {t.noSuggestions}
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
