import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ChevronDown, ChevronUp, Package, Check, DollarSign, Percent, FileText, AlertCircle, TrendingUp, TrendingDown, Info, Car, Leaf, Cog, Zap, Maximize2, Minimize2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
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

  const formatCurrency = useCallback((amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }, []);

  const calculateEstimatedDuties = useCallback((position) => {
    const value = parseFloat(cifValue) || 0;
    const ddRate = position.dd || position.duty_rate_pct || 0;
    return value * ddRate / 100;
  }, [cifValue]);

  const sortedPositions = useMemo(() => {
    return [...positions].sort((a, b) => (a.dd || a.duty_rate_pct || 0) - (b.dd || b.duty_rate_pct || 0));
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
    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden transition-all duration-300">
      <CardHeader 
        className="py-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <Package className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-white flex items-center gap-2">
                {t.title}
                {positions.length > 0 && (
                  <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 border">
                    {positions.length} {t.positions}
                  </Badge>
                )}
              </CardTitle>
              <p className="text-slate-400 text-sm">{t.subtitle}</p>
            </div>
          </div>
          {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-4">
          {cifValue && (
            <div className="p-4 bg-gradient-to-r from-emerald-500/10 to-emerald-600/5 rounded-xl border border-emerald-500/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/20 rounded-lg">
                    < DollarSign className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs uppercase tracking-wide">{t.cifValue}</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {formatCurrency(parseFloat(cifValue) || 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {apiNote && (
            <div className="flex items-start gap-2 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-300">{apiNote}</p>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-3 text-slate-400">Chargement des positions nationales...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-300">{error}</p>
            </div>
          )}

          {!loading && !error && positions.length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-slate-700/50 rounded-full flex items-center justify-center">
                <Package className="w-8 h-8 text-slate-500" />
              </div>
              <p className="text-slate-400">{t.noPositions}</p>
            </div>
          )}

          {!loading && sortedPositions.length > 0 && (
            <div className="space-y-3">
              {sortedPositions.map((position, idx) => {
                const currentCode = position.code || position.hs_code || '';
                const isSelected = selectedPosition === currentCode;
                const estimatedDuties = calculateEstimatedDuties(position);
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
                        ? 'border-purple-500 bg-purple-500/10' 
                        : 'border-slate-700 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50'
                    }`}
                    onClick={() => handleSelect(position)}
                  >
                    <div className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <span className={`font-mono text-lg font-bold px-3 py-1 rounded-lg ${
                              isSelected ? 'bg-purple-500/30 text-purple-300' : 'bg-amber-500/20 text-amber-400'
                            }`}>
                              {currentCode}
                            </span>
                            <Badge variant="outline" className="text-xs border-slate-600 text-slate-400 uppercase">
                              {badgeLabel}
                            </Badge>
                          </div>
                          
                          <div className="relative">
                            <p className={`text-base leading-relaxed transition-all ${
                              isSelected ? 'text-white' : 'text-slate-200'
                            } ${!isDescExpanded && isLongDesc ? 'line-clamp-2' : ''}`}>
                              {desc}
                            </p>
                            {isLongDesc && (
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleDescription(idx);
                                }}
                                className="mt-1 text-purple-400 hover:text-purple-300 text-xs font-semibold flex items-center gap-1"
                              >
                                {isDescExpanded ? <><Minimize2 className="w-3 h-3"/> {t.showLess}</> : <><Maximize2 className="w-3 h-3"/> {t.showMore}</>}
                              </button>
                            )}
                          </div>
                        </div>

                        <div className="flex-shrink-0 text-right space-y-2">
                          <div>
                            <p className="text-xs text-slate-500 uppercase">{t.ddRate}</p>
                            <p className={`text-2xl font-bold ${
                              (position.dd || position.duty_rate_pct) === 0 ? 'text-emerald-400' : 'text-amber-400'
                            }`}>
                              {position.dd || position.duty_rate_pct || 0}%
                            </p>
                          </div>
                          {cifValue && (
                            <div className="pt-2 border-t border-slate-700">
                              <p className="text-xs text-slate-500 uppercase">{t.estimatedDuties}</p>
                              <p className="text-xl font-bold text-amber-400">
                                {formatCurrency(estimatedDuties)}
                              </p>
                            </div>
                          )}
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
