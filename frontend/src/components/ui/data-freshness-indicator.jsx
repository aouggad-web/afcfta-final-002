/**
 * Data Freshness Indicator Component
 * Displays a discrete badge showing when data was last updated
 */
import React from 'react';
import { Clock, Database, Zap } from 'lucide-react';
import { Badge } from './badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip';

/**
 * Data freshness information from the API
 */
interface DataFreshness {
  is_fresh: boolean;
  from_cache: boolean;
  age_seconds: number;
  age_human: string;
  age_human_en?: string;
  cached_at?: string;
}

interface DataFreshnessIndicatorProps {
  freshness?: DataFreshness | null;
  language?: 'fr' | 'en';
  className?: string;
  showTooltip?: boolean;
}

export function DataFreshnessIndicator({
  freshness,
  language = 'fr',
  className = '',
  showTooltip = true
}: DataFreshnessIndicatorProps) {
  // If no freshness data, show live indicator
  if (!freshness) {
    return (
      <Badge 
        variant="outline" 
        className={`text-xs font-medium bg-emerald-50 text-emerald-700 border-emerald-200 ${className}`}
        data-testid="data-freshness-live"
      >
        <Zap className="h-3 w-3 mr-1" />
        {language === 'fr' ? 'Données en direct' : 'Live data'}
      </Badge>
    );
  }

  const ageText = language === 'fr' ? freshness.age_human : (freshness.age_human_en || freshness.age_human);
  
  // Determine badge style based on freshness
  const getBadgeStyle = () => {
    if (!freshness.from_cache) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (freshness.is_fresh) {
      return 'bg-blue-50 text-blue-700 border-blue-200';
    }
    // Older than 1 hour but still valid cache
    if (freshness.age_seconds < 21600) { // Less than 6 hours
      return 'bg-amber-50 text-amber-700 border-amber-200';
    }
    return 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const getIcon = () => {
    if (!freshness.from_cache) {
      return <Zap className="h-3 w-3 mr-1" />;
    }
    return <Database className="h-3 w-3 mr-1" />;
  };

  const getTooltipText = () => {
    if (!freshness.from_cache) {
      return language === 'fr' 
        ? 'Données fraîchement générées par l\'IA'
        : 'Freshly generated AI data';
    }
    return language === 'fr'
      ? `Données mises en cache ${ageText}`
      : `Cached data from ${ageText}`;
  };

  const badge = (
    <Badge 
      variant="outline" 
      className={`text-xs font-medium ${getBadgeStyle()} ${className}`}
      data-testid="data-freshness-indicator"
    >
      {getIcon()}
      {language === 'fr' ? 'Données: ' : 'Data: '}{ageText}
    </Badge>
  );

  if (!showTooltip) {
    return badge;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {badge}
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">{getTooltipText()}</p>
          {freshness.from_cache && (
            <p className="text-xs text-slate-400 mt-1">
              <Clock className="h-3 w-3 inline mr-1" />
              {language === 'fr' ? 'Cache: 6h' : 'Cache TTL: 6h'}
            </p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Compact version for inline use
 */
export function DataFreshnessCompact({
  freshness,
  language = 'fr'
}: {
  freshness?: DataFreshness | null;
  language?: 'fr' | 'en';
}) {
  if (!freshness || !freshness.from_cache) {
    return null;
  }

  const ageText = language === 'fr' ? freshness.age_human : (freshness.age_human_en || freshness.age_human);
  
  return (
    <span 
      className="text-xs text-slate-400 italic ml-2"
      data-testid="data-freshness-compact"
    >
      ({ageText})
    </span>
  );
}

export default DataFreshnessIndicator;
