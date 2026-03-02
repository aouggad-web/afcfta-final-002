import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ChevronDown, ChevronUp, Package, Check, DollarSign, Percent, FileText } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Composant pour afficher et sélectionner les positions nationales disponibles
 * avec leurs intitulés exacts et valeurs
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

  const texts = {
    fr: {
      title: "Positions Nationales Disponibles",
      subtitle: "Sélectionnez la position exacte pour un calcul précis",
      code: "Code National",
      description: "Désignation",
      ddRate: "DD",
      totalRate: "Total Taxes",
      estimatedDuties: "Droits Estimés",
      select: "Sélectionner",
      selected: "Sélectionné",
      noPositions: "Aucune position nationale trouvée",
      loadError: "Erreur de chargement",
      positions: "positions",
      cifValue: "Valeur CIF",
      vatRate: "TVA",
      otherTaxes: "Autres"
    },
    en: {
      title: "Available National Positions",
      subtitle: "Select the exact position for accurate calculation",
      code: "National Code",
      description: "Description",
      ddRate: "Duty",
      totalRate: "Total Taxes",
      estimatedDuties: "Estimated Duties",
      select: "Select",
      selected: "Selected",
      noPositions: "No national positions found",
      loadError: "Loading error",
      positions: "positions",
      cifValue: "CIF Value",
      vatRate: "VAT",
      otherTaxes: "Other"
    }
  };

  const t = texts[language] || texts.fr;

  useEffect(() => {
    if (countryCode && hs6Code && hs6Code.length >= 6) {
      fetchPositions();
    }
  }, [countryCode, hs6Code]);

  const fetchPositions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Essayer d'abord avec les données authentiques
      const response = await axios.get(
        `${API}/authentic-tariffs/country/${countryCode}/sub-positions/${hs6Code.substring(0, 6)}`,
        { params: { language } }
      );
      
      if (response.data.sub_positions && response.data.sub_positions.length > 0) {
        setPositions(response.data.sub_positions);
      } else {
        // Fallback: Rechercher dans PostgreSQL
        const searchResponse = await axios.get(
          `${API}/commodities/search/simple`,
          { params: { q: hs6Code.substring(0, 6), country: countryCode, limit: 50 } }
        );
        
        if (searchResponse.data.results) {
          // Transformer les résultats au format attendu
          setPositions(searchResponse.data.results.map(r => ({
            code: r.national_code,
            description_fr: r.description,
            description_en: r.description,
            dd_rate_pct: r.npf_rate || 0,
            vat_rate_pct: 18, // Default VAT
            total_rate_pct: (r.npf_rate || 0) + 18
          })));
        }
      }
    } catch (err) {
      console.error('Error fetching positions:', err);
      setError(t.loadError);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const calculateEstimatedDuties = (position) => {
    const value = parseFloat(cifValue) || 0;
    const ddRate = position.dd_rate_pct || 0;
    return value * ddRate / 100;
  };

  const handleSelect = (position) => {
    if (onPositionSelect) {
      onPositionSelect(position.code, position.description_fr || position.description_en);
    }
  };

  // Fonction pour nettoyer la description et enlever les "Type X" génériques
  const cleanDescription = (position) => {
    const desc = position.description_fr || position.description_en || '';
    const code = position.code || '';
    
    // Si la description contient juste "Type X" ou "Autre", afficher plus d'infos
    if (/^(Type \d+|Autre|Other|Autres)$/i.test(desc.split(' - ').pop()?.trim())) {
      // Retourner la description complète avec le code national pour clarté
      return (
        <div>
          <span className="text-slate-300">{desc}</span>
          <span className="text-slate-500 text-xs ml-2">({code})</span>
        </div>
      );
    }
    
    return <span className="text-slate-300">{desc}</span>;
  };

  if (!countryCode || !hs6Code || hs6Code.length < 6) {
    return null;
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
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
        <CardContent className="pt-0">
          {/* Valeur CIF affichée */}
          {cifValue && (
            <div className="mb-4 p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-300 text-sm">{t.cifValue}:</span>
              </div>
              <span className="text-emerald-400 font-bold text-lg">
                {formatCurrency(parseFloat(cifValue) || 0)}
              </span>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-3 text-slate-400">Chargement...</span>
            </div>
          )}

          {error && (
            <div className="text-center py-6 text-red-400">
              {error}
            </div>
          )}

          {!loading && !error && positions.length === 0 && (
            <div className="text-center py-6 text-slate-500">
              {t.noPositions}
            </div>
          )}

          {!loading && positions.length > 0 && (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700 hover:bg-transparent">
                    <TableHead className="text-slate-400 font-medium">{t.code}</TableHead>
                    <TableHead className="text-slate-400 font-medium">{t.description}</TableHead>
                    <TableHead className="text-slate-400 font-medium text-center">{t.ddRate}</TableHead>
                    {cifValue && (
                      <TableHead className="text-slate-400 font-medium text-right">{t.estimatedDuties}</TableHead>
                    )}
                    <TableHead className="text-slate-400 font-medium text-center">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.map((position, idx) => {
                    const isSelected = selectedPosition === position.code;
                    const estimatedDuties = calculateEstimatedDuties(position);
                    
                    return (
                      <TableRow 
                        key={idx}
                        className={`
                          border-slate-700 cursor-pointer transition-colors
                          ${isSelected 
                            ? 'bg-purple-500/20 hover:bg-purple-500/30' 
                            : 'hover:bg-slate-700/30'
                          }
                        `}
                        onClick={() => handleSelect(position)}
                      >
                        <TableCell className="font-mono">
                          <div className="flex items-center gap-2">
                            {isSelected && (
                              <Check className="w-4 h-4 text-purple-400" />
                            )}
                            <span className={`
                              px-2 py-1 rounded text-sm font-bold
                              ${isSelected 
                                ? 'bg-purple-500/30 text-purple-300' 
                                : 'bg-slate-700 text-amber-400'
                              }
                            `}>
                              {position.code}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {cleanDescription(position)}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 border">
                            {position.dd_rate_pct || 0}%
                          </Badge>
                        </TableCell>
                        {cifValue && (
                          <TableCell className="text-right">
                            <span className="text-amber-400 font-semibold">
                              {formatCurrency(estimatedDuties)}
                            </span>
                          </TableCell>
                        )}
                        <TableCell className="text-center">
                          <Button
                            size="sm"
                            variant={isSelected ? "default" : "outline"}
                            className={`
                              text-xs
                              ${isSelected 
                                ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                                : 'border-purple-500/40 text-purple-400 hover:bg-purple-500/10'
                              }
                            `}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelect(position);
                            }}
                          >
                            {isSelected ? t.selected : t.select}
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Légende */}
          {!loading && positions.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-700 flex flex-wrap gap-4 text-xs text-slate-500">
              <div className="flex items-center gap-1">
                <Percent className="w-3 h-3" />
                <span>{language === 'fr' ? 'DD = Droits de Douane' : 'DD = Customs Duties'}</span>
              </div>
              <div className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                <span>{language === 'fr' ? 'Cliquez pour sélectionner une position' : 'Click to select a position'}</span>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
