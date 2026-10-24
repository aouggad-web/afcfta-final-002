import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Search } from 'lucide-react';
import { ISO2_TO_ISO3 } from '../utils/countryCodes';

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
      chooseDestination: "Choisissez d’abord le pays de destination",
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
      chooseDestination: "Choose the destination country first",
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

      const iso3 = destinationCountry && destinationCountry.length === 2
        ? (ISO2_TO_ISO3[destinationCountry] || destinationCountry)
        : destinationCountry;
      const timer = setTimeout(async () => {
        try {
          if (!iso3) {
            throw new Error('pays de destination requis');
          }
          // Les positions du socle : celles que POST /calcul sait liquider.
          const response = await axios.get(`${API}/consultation/${iso3}/recherche`, {
            params: { q: query, limit: 25 },
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
    [destinationCountry]
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

  // Sélection d'une position nationale : code, désignation, règle d'origine.
  const handlePositionSelect = (code, description) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
      searchTimeoutRef.current = null;
    }
    setSearchQuery(code);
    setShowResults(false);
    onChange(code);
    loadSuggestions(code);
    if (onSubPositionSelect) {
      onSubPositionSelect(code, description, null);
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
            {searchResults.map((result) => {
              const description = language === 'fr' ? result.description_fr : (result.description_en || result.description_fr);
              return (
                <div
                  key={result.code}
                  className="p-3 border-b border-[var(--afcfta-border)] last:border-b-0 hover:bg-[var(--goldSoft)] cursor-pointer transition-colors"
                  onClick={() => handlePositionSelect(result.code, description)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono tabular-nums font-bold text-[var(--gold)] bg-[var(--goldSoft)] px-2 py-0.5 rounded text-base">{result.code}</span>
                        {result.dd_rate != null && (
                          <Badge className="bg-[var(--goldSoft)] text-[var(--gold)] text-xs tabular-nums border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">DD: {result.dd_rate}%</Badge>
                        )}
                        {result.dd_rate == null && result.dd_expression && (
                          <Badge className="bg-[var(--goldSoft)] text-[var(--gold)] text-xs font-mono border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">DD: {result.dd_expression}</Badge>
                        )}
                      </div>
                      <p className="text-[var(--text)] mt-1 text-sm leading-snug">{description}</p>
                      {result.intitule_sh4 && (
                        <p className="text-xs text-[var(--afcfta-muted)] mt-0.5">{result.code.slice(0, 4)} — {result.intitule_sh4}</p>
                      )}
                    </div>
                    <Button size="sm" variant="ghost" className="shrink-0 text-[var(--gold)] hover:bg-[var(--goldSoft)]">
                      {t.useCode}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {showResults && searchResults.length === 0 && searchQuery.length >= 2 && !loading && (
          <div className="absolute z-50 w-full mt-1 bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] rounded-lg shadow-lg p-4 text-center text-[var(--afcfta-muted)]">
            {destinationCountry ? t.noResults : t.chooseDestination}
          </div>
        )}
      </div>
    </div>
  );
}
