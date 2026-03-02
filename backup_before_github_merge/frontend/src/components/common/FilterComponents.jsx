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
    <Card className={`border-0 shadow-sm bg-gradient-to-r from-slate-50 to-gray-50 ${className}`}>
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
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`pl-10 pr-8 ${sizeClasses[size]} border-gray-200 focus:border-blue-400 focus:ring-blue-400/20`}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
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
        <Label className="text-sm font-medium text-gray-600 whitespace-nowrap">
          {label}
        </Label>
      )}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className={`min-w-[160px] ${sizeClasses[size]} border-gray-200`}>
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
    <div className={`flex items-center bg-white rounded-lg border border-gray-200 p-0.5 ${className}`}>
      {modes.map((mode) => (
        <Button
          key={mode}
          variant="ghost"
          size="sm"
          onClick={() => onChange(mode)}
          className={`h-8 px-3 rounded-md transition-all ${
            value === mode 
              ? 'bg-blue-100 text-blue-700 shadow-sm' 
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
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
      className={`bg-white border border-gray-200 text-gray-600 font-normal px-3 py-1 ${className}`}
    >
      <span className="font-semibold text-gray-800">{count}</span>
      {total && total !== count && (
        <span className="text-gray-400">/{total}</span>
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
    blue: "bg-blue-100 text-blue-700 border-blue-200",
    green: "bg-green-100 text-green-700 border-green-200",
    orange: "bg-orange-100 text-orange-700 border-orange-200",
    purple: "bg-purple-100 text-purple-700 border-purple-200",
    gray: "bg-gray-100 text-gray-700 border-gray-200"
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm border ${colorClasses[color]} ${className}`}>
      {label}
      {onRemove && (
        <button 
          onClick={onRemove}
          className="hover:bg-white/50 rounded-full p-0.5 transition-colors"
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
  return <div className={`h-6 w-px bg-gray-200 mx-1 ${className}`} />;
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
      className={`text-gray-500 hover:text-gray-700 h-8 ${className}`}
    >
      <X className="h-4 w-4 mr-1" />
      {label}
    </Button>
  );
}

export default FilterBar;
