import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ChevronDown, ChevronUp, Package, Check, DollarSign, Percent, FileText, AlertCircle, TrendingUp, TrendingDown, Info, Car, Leaf, Cog, Zap, Maximize2, Minimize2 } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

/**
 * Optimized component to display and select national tariff positions.
 * Now handles long, multi-line denominations correctly with expandable view.
 */
export default function NationalPositionsSelector({
  countryCode,
  hs6Code,
  cifValue,
  language = 'fr',
  onPositionSelect,
  selectedPosition
}) {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [expandedDescriptions, setExpandedDescriptions] = useState({});
  const [error, setError] = useState(null);
  const [apiNote, setApiNote] = useState(null);

  const texts = {
    fr: {
      title: "Positions Tarifaires Nationales",
      subtitle: "Sélectionnez la position exacte correspondant à votre marchandise",
      code: "Code National",
      description: "Désignation Officielle",
      ddRate: "Droit de Douane",
      estimatedDuties: "Droits Estimés",
      select: "Sélectionner",
      selected: "Sélectionnée",
      noPositions: "Aucune sous-position nationale disponible pour ce code HS",
      loadError: "Erreur lors du chargement des positions",
      positions: "positions disponibles",
      cifValue: "Valeur CIF Déclarée",
      source: "Source",
      digits: "chiffres",
      showMore: "Voir plus",
      showLess: "Voir moins",
      selectToCalculate: "Sélectionner pour calculer les droits exacts",
      nationalPosition: "Position tarifaire nationale",
      nationalSubPosition: "Sous-position tarifaire nationale"
    },
    en: {
      title: "National Tariff Positions",
      subtitle: "Select the exact position matching your goods",
      code: "National Code",
      description: "Official Description",
      ddRate: "Customs Duty",
      estimatedDuties: "Estimated Duties",
      select: "Select",
      selected: "Selected",
      noPositions: "No national sub-positions available for this HS code",
      loadError: "Error loading positions",
      positions: "available positions",
      cifValue: "Declared CIF Value",
      source: "Source",
      digits: "digits",
      showMore: "Show more",
      showLess: "Show less",
      selectToCalculate: "Select to calculate exact duties",
      nationalPosition: "National tariff position",
      nationalSubPosition: "National tariff sub-position"
    }
  };

  const t = texts[language] || texts.fr;

  const toggleDescription = (idx) => {
    setExpandedDescriptions(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const fetchPositions = useCallback(async () => {
    if (!countryCode || !hs6Code || hs6Code.length < 6) {
      return;
    }
    
    setLoading(true);
    setError(null);
    setApiNote(null);
    
    try {
      // Try PostgreSQL API first (has real descriptions)
      let response;
      try {
        response = await axios.get(
          `${API}/postgres-tariffs/country/${countryCode}/sub-positions/${hs6Code.substring(0, 6)}`,
          { params: { language } }
        );
      } catch (pgErr) {
        // Fallback to optimized smart search if PG is missing
        response = await axios.get(
          `${API}/hs6/smart-search`,
          { params: { q: hs6Code.substring(0, 6), country_code: countryCode, include_sub_positions: true } }
        );
      }
      
      const data = response.data;
      if (data.results || (data.success && data.sub_positions)) {
        const results = data.results || data.sub_positions;
        setPositions(results);
        setApiNote(data.note || (language === 'fr' ? data.note_fr : data.note_en));
      } else {
        setPositions([]);
      }
    } catch (err) {
      console.error('Error fetching positions:', err);
      setError(t.loadError);
      setPositions([]);
    } finally {
      setLoading(false);
    }
  }, [countryCode, hs6Code, language, t.loadError]);

  useEffect(() => {
    if (countryCode && hs6Code && hs6Code.length >= 6) {
      const timeoutId = setTimeout(() => {
        fetchPositions();
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  }, [countryCode, hs6Code, fetchPositions]);

  const sortedPositions = useMemo(() => {
    return [...positions].sort((a, b) => {
      const ca = (a.code || a.hs_code || '').replace(/\./g, '');
      const cb = (b.code || b.hs_code || '').replace(/\./g, '');
      return ca.localeCompare(cb);
    });
  }, [positions]);

  const handleSelect = useCallback((position) => {
    if (onPositionSelect) {
      const code = position.code || position.hs_code;
      const desc = language === 'fr' ? (position.description_fr || position.description) : (position.description_en || position.description);
      onPositionSelect(code, desc);
    }
  }, [onPositionSelect, language]);

  if (!countryCode || !hs6Code || hs6Code.length < 6) {
    return null;
  }

  return (
    <Card className="bg-[var(--afcfta-card2)] border-[var(--afcfta-border)] overflow-hidden transition-all duration-300">
      <CardHeader 
        className="py-3 cursor-pointer hover:bg-[var(--overlay)] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--violet)_25%,transparent)]">
              <Package className="w-5 h-5 text-[var(--violet)]" />
            </div>
            <div>
              <CardTitle className="text-lg text-[var(--text)] flex items-center gap-2">
                {t.title}
                {positions.length > 0 && (
                  <Badge className="bg-[color-mix(in_srgb,var(--violet)_14%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)] border">
                    {positions.length} {t.positions}
                  </Badge>
                )}
              </CardTitle>
              <p className="text-[var(--afcfta-muted)] text-sm">{t.subtitle}</p>
            </div>
          </div>
          {expanded ? <ChevronUp className="w-5 h-5 text-[var(--afcfta-muted)]" /> : <ChevronDown className="w-5 h-5 text-[var(--afcfta-muted)]" />}
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-4">
          {apiNote && (
            <div className="flex items-start gap-2 p-3 bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_22%,transparent)]">
              <Info className="w-4 h-4 text-[var(--info)] mt-0.5 flex-shrink-0" />
              <p className="text-sm text-[var(--info)]">{apiNote}</p>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-2 border-[var(--violet)] border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-3 text-[var(--afcfta-muted)]">Chargement des positions nationales...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 p-4 bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--danger)_25%,transparent)]">
              <AlertCircle className="w-5 h-5 text-[var(--danger)]" />
              <p className="text-[var(--danger)]">{error}</p>
            </div>
          )}

          {!loading && !error && positions.length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-[var(--overlay)] rounded-full flex items-center justify-center">
                <Package className="w-8 h-8 text-[var(--afcfta-muted)]" />
              </div>
              <p className="text-[var(--afcfta-muted)]">{t.noPositions}</p>
            </div>
          )}

          {!loading && sortedPositions.length > 0 && (
            <div className="space-y-3">
              {sortedPositions.map((position, idx) => {
                const currentCode = position.code || position.hs_code || '';
                const isSelected = selectedPosition === currentCode;
                const desc = language === 'fr' ? (position.description_fr || position.description) : (position.description_en || position.description);
                const isLongDesc = desc && desc.length > 150;
                const isDescExpanded = expandedDescriptions[idx];
                
                // Logic for dynamic badge label
                const codeLen = currentCode.replace(/\./g, '').length;
                let badgeLabel = `HS${codeLen} digits`;
                if (codeLen === 8) badgeLabel = t.nationalPosition;
                if (codeLen === 10) badgeLabel = t.nationalSubPosition;

                return (
                  <div 
                    key={idx}
                    className={`relative rounded-xl border-2 transition-all duration-200 cursor-pointer overflow-hidden ${
                      isSelected 
                        ? 'border-[var(--violet)] bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]' 
                        : 'border-[var(--afcfta-border)] bg-[var(--afcfta-card)] hover:border-[color-mix(in_srgb,var(--violet)_45%,transparent)]'
                    }`}
                    onClick={() => handleSelect(position)}
                  >
                    <div className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <span className={`font-mono tabular-nums text-lg font-bold px-3 py-1 rounded-lg ${
                              isSelected ? 'bg-[var(--violet)] text-[var(--bg)]' : 'bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)]'
                            }`}>
                              {currentCode}
                            </span>
                            <Badge variant="outline" className="text-xs border-[var(--afcfta-border)] text-[var(--afcfta-muted)]">
                              {badgeLabel}
                            </Badge>
                          </div>
                          
                          <div className="relative">
                            <p className={`text-base leading-relaxed transition-all ${
                              isSelected ? 'text-[var(--text)]' : 'text-[var(--text-soft)]'
                            } ${!isDescExpanded && isLongDesc ? 'line-clamp-2' : ''}`}>
                              {desc}
                            </p>
                            {isLongDesc && (
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleDescription(idx);
                                }}
                                className="mt-1 text-[var(--violet)] hover:opacity-80 text-xs font-semibold flex items-center gap-1"
                              >
                                {isDescExpanded ? <><Minimize2 className="w-3 h-3"/> {t.showLess}</> : <><Maximize2 className="w-3 h-3"/> {t.showMore}</>}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
