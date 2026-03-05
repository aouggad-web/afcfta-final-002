import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { apiV2 } from '../../services/api-v2';
import { aiHelpers } from '../../utils/ai-helpers';

const SECTORS = ['Agriculture', 'Manufacturing', 'Technology', 'Energy', 'Infrastructure', 'Finance'];
const RISK_LEVELS = ['low', 'medium', 'high'];

const DEFAULT_PROFILE = {
  riskTolerance: 'medium',
  sectors: [],
  investmentSize: 1000000,
};

function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
    </div>
  );
}

function RecommendationCard({ rec, language }) {
  const riskLabel = aiHelpers.getRiskLabel(rec.riskLevel);
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-200">
      <div className="bg-gradient-to-r from-blue-700 to-indigo-700 px-4 py-3 text-white flex items-start justify-between gap-2">
        <div>
          <h3 className="font-bold text-base leading-tight">{rec.title || rec.opportunity}</h3>
          <p className="text-blue-200 text-xs mt-0.5">{rec.sector} · {rec.country}</p>
        </div>
        <Badge className="bg-white/20 text-white border-0 shrink-0 text-xs">
          {aiHelpers.formatConfidenceScore(rec.confidenceScore)}
        </Badge>
      </div>
      <CardContent className="p-4 space-y-3">
        <p className="text-sm text-gray-600 leading-relaxed">{rec.description}</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-green-50 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-500 mb-0.5">{language === 'fr' ? 'ROI Estimé' : 'Est. ROI'}</p>
            <p className="font-bold text-green-700 text-sm">{aiHelpers.formatROI(rec.roi)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-500 mb-0.5">{language === 'fr' ? 'Taille' : 'Size'}</p>
            <p className="font-bold text-gray-700 text-sm">{aiHelpers.formatInvestmentSize(rec.investmentSize)}</p>
          </div>
        </div>
        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${riskLabel.color}`}>
          {language === 'fr' ? riskLabel.fr : riskLabel.en}
        </div>
        {rec.advantages?.length > 0 && (
          <ul className="space-y-1">
            {rec.advantages.map((adv, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                <span className="text-green-500 mt-0.5">✓</span>
                {adv}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default function AIRecommendations({ language = 'fr' }) {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fetched, setFetched] = useState(false);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiV2.getAIRecommendations(profile);
      setRecommendations(data.recommendations || data || []);
      setFetched(true);
    } catch (err) {
      console.error('[AIRecommendations]', err);
      setError(language === 'fr' ? 'Impossible de charger les recommandations.' : 'Failed to load recommendations.');
    } finally {
      setLoading(false);
    }
  }, [profile, language]);

  const toggleSector = (sector) => {
    setProfile((p) => ({
      ...p,
      sectors: p.sectors.includes(sector)
        ? p.sectors.filter((s) => s !== sector)
        : [...p.sectors, sector],
    }));
  };

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-r from-indigo-700 via-blue-700 to-blue-800 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            🤖 {language === 'fr' ? 'Recommandations IA' : 'AI Recommendations'}
          </CardTitle>
          <CardDescription className="text-blue-200">
            {language === 'fr'
              ? 'Personnalisez votre profil pour obtenir des recommandations adaptées'
              : 'Customize your profile to get tailored recommendations'}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Profile Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {language === 'fr' ? 'Votre Profil Investisseur' : 'Your Investor Profile'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Risk Tolerance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Tolérance au Risque' : 'Risk Tolerance'}
            </label>
            <div className="flex gap-2 flex-wrap">
              {RISK_LEVELS.map((level) => (
                <button
                  key={level}
                  onClick={() => setProfile((p) => ({ ...p, riskTolerance: level }))}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                    profile.riskTolerance === level
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {language === 'fr'
                    ? { low: 'Faible', medium: 'Moyen', high: 'Élevé' }[level]
                    : { low: 'Low', medium: 'Medium', high: 'High' }[level]}
                </button>
              ))}
            </div>
          </div>

          {/* Sectors */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Secteurs Préférés' : 'Preferred Sectors'}
            </label>
            <div className="flex gap-2 flex-wrap">
              {SECTORS.map((sector) => (
                <button
                  key={sector}
                  onClick={() => toggleSector(sector)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                    profile.sectors.includes(sector)
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'
                  }`}
                >
                  {sector}
                </button>
              ))}
            </div>
          </div>

          {/* Investment Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Taille d\'Investissement' : 'Investment Size'}:{' '}
              <span className="font-bold text-blue-700">{aiHelpers.formatInvestmentSize(profile.investmentSize)}</span>
            </label>
            <input
              type="range"
              min={100000}
              max={100000000}
              step={100000}
              value={profile.investmentSize}
              onChange={(e) => setProfile((p) => ({ ...p, investmentSize: Number(e.target.value) }))}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>$100K</span><span>$100M</span>
            </div>
          </div>

          <Button
            onClick={fetchRecommendations}
            disabled={loading}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            {loading
              ? (language === 'fr' ? 'Analyse en cours...' : 'Analyzing...')
              : (language === 'fr' ? 'Obtenir mes Recommandations' : 'Get My Recommendations')}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && <Spinner />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {!loading && fetched && recommendations.length === 0 && (
        <div className="text-center py-10 text-gray-400">
          {language === 'fr' ? 'Aucune recommandation trouvée.' : 'No recommendations found.'}
        </div>
      )}

      {!loading && recommendations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {recommendations.map((rec, i) => (
            <RecommendationCard key={rec.id || i} rec={rec} language={language} />
          ))}
        </div>
      )}
    </div>
  );
}
