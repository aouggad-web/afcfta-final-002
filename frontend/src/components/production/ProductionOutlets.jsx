/**
 * Débouchés — le chaînage « ce pays produit ceci, où le vendre »
 * ================================================================
 * Le module Production savait dire ce qu'un pays produit. Le module
 * Opportunités savait dire où vendre un produit. Rien ne reliait les deux :
 * il fallait relever un code SH d'un côté et le ressaisir de l'autre.
 *
 * Cet écran fait le pont. Il liste la production réelle du pays — FAOSTAT,
 * USGS, UNIDO — chaque ligne portant son code SH, et ouvre d'un clic la
 * recherche de marchés pour ce produit.
 *
 * DEUX PARTIS PRIS D'AFFICHAGE
 * -----------------------------
 * 1. Le rang continental n'est JAMAIS montré seul. « 1ᵉʳ producteur » ne veut
 *    rien dire si trois pays seulement sont couverts ; « 1ᵉʳ sur 3 pays
 *    couverts » se juge tout seul. Le dénominateur accompagne donc toujours
 *    le rang, et les réserves que le serveur attache à une commodité ou à une
 *    couverture sont rendues telles quelles.
 * 2. Rien n'est recalculé ici. Les valeurs, rangs et parts viennent du
 *    serveur ; cet écran les met en page, il ne les produit pas.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, ArrowRight, Loader2, PackageSearch } from 'lucide-react';

import EnhancedCountrySelector from './EnhancedCountrySelector';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const DATASET_LABEL_KEY = {
  agri: 'production.outlets.datasetAgri',
  mining: 'production.outlets.datasetMining',
  manufacturing: 'production.outlets.datasetManufacturing',
};

/**
 * Dépose l'intention dans sessionStorage puis navigue vers le module qui la
 * traite. Le canal existe déjà (module Statistiques) ; on le réutilise en
 * précisant l'intention « market » — perspective exportateur — car sans elle
 * le lecteur atterrirait sur l'écran du besoin national, qui répond à la
 * question inverse.
 */
export function handoffToMarkets({ iso3, hsCode }) {
  if (!hsCode) return false;
  try {
    sessionStorage.setItem(
      'zlecaf_opportunites_handoff',
      JSON.stringify({ country: iso3, hsCode: String(hsCode), mode: 'market', k: Date.now() }),
    );
  } catch {
    /* stockage indisponible : la navigation reste utile */
  }
  window.dispatchEvent(new CustomEvent('zlecaf:goto-tab', { detail: { tab: 'reports' } }));
  return true;
}

function ProductionOutlets({ language = 'fr' }) {
  const { t } = useTranslation();
  const [country, setCountry] = useState('KEN');
  const [profile, setProfile] = useState(null);
  const [status, setStatus] = useState('idle');

  // Les requêtes peuvent se croiser : choisir B pendant que A charge, et la
  // réponse de A — plus lente — écraserait le profil de B. Le tableau
  // afficherait alors les produits de A pendant que le bouton enverrait le
  // pays B. Une réponse dont le pays n'est plus celui sélectionné est donc
  // ignorée.
  const requestedCountry = useRef(null);

  const fetchProfile = useCallback(async (iso3) => {
    requestedCountry.current = iso3;
    setStatus('loading');
    try {
      const res = await axios.get(`${API}/production/country-profile/${iso3}?top_n=40`);
      if (requestedCountry.current !== iso3) return;
      setProfile(res.data || null);
      setStatus('ready');
    } catch {
      if (requestedCountry.current !== iso3) return;
      setProfile(null);
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    if (country) fetchProfile(country);
  }, [country, fetchProfile]);

  const products = profile?.products || [];

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-[var(--text)]">
          {t('production.outlets.title')}
        </h2>
        <p className="text-sm text-gray-400 max-w-3xl">{t('production.outlets.intro')}</p>
      </div>

      <EnhancedCountrySelector
        value={country}
        onChange={setCountry}
        language={language}
      />

      {status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-gray-400 py-6">
          <Loader2 className="w-4 h-4 animate-spin" />
          {t('production.outlets.loading')}
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-start gap-2 text-sm text-amber-500 py-6" role="status">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          {t('production.outlets.error')}
        </div>
      )}

      {status === 'ready' && !products.length && (
        <div className="flex items-start gap-2 text-sm text-gray-400 py-6" role="status">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          {t('production.outlets.empty')}
        </div>
      )}

      {status === 'ready' && products.length > 0 && (
        <>
          <p className="text-xs text-gray-500">
            {t('production.outlets.count', { count: products.length })}
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="outlets-table">
              <thead>
                <tr className="text-left text-xs uppercase text-gray-500 border-b border-[var(--afcfta-border)]">
                  <th className="py-2 pr-3">{t('production.outlets.colProduct')}</th>
                  <th className="py-2 pr-3">{t('production.outlets.colHs')}</th>
                  <th className="py-2 pr-3 text-right">{t('production.outlets.colOutput')}</th>
                  <th className="py-2 pr-3">{t('production.outlets.colRank')}</th>
                  <th className="py-2 pr-3">{t('production.outlets.colSource')}</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {products.map((p) => {
                  const caveat = p.coverage_caveat || p.commodity_caveat;
                  return (
                    <tr
                      key={`${p.dataset}-${p.hs_code}-${p.commodity}`}
                      className="border-b border-[var(--afcfta-border)] align-top"
                    >
                      <td className="py-2 pr-3 text-[var(--text)]">
                        {p.commodity}
                        {caveat && (
                          <div
                            className="flex items-start gap-1 mt-1 text-[11px] text-amber-500"
                            data-testid="outlets-caveat"
                          >
                            <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                            <span>{caveat}</span>
                          </div>
                        )}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs text-gray-400">{p.hs_code}</td>
                      <td className="py-2 pr-3 text-right tabular-nums text-[var(--text)]">
                        {typeof p.value === 'number' ? p.value.toLocaleString(language) : '—'}
                        <span className="text-gray-500 text-xs"> {p.unit}</span>
                      </td>
                      <td className="py-2 pr-3 text-xs text-gray-400">
                        {/* Jamais le rang seul : le dénominateur le rend jugeable. */}
                        {p.rank
                          ? t('production.outlets.rankOf', {
                              rank: p.rank,
                              total: p.total_countries,
                            })
                          : '—'}
                      </td>
                      <td className="py-2 pr-3 text-xs text-gray-500">
                        {p.institution}
                        {p.year ? ` ${p.year}` : ''}
                        {DATASET_LABEL_KEY[p.dataset] && (
                          <span className="ml-1 opacity-70">
                            ({t(DATASET_LABEL_KEY[p.dataset])})
                          </span>
                        )}
                      </td>
                      <td className="py-2">
                        <button
                          type="button"
                          onClick={() => handoffToMarkets({ iso3: country, hsCode: p.hs_code })}
                          data-testid={`outlets-go-${p.hs_code}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-[var(--gold)] hover:underline whitespace-nowrap"
                        >
                          <PackageSearch className="w-3.5 h-3.5" />
                          {t('production.outlets.findMarkets')}
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500">{t('production.outlets.footnote')}</p>
        </>
      )}
    </div>
  );
}

export default ProductionOutlets;
