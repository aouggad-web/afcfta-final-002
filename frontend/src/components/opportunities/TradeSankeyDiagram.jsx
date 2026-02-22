/**
 * Trade Sankey Diagram Component
 * Visualizes trade flows: Exporter → Product → Importer
 * Adapted from AI Studio app with real data integration
 */
import React, { useMemo, useState, useCallback } from 'react';
import { 
  ResponsiveContainer, 
  Sankey, 
  Tooltip 
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { X, Filter, RotateCcw } from 'lucide-react';

// Color palettes for different node types
const SOURCE_COLORS = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'];
const MIDDLE_COLORS = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0'];
const SINK_COLORS = ['#f97316', '#fb923c', '#fdba74', '#fed7aa'];

// Hash function for consistent colors
const colorHash = (str) => {
  let hash = 0;
  if (!str) return 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return hash;
};

const getColor = (type, name) => {
  const index = Math.abs(colorHash(name));
  switch (type) {
    case 'source':
      return SOURCE_COLORS[index % SOURCE_COLORS.length];
    case 'middle':
      return MIDDLE_COLORS[index % MIDDLE_COLORS.length];
    case 'sink':
      return SINK_COLORS[index % SINK_COLORS.length];
    default:
      return '#8884d8';
  }
};

// Format value for display
const formatValue = (value) => {
  if (!value || isNaN(value)) return '$0';
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}B`;
  return `$${value.toFixed(0)}M`;
};

// Custom Tooltip
const CustomSankeyTooltip = ({ active, payload, language = 'fr' }) => {
  const texts = {
    fr: {
      from: 'De',
      to: 'Vers',
      value: 'Valeur',
      potential: 'Potentiel'
    },
    en: {
      from: 'From',
      to: 'To',
      value: 'Value',
      potential: 'Potential'
    }
  };
  const t = texts[language] || texts.fr;

  if (active && payload && payload.length) {
    const { source, target, value } = payload[0];
    if (!source?.payload || !target?.payload) return null;

    return (
      <div className="bg-white/95 dark:bg-slate-800/95 p-3 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl text-xs">
        <div className="flex justify-between items-center mb-2 gap-4">
          <span className="font-bold text-slate-900 dark:text-white">
            {source.payload.name}
          </span>
          <span className="text-slate-400">→</span>
          <span className="font-bold text-slate-900 dark:text-white">
            {target.payload.name}
          </span>
        </div>
        <p className="font-semibold text-emerald-600 dark:text-emerald-400">
          {t.value}: {formatValue(value)}
        </p>
      </div>
    );
  }
  return null;
};

// Custom Node renderer
const CustomSankeyNode = (props) => {
  const { x, y, width, height, payload, containerWidth, onNodeClick } = props;
  
  if (!payload || !payload.name) return null;
  if (height < 1) return null;

  const isSource = x < containerWidth / 3;
  const isSink = x > containerWidth * 2 / 3;
  const isActive = payload.isActive;
  const color = payload.color || '#8884d8';

  const handleClick = () => {
    if (onNodeClick) {
      const filterType = isSource ? 'source' : isSink ? 'target' : 'product';
      onNodeClick(filterType, payload.name);
    }
  };

  return (
    <g
      onClick={handleClick}
      className="cursor-pointer transition-all hover:opacity-100"
      style={{ opacity: 0.9 }}
    >
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color}
        stroke={isActive ? '#000' : 'none'}
        strokeWidth={isActive ? 2 : 0}
        rx={2}
      />
      {height > 10 && (
        <text
          x={isSource ? x - 6 : isSink ? x + width + 6 : x + width / 2}
          y={y + height / 2}
          dy="0.35em"
          textAnchor={isSource ? 'end' : isSink ? 'start' : 'middle'}
          fontSize="10"
          fontWeight={isActive ? '900' : '600'}
          fill="currentColor"
          className={`${isActive ? 'fill-slate-900' : 'fill-slate-600'}`}
          style={{ pointerEvents: 'none' }}
        >
          {payload.name.length > 20 ? payload.name.substring(0, 17) + '...' : payload.name}
        </text>
      )}
    </g>
  );
};

/**
 * Trade Sankey Diagram
 * 
 * Props:
 * - opportunities: Array of trade opportunities
 * - mode: 'export' | 'import' | 'product'
 * - language: 'fr' | 'en'
 * - onFilterChange: Callback when filters change
 */
export default function TradeSankeyDiagram({ 
  opportunities = [], 
  mode = 'export',
  language = 'fr',
  onFilterChange
}) {
  const [valueType, setValueType] = useState('potential'); // potential or current
  const [activeFilters, setActiveFilters] = useState({
    source: '',
    product: '',
    target: ''
  });

  const texts = {
    fr: {
      title: 'Flux Commerciaux',
      subtitle: 'Visualisation des opportunités',
      noData: 'Aucune donnée à visualiser',
      filterTip: 'Cliquez sur un nœud pour filtrer',
      clearFilters: 'Réinitialiser',
      potential: 'Potentiel',
      current: 'Actuel',
      source: 'Source',
      product: 'Produit',
      destination: 'Destination'
    },
    en: {
      title: 'Trade Flows',
      subtitle: 'Opportunities visualization',
      noData: 'No data to display',
      filterTip: 'Click a node to filter',
      clearFilters: 'Reset',
      potential: 'Potential',
      current: 'Current',
      source: 'Source',
      product: 'Product',
      destination: 'Destination'
    }
  };
  const t = texts[language] || texts.fr;

  const hasAnyFilter = activeFilters.source || activeFilters.product || activeFilters.target;

  // Handle node click for filtering
  const handleNodeClick = useCallback((filterType, value) => {
    setActiveFilters(prev => {
      const newFilters = { ...prev };
      // Toggle filter
      if (newFilters[filterType] === value) {
        newFilters[filterType] = '';
      } else {
        newFilters[filterType] = value;
      }
      if (onFilterChange) {
        onFilterChange(newFilters);
      }
      return newFilters;
    });
  }, [onFilterChange]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    const emptyFilters = { source: '', product: '', target: '' };
    setActiveFilters(emptyFilters);
    if (onFilterChange) {
      onFilterChange(emptyFilters);
    }
  }, [onFilterChange]);

  // Build Sankey data from opportunities
  const data = useMemo(() => {
    const nodes = [];
    const links = [];
    const nodeMap = new Map();

    const getNodeIndex = (name, type) => {
      const key = `${name}-${type}`;
      const isActive = 
        (type === 'source' && activeFilters.source === name) ||
        (type === 'middle' && activeFilters.product === name) ||
        (type === 'sink' && activeFilters.target === name);

      if (!nodeMap.has(key)) {
        nodeMap.set(key, nodes.length);
        nodes.push({
          name,
          type,
          color: getColor(type, name),
          isActive
        });
      }
      return nodeMap.get(key);
    };

    // Process opportunities
    opportunities.forEach(opp => {
      // Get source and target based on mode
      let sourceName, productName, targetName, value;

      if (mode === 'export') {
        sourceName = opp.exportingCountry || opp.country || 'Source';
        productName = opp.product_name || opp.product?.name || 'Produit';
        targetName = opp.potential_partner || opp.potentialPartner || 'Destination';
        value = valueType === 'potential' 
          ? (opp.potential_value_musd || opp.potentialTradeValue || 0)
          : (opp.current_value_musd || opp.currentTradeValue || 0);
      } else if (mode === 'import') {
        sourceName = opp.potential_supplier || opp.currentSource || 'Source';
        productName = opp.product_name || opp.product?.name || 'Produit';
        targetName = opp.importingCountry || opp.country || 'Destination';
        value = opp.substitution_potential_musd || opp.import_value_musd || opp.importValue || 0;
      } else if (mode === 'industrial') {
        // Industrial/Value Chain mode: input -> output transformation
        sourceName = opp.country || opp.exportingCountry || 'Source';
        productName = opp.output_product || opp.product_name || 'Produit Fini';
        // For industrial mode, target markets is an array - use first one
        const targets = opp.target_markets || [];
        targetName = Array.isArray(targets) ? targets[0] : (targets || 'Destination');
        // Parse estimated_output which may be string like "1800 MUSD"
        const outputStr = opp.estimated_output || '';
        const match = outputStr.match(/(\d+)/);
        value = match ? parseFloat(match[1]) : 0;
      } else {
        // Product analysis mode
        sourceName = opp.country || opp.exportingCountry || 'Source';
        productName = opp.product_name || opp.product?.name || 'Produit';
        targetName = opp.partner || opp.importingCountry || 'Destination';
        value = opp.trade_value || opp.value || 0;
      }

      // Apply filters
      if (activeFilters.source && activeFilters.source !== sourceName) return;
      if (activeFilters.product && activeFilters.product !== productName) return;
      if (activeFilters.target && activeFilters.target !== targetName) return;

      if (value <= 0) return;

      // Add HS code to product name if available
      const hsCode = opp.hs_code || opp.product?.hsCode;
      const productLabel = hsCode ? `${productName} (${hsCode})` : productName;

      const srcIdx = getNodeIndex(sourceName, 'source');
      const midIdx = getNodeIndex(productLabel, 'middle');
      const snkIdx = getNodeIndex(targetName, 'sink');

      // Create links: source -> product -> target
      links.push({ source: srcIdx, target: midIdx, value });
      links.push({ source: midIdx, target: snkIdx, value });
    });

    return { nodes, links };
  }, [opportunities, mode, valueType, activeFilters]);

  // Empty state
  if (data.nodes.length === 0) {
    return (
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-16 text-center">
          <div className="text-slate-400 mb-4">
            <Filter className="h-12 w-12 mx-auto opacity-50" />
          </div>
          <p className="text-slate-500 italic mb-4">{t.noData}</p>
          {hasAnyFilter && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearFilters}
              className="text-xs"
            >
              <RotateCcw className="h-3 w-3 mr-2" />
              {t.clearFilters}
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <CardTitle className="text-lg font-bold">{t.title}</CardTitle>
            <p className="text-sm text-slate-500">{t.subtitle}</p>
          </div>
          
          {/* Value type toggle */}
          <div className="flex items-center gap-2">
            <div className="inline-flex rounded-lg border border-slate-200 p-1">
              <button
                onClick={() => setValueType('potential')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                  valueType === 'potential'
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {t.potential}
              </button>
              <button
                onClick={() => setValueType('current')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                  valueType === 'current'
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {t.current}
              </button>
            </div>
          </div>
        </div>

        {/* Active filters */}
        <div className="flex flex-wrap gap-2 mt-3">
          {activeFilters.source && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-700 gap-1">
              {t.source}: {activeFilters.source}
              <button onClick={() => handleNodeClick('source', activeFilters.source)}>
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          {activeFilters.product && (
            <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 gap-1">
              {t.product}: {activeFilters.product.substring(0, 20)}...
              <button onClick={() => handleNodeClick('product', activeFilters.product)}>
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          {activeFilters.target && (
            <Badge variant="secondary" className="bg-orange-100 text-orange-700 gap-1">
              {t.destination}: {activeFilters.target}
              <button onClick={() => handleNodeClick('target', activeFilters.target)}>
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          {hasAnyFilter && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="h-6 px-2 text-xs text-slate-500"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              {t.clearFilters}
            </Button>
          )}
          {!hasAnyFilter && (
            <span className="text-xs text-slate-400 italic">{t.filterTip}</span>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <Sankey
              data={data}
              node={<CustomSankeyNode onNodeClick={handleNodeClick} />}
              nodePadding={25}
              margin={{ top: 10, right: 120, bottom: 10, left: 120 }}
              link={{ stroke: '#cbd5e1', strokeOpacity: 0.3 }}
            >
              <Tooltip content={<CustomSankeyTooltip language={language} />} />
            </Sankey>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-blue-500"></div>
            <span className="text-slate-600">{t.source}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-emerald-500"></div>
            <span className="text-slate-600">{t.product}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-orange-500"></div>
            <span className="text-slate-600">{t.destination}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
