import axios from 'axios';

/**
 * Client API "v2" pour le module réglementaire (RegulatoryComplianceTab,
 * RegulatoryQAPanel). Chaque méthode interroge le backend et renvoie
 * `response.data`. La base URL suit la convention du reste de l'app
 * (VITE_BACKEND_URL, requêtes relatives /api par défaut).
 */
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API,
  withCredentials: true,
});

async function get(path, params) {
  const { data } = await client.get(path, params ? { params } : undefined);
  return data;
}

export const regulatoryApi = {
  /** Pays supportés par le module de conformité réglementaire. */
  getSupportedCountries: () => get('/regulatory/countries'),

  /** Conformité réglementaire détaillée pour un pays (ISO3). */
  getCountryCompliance: (iso3) => get(`/regulatory/compliance/${iso3}`),

  /** Pays présents dans le registre maître réglementaire. */
  getMasterRegistryCountries: () => get('/regulatory/master-registry/countries'),

  /** Contradictions détectées par le contrôle qualité (QA). */
  getQAContradictions: () => get('/regulatory/qa/contradictions'),

  /** Rapport de couverture du contrôle qualité. */
  getQACoverageReport: () => get('/regulatory/qa/coverage'),

  /** Pays dont les données réglementaires sont périmées. */
  getQAStaleCountries: () => get('/regulatory/qa/stale-countries'),
};

export default regulatoryApi;
