import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Search, X, Package, ChevronDown, ChevronRight, Loader2, 
  Filter, List, Grid, FileText, Globe, Info
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: "Codes SH6 - Système Harmonisé",
    searchPlaceholder: "Rechercher un produit ou code HS...",
    chapters: "Chapitres",
    allChapters: "Tous les chapitres",
    results: "résultats",
    noResults: "Aucun résultat pour",
    loading: "Chargement...",
    selectCode: "Sélectionner",
    selectedCode: "Code sélectionné",
    clearSelection: "Effacer",
    browseByChapter: "Parcourir par chapitre",
    topChapters: "Chapitres principaux",
    recentSearches: "Recherches récentes",
    searchTab: "Recherche",
    browseTab: "Navigation",
    hierarchyTab: "Hiérarchie",
    codesInChapter: "codes dans ce chapitre",
    selectChapter: "Sélectionner un chapitre",
    rulesOfOrigin: "Règles d'origine",
    ruleType: "Type de règle",
    requirement: "Exigence",
    regionalContent: "Contenu régional",
    viewRules: "Voir les règles",
    section: "Section",
    chapter: "Chapitre",
    position: "Position",
    subPosition: "Sous-position"
  },
  en: {
    title: "HS6 Codes - Harmonized System",
    searchPlaceholder: "Search product or HS code...",
    chapters: "Chapters",
    allChapters: "All chapters",
    results: "results",
    noResults: "No results for",
    loading: "Loading...",
    selectCode: "Select",
    selectedCode: "Selected code",
    clearSelection: "Clear",
    browseByChapter: "Browse by chapter",
    topChapters: "Main chapters",
    recentSearches: "Recent searches",
    searchTab: "Search",
    browseTab: "Browse",
    hierarchyTab: "Hierarchy",
    codesInChapter: "codes in this chapter",
    selectChapter: "Select a chapter",
    rulesOfOrigin: "Rules of origin",
    ruleType: "Rule type",
    requirement: "Requirement",
    regionalContent: "Regional content",
    viewRules: "View rules",
    section: "Section",
    chapter: "Chapter",
    position: "Position",
    subPosition: "Sub-position"
  }
};

// Sections HS pour affichage hiérarchique
const HS_SECTIONS = {
  fr: [
    { id: 'I', chapters: ['01', '02', '03', '04', '05'], name: "Animaux vivants et produits du règne animal" },
    { id: 'II', chapters: ['06', '07', '08', '09', '10', '11', '12', '13', '14'], name: "Produits du règne végétal" },
    { id: 'III', chapters: ['15'], name: "Graisses et huiles" },
    { id: 'IV', chapters: ['16', '17', '18', '19', '20', '21', '22', '23', '24'], name: "Produits alimentaires" },
    { id: 'V', chapters: ['25', '26', '27'], name: "Produits minéraux" },
    { id: 'VI', chapters: ['28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38'], name: "Produits chimiques" },
    { id: 'VII', chapters: ['39', '40'], name: "Matières plastiques et caoutchouc" },
    { id: 'VIII', chapters: ['41', '42', '43'], name: "Peaux, cuirs, pelleteries" },
    { id: 'IX', chapters: ['44', '45', '46'], name: "Bois et ouvrages en bois" },
    { id: 'X', chapters: ['47', '48', '49'], name: "Pâtes de bois, papier" },
    { id: 'XI', chapters: ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63'], name: "Matières textiles" },
    { id: 'XII', chapters: ['64', '65', '66', '67'], name: "Chaussures, coiffures" },
    { id: 'XIII', chapters: ['68', '69', '70'], name: "Ouvrages en pierres, céramiques, verre" },
    { id: 'XIV', chapters: ['71'], name: "Perles, pierres et métaux précieux" },
    { id: 'XV', chapters: ['72', '73', '74', '75', '76', '78', '79', '80', '81', '82', '83'], name: "Métaux communs" },
    { id: 'XVI', chapters: ['84', '85'], name: "Machines et appareils" },
    { id: 'XVII', chapters: ['86', '87', '88', '89'], name: "Matériel de transport" },
    { id: 'XVIII', chapters: ['90', '91', '92'], name: "Instruments et appareils" },
    { id: 'XIX', chapters: ['93'], name: "Armes et munitions" },
    { id: 'XX', chapters: ['94', '95', '96'], name: "Marchandises et produits divers" },
    { id: 'XXI', chapters: ['97', '99'], name: "Objets d'art, de collection" }
  ],
  en: [
    { id: 'I', chapters: ['01', '02', '03', '04', '05'], name: "Live animals and animal products" },
    { id: 'II', chapters: ['06', '07', '08', '09', '10', '11', '12', '13', '14'], name: "Vegetable products" },
    { id: 'III', chapters: ['15'], name: "Fats and oils" },
    { id: 'IV', chapters: ['16', '17', '18', '19', '20', '21', '22', '23', '24'], name: "Food products" },
    { id: 'V', chapters: ['25', '26', '27'], name: "Mineral products" },
    { id: 'VI', chapters: ['28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38'], name: "Chemical products" },
    { id: 'VII', chapters: ['39', '40'], name: "Plastics and rubber" },
    { id: 'VIII', chapters: ['41', '42', '43'], name: "Hides, leather, furskins" },
    { id: 'IX', chapters: ['44', '45', '46'], name: "Wood and articles of wood" },
    { id: 'X', chapters: ['47', '48', '49'], name: "Pulp, paper" },
    { id: 'XI', chapters: ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63'], name: "Textiles" },
    { id: 'XII', chapters: ['64', '65', '66', '67'], name: "Footwear, headgear" },
    { id: 'XIII', chapters: ['68', '69', '70'], name: "Articles of stone, ceramics, glass" },
    { id: 'XIV', chapters: ['71'], name: "Pearls, precious stones and metals" },
    { id: 'XV', chapters: ['72', '73', '74', '75', '76', '78', '79', '80', '81', '82', '83'], name: "Base metals" },
    { id: 'XVI', chapters: ['84', '85'], name: "Machinery and equipment" },
    { id: 'XVII', chapters: ['86', '87', '88', '89'], name: "Transport equipment" },
    { id: 'XVIII', chapters: ['90', '91', '92'], name: "Instruments and apparatus" },
    { id: 'XIX', chapters: ['93'], name: "Arms and ammunition" },
    { id: 'XX', chapters: ['94', '95', '96'], name: "Miscellaneous manufactured articles" },
    { id: 'XXI', chapters: ['97', '99'], name: "Works of art, collectors' pieces" }
  ]
};

// ============================================================================
// Composant de recherche rapide (inline) - Pour intégration dans formulaires
// ============================================================================
export function HSCodeSearch({ value, onChange, language = 'fr', placeholder, showRules = false, className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  
  const t = texts[language] || texts.fr;

  const searchCodes = useCallback(async (query) => {
    if (query.length < 2) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/hs-codes/search`, {
        params: { q: query, language, limit: 15 }
      });
      setResults(response.data.results || []);
    } catch (error) {
      console.error('Error searching HS codes:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [language]);

  // Charger les détails du code sélectionné
  useEffect(() => {
    const fetchDetails = async () => {
      if (value && value.length === 6) {
        try {
          const response = await axios.get(`${API}/hs-codes/code/${value}`, {
            params: { language }
          });
          setSelectedDetails(response.data);
        } catch (error) {
          setSelectedDetails(null);
        }
      } else {
        setSelectedDetails(null);
      }
    };
    fetchDetails();
  }, [value, language]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchTerm) {
        searchCodes(searchTerm);
      }
    }, 300);
    return () => clearTimeout(debounce);
  }, [searchTerm, searchCodes]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      const rect = inputRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: rect.width
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (code) => {
    onChange(code);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder || t.searchPlaceholder}
          value={searchTerm || (value && selectedDetails ? `${value} - ${selectedDetails.label}` : value || '')}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className="pl-10 pr-10"
          data-testid="hs-code-search-input"
        />
        {value && (
          <button
            onClick={() => {
              onChange('');
              setSearchTerm('');
              setSelectedDetails(null);
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            data-testid="hs-code-clear-btn"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Selected code details */}
      {value && selectedDetails && !isOpen && (
        <div className="mt-2 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge className="font-mono bg-blue-600 text-white">{value}</Badge>
              <span className="text-sm font-medium text-gray-700">{selectedDetails.label}</span>
            </div>
            <Badge variant="outline" className="text-xs">
              Ch. {selectedDetails.chapter} - {selectedDetails.chapter_name}
            </Badge>
          </div>
        </div>
      )}

      {isOpen && (searchTerm.length >= 2 || results.length > 0) && createPortal(
        <div
          ref={dropdownRef}
          className="bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto"
          style={{
            position: 'absolute',
            top: dropdownPosition.top,
            left: dropdownPosition.left,
            width: Math.max(dropdownPosition.width, 400),
            zIndex: 99999
          }}
          data-testid="hs-code-dropdown"
        >
          {loading ? (
            <div className="p-4 text-center text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
              <span className="text-sm">{t.loading}</span>
            </div>
          ) : results.length > 0 ? (
            <div className="py-1">
              <div className="px-3 py-2 text-xs text-gray-500 border-b bg-gray-50 sticky top-0">
                {results.length} {t.results}
              </div>
              {results.map((item) => (
                <button
                  key={item.code}
                  onClick={() => handleSelect(item.code)}
                  className={`w-full px-3 py-3 text-left hover:bg-green-50 transition-colors flex items-start gap-3 border-b border-gray-100 ${
                    value === item.code ? 'bg-green-100' : ''
                  }`}
                  data-testid={`hs-code-result-${item.code}`}
                >
                  <Badge variant="outline" className="font-mono text-xs shrink-0 bg-blue-50 text-blue-700 px-2 py-1">
                    {item.code}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800">{item.label}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      <span className="inline-flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        Ch. {item.chapter} - {item.chapter_name}
                      </span>
                    </p>
                  </div>
                </button>
              ))}
            </div>
          ) : searchTerm.length >= 2 ? (
            <div className="p-4 text-center text-gray-500">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">{t.noResults} &quot;{searchTerm}&quot;</p>
            </div>
          ) : null}
        </div>,
        document.body
      )}
    </div>
  );
}

// ============================================================================
// Composant de navigation par chapitres (panel complet)
// ============================================================================
export function HSCodeBrowser({ onSelect, language = 'fr', showRulesOfOrigin = true }) {
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [chapterCodes, setChapterCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [activeTab, setActiveTab] = useState('search');
  const [expandedSections, setExpandedSections] = useState([]);
  const [rulesOfOrigin, setRulesOfOrigin] = useState(null);
  
  const t = texts[language] || texts.fr;
  const sections = HS_SECTIONS[language] || HS_SECTIONS.fr;

  const fetchChapters = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/hs-codes/chapters`);
      const chaptersData = response.data.chapters || {};
      setChapters(Object.entries(chaptersData).map(([code, labels]) => ({
        code,
        label_fr: labels.fr,
        label_en: labels.en,
        label: language === 'en' ? labels.en : labels.fr
      })));
    } catch (error) {
      console.error('Error fetching chapters:', error);
    }
  }, [language]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/hs-codes/statistics`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  useEffect(() => {
    fetchChapters();
    fetchStats();
  }, [fetchChapters, fetchStats]);

  const fetchChapterCodes = async (chapter) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/hs-codes/chapter/${chapter}`, {
        params: { language }
      });
      setChapterCodes(response.data.codes || []);
    } catch (error) {
      console.error('Error fetching chapter codes:', error);
      setChapterCodes([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchRulesOfOrigin = async (hsCode) => {
    try {
      const response = await axios.get(`${API}/rules-of-origin/${hsCode}`, {
        params: { lang: language }
      });
      setRulesOfOrigin(response.data);
    } catch (error) {
      console.error('Error fetching rules:', error);
      setRulesOfOrigin(null);
    }
  };

  const handleChapterClick = (chapter) => {
    if (selectedChapter === chapter) {
      setSelectedChapter(null);
      setChapterCodes([]);
    } else {
      setSelectedChapter(chapter);
      fetchChapterCodes(chapter);
    }
  };

  const handleCodeSelect = (code) => {
    if (showRulesOfOrigin) {
      fetchRulesOfOrigin(code.code);
    }
    if (onSelect) {
      onSelect(code);
    }
  };

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => 
      prev.includes(sectionId) 
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const searchCodes = useCallback(async (query) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      const response = await axios.get(`${API}/hs-codes/search`, {
        params: { q: query, language, limit: 25 }
      });
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Error searching:', error);
    }
  }, [language]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchTerm) {
        searchCodes(searchTerm);
      } else {
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(debounce);
  }, [searchTerm, searchCodes]);

  const getChapterInfo = (chapterCode) => {
    return chapters.find(c => c.code === chapterCode);
  };

  return (
    <Card className="shadow-lg" data-testid="hs-code-browser">
      <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-t-lg">
        <CardTitle className="flex items-center gap-2">
          <Package className="w-5 h-5" />
          {t.title}
        </CardTitle>
        {stats && (
          <p className="text-blue-100 text-sm">
            {stats.total_chapters} {t.chapters} • {stats.total_codes} codes SH6
          </p>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full grid grid-cols-3 rounded-none border-b">
            <TabsTrigger value="search" className="flex items-center gap-2" data-testid="tab-search">
              <Search className="w-4 h-4" />
              {t.searchTab}
            </TabsTrigger>
            <TabsTrigger value="browse" className="flex items-center gap-2" data-testid="tab-browse">
              <List className="w-4 h-4" />
              {t.browseTab}
            </TabsTrigger>
            <TabsTrigger value="hierarchy" className="flex items-center gap-2" data-testid="tab-hierarchy">
              <Grid className="w-4 h-4" />
              {t.hierarchyTab}
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="p-4 m-0">
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder={t.searchPlaceholder}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="hs-browser-search"
                />
              </div>

              {searchResults.length > 0 && (
                <ScrollArea className="h-[400px] border rounded-lg">
                  <div className="px-3 py-2 text-xs text-gray-500 bg-gray-50 border-b sticky top-0">
                    {searchResults.length} {t.results}
                  </div>
                  {searchResults.map((item) => (
                    <button
                      key={item.code}
                      onClick={() => handleCodeSelect(item)}
                      className="w-full px-3 py-3 text-left hover:bg-green-50 transition-colors flex items-start gap-3 border-b last:border-0"
                      data-testid={`search-result-${item.code}`}
                    >
                      <Badge variant="outline" className="font-mono text-xs shrink-0 bg-blue-50 text-blue-700">
                        {item.code}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800">{item.label}</p>
                        <p className="text-xs text-gray-500">Ch. {item.chapter} - {item.chapter_name}</p>
                      </div>
                    </button>
                  ))}
                </ScrollArea>
              )}

              {!searchTerm && stats && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">{t.topChapters}</h4>
                  <div className="flex flex-wrap gap-2">
                    {stats.top_chapters?.slice(0, 8).map((ch) => {
                      const chapterInfo = getChapterInfo(ch.chapter);
                      return (
                        <Badge
                          key={ch.chapter}
                          variant="outline"
                          className="cursor-pointer hover:bg-blue-50 transition-colors px-3 py-1"
                          onClick={() => {
                            setActiveTab('browse');
                            handleChapterClick(ch.chapter);
                          }}
                        >
                          <span className="font-mono mr-1">{ch.chapter}</span>
                          {chapterInfo?.label?.slice(0, 25)}...
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Browse Tab - Chapter list */}
          <TabsContent value="browse" className="p-0 m-0">
            <ScrollArea className="h-[450px]">
              {chapters.map((chapter) => (
                <div key={chapter.code} className="border-b last:border-0">
                  <button
                    onClick={() => handleChapterClick(chapter.code)}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors flex items-center gap-3 ${
                      selectedChapter === chapter.code ? 'bg-blue-50' : ''
                    }`}
                    data-testid={`chapter-${chapter.code}`}
                  >
                    {selectedChapter === chapter.code ? (
                      <ChevronDown className="w-4 h-4 text-blue-600 shrink-0" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />
                    )}
                    <Badge variant="outline" className="font-mono text-xs bg-gray-100 shrink-0">
                      {chapter.code}
                    </Badge>
                    <span className="text-sm text-gray-700 flex-1">
                      {chapter.label}
                    </span>
                  </button>
                  
                  {selectedChapter === chapter.code && (
                    <div className="bg-gray-50 border-t">
                      {loading ? (
                        <div className="p-4 text-center">
                          <Loader2 className="w-5 h-5 animate-spin mx-auto text-blue-600" />
                        </div>
                      ) : (
                        <div className="max-h-60 overflow-y-auto">
                          <div className="px-4 py-2 text-xs text-gray-500 bg-gray-100 sticky top-0 border-b">
                            {chapterCodes.length} {t.codesInChapter}
                          </div>
                          {chapterCodes.map((code) => (
                            <button
                              key={code.code}
                              onClick={() => handleCodeSelect(code)}
                              className="w-full px-4 py-2 text-left hover:bg-green-100 transition-colors flex items-start gap-3 border-b border-gray-100 last:border-0"
                              data-testid={`code-${code.code}`}
                            >
                              <Badge className="font-mono text-xs bg-green-600 text-white shrink-0">
                                {code.code}
                              </Badge>
                              <span className="text-sm text-gray-700">{code.label}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </ScrollArea>
          </TabsContent>

          {/* Hierarchy Tab - Sections view */}
          <TabsContent value="hierarchy" className="p-0 m-0">
            <ScrollArea className="h-[450px]">
              {sections.map((section) => (
                <div key={section.id} className="border-b last:border-0">
                  <button
                    onClick={() => toggleSection(section.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-amber-50 transition-colors flex items-center gap-3 ${
                      expandedSections.includes(section.id) ? 'bg-amber-50' : ''
                    }`}
                    data-testid={`section-${section.id}`}
                  >
                    {expandedSections.includes(section.id) ? (
                      <ChevronDown className="w-4 h-4 text-amber-600 shrink-0" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />
                    )}
                    <Badge className="font-bold bg-amber-600 text-white shrink-0">
                      {t.section} {section.id}
                    </Badge>
                    <span className="text-sm font-medium text-gray-800 flex-1">
                      {section.name}
                    </span>
                    <span className="text-xs text-gray-500">
                      Ch. {section.chapters[0]}-{section.chapters[section.chapters.length - 1]}
                    </span>
                  </button>
                  
                  {expandedSections.includes(section.id) && (
                    <div className="bg-gray-50 border-t pl-8">
                      {section.chapters.map((chapterCode) => {
                        const chapterInfo = getChapterInfo(chapterCode);
                        return (
                          <button
                            key={chapterCode}
                            onClick={() => {
                              setActiveTab('browse');
                              handleChapterClick(chapterCode);
                            }}
                            className="w-full px-4 py-2 text-left hover:bg-blue-50 transition-colors flex items-center gap-3 border-b border-gray-100 last:border-0"
                          >
                            <Badge variant="outline" className="font-mono text-xs shrink-0">
                              {chapterCode}
                            </Badge>
                            <span className="text-sm text-gray-700">
                              {chapterInfo?.label || `${t.chapter} ${chapterCode}`}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </ScrollArea>
          </TabsContent>
        </Tabs>

        {/* Rules of Origin Panel */}
        {showRulesOfOrigin && rulesOfOrigin && (
          <div className="border-t bg-gradient-to-r from-orange-50 to-amber-50 p-4">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-orange-600" />
              <h4 className="font-semibold text-orange-800">{t.rulesOfOrigin}</h4>
              <Badge variant="outline" className="font-mono ml-auto">
                {rulesOfOrigin.hs_code}
              </Badge>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-xs text-gray-500 mb-1">{t.ruleType}</p>
                <p className="font-medium text-gray-800">{rulesOfOrigin.rules.rule}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">{t.requirement}</p>
                <p className="font-medium text-gray-800">{rulesOfOrigin.rules.requirement}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">{t.regionalContent}</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full"
                      style={{ width: `${rulesOfOrigin.rules.regional_content}%` }}
                    />
                  </div>
                  <span className="font-bold text-green-700">{rulesOfOrigin.rules.regional_content}%</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Composant combiné avec sélecteur et règles d'origine
// ============================================================================
export function HSCodeSelectorWithRules({ value, onChange, language = 'fr' }) {
  const [showBrowser, setShowBrowser] = useState(false);
  const t = texts[language] || texts.fr;

  const handleSelectFromBrowser = (code) => {
    onChange(code.code);
    setShowBrowser(false);
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1">
          <HSCodeSearch 
            value={value} 
            onChange={onChange} 
            language={language}
            showRules={true}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowBrowser(!showBrowser)}
          className="shrink-0"
          data-testid="toggle-browser-btn"
        >
          <Filter className="w-4 h-4 mr-2" />
          {t.browseByChapter}
        </Button>
      </div>

      {showBrowser && (
        <div className="mt-4">
          <HSCodeBrowser 
            onSelect={handleSelectFromBrowser}
            language={language}
            showRulesOfOrigin={true}
          />
        </div>
      )}
    </div>
  );
}

export default HSCodeSearch;
