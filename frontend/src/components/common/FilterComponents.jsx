import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Search, Filter, X, LayoutGrid, List, Map } from 'lucide-react';

/**
 * Unified Filter Bar Component
 * Provides consistent filtering UI across all app sections
 */
export function FilterBar({ 
  children, 
  className = "",
  compact = false 
}) {
  return (
    <Card className={`border border-[var(--afcfta-border)] shadow-sm bg-[var(--afcfta-card2)] ${className}`}>
      <CardContent className={compact ? "py-3 px-4" : "py-4 px-5"}>
        <div className="flex flex-wrap items-center gap-3">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Search Input with icon
 */
export function SearchFilter({ 
  value, 
  onChange, 
  placeholder = "Rechercher...",
  className = "",
  size = "default" // "sm" | "default" | "lg"
}) {
  const sizeClasses = {
    sm: "h-8 text-sm",
    default: "h-10",
    lg: "h-12 text-lg"
  };

  return (
    <div className={`relative flex-1 min-w-[200px] max-w-md ${className}`}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--afcfta-muted)]" />
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`pl-10 pr-8 ${sizeClasses[size]} border-[var(--afcfta-border)] focus:border-[color-mix(in_srgb,var(--info)_30%,transparent)] focus:ring-blue-400/20`}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--afcfta-muted)] hover:text-[var(--afcfta-muted)] transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

/**
 * Select Filter with label
 */
export function SelectFilter({
  label,
  value,
  onChange,
  options = [],
  placeholder = "Sélectionner...",
  className = "",
  size = "default",
  showLabel = true
}) {
  const sizeClasses = {
    sm: "h-8 text-sm",
    default: "h-10",
    lg: "h-12"
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {showLabel && label && (
        <Label className="text-sm font-medium text-[var(--afcfta-muted)] whitespace-nowrap">
          {label}
        </Label>
      )}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className={`min-w-[160px] ${sizeClasses[size]} border-[var(--afcfta-border)]`}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent className="z-50">
          {options.map((option) => (
            <SelectItem 
              key={option.value} 
              value={option.value}
              className="cursor-pointer"
            >
              <span className="flex items-center gap-2">
                {option.icon && <span>{option.icon}</span>}
                {option.label}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

/**
 * View Mode Toggle (Grid/List/Map)
 */
export function ViewModeToggle({
  value,
  onChange,
  modes = ['grid', 'list'],
  className = ""
}) {
  const modeIcons = {
    grid: <LayoutGrid className="h-4 w-4" />,
    list: <List className="h-4 w-4" />,
    map: <Map className="h-4 w-4" />
  };

  const modeLabels = {
    grid: 'Grille',
    list: 'Liste',
    map: 'Carte'
  };

  return (
    <div className={`flex items-center bg-[var(--afcfta-card)] rounded-lg border border-[var(--afcfta-border)] p-0.5 ${className}`}>
      {modes.map((mode) => (
        <Button
          key={mode}
          variant="ghost"
          size="sm"
          onClick={() => onChange(mode)}
          className={`h-8 px-3 rounded-md transition-all ${
            value === mode 
              ? 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] shadow-sm' 
              : 'text-[var(--afcfta-muted)] hover:text-[var(--text)] hover:bg-[var(--afcfta-card2)]'
          }`}
        >
          {modeIcons[mode]}
          <span className="ml-1.5 text-xs font-medium hidden sm:inline">
            {modeLabels[mode]}
          </span>
        </Button>
      ))}
    </div>
  );
}

/**
 * Results Counter Badge
 */
export function ResultsCounter({
  count,
  total,
  label = "résultat(s)",
  className = ""
}) {
  return (
    <Badge 
      variant="secondary" 
      className={`bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] text-[var(--afcfta-muted)] font-normal px-3 py-1 ${className}`}
    >
      <span className="font-semibold text-[var(--text)]">{count}</span>
      {total && total !== count && (
        <span className="text-[var(--afcfta-muted)]">/{total}</span>
      )}
      <span className="ml-1">{label}</span>
    </Badge>
  );
}

/**
 * Filter Chip/Tag
 */
export function FilterChip({
  label,
  onRemove,
  color = "blue",
  className = ""
}) {
  const colorClasses = {
    blue: "bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]",
    green: "bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]",
    orange: "bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)] border-[color-mix(in_srgb,var(--terra)_30%,transparent)]",
    purple: "bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]",
    gray: "bg-[var(--afcfta-card2)] text-[var(--text)] border-[var(--afcfta-border)]"
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm border ${colorClasses[color]} ${className}`}>
      {label}
      {onRemove && (
        <button 
          onClick={onRemove}
          className="hover:bg-[var(--afcfta-card)] rounded-full p-0.5 transition-colors"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}

/**
 * Filter Section Divider
 */
export function FilterDivider({ className = "" }) {
  return <div className={`h-6 w-px bg-[var(--afcfta-card2)] mx-1 ${className}`} />;
}

/**
 * Reset Filters Button
 */
export function ResetFiltersButton({
  onClick,
  disabled = false,
  label = "Réinitialiser",
  className = ""
}) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className={`text-[var(--afcfta-muted)] hover:text-[var(--text)] h-8 ${className}`}
    >
      <X className="h-4 w-4 mr-1" />
      {label}
    </Button>
  );
}

export default FilterBar;
