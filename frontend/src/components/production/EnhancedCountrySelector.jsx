import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Badge } from '../ui/badge';
import { Search, ChevronDown, X, Globe, Star } from 'lucide-react';
import { getCountriesByRegion } from '../../utils/translations';

const MAJOR_ECONOMIES = ['ZAF', 'NGA', 'EGY', 'KEN', 'GHA', 'ETH', 'MAR', 'DZA', 'TZA', 'CIV'];

function EnhancedCountrySelector({ value, onChange, label, variant = 'default', language = 'fr' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);
  const inputRef = useRef(null);

  const AFRICAN_COUNTRIES_BY_REGION = useMemo(() => getCountriesByRegion(language), [language]);

  const texts = {
    fr: {
      selectCountry: 'Sélectionner un pays',
      searchPlaceholder: 'Rechercher un pays...',
      majorEconomies: 'Grandes économies',
      availableCountries: 'pays africains disponibles',
      results: 'résultats',
      noResults: 'Aucun pays trouvé',
      searchCountry: 'Rechercher un pays africain...',
      code: 'Code',
      top10: 'Top 10',
    },
    en: {
      selectCountry: 'Select a country',
      searchPlaceholder: 'Search for a country...',
      majorEconomies: 'Major economies',
      availableCountries: 'African countries available',
      results: 'results',
      noResults: 'No country found',
      searchCountry: 'Search for an African country...',
      code: 'Code',
      top10: 'Top 10',
    },
  };

  const t = texts[language] || texts.fr;
  const displayLabel = label || t.selectCountry;
  const isProminent = variant === 'prominent';

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target)
      ) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  useEffect(() => {
    if (!isOpen || !buttonRef.current) return;

    const updatePosition = () => {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 8,
        left: rect.left + window.scrollX,
        width: rect.width,
      });
    };

    updatePosition();
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen]);

  const allCountries = useMemo(() => {
    const countries = [];
    Object.values(AFRICAN_COUNTRIES_BY_REGION).forEach((region) => {
      countries.push(...region);
    });
    return countries;
  }, [AFRICAN_COUNTRIES_BY_REGION]);

  const selectedCountry = useMemo(
    () => allCountries.find((country) => country.code === value),
    [value, allCountries]
  );

  const filteredRegions = useMemo(() => {
    if (!searchTerm) return AFRICAN_COUNTRIES_BY_REGION;

    const normalizedSearch = searchTerm.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const filtered = {};

    Object.entries(AFRICAN_COUNTRIES_BY_REGION).forEach(([region, countries]) => {
      const matchedCountries = countries.filter((country) => {
        const normalizedName = country.name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        return normalizedName.includes(normalizedSearch) || country.code.toLowerCase().includes(normalizedSearch);
      });

      if (matchedCountries.length > 0) {
        filtered[region] = matchedCountries;
      }
    });

    return filtered;
  }, [searchTerm, AFRICAN_COUNTRIES_BY_REGION]);

  const majorEconomiesFiltered = useMemo(() => {
    const majors = allCountries.filter((country) => MAJOR_ECONOMIES.includes(country.code));

    if (!searchTerm) return majors;

    const normalizedSearch = searchTerm.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    return majors.filter((country) => {
      const normalizedName = country.name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return normalizedName.includes(normalizedSearch) || country.code.toLowerCase().includes(normalizedSearch);
    });
  }, [searchTerm, allCountries]);

  const totalResults = Object.values(filteredRegions).flat().length;

  const handleToggle = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsOpen((prev) => !prev);
  }, []);

  const handleSelect = useCallback(
    (country) => {
      onChange(country.code);
      setIsOpen(false);
      setSearchTerm('');
    },
    [onChange]
  );

  const handleClear = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      onChange('');
      setSearchTerm('');
    },
    [onChange]
  );

  const surfaceClass = isProminent
    ? 'bg-[linear-gradient(135deg,rgba(24,32,48,0.98),rgba(18,26,40,0.98))] border-[rgba(212,137,26,0.28)]'
    : 'bg-[rgba(24,32,48,0.96)] border-[rgba(212,137,26,0.18)]';

  return (
    <div className="relative w-full">
      <label className="block text-xs font-semibold tracking-wide text-[var(--afcfta-muted)] mb-2 flex items-center gap-2 uppercase">
        <Globe className="w-4 h-4 text-[var(--gold)]" />
        {displayLabel}
      </label>

      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        className={[
          'w-full text-left cursor-pointer rounded-xl border transition-all duration-200',
          'min-h-[72px] px-4 py-3 shadow-sm',
          surfaceClass,
          isOpen
            ? 'ring-2 ring-[rgba(212,137,26,0.18)] border-[rgba(212,137,26,0.45)] shadow-[0_18px_40px_rgba(0,0,0,0.35)]'
            : 'hover:border-[rgba(212,137,26,0.32)] hover:shadow-[0_10px_28px_rgba(0,0,0,0.22)]',
        ].join(' ')}
      >
        <div className="flex items-center justify-between gap-3">
          {selectedCountry ? (
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-3xl shrink-0">{selectedCountry.flag}</span>
              <div className="min-w-0">
                <p className={`font-semibold ${isProminent ? 'text-lg' : 'text-base'} text-[var(--text)] truncate`}>
                  {selectedCountry.name}
                </p>
                <p className="text-xs text-[var(--afcfta-muted)]">
                  {t.code}: {selectedCountry.code}
                </p>
              </div>

              {MAJOR_ECONOMIES.includes(selectedCountry.code) && (
                <Badge className="ml-1 bg-[rgba(212,137,26,0.14)] text-[var(--gold)] border border-[rgba(212,137,26,0.28)] hover:bg-[rgba(212,137,26,0.14)]">
                  <Star className="w-3 h-3 mr-1" /> {t.top10}
                </Badge>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-[var(--afcfta-muted)] min-w-0">
              <Search className="w-5 h-5 shrink-0" />
              <span className={isProminent ? 'text-base' : 'text-sm'}>{t.searchCountry}</span>
            </div>
          )}

          <div className="flex items-center gap-2 shrink-0">
            {selectedCountry && (
              <span
                onClick={handleClear}
                className="p-1.5 hover:bg-[rgba(255,255,255,0.06)] rounded-full transition-colors cursor-pointer"
              >
                <X className="w-4 h-4 text-[var(--afcfta-muted)]" />
              </span>
            )}
            <ChevronDown
              className={`w-5 h-5 text-[var(--afcfta-muted)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
            />
          </div>
        </div>
      </button>

      {isOpen &&
        createPortal(
          <div
            ref={dropdownRef}
            className="rounded-xl border shadow-2xl overflow-hidden"
            style={{
              position: 'absolute',
              top: dropdownPosition.top,
              left: dropdownPosition.left,
              width: dropdownPosition.width,
              zIndex: 99999,
              background: 'rgba(17, 24, 39, 0.985)',
              borderColor: 'rgba(212, 137, 26, 0.22)',
              boxShadow: '0 30px 70px rgba(0,0,0,0.55)',
            }}
          >
            <div
              className="p-3 border-b"
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'rgba(12,18,25,0.96)',
                borderColor: 'rgba(212,137,26,0.12)',
              }}
            >
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--afcfta-muted)] pointer-events-none" />
                <input
                  ref={inputRef}
                  type="text"
                  placeholder={t.searchPlaceholder}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg focus:outline-none text-sm border"
                  style={{
                    background: 'rgba(24,32,48,0.95)',
                    color: 'var(--text)',
                    borderColor: 'rgba(212,137,26,0.18)',
                  }}
                />
              </div>

              <p className="text-xs text-[var(--afcfta-muted)] mt-2 flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {allCountries.length} {t.availableCountries}
                {searchTerm && ` • ${totalResults} ${t.results}`}
              </p>
            </div>

            <div className="max-h-80 overflow-y-auto" style={{ background: 'rgba(17,24,39,0.985)' }}>
              {!searchTerm && majorEconomiesFiltered.length > 0 && (
                <div className="p-2.5">
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-[11px] font-semibold rounded-lg mb-2 uppercase tracking-wide"
                    style={{
                      color: 'var(--gold)',
                      background: 'rgba(212,137,26,0.08)',
                      border: '1px solid rgba(212,137,26,0.14)',
                    }}
                  >
                    <Star className="w-3.5 h-3.5" />
                    {t.majorEconomies}
                  </div>

                  <div className="grid grid-cols-2 gap-1.5">
                    {majorEconomiesFiltered.map((country) => {
                      const active = value === country.code;
                      return (
                        <button
                          key={country.code}
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleSelect(country);
                          }}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors"
                          style={{
                            background: active ? 'rgba(34,197,94,0.12)' : 'rgba(255,255,255,0.02)',
                            color: 'var(--text)',
                            border: active
                              ? '1px solid rgba(34,197,94,0.28)'
                              : '1px solid rgba(255,255,255,0.04)',
                          }}
                        >
                          <span className="text-xl">{country.flag}</span>
                          <span className="text-sm font-medium truncate">{country.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {!searchTerm && (
                <div className="mx-2 my-1 border-t" style={{ borderColor: 'rgba(212,137,26,0.10)' }} />
              )}

              {Object.entries(filteredRegions).map(([region, countries]) => (
                <div key={region} className="p-2.5 pt-1.5">
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-[11px] font-semibold rounded-lg mb-1.5"
                    style={{
                      color: 'var(--afcfta-muted)',
                      background: 'rgba(255,255,255,0.04)',
                    }}
                  >
                    {region} ({countries.length})
                  </div>

                  <div className="space-y-1">
                    {countries.map((country) => {
                      const active = value === country.code;
                      return (
                        <button
                          key={country.code}
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleSelect(country);
                          }}
                          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors"
                          style={{
                            background: active ? 'rgba(34,197,94,0.10)' : 'transparent',
                            color: 'var(--text)',
                            border: active
                              ? '1px solid rgba(34,197,94,0.28)'
                              : '1px solid transparent',
                          }}
                          onMouseEnter={(e) => {
                            if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                          }}
                          onMouseLeave={(e) => {
                            if (!active) e.currentTarget.style.background = 'transparent';
                          }}
                        >
                          <span className="text-xl">{country.flag}</span>
                          <span className="flex-1 text-sm truncate">{country.name}</span>
                          <Badge
                            variant="outline"
                            className="text-[10px] font-mono border-[rgba(212,137,26,0.18)] text-[var(--afcfta-muted)]"
                          >
                            {country.code}
                          </Badge>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {Object.keys(filteredRegions).length === 0 && (
                <div className="p-8 text-center text-[var(--afcfta-muted)]">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>
                    {t.noResults} "{searchTerm}"
                  </p>
                </div>
              )}
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}

export default EnhancedCountrySelector;
