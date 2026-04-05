import React, { useState, useEffect, useMemo } from 'react';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  ExternalLink,
  RefreshCw,
  Globe,
  Newspaper,
  Clock,
  MapPin,
  Tag,
  Sparkles,
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const REGION_ACCENTS = {
  'Afrique du Nord': '#4f8ef7',
  "Afrique de l'Ouest": '#20c997',
  'Afrique Centrale': '#d4a017',
  "Afrique de l'Est": '#e67e22',
  'Afrique Australe': '#9b6ef5',
  Afrique: '#9aa7b8',
};

const CATEGORY_ACCENTS = {
  Finance: { icon: '💰', accent: '#20c997' },
  Commerce: { icon: '🚢', accent: '#4f8ef7' },
  Énergie: { icon: '⚡', accent: '#d4a017' },
  Agriculture: { icon: '🌾', accent: '#66bb6a' },
  Mines: { icon: '⛏️', accent: '#d4891a' },
  Télécoms: { icon: '📱', accent: '#7c83fd' },
  Infrastructure: { icon: '🏗️', accent: '#94a3b8' },
  Gouvernance: { icon: '🏛️', accent: '#ef4444' },
  Économie: { icon: '📊', accent: '#38bdf8' },
};

const translations = {
  fr: {
    title: "Fil d'Actualités Économiques Africaines",
    subtitle: 'Sources: AllAfrica, Google News (Reuters, AFP)',
    lastUpdate: 'Dernière mise à jour',
    refresh: 'Actualiser',
    refreshing: 'Actualisation...',
    byRegion: 'Par Région',
    byCategory: 'Par Catégorie',
    allNews: 'Toutes les Actualités',
    readMore: "Lire l'article",
    articles: 'articles',
    noArticles: 'Aucun article disponible',
    loading: 'Chargement des actualités...',
    error: 'Erreur de chargement',
    source: 'Source',
    today: "Aujourd'hui",
    yesterday: 'Hier',
    daysAgo: 'il y a {days} jours',
    strategicHeadline: 'Lecture stratégique du flux économique africain',
    strategicLead: 'Surveillance des signaux commerce, finance, énergie, infrastructures et chaînes d'approvisionnement.',
    footer:
      'Actualités agrégées depuis Agence Ecofin, AllAfrica et flux associés. Les articles complets restent consultables sur les sites sources.',
  },
  en: {
    title: 'African Economic News Feed',
    subtitle: 'Sources: AllAfrica, Google News (Reuters, AFP)',
    lastUpdate: 'Last update',
    refresh: 'Refresh',
    refreshing: 'Refreshing...',
    byRegion: 'By Region',
    byCategory: 'By Category',
    allNews: 'All News',
    readMore: 'Read article',
    articles: 'articles',
    noArticles: 'No articles available',
    loading: 'Loading news...',
    error: 'Loading error',
    source: 'Source',
    today: 'Today',
    yesterday: 'Yesterday',
    daysAgo: '{days} days ago',
    strategicHeadline: 'Strategic reading of the African economic feed',
    strategicLead: 'Monitoring trade, finance, energy, infrastructure and supply-chain signals.',
    footer:
      'News aggregated from Agence Ecofin, AllAfrica and related feeds. Full articles remain available on source websites.',
  },
};

const formatRelativeDate = (dateString, t) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return t.today;
  if (diffDays === 1) return t.yesterday;
  return t.daysAgo.replace('{days}', diffDays);
};

const ArticleCard = ({ article, t, featured = false }) => {
  const regionAccent = REGION_ACCENTS[article.region] || REGION_ACCENTS.Afrique;
  const categoryStyle = CATEGORY_ACCENTS[article.category] || CATEGORY_ACCENTS.Économie;

  return (
    <article
      className={`rounded-2xl border p-4 ${featured ? 'md:p-5' : ''}`}
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015))',
        borderColor: 'rgba(255,255,255,0.06)',
        boxShadow: featured ? '0 16px 34px rgba(0,0,0,0.18)' : 'none',
      }}
    >
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <Badge
          className="border"
          style={{
            background: `${categoryStyle.accent}18`,
            color: categoryStyle.accent,
            borderColor: `${categoryStyle.accent}40`,
          }}
        >
          {categoryStyle.icon} {article.category}
        </Badge>

        <Badge
          variant="outline"
          className="border"
          style={{
            background: 'rgba(255,255,255,0.03)',
            color: 'var(--text)',
            borderColor: `${regionAccent}50`,
          }}
        >
          <MapPin className="w-3 h-3 mr-1" />
          {article.region}
        </Badge>
      </div>

      <h3
        className={`font-semibold text-[var(--text)] leading-snug mb-2 ${
          featured ? 'text-lg md:text-xl' : 'text-base'
        }`}
      >
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:opacity-90"
        >
          {article.title}
        </a>
      </h3>

      <p className={`text-[var(--afcfta-muted)] mb-4 ${featured ? 'text-sm md:text-base' : 'text-sm'} line-clamp-3`}>
        {article.summary}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--afcfta-muted)]">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1">
            <Newspaper className="w-3.5 h-3.5" />
            {article.source}
          </span>

          <span className="inline-flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {formatRelativeDate(article.published_at, t)}
          </span>
        </div>

        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-medium"
          style={{ color: categoryStyle.accent }}
        >
          {t.readMore}
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </article>
  );
};

const RegionSection = ({ region, articles, t }) => {
  const accent = REGION_ACCENTS[region] || REGION_ACCENTS.Afrique;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold"
          style={{
            background: `${accent}18`,
            color: accent,
            border: `1px solid ${accent}40`,
          }}
        >
          <Globe className="w-4 h-4" />
          {region}
        </div>

        <span className="text-xs text-[var(--afcfta-muted)]">
          {articles.length} {t.articles}
        </span>
      </div>

      <div className="grid gap-3">
        {articles.slice(0, 5).map((article) => (
          <ArticleCard key={article.id} article={article} t={t} />
        ))}
      </div>
    </section>
  );
};

const CategorySection = ({ category, articles, t }) => {
  const categoryStyle = CATEGORY_ACCENTS[category] || CATEGORY_ACCENTS.Économie;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold"
          style={{
            background: `${categoryStyle.accent}18`,
            color: categoryStyle.accent,
            border: `1px solid ${categoryStyle.accent}40`,
          }}
        >
          <span>{categoryStyle.icon}</span>
          {category}
        </div>

        <span className="text-xs text-[var(--afcfta-muted)]">
          {articles.length} {t.articles}
        </span>
      </div>

      <div className="grid gap-3">
        {articles.slice(0, 5).map((article) => (
          <ArticleCard key={article.id} article={article} t={t} />
        ))}
      </div>
    </section>
  );
};

const NewsDashboard = ({ language = 'fr' }) => {
  const [news, setNews] = useState({ articles: [], by_region: {}, by_category: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const t = translations[language] || translations.fr;

  const featuredArticles = useMemo(() => news.articles.slice(0, 3), [news.articles]);
  const remainingArticles = useMemo(() => news.articles.slice(3, 15), [news.articles]);

  const fetchNews = async (forceRefresh = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);

      const [allNews, byRegion, byCategory] = await Promise.all([
        fetch(`${API}/news?force_refresh=${forceRefresh}`).then((r) => r.json()),
        fetch(`${API}/news/by-region?force_refresh=${forceRefresh}`).then((r) => r.json()),
        fetch(`${API}/news/by-category?force_refresh=${forceRefresh}`).then((r) => r.json()),
      ]);

      setNews({
        articles: allNews.articles || [],
        by_region: byRegion.articles_by_region || {},
        by_category: byCategory.articles_by_category || {},
      });
      setLastUpdate(allNews.last_update);
      setError(null);
    } catch (err) {
      console.error('Error fetching news:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const handleRefresh = () => {
    fetchNews(true);
  };

  if (loading) {
    return (
      <div
        className="rounded-2xl border py-20"
        style={{
          background: 'rgba(255,255,255,0.025)',
          borderColor: 'rgba(255,255,255,0.06)',
        }}
      >
        <div className="flex flex-col items-center justify-center gap-4">
          <RefreshCw className="w-10 h-10 text-[var(--gold)] animate-spin" />
          <p className="text-[var(--afcfta-muted)]">{t.loading}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="rounded-2xl border p-8"
        style={{
          background: 'rgba(255,255,255,0.025)',
          borderColor: 'rgba(239,68,68,0.25)',
        }}
      >
        <div className="text-center text-red-400">
          <p>
            {t.error}: {error}
          </p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 rounded-lg text-sm font-medium"
            style={{
              background: 'rgba(239,68,68,0.12)',
              border: '1px solid rgba(239,68,68,0.22)',
            }}
          >
            {t.refresh}
          </button>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-4">
      <div
        className="rounded-2xl border overflow-hidden"
        style={{
          background:
            'radial-gradient(900px 240px at 0% 0%, rgba(212,137,26,0.10), transparent 55%), radial-gradient(720px 220px at 100% 0%, rgba(79,142,247,0.08), transparent 60%), linear-gradient(135deg, rgba(18,26,40,0.98), rgba(12,18,25,0.98))',
          borderColor: 'rgba(212,137,26,0.14)',
        }}
      >
        <div className="p-5 md:p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide font-bold text-[var(--gold)] mb-3">
                <Sparkles className="w-4 h-4" />
                intelligence feed
              </div>

              <h3 className="text-2xl md:text-3xl font-bold text-[var(--text)]">
                {t.title}
              </h3>

              <p className="mt-2 text-sm md:text-base text-[rgba(234,224,208,0.9)]">
                {t.strategicHeadline}
              </p>

              <p className="mt-2 text-sm text-[var(--afcfta-muted)]">
                {t.strategicLead}
              </p>

              <p className="mt-3 text-xs text-[var(--afcfta-muted)]">
                {t.subtitle} • {news.articles.length} {t.articles}
              </p>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {lastUpdate && (
                <div className="text-xs md:text-sm text-[var(--afcfta-muted)] inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-[rgba(255,255,255,0.05)]">
                  <Clock className="w-4 h-4" />
                  {t.lastUpdate}: {new Date(lastUpdate).toLocaleString(language === 'fr' ? 'fr-FR' : 'en-US')}
                </div>
              )}

              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-50 text-sm font-medium"
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  color: 'var(--text)',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? t.refreshing : t.refresh}
              </button>
            </div>
          </div>
        </div>
      </div>

      {featuredArticles.length > 0 && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {featuredArticles.map((article, index) => (
            <ArticleCard key={article.id || index} article={article} t={t} featured />
          ))}
        </div>
      )}

      <div
        className="rounded-2xl border p-4 md:p-5"
        style={{
          background: 'rgba(255,255,255,0.025)',
          borderColor: 'rgba(255,255,255,0.06)',
        }}
      >
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3 mb-5">
            <TabsTrigger value="all" className="flex items-center gap-2">
              <Newspaper className="w-4 h-4" />
              {t.allNews}
            </TabsTrigger>
            <TabsTrigger value="region" className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {t.byRegion}
            </TabsTrigger>
            <TabsTrigger value="category" className="flex items-center gap-2">
              <Tag className="w-4 h-4" />
              {t.byCategory}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            {news.articles.length === 0 ? (
              <p className="text-center text-[var(--afcfta-muted)] py-10">{t.noArticles}</p>
            ) : (
              <div className="grid gap-4">
                {remainingArticles.map((article) => (
                  <ArticleCard key={article.id} article={article} t={t} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="region">
            {Object.keys(news.by_region).length === 0 ? (
              <p className="text-center text-[var(--afcfta-muted)] py-10">{t.noArticles}</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {Object.entries(news.by_region).map(([region, articles]) => (
                  <RegionSection key={region} region={region} articles={articles} t={t} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="category">
            {Object.keys(news.by_category).length === 0 ? (
              <p className="text-center text-[var(--afcfta-muted)] py-10">{t.noArticles}</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {Object.entries(news.by_category).map(([category, articles]) => (
                  <CategorySection key={category} category={category} articles={articles} t={t} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      <div className="text-center text-xs text-[var(--afcfta-muted)] py-1">
        📰 {t.footer}
      </div>
    </section>
  );
};

export default NewsDashboard;
