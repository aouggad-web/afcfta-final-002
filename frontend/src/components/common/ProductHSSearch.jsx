/**
 * ProductHSSearch — Recherche « nom de marchandise -> code SH ».
 *
 * Composant réutilisable dans TOUS les modules du SaaS : il permet à un
 * utilisateur SANS connaissance douanière de retrouver le code SH d'un produit
 * en tapant son nom courant (« huile de palme », « machine à coudre », « thé
 * vert »…). Source : index alphabétique officiel de l'OMD (Système Harmonisé,
 * 7e éd. 2022), via GET /api/hs-codes/product-index.
 *
 * Props :
 *   - lang : 'fr' | 'en' (défaut 'fr')
 *   - onSelect(code, entry) : rappel optionnel quand l'utilisateur clique un
 *     code SH — permet de brancher la recherche sur n'importe quel module
 *     (flux stratégiques, tarifs, règles d'origine…).
 *   - placeholder : texte d'invite optionnel.
 *   - autoFocus : focus au montage.
 */
import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Search, Loader2, ArrowRight, Info } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const T = {
  fr: {
    placeholder: 'Rechercher un produit (ex : huile de palme, ciment, thé vert)…',
    hint: 'Tapez le nom courant du produit — nul besoin de connaître la nomenclature douanière.',
    searching: 'Recherche…',
    noResults: 'Aucun produit trouvé. Essayez un synonyme ou un terme plus général.',
    resultsCount: (n) => `${n} produit${n > 1 ? 's' : ''} trouvé${n > 1 ? 's' : ''}`,
    seeAlso: 'voir',
    range: 'plage',
    chapter: 'Chapitre',
    source: 'Source : OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)',
    copied: 'Copié',
  },
  en: {
    placeholder: 'Search a product (e.g. palm oil, cement, green tea)…',
    hint: 'Type the common product name — no customs nomenclature knowledge required.',
    searching: 'Searching…',
    noResults: 'No product found. Try a synonym or a broader term.',
    resultsCount: (n) => `${n} product${n > 1 ? 's' : ''} found`,
    seeAlso: 'see',
    range: 'range',
    chapter: 'Chapter',
    source: 'Source: WCO — Harmonized System Alphabetical Index (7th ed. 2022)',
    copied: 'Copied',
  },
};

const LEVEL_BADGE = {
  chapter: { fr: 'SH2', en: 'HS2' },
  heading: { fr: 'SH4', en: 'HS4' },
  subheading: { fr: 'SH6', en: 'HS6' },
  other: { fr: 'SH', en: 'HS' },
};

export default function ProductHSSearch({
  lang,
  language,
  onSelect,
  placeholder,
  autoFocus = false,
}) {
  const uiLang = lang || language || 'fr';
  const t = T[uiLang] || T.fr;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState(false);
  const [copied, setCopied] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      setCount(0);
      return;
    }
    // Verrou d'obsolescence : si une requête plus récente est lancée avant que
    // celle-ci ne résolve (frappe rapide) ou si le composant est démonté, on
    // ignore sa réponse — évite d'écraser des résultats plus frais avec une
    // réponse tardive, et tout setState après démontage.
    let stale = false;
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      setTouched(true);
      try {
        const r = await axios.get(`${API}/hs-codes/product-index`, {
          params: { q, language: uiLang, limit: 25 },
        });
        if (stale) return;
        setResults(r.data.results || []);
        setCount(r.data.count || 0);
      } catch {
        if (stale) return;
        setResults([]);
        setCount(0);
      } finally {
        if (!stale) setLoading(false);
      }
    }, 280);
    return () => {
      stale = true;
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, uiLang]);

  const handleCode = (code, entry) => {
    if (onSelect) onSelect(code, entry);
    const clipboard = typeof navigator !== 'undefined' ? navigator.clipboard : null;
    if (clipboard && typeof clipboard.writeText === 'function') {
      clipboard.writeText(code).then(
        () => {
          setCopied(code);
          setTimeout(() => setCopied(null), 1200);
        },
        () => {},
      );
    }
  };

  return (
    <div className="product-hs-search" data-testid="product-hs-search">
      <div style={{ position: 'relative' }}>
        <Search
          size={18}
          style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--afcfta-muted, #94a3b8)',
          }}
        />
        <input
          type="text"
          value={query}
          autoFocus={autoFocus}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder || t.placeholder}
          aria-label={placeholder || t.placeholder}
          data-testid="product-hs-input"
          style={{
            width: '100%',
            padding: '11px 14px 11px 40px',
            borderRadius: 10,
            border: '1px solid var(--afcfta-border, #e2e8f0)',
            fontSize: 14,
            outline: 'none',
            background: 'var(--afcfta-bg, #fff)',
            color: 'var(--afcfta-text, #0f172a)',
          }}
        />
        {loading && (
          <Loader2
            size={16}
            className="spin"
            style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)' }}
          />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '6px 2px 0' }}>
        <Info size={12} style={{ color: 'var(--afcfta-muted, #94a3b8)' }} />
        <span style={{ fontSize: 12, color: 'var(--afcfta-muted, #94a3b8)' }}>{t.hint}</span>
      </div>

      {touched && !loading && query.trim().length >= 2 && count === 0 && (
        <div
          data-testid="product-hs-empty"
          style={{ padding: 16, textAlign: 'center', color: 'var(--afcfta-muted, #94a3b8)', fontSize: 13 }}
        >
          {t.noResults}
        </div>
      )}

      {results.length > 0 && (
        <>
          <div style={{ fontSize: 12, color: 'var(--afcfta-muted, #94a3b8)', margin: '10px 2px 6px' }}>
            {t.resultsCount(count)}
          </div>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 8 }}>
            {results.map((r, i) => (
              <li
                key={`${r.label}-${i}`}
                style={{
                  border: '1px solid var(--afcfta-border, #e2e8f0)',
                  borderRadius: 10,
                  padding: '10px 12px',
                  background: 'var(--afcfta-bg, #fff)',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--afcfta-text, #0f172a)' }}>
                  {r.label}
                  {r.is_range && (
                    <span
                      style={{
                        marginLeft: 8,
                        fontSize: 10,
                        fontWeight: 500,
                        color: 'var(--afcfta-muted, #94a3b8)',
                        border: '1px solid var(--afcfta-border, #e2e8f0)',
                        borderRadius: 6,
                        padding: '1px 6px',
                      }}
                    >
                      {t.range}
                    </span>
                  )}
                </div>

                {r.see_also && (
                  <div style={{ fontSize: 13, color: 'var(--afcfta-muted, #94a3b8)', marginTop: 4 }}>
                    {t.seeAlso} « {r.see_also} »
                  </div>
                )}

                {r.codes && r.codes.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                    {r.codes.map((c) => (
                      <button
                        key={c.code}
                        type="button"
                        onClick={() => handleCode(c.code, r)}
                        title={
                          c.official_label
                            ? `${c.official_label} · ${t.chapter} ${c.chapter} — ${c.chapter_name}`
                            : `${t.chapter} ${c.chapter} — ${c.chapter_name}`
                        }
                        data-testid="product-hs-code"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '4px 9px',
                          borderRadius: 8,
                          border: '1px solid var(--afcfta-accent, #2563eb)',
                          background: copied === c.code ? 'var(--afcfta-accent, #2563eb)' : 'transparent',
                          color: copied === c.code ? '#fff' : 'var(--afcfta-accent, #2563eb)',
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: 'pointer',
                          fontVariantNumeric: 'tabular-nums',
                        }}
                      >
                        <span
                          style={{
                            fontSize: 9,
                            fontWeight: 700,
                            opacity: 0.7,
                          }}
                        >
                          {(LEVEL_BADGE[c.level] || LEVEL_BADGE.other)[uiLang] ||
                            LEVEL_BADGE.other.fr}
                        </span>
                        {copied === c.code ? t.copied : c.code}
                        {onSelect && copied !== c.code && <ArrowRight size={12} />}
                      </button>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
          <div style={{ fontSize: 11, color: 'var(--afcfta-muted, #94a3b8)', marginTop: 10 }}>
            {t.source}
          </div>
        </>
      )}
    </div>
  );
}
