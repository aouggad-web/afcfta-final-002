import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ChevronDown, ChevronUp, Package, Check, DollarSign, Percent, FileText, AlertCircle, TrendingUp, TrendingDown, Info, Car, Leaf, Cog, Zap } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

/**
 * Composant amélioré pour afficher et sélectionner les positions nationales
 * avec détails complets des tarifs et descriptions exactes
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
      selected: "Sélectionné",
      noPositions: "Aucune sous-position nationale disponible pour ce code HS",
      loadError: "Erreur lors du chargement des positions",
      positions: "positions disponibles",
      cifValue: "Valeur CIF Déclarée",
      source: "Source",
      digits: "chiffres",
      newProduct: "Neuf",
      usedProduct: "Occasion",
      ageCategory: "Catégorie d'âge",
      taxImpact: "Impact fiscal",
      selectToCalculate: "Sélectionner pour calculer les droits exacts"
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
      newProduct: "New",
      usedProduct: "Used",
      ageCategory: "Age category",
      taxImpact: "Tax impact",
      selectToCalculate: "Select to calculate exact duties"
    }
  };

  const t = texts[language] || texts.fr;

  // Fonction pour déterminer l'icône selon le type de produit
  const getProductIcon = useCallback((description) => {
    const desc = (description || '').toLowerCase();
    if (desc.includes('neuf') || desc.includes('new')) return <Zap className="w-4 h-4 text-emerald-400" />;
    if (desc.includes('occasion') || desc.includes('used')) return <Cog className="w-4 h-4 text-amber-400" />;
    if (desc.includes('voiture') || desc.includes('car') || desc.includes('véhicule')) return <Car className="w-4 h-4 text-blue-400" />;
    if (desc.includes('agricole') || desc.includes('agri')) return <Leaf className="w-4 h-4 text-green-400" />;
    return <Package className="w-4 h-4 text-slate-400" />;
  }, []);

  // Fonction pour extraire les tags de la description
  const extractTags = useCallback((description) => {
    const tags = [];
    const desc = (description || '').toLowerCase();
    
    if (desc.includes('neuf') || desc.includes('new')) tags.push({ label: language === 'fr' ? 'Neuf' : 'New', color: 'emerald' });
    if (desc.includes('occasion') || desc.includes('used')) tags.push({ label: language === 'fr' ? 'Occasion' : 'Used', color: 'amber' });
    
    // Catégories d'âge pour véhicules
    const ageMatch = desc.match(/<(\d+)\s*ans?|>(\d+)\s*ans?|(\d+)-(\d+)\s*ans?/i);
    if (ageMatch) {
      if (desc.includes('<')) tags.push({ label: `<${ageMatch[1] || ageMatch[3]} ans`, color: 'blue' });
      else if (desc.includes('>')) tags.push({ label: `>${ageMatch[2] || ageMatch[4]} ans`, color: 'orange' });
      else if (ageMatch[3] && ageMatch[4]) tags.push({ label: `${ageMatch[3]}-${ageMatch[4]} ans`, color: 'purple' });
    }
    
    return tags;
  }, [language]);

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
        // Fallback to old API if PostgreSQL not available
        response = await axios.get(
          `${API}/authentic-tariffs/country/${countryCode}/sub-positions/${hs6Code.substring(0, 6)}`,
          { params: { language } }
        );
      }
      
      if (response.data.success && response.data.sub_positions?.length > 0) {
        setPositions(response.data.sub_positions);
        setApiNote(response.data.note || (language === 'fr' ? response.data.note_fr : response.data.note_en));
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
    const ddRate = position.dd || 0;
    return value * ddRate / 100;
  }, [cifValue]);

  // Trier les positions par taux de DD (plus bas en premier)
  const sortedPositions = useMemo(() => {
    return [...positions].sort((a, b) => (a.dd || 0) - (b.dd || 0));
  }, [positions]);

  // Calculer le min et max DD pour la visualisation
  const { minDD, maxDD } = useMemo(() => {
    if (positions.length === 0) return { minDD: 0, maxDD: 100 };
    const dds = positions.map(p => p.dd || 0);
    return { minDD: Math.min(...dds), maxDD: Math.max(...dds) };
  }, [positions]);

  const handleSelect = useCallback((position) => {
    if (onPositionSelect) {
      onPositionSelect(position.code, position.description_fr || position.description_en);
    }
  }, [onPositionSelect]);

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
          {/* Valeur CIF affichée */}
          {cifValue && (
            <div className="p-4 bg-gradient-to-r from-emerald-500/10 to-emerald-600/5 rounded-xl border border-emerald-500/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/20 rounded-lg">
                    <DollarSign className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs uppercase tracking-wide">{t.cifValue}</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {formatCurrency(parseFloat(cifValue) || 0)}
                    </p>
                  </div>
                </div>
                {positions.length > 0 && (
                  <div className="text-right">
                    <p className="text-slate-500 text-xs">{t.taxImpact}</p>
                    <p className="text-sm text-slate-300">
                      {formatCurrency(calculateEstimatedDuties({ dd: minDD }))} - {formatCurrency(calculateEstimatedDuties({ dd: maxDD }))}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Note informative */}
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
                const isSelected = selectedPosition === position.code;
                const estimatedDuties = calculateEstimatedDuties(position);
                const tags = extractTags(position.description_fr || position.description_en);
                const isLowestRate = position.dd === minDD;
                const isHighestRate = position.dd === maxDD;
                
                return (
                  <div 
                    key={idx}
                    className={`
                      relative rounded-xl border-2 transition-all duration-200 cursor-pointer overflow-hidden
                      ${isSelected 
                        ? 'border-purple-500 bg-purple-500/10' 
                        : 'border-slate-700 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50'
                      }
                    `}
                    onClick={() => handleSelect(position)}
                  >
                    {/* Badge meilleur taux */}
                    {isLowestRate && positions.length > 1 && (
                      <div className="absolute top-0 right-0">
                        <div className="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg flex items-center gap-1">
                          <TrendingDown className="w-3 h-3" />
                          {language === 'fr' ? 'Meilleur taux' : 'Best rate'}
                        </div>
                      </div>
                    )}
                    
                    {isHighestRate && positions.length > 1 && !isLowestRate && (
                      <div className="absolute top-0 right-0">
                        <div className="bg-red-500/80 text-white text-xs font-bold px-3 py-1 rounded-bl-lg flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {language === 'fr' ? 'Taux élevé' : 'High rate'}
                        </div>
                      </div>
                    )}

                    <div className="p-4">
                      <div className="flex items-start gap-4">
                        {/* Icône et Code */}
                        <div className="flex-shrink-0">
                          <div className={`
                            p-3 rounded-xl
                            ${isSelected ? 'bg-purple-500/20' : 'bg-slate-700/50'}
                          `}>
                            {getProductIcon(position.description_fr || position.description_en)}
                          </div>
                        </div>

                        {/* Détails */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <span className={`
                              font-mono text-lg font-bold px-3 py-1 rounded-lg
                              ${isSelected 
                                ? 'bg-purple-500/30 text-purple-300' 
                                : 'bg-amber-500/20 text-amber-400'
                              }
                            `}>
                              {position.code}
                            </span>
                            <Badge variant="outline" className="text-xs border-slate-600 text-slate-400">
                              HS{position.digits || 10}
                            </Badge>
                            {isSelected && (
                              <Badge className="bg-purple-500 text-white">
                                <Check className="w-3 h-3 mr-1" />
                                {t.selected}
                              </Badge>
                            )}
                          </div>
                          
                          {/* Description */}
                          <p className={`text-base mb-2 ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                            {language === 'fr' ? position.description_fr : position.description_en}
                          </p>
                          
                          {/* Tags */}
                          {tags.length > 0 && (
                            <div className="flex items-center gap-2 mb-3">
                              {tags.map((tag, tagIdx) => (
                                <Badge 
                                  key={tagIdx} 
                                  className={`text-xs bg-${tag.color}-500/20 text-${tag.color}-400 border-${tag.color}-500/30 border`}
                                >
                                  {tag.label}
                                </Badge>
                              ))}
                            </div>
                          )}

                          {/* Source */}
                          {position.source && (
                            <p className="text-xs text-slate-500 flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {t.source}: {position.source}
                            </p>
                          )}
                        </div>

                        {/* Taux et Montants */}
                        <div className="flex-shrink-0 text-right space-y-2">
                          <div>
                            <p className="text-xs text-slate-500 uppercase">{t.ddRate}</p>
                            <p className={`text-2xl font-bold ${
                              isLowestRate ? 'text-emerald-400' : 
                              isHighestRate ? 'text-red-400' : 
                              'text-amber-400'
                            }`}>
                              {position.dd || 0}%
                            </p>
                          </div>
                          {cifValue && (
                            <div className="pt-2 border-t border-slate-700">
                              <p className="text-xs text-slate-500 uppercase">{t.estimatedDuties}</p>
                              <p className={`text-xl font-bold ${
                                isLowestRate ? 'text-emerald-400' : 
                                isHighestRate ? 'text-red-400' : 
                                'text-amber-400'
                              }`}>
                                {formatCurrency(estimatedDuties)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Bouton de sélection */}
                      {!isSelected && (
                        <div className="mt-3 pt-3 border-t border-slate-700/50">
                          <Button
                            size="sm"
                            className="w-full bg-slate-700 hover:bg-slate-600 text-slate-200"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelect(position);
                            }}
                          >
                            {t.selectToCalculate}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Légende */}
          {!loading && positions.length > 1 && (
            <div className="flex items-center justify-center gap-6 pt-4 border-t border-slate-700 text-xs text-slate-500">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                <span>{language === 'fr' ? 'Taux le plus bas' : 'Lowest rate'}</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>{language === 'fr' ? 'Taux le plus élevé' : 'Highest rate'}</span>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
