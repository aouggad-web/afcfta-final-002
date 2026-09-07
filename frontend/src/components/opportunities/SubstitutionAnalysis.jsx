import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: '🔄 Analyse de substitution des importations',
    subtitle:
      'Identifier les produits importés hors Afrique qui pourraient être fournis par un partenaire africain sous ZLECAf.',
    intro:
      'Cette analyse compare les importations extra-africaines d’un pays avec les capacités de production réelles du continent, pour repérer des opportunités de substitution intra-africaine.',
    load: 'Lancer l’analyse',
    loading: 'Analyse en cours…',
    error: 'Erreur lors du chargement',
    empty: 'Aucune donnée de substitution disponible pour le moment.',
  },
  en: {
    title: '🔄 Import substitution analysis',
    subtitle:
      'Identify non-African imports that could be supplied by an African partner under AfCFTA.',
    intro:
      "This analysis compares a country's extra-African imports with the continent's real production capacity to spot intra-African substitution opportunities.",
    load: 'Run analysis',
    loading: 'Analyzing…',
    error: 'Error while loading',
    empty: 'No substitution data available yet.',
  },
};

export default function SubstitutionAnalysis({ language = 'fr' }) {
  const t = texts[language === 'en' ? 'en' : 'fr'];
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: res } = await axios.get(`${API}/opportunities/substitution`, {
        withCredentials: true,
      });
      setData(res);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">{t.title}</CardTitle>
        <p className="text-sm text-muted-foreground">{t.subtitle}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm">{t.intro}</p>
        <Button onClick={runAnalysis} disabled={loading}>
          {loading ? t.loading : t.load}
        </Button>
        {error && <p className="text-sm text-destructive">{t.error}: {error}</p>}
        {data && Array.isArray(data?.items) && data.items.length === 0 && (
          <p className="text-sm text-muted-foreground">{t.empty}</p>
        )}
        {data && Array.isArray(data?.items) && data.items.length > 0 && (
          <ul className="space-y-1 text-sm">
            {data.items.map((it, idx) => (
              <li key={it.hs_code || idx}>
                <span className="font-medium">{it.hs_code}</span> — {it.label || it.description}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
