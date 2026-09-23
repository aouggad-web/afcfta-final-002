import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Ship, TrendingUp, Globe, Loader2 } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function UNCTADDataPanel({ language = 'fr' }) {
  const [portData, setPortData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const texts = {
    fr: {
      title: "Statistiques UNCTAD",
      subtitle: "Données officielles - UNCTAD Maritime Transport Review 2024",
      totalThroughput: "Trafic Total",
      growth: "Croissance 2023-2024",
      globalShare: "Part du Commerce Mondial",
      mTeu: "M TEU",
      loading: "Chargement des données UNCTAD...",
      error: "Erreur lors du chargement des données",
      source: "Source: UNCTAD - Review of Maritime Transport 2024"
    },
    en: {
      title: "UNCTAD Statistics",
      subtitle: "Official data - UNCTAD Maritime Transport Review 2024",
      totalThroughput: "Total Throughput",
      growth: "Growth 2023-2024",
      globalShare: "Global Trade Share",
      mTeu: "M TEU",
      loading: "Loading UNCTAD data...",
      error: "Error loading data",
      source: "Source: UNCTAD - Review of Maritime Transport 2024"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchUNCTADData();
  }, []);

  const fetchUNCTADData = async () => {
    setLoading(true);
    setError(null);
    try {
      const portsRes = await axios.get(`${API}/statistics/unctad/ports`);
      setPortData(portsRes.data);
    } catch (err) {
      console.error('Error fetching UNCTAD data:', err);
      setError(t.error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardContent className="flex items-center justify-center h-48">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-[var(--info)] mx-auto" />
            <p className="mt-4 text-[var(--afcfta-muted)]">{t.loading}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-l-4 border-l-red-500">
        <CardContent className="py-8 text-center text-[var(--danger)]">
          {error}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="unctad-panel">
      {/* Header */}
      <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] text-[var(--text)] shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            <Ship className="w-7 h-7" />
            {t.title}
          </CardTitle>
          <CardDescription className="text-[var(--atlantic)] text-base">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Key Metrics */}
      {portData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-cyan-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[var(--info)] text-sm">{t.totalThroughput}</p>
                  <p className="text-3xl font-bold">
                    {(portData.total_african_port_throughput_teu_2024 / 1000000).toFixed(1)} {t.mTeu}
                  </p>
                </div>
                <Ship className="w-10 h-10 text-[var(--info)]" />
              </div>
              <p className="text-xs text-[var(--info)] mt-2">2024</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[var(--success)] text-sm">{t.growth}</p>
                  <p className="text-3xl font-bold">+{portData.growth_rate_2023_2024}%</p>
                </div>
                <TrendingUp className="w-10 h-10 text-[var(--success)]" />
              </div>
              <p className="text-xs text-[var(--success)] mt-2">YoY</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-violet-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[var(--violet)] text-sm">{t.globalShare}</p>
                  <p className="text-3xl font-bold">{portData.share_global_trade}%</p>
                </div>
                <Globe className="w-10 h-10 text-[var(--violet)]" />
              </div>
              <p className="text-xs text-[var(--violet)] mt-2">{language === 'en' ? 'World Trade' : 'Commerce Mondial'}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Source Footer */}
      <Card className="bg-[var(--afcfta-card2)] border-[var(--afcfta-border)]">
        <CardContent className="py-3">
          <p className="text-xs text-[var(--afcfta-muted)] text-center">
            {t.source}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
