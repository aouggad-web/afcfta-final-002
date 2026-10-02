import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Search, Info } from 'lucide-react';

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
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const texts = {
    fr: {
      searchPlaceholder: "Rechercher par code ou mot-clé (ex: voiture, 870323, café)",
      noResults: "Aucun résultat trouvé",
      selectSubPosition: "Sélectionner cette sous-position",
      sensitivity: "Sensibilité",
      category: "Catégorie",
      sensitive: "Sensible",
      normal: "Normal",
      excluded: "Exclu",
      useCode: "Utiliser ce code",
      viewDetails: "Voir les détails"
    },
    en: {
      searchPlaceholder: "Search by code or keyword (e.g.: car, 870323, coffee)",
      noResults: "No results found",
      selectSubPosition: "Select this sub-position",
      sensitivity: "Sensitivity",
      category: "Category",
      sensitive: "Sensitive",
      normal: "Normal",
      excluded: "Excluded",
      useCode: "Use this code",
      viewDetails: "View details"
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

  const loadSuggestions = async (hsCode) => {
    if (!hsCode || hsCode.length < 6) return;

    if (onRuleOfOriginLoad) {
      onRuleOfOriginLoad(null);
    }
    try {
      const ruleResponse = await axios.get(`${API}/rules-of-origin/${hsCode}`, {
        params: { lang: language }
      });
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
    </div>
  );
}
