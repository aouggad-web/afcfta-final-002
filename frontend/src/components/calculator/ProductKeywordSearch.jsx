import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { Search, X, Loader2, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const ISO2_TO_ISO3 = {
  'DZ':'DZA','AO':'AGO','BJ':'BEN','BW':'BWA','BF':'BFA','BI':'BDI','CM':'CMR','CV':'CPV',
  'CF':'CAF','TD':'TCD','KM':'COM','CG':'COG','CD':'COD','CI':'CIV','DJ':'DJI','EG':'EGY',
  'GQ':'GNQ','ER':'ERI','SZ':'SWZ','ET':'ETH','GA':'GAB','GM':'GMB','GH':'GHA','GN':'GIN',
  'GW':'GNB','KE':'KEN','LS':'LSO','LR':'LBR','LY':'LBY','MG':'MDG','MW':'MWI','ML':'MLI',
  'MR':'MRT','MU':'MUS','MA':'MAR','MZ':'MOZ','NA':'NAM','NE':'NER','NG':'NGA','RW':'RWA',
  'ST':'STP','SN':'SEN','SC':'SYC','SL':'SLE','SO':'SOM','ZA':'ZAF','SS':'SSD','SD':'SDN',
  'TZ':'TZA','TG':'TGO','TN':'TUN','UG':'UGA','ZM':'ZMB','ZW':'ZWE'
};

function toISO3(code) {
  if (!code) return '';
  return code.length === 2 ? (ISO2_TO_ISO3[code] || code) : code;
}

function TaxBadge({ label, value, color }) {
  if (!value && value !== 0) return null;
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold ${color}`}>
      {label} {value}%
    </span>
  );
}

export default function ProductKeywordSearch({ destinationCountry, language = 'fr', onSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  const iso3 = toISO3(destinationCountry);

  const search = useCallback(async (q) => {
    if (!q || q.length < 2) { setResults([]); return; }
    setLoading(true);
    setError('');
    try {
      const country = iso3 || 'DZA';
      const res = await axios.get(`${API}/authentic-tariffs/search/${country}`, {
        params: { q, language, limit: 25 }
      });
      setResults(res.data.results || []);
      setOpen(true);
    } catch (e) {
      setError(language === 'fr' ? 'Erreur de recherche' : 'Search error');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [iso3, language]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (query.length >= 2) {
      debounceRef.current = setTimeout(() => search(query), 350);
    } else {
      setResults([]);
      setOpen(false);
    }
    return () => clearTimeout(debounceRef.current);
  }, [query, search]);

  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSelect = (item) => {
    const code = item.national_code || item.hs6 || '';
    const desc = item.description_fr || item.designation || '';
    setSelected({ code, desc, item });
    setQuery(desc.length > 60 ? desc.slice(0, 60) + '…' : desc);
    setOpen(false);
    onSelect && onSelect(code, desc, item);
  };

  const handleClear = () => {
    setQuery('');
    setSelected(null);
    setResults([]);
    setOpen(false);
    onSelect && onSelect('', '', null);
    inputRef.current?.focus();
  };

  const placeholder = language === 'fr'
    ? 'Ex: aluminium, chaussures, téléphone, blé...'
    : 'Ex: aluminium, shoes, telephone, wheat...';

  const labelText = language === 'fr' ? 'Recherche par mot-clé produit' : 'Product keyword search';
  const hintText = language === 'fr'
    ? `Recherche dans ${iso3 ? iso3 + ' — ' : ''}17 000+ positions douanières authentiques`
    : `Search across ${iso3 ? iso3 + ' — ' : ''}17 000+ authentic tariff positions`;

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Label */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
          <Search className="w-3 h-3 text-purple-400" />
          {labelText}
        </span>
        {selected && (
          <span className="text-xs text-emerald-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            {selected.code}
          </span>
        )}
      </div>

      {/* Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="w-full h-11 pl-9 pr-9 rounded-lg bg-slate-800/60 border border-slate-600 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-purple-500/70 focus:ring-1 focus:ring-purple-500/30 transition-colors"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-purple-400 animate-spin" />
        )}
        {!loading && query && (
          <button onClick={handleClear} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Hint */}
      <p className="text-[11px] text-slate-600 mt-1">{hintText}</p>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {!error && results.length === 0 && !loading && (
            <div className="px-4 py-4 text-slate-500 text-sm text-center">
              {language === 'fr' ? 'Aucun résultat pour' : 'No results for'} <span className="text-slate-300">"{query}"</span>
            </div>
          )}

          {results.length > 0 && (
            <>
              <div className="px-4 py-2 border-b border-slate-700 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  {results.length} {language === 'fr' ? 'résultats' : 'results'}
                  {iso3 && <span className="ml-1 text-purple-400">· {iso3}</span>}
                </span>
                {results[0]?.source_quality === 'crawled_authentic' && (
                  <span className="text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                    douane.gov.dz
                  </span>
                )}
              </div>

              <ul className="max-h-80 overflow-y-auto divide-y divide-slate-700/50">
                {results.map((item, i) => {
                  const code = item.national_code || item.hs6 || '';
                  const desc = item.description_fr || item.designation || '';
                  const isAuthentic = item.source_quality === 'crawled_authentic';
                  const dd = item.dd_rate ?? item.dd_rate;
                  const tva = item.tva_rate ?? item.vat_rate;
                  const daps = item.daps_rate;
                  const tcs = item.tcs_rate;
                  const prct = item.prct_rate;
                  const total = item.total_rate ?? item.total_taxes_pct;
                  const hasAdvantages = item.advantages?.length > 0 || item.fiscal_advantages?.length > 0;

                  return (
                    <li key={i}>
                      <button
                        onClick={() => handleSelect(item)}
                        className="w-full text-left px-4 py-3 hover:bg-slate-700/60 transition-colors group"
                      >
                        <div className="flex items-start gap-3">
                          {/* Code */}
                          <div className="shrink-0 mt-0.5">
                            <span className="font-mono text-xs font-bold text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded">
                              {code}
                            </span>
                          </div>

                          {/* Description + taxes */}
                          <div className="flex-1 min-w-0">
                            <p className="text-slate-200 text-sm leading-tight line-clamp-2">
                              {desc}
                            </p>
                            {/* Tax badges */}
                            <div className="flex flex-wrap gap-1 mt-1.5">
                              {dd != null && <TaxBadge label="DD" value={dd} color="bg-blue-500/15 text-blue-300" />}
                              {daps > 0 && <TaxBadge label="DAPS" value={daps} color="bg-orange-500/15 text-orange-300" />}
                              {prct > 0 && <TaxBadge label="PRCT" value={prct} color="bg-yellow-500/15 text-yellow-300" />}
                              {tcs > 0 && <TaxBadge label="TCS" value={tcs} color="bg-cyan-500/15 text-cyan-300" />}
                              {tva != null && <TaxBadge label="TVA" value={tva} color="bg-slate-500/30 text-slate-300" />}
                              {total != null && (
                                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-red-500/15 text-red-300">
                                  Total {total}%
                                </span>
                              )}
                              {hasAdvantages && (
                                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-300">
                                  ZLECAf ✓
                                </span>
                              )}
                              {isAuthentic && (
                                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-purple-500/15 text-purple-300">
                                  authentique
                                </span>
                              )}
                            </div>
                          </div>

                          <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 shrink-0 mt-1 transition-colors" />
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
