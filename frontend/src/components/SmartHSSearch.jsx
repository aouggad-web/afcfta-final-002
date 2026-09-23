import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Separator } from './ui/separator';
import { ChevronDown, ChevronUp, Search, Info, AlertTriangle } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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
      viewDetails: "Voir les détails",
      alternativeRule: "Règle alternative"
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
      viewDetails: "View details",
      alternativeRule: "Alternative rule"
    }
  };

  const t = texts[language] || texts.fr;

  // Debounce search
  const searchTimeoutRef = useRef(null);
  const latestRequestRef = useRef(0);

  // Search HS6 codes
  const searchHS6 = useCallback(
    (query) => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      if (!query || query.length < 2) {
        setLoading(false);
        setSearchResults([]);
        setShowResults(false);
        return;
      }

      setLoading(true);
      setShowResults(true);
      const requestId = latestRequestRef.current + 1;
      latestRequestRef.current = requestId;

      const timer = setTimeout(async () => {
        try {
          const response = await axios.get(`${API}/hs6/smart-search`, {
            params: {
              q: query,
              country_code: destinationCountry || undefined,
              language,
              include_sub_positions: true,
            },
          });
          if (requestId === latestRequestRef.current) {
            setSearchResults(response.data.results || []);
            setShowResults(true);
          }
        } catch (error) {
          if (requestId === latestRequestRef.current) {
            setSearchResults([]);
          }
        } finally {
          if (searchTimeoutRef.current === timer) {
            searchTimeoutRef.current = null;
          }
          if (requestId === latestRequestRef.current) {
            setLoading(false);
          }
        }
      }, 300);
      searchTimeoutRef.current = timer;
    },
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
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }

    // Load rule of origin in its own try/catch so a failure here
    // does not leave stale data displayed and always notifies the caller.
    setRuleOfOrigin(null);
    if (onRuleOfOriginLoad) {
      onRuleOfOriginLoad(null);
    }
    try {
      const ruleResponse = await axios.get(`${API}/rules-of-origin/${hsCode}`, {
        params: { lang: language }
      });
      setRuleOfOrigin(ruleResponse.data);
      if (onRuleOfOriginLoad) {
        onRuleOfOriginLoad(ruleResponse.data);
      }
    } catch (error) {
      console.error('Error loading rule of origin:', error);
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
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
      searchTimeoutRef.current = null;
    }
    setSearchQuery(code);
    setSelectedCode(code);
    setShowResults(false);
    onChange(code);
    loadSuggestions(code);
  };

  // Handle sub-position selection — passe code, description ET formalités
  const handleSubPositionSelect = (fullCode, description, formalities) => {
    setSearchQuery(fullCode);
    onChange(fullCode);
    if (onSubPositionSelect) {
      onSubPositionSelect(fullCode, description, formalities || null);
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

  useEffect(() => () => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
      searchTimeoutRef.current = null;
    }
  }, []);

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
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--afcfta-muted)]" />
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
          <div className="absolute z-50 w-full mt-1 bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] rounded-lg shadow-2xl max-h-96 overflow-y-auto">
            {/* Chapter header if code search */}
            {searchResults[0]?.chapter_name && (
              <div className="sticky top-0 bg-gradient-to-r from-[#C17A2B] to-[#D4AF37] text-[#0b0f14] px-4 py-2 text-sm font-bold">
                📦 {searchResults[0].full_position}
              </div>
            )}
            
            {searchResults.map((result, idx) => (
              <div key={idx} className="border-b border-[var(--afcfta-border)] last:border-b-0">
                {/* Main HS6 code */}
                <div
                  className="p-3 hover:bg-[var(--goldSoft)] cursor-pointer transition-colors"
                  onClick={() => handleCodeSelect(result.code, result.description)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono tabular-nums font-bold text-[var(--gold)] bg-[var(--goldSoft)] px-2 py-0.5 rounded text-base">{result.code}</span>
                        <span className="text-xs text-[var(--afcfta-muted)]">HS6</span>
                        {result.category && (
                          <Badge variant="outline" className="text-xs border-[var(--afcfta-border)] text-[var(--afcfta-muted)]">{result.category}</Badge>
                        )}
                      </div>
                      <p className="text-[var(--text)] mt-1 text-sm leading-snug">{result.description}</p>
                    </div>
                    <Button size="sm" variant="ghost" className="shrink-0 text-[var(--gold)] hover:bg-[var(--goldSoft)]">
                      {t.useCode}
                    </Button>
                  </div>
                </div>
                
                {/* Sub-positions nationales (HS8-HS12) */}
                {result.sub_positions && result.sub_positions.length > 0 && (
                  <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] px-3 py-2 border-t border-[color-mix(in_srgb,var(--violet)_22%,transparent)]">
                    <p className="text-xs font-semibold text-[var(--violet)] mb-2 flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      {language === 'fr' ? 'Sous-positions nationales disponibles:' : 'National sub-positions available:'}
                    </p>
                    <div className="space-y-1">
                      {result.sub_positions.slice(0, 5).map((sp, spIdx) => (
                        <div 
                          key={spIdx}
                          className="flex items-center justify-between bg-[var(--afcfta-card2)] p-2 rounded border border-[color-mix(in_srgb,var(--violet)_28%,transparent)] hover:border-[var(--violet)] cursor-pointer transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSubPositionSelect(
                              sp.code,
                              language === 'fr' ? sp.description_fr : (sp.description_en || sp.description_fr),
                              sp.administrative_formalities || null
                            );
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono tabular-nums text-sm font-bold text-[var(--violet)] bg-[color-mix(in_srgb,var(--violet)_15%,var(--afcfta-card))] px-2 py-0.5 rounded">{sp.code}</span>
                            <span className="text-xs text-[var(--afcfta-muted)]">HS{sp.digits}</span>
                          </div>
                          <div className="flex-1 px-2">
                            <span className="text-sm text-[var(--text)]">{language === 'fr' ? sp.description_fr : sp.description_en}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-[var(--goldSoft)] text-[var(--gold)] text-xs tabular-nums border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">DD: {sp.dd}%</Badge>
                            <Button size="sm" variant="outline" className="text-xs h-6 text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_40%,transparent)] hover:bg-[color-mix(in_srgb,var(--violet)_15%,var(--afcfta-card))]">
                              {language === 'fr' ? 'Utiliser' : 'Use'}
                            </Button>
                          </div>
                        </div>
                      ))}
                      {result.sub_positions.length > 5 && (
                        <p className="text-xs text-[var(--violet)] text-center pt-1">
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
          <div className="absolute z-50 w-full mt-1 bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] rounded-lg shadow-lg p-4 text-center text-[var(--afcfta-muted)]">
            {t.noResults}
          </div>
        )}
      </div>

      {/* Suggestions Panel */}
      {suggestions && (
        <Card className="border-[color-mix(in_srgb,var(--violet)_30%,transparent)] bg-[color-mix(in_srgb,var(--violet)_6%,var(--afcfta-card))]">
          <CardHeader className="py-3 cursor-pointer" onClick={() => setShowSuggestions(!showSuggestions)}>
            <CardTitle className="text-sm flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="text-[var(--violet)]">{t.subPositionSuggestions}</span>
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
                  <h4 className="text-xs font-semibold text-[var(--afcfta-muted)] mb-2">{t.genericSuggestions}</h4>
                  <div className="space-y-2">
                    {suggestions.generic_suggestions.map((sg, idx) => (
                      <div key={idx} className="bg-[var(--afcfta-card)] p-2 rounded border">
                        <div className="font-medium text-sm text-[var(--violet)] mb-1">{sg.label}</div>
                        <div className="flex flex-wrap gap-1">
                          {sg.options.map((opt, optIdx) => (
                            <Button
                              key={optIdx}
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 hover:bg-[color-mix(in_srgb,var(--violet)_14%,var(--afcfta-card))]"
                              onClick={() => handleSubPositionSelect(opt.full_code, opt.label)}
                            >
                              <span className="font-mono mr-1">{opt.full_code}</span>
                              <span className="text-[var(--afcfta-muted)]">{opt.label}</span>
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
                  <h4 className="text-xs font-semibold text-[var(--afcfta-muted)] mb-2 flex items-center gap-2">
                    {suggestions.authentic_data 
                      ? (language === 'fr' ? 'Positions tarifaires nationales (source officielle)' : 'National tariff positions (official source)')
                      : t.countrySpecificRates}
                    <Badge className="bg-[var(--success)] text-[var(--bg)] text-xs">{suggestions.country_code}</Badge>
                    {suggestions.authentic_data && (
                      <Badge className="bg-[var(--success)] text-[var(--bg)] text-xs">
                        {language === 'fr' ? 'Données authentiques' : 'Authentic data'}
                      </Badge>
                    )}
                  </h4>
                  <div className="text-xs text-[var(--afcfta-muted)] mb-2">
                    {suggestions.country_sub_positions.length} {language === 'fr' ? 'positions trouvées' : 'positions found'}
                    {suggestions.country_sub_positions[0]?.source && (
                      <span> — {language === 'fr' ? 'Source' : 'Source'}: {suggestions.country_sub_positions[0].source}</span>
                    )}
                  </div>
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {suggestions.country_sub_positions.map((sp, idx) => (
                      <div
                        key={idx}
                        className="bg-[var(--afcfta-card)] p-2 rounded border border-[var(--afcfta-border)] hover:bg-[var(--greenSoft)] cursor-pointer"
                        onClick={() => handleSubPositionSelect(
                          sp.code_clean || sp.code,
                          sp.description_fr || sp.description,
                          sp.administrative_formalities || null
                        )}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <span className="font-mono tabular-nums font-bold text-[var(--success)]">{sp.code}</span>
                            <span className="mx-2 text-[var(--afcfta-muted)]">—</span>
                            <span className="text-sm text-[var(--text)]">{sp.description_fr || sp.description}</span>
                          </div>
                          {sp.dd_rate_pct && (
                            <Badge className="bg-[var(--info)] text-[var(--bg)] ml-2 shrink-0">
                              DD {sp.dd_rate_pct}
                            </Badge>
                          )}
                        </div>
                        {sp.taxes_display && sp.taxes_display.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {sp.taxes_display.map((tax, tIdx) => (
                              <span key={tIdx} className="text-xs bg-[var(--overlay)] text-[var(--afcfta-muted)] px-1.5 py-0.5 rounded">
                                {tax}
                              </span>
                            ))}
                          </div>
                        )}
                        {sp.administrative_formalities && sp.administrative_formalities.length > 0 && (
                          <div className="mt-1">
                            {sp.administrative_formalities.slice(0, 2).map((f, fIdx) => (
                              <span key={fIdx} className="text-xs text-[var(--terra)] mr-2">
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
              {ruleOfOrigin && ruleOfOrigin.rule && ruleOfOrigin.rules && (
                <div>
                  <Separator className="my-3" />
                  <h4 className="text-xs font-semibold text-[var(--afcfta-muted)] mb-2">{t.ruleOfOrigin}</h4>
                  <div className="bg-[var(--afcfta-card)] p-3 rounded border space-y-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <Badge variant="outline" className="text-xs">
                        {ruleOfOrigin.rules.primary_rule?.name || ruleOfOrigin.rules.primary_rule?.code}
                      </Badge>
                      {ruleOfOrigin.rules.regional_content != null && (
                        <Badge className="bg-[var(--gold)] text-[var(--bg)]">
                          {t.regionalContent}: {ruleOfOrigin.rules.regional_content}%
                        </Badge>
                      )}
                      {ruleOfOrigin.status === 'YTB' && (
                        <Badge className="bg-[var(--terra)] text-[var(--bg)]">
                          {language === 'fr' ? 'En cours de négociation' : 'Yet to be agreed'}
                        </Badge>
                      )}
                    </div>
                    {ruleOfOrigin.rules.primary_rule?.explanation && (
                      <p className="text-sm text-[var(--text)]">{ruleOfOrigin.rules.primary_rule.explanation}</p>
                    )}
                    {ruleOfOrigin.rules.alternative_rule && (
                      <p className="text-xs text-[var(--afcfta-muted)]">
                        {t.alternativeRule}: {ruleOfOrigin.rules.alternative_rule.name}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* No suggestions message */}
              {(!suggestions.generic_suggestions || suggestions.generic_suggestions.length === 0) &&
               (!suggestions.country_sub_positions || suggestions.country_sub_positions.length === 0) && (
                <div className="text-center text-[var(--afcfta-muted)] py-2">
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
