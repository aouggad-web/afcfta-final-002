import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ExternalLink, RefreshCw, Globe, TrendingUp, Newspaper, Clock, MapPin, Tag } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Couleurs par région
const REGION_COLORS = {
  "Afrique du Nord": { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-700", badge: "bg-blue-100 text-blue-800" },
  "Afrique de l'Ouest": { bg: "bg-green-50", border: "border-green-300", text: "text-green-700", badge: "bg-green-100 text-green-800" },
  "Afrique Centrale": { bg: "bg-yellow-50", border: "border-yellow-300", text: "text-yellow-700", badge: "bg-yellow-100 text-yellow-800" },
  "Afrique de l'Est": { bg: "bg-orange-50", border: "border-orange-300", text: "text-orange-700", badge: "bg-orange-100 text-orange-800" },
  "Afrique Australe": { bg: "bg-purple-50", border: "border-purple-300", text: "text-purple-700", badge: "bg-purple-100 text-purple-800" },
  "Afrique": { bg: "bg-gray-50", border: "border-gray-300", text: "text-gray-700", badge: "bg-gray-100 text-gray-800" }
};

// Couleurs par catégorie
const CATEGORY_COLORS = {
  "Finance": { icon: "💰", color: "bg-emerald-100 text-emerald-800" },
  "Commerce": { icon: "🚢", color: "bg-blue-100 text-blue-800" },
  "Énergie": { icon: "⚡", color: "bg-yellow-100 text-yellow-800" },
  "Agriculture": { icon: "🌾", color: "bg-lime-100 text-lime-800" },
  "Mines": { icon: "⛏️", color: "bg-amber-100 text-amber-800" },
  "Télécoms": { icon: "📱", color: "bg-indigo-100 text-indigo-800" },
  "Infrastructure": { icon: "🏗️", color: "bg-slate-100 text-slate-800" },
  "Gouvernance": { icon: "🏛️", color: "bg-red-100 text-red-800" },
  "Économie": { icon: "📊", color: "bg-cyan-100 text-cyan-800" }
};

// Traductions
const translations = {
  fr: {
    title: "Fil d'Actualités Économiques Africaines",
    subtitle: "Sources: AllAfrica, Google News (Reuters, AFP)",
    lastUpdate: "Dernière mise à jour",
    refresh: "Actualiser",
    refreshing: "Actualisation...",
    byRegion: "Par Région",
    byCategory: "Par Catégorie",
    allNews: "Toutes les Actualités",
    readMore: "Lire l'article",
    articles: "articles",
    noArticles: "Aucun article disponible",
    loading: "Chargement des actualités...",
    error: "Erreur de chargement",
    source: "Source",
    today: "Aujourd'hui",
    yesterday: "Hier",
    daysAgo: "il y a {days} jours"
  },
  en: {
    title: "African Economic News Feed",
    subtitle: "Sources: AllAfrica, Google News (Reuters, AFP)",
    lastUpdate: "Last update",
    refresh: "Refresh",
    refreshing: "Refreshing...",
    byRegion: "By Region",
    byCategory: "By Category",
    allNews: "All News",
    readMore: "Read article",
    articles: "articles",
    noArticles: "No articles available",
    loading: "Loading news...",
    error: "Loading error",
    source: "Source",
    today: "Today",
    yesterday: "Yesterday",
    daysAgo: "{days} days ago"
  }
};

// Formater la date relative
const formatRelativeDate = (dateString, t) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return t.today;
  if (diffDays === 1) return t.yesterday;
  return t.daysAgo.replace('{days}', diffDays);
};

// Composant Article
const NewsArticle = ({ article, t }) => {
  const regionStyle = REGION_COLORS[article.region] || REGION_COLORS["Afrique"];
  const categoryStyle = CATEGORY_COLORS[article.category] || CATEGORY_COLORS["Économie"];
  
  return (
    <div className={`p-4 rounded-lg border-l-4 ${regionStyle.bg} ${regionStyle.border} hover:shadow-md transition-all duration-200`}>
      <div className="flex flex-wrap gap-2 mb-2">
        <Badge className={categoryStyle.color}>
          {categoryStyle.icon} {article.category}
        </Badge>
        <Badge variant="outline" className={regionStyle.badge}>
          <MapPin className="w-3 h-3 mr-1" />
          {article.region}
        </Badge>
      </div>
      
      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600">
        <a href={article.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
          {article.title}
        </a>
      </h3>
      
      <p className="text-sm text-gray-600 mb-3 line-clamp-3">
        {article.summary}
      </p>
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Newspaper className="w-3 h-3" />
            {article.source}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatRelativeDate(article.published_at, t)}
          </span>
        </div>
        
        <a 
          href={article.link} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium"
        >
          {t.readMore}
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
};

// Composant Section par Région
const RegionSection = ({ region, articles, t }) => {
  const regionStyle = REGION_COLORS[region] || REGION_COLORS["Afrique"];
  
  return (
    <div className="mb-6">
      <div className={`flex items-center gap-2 mb-3 pb-2 border-b-2 ${regionStyle.border}`}>
        <Globe className={`w-5 h-5 ${regionStyle.text}`} />
        <h3 className={`font-bold text-lg ${regionStyle.text}`}>{region}</h3>
        <Badge variant="secondary" className="ml-2">{articles.length} {t.articles}</Badge>
      </div>
      
      <div className="grid gap-3">
        {articles.slice(0, 5).map((article) => (
          <NewsArticle key={article.id} article={article} t={t} />
        ))}
      </div>
    </div>
  );
};

// Composant Section par Catégorie
const CategorySection = ({ category, articles, t }) => {
  const categoryStyle = CATEGORY_COLORS[category] || CATEGORY_COLORS["Économie"];
  
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b-2 border-gray-200">
        <span className="text-xl">{categoryStyle.icon}</span>
        <h3 className="font-bold text-lg text-gray-800">{category}</h3>
        <Badge variant="secondary" className="ml-2">{articles.length} {t.articles}</Badge>
      </div>
      
      <div className="grid gap-3">
        {articles.slice(0, 5).map((article) => (
          <NewsArticle key={article.id} article={article} t={t} />
        ))}
      </div>
    </div>
  );
};

// Composant Principal
const NewsDashboard = ({ language = 'fr' }) => {
  const [news, setNews] = useState({ articles: [], by_region: {}, by_category: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  
  const t = translations[language] || translations.fr;

  const fetchNews = async (forceRefresh = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);
      
      // Fetch all endpoints in parallel
      const [allNews, byRegion, byCategory] = await Promise.all([
        fetch(`${API}/news?force_refresh=${forceRefresh}`).then(r => r.json()),
        fetch(`${API}/news/by-region?force_refresh=${forceRefresh}`).then(r => r.json()),
        fetch(`${API}/news/by-category?force_refresh=${forceRefresh}`).then(r => r.json())
      ]);
      
      setNews({
        articles: allNews.articles || [],
        by_region: byRegion.articles_by_region || {},
        by_category: byCategory.articles_by_category || {}
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
      <Card className="shadow-lg">
        <CardContent className="py-20">
          <div className="flex flex-col items-center justify-center gap-4">
            <RefreshCw className="w-10 h-10 text-blue-500 animate-spin" />
            <p className="text-gray-500">{t.loading}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="shadow-lg border-red-200">
        <CardContent className="py-10">
          <div className="text-center text-red-500">
            <p>{t.error}: {error}</p>
            <button 
              onClick={handleRefresh}
              className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
            >
              {t.refresh}
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* En-tête */}
      <Card className="shadow-lg bg-gradient-to-r from-green-600 via-yellow-500 to-red-500">
        <CardHeader className="text-white">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Newspaper className="w-7 h-7" />
                {t.title}
              </CardTitle>
              <CardDescription className="text-white/80 mt-1">
                {t.subtitle} • {news.articles.length} {t.articles}
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-4">
              {lastUpdate && (
                <div className="text-sm text-white/80">
                  <Clock className="w-4 h-4 inline mr-1" />
                  {t.lastUpdate}: {new Date(lastUpdate).toLocaleString(language === 'fr' ? 'fr-FR' : 'en-US')}
                </div>
              )}
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? t.refreshing : t.refresh}
              </button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Onglets */}
      <Card className="shadow-lg">
        <CardContent className="pt-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 mb-4">
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

            {/* Toutes les actualités */}
            <TabsContent value="all">
              {news.articles.length === 0 ? (
                <p className="text-center text-gray-500 py-10">{t.noArticles}</p>
              ) : (
                <div className="grid gap-4">
                  {news.articles.slice(0, 20).map((article) => (
                    <NewsArticle key={article.id} article={article} t={t} />
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Par Région */}
            <TabsContent value="region">
              {Object.keys(news.by_region).length === 0 ? (
                <p className="text-center text-gray-500 py-10">{t.noArticles}</p>
              ) : (
                <div className="grid md:grid-cols-2 gap-6">
                  {Object.entries(news.by_region).map(([region, articles]) => (
                    <RegionSection key={region} region={region} articles={articles} t={t} />
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Par Catégorie */}
            <TabsContent value="category">
              {Object.keys(news.by_category).length === 0 ? (
                <p className="text-center text-gray-500 py-10">{t.noArticles}</p>
              ) : (
                <div className="grid md:grid-cols-2 gap-6">
                  {Object.entries(news.by_category).map(([category, articles]) => (
                    <CategorySection key={category} category={category} articles={articles} t={t} />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Footer avec attribution */}
      <div className="text-center text-xs text-gray-500 py-2">
        📰 Actualités agrégées depuis Agence Ecofin et AllAfrica. 
        Les articles complets sont disponibles sur les sites sources. 
        Cliquez sur "Lire l'article" pour accéder au contenu original.
      </div>
    </div>
  );
};

export default NewsDashboard;
