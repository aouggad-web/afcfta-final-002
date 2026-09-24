import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import { Factory, TrendingUp, Award, Building2, Package, Loader2, AlertTriangle, Info, DollarSign, Users, Download } from 'lucide-react';
import { buildProductionPdf, productionPdfFilename } from '../../utils/productionPdf';
import { chiffres, montant, montantCompact, montantUnite, nombre } from '../../utils/nombres';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Skill dataviz : les secteurs sont des catégories sans ordre — séries
// validées, dans l'ordre fixe, jamais une rampe d'un même bleu. Au-delà de
// huit, le reste passe en gris plutôt que de recycler une teinte.
const SECTOR_COLORS = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)',
  'var(--series-5)', 'var(--series-6)', 'var(--series-7)', 'var(--series-8)'];
const couleurSecteur = (index) => SECTOR_COLORS[index] || 'var(--afcfta-muted)';
// Au-delà de six branches (entrée recalculée sur un office national : treize
// pour l'Algérie), le camembert garde les cinq premières et réunit le reste.
const MAX_PARTS_CAMEMBERT = 6;
const PARTS_NOMMEES = 5;

// Nature d'un chiffre, quand l'entrée la déclare (entrée recalculée sur un
// office statistique national) : officiel, calculé sur l'officiel, estimation,
// ou champ que seul UNIDO publie. Jetons du thème, comme dans Opportunités.
const NATURES = {
  officiel: { couleur: 'var(--success)', cle: 'production.manufacturing.panel.natureOfficial' },
  calcul_officiel: { couleur: 'var(--success)', cle: 'production.manufacturing.panel.natureComputed' },
  estimation: { couleur: 'var(--warning)', cle: 'production.manufacturing.panel.natureEstimate' },
  unido: { couleur: 'var(--info)', cle: 'production.manufacturing.panel.natureUnido' },
};

function NatureValeur({ nature, t }) {
  const n = NATURES[nature];
  if (!n) return null;
  // Le texte garde l'encre du thème : posé sur une tuile déjà teintée de la
  // même couleur, un texte coloré tombait sous 4,5:1. La nature se lit à la
  // pastille et à la bordure.
  return (
    <span
      data-testid={`nature-${nature}`}
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold text-[var(--text)]"
      style={{
        background: `color-mix(in srgb, ${n.couleur} 10%, var(--afcfta-card))`,
        border: `1px solid color-mix(in srgb, ${n.couleur} 55%, transparent)`,
      }}
    >
      <span aria-hidden="true" className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: n.couleur }} />
      {t(n.cle)}
    </span>
  );
}

// Classement : emphase — le pays choisi en safran, les autres en gris neutre
// (90 % : ≥ 5:1 sur la carte, et distinct du safran en daltonisme).
const RANG_AUTRES = 'color-mix(in srgb, var(--afcfta-muted) 90%, var(--afcfta-card))';
const RANG_CHOISI = 'var(--series-5)';

// Libellés officiels ISIC Rev.4, divisions manufacturières (Section C, 10-33).

// Libellés des indicateurs UNIDO IDSB (estimations dérivées) + INDSTAT (statistiques officielles).

// Ordre d'affichage stable des indicateurs (IDSB puis INDSTAT).
const ISIC4_INDICATOR_ORDER = [
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'establishments', 'employees',
  'female_employees', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
  'share_mva_pct',
];

// Indicateur mis en avant sur la ligne repliée, par ordre de préférence : c'est
// le chiffre qui permet de situer la classe d'un coup d'œil. La ligne affichait
// jusqu'ici un décompte d'indicateurs, qui ne renseignait sur rien.
const HEADLINE_INDICATORS = [
  'value_added_usd', 'output_usd_official', 'output_usd', 'apparent_consumption_usd',
  'establishments', 'employees',
  // En dernier recours : la part de MVA estimée. Les classes dont la division
  // n'a pas de valeur monétaire publiée ne portent QUE cet indicateur ; sans
  // lui, la ligne affichait « — » alors qu'une valeur existe. Le mettre en fin
  // de liste garde la préférence aux grandeurs mesurées.
  'share_mva_pct',
];

const PERCENT_INDICATORS = new Set(['share_mva_pct']);

const USD_INDICATORS = new Set([
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
]);

function ProductionManufacturing({ language = 'fr' }) {
  const { t } = useTranslation();
  const [selectedCountry, setSelectedCountry] = useState('MAR');
  const [unidoData, setUnidoData] = useState(null);
  const [unidoStats, setUnidoStats] = useState(null);
  const [mvaRanking, setMvaRanking] = useState([]);
  const [loading, setLoading] = useState(false);
  // Table ISIC4 complète (tous les secteurs manufacturiers du pays, pas seulement les principaux)
  const [isic4Sectors, setIsic4Sectors] = useState([]);
  const [isic4DataQuality, setIsic4DataQuality] = useState(null);
  // Nature de ce que sert l'API : mesuré par UNIDO, ou structure estimée à
  // partir des divisions ISIC2 pour les 34 pays absents du jeu au niveau classe.
  const [isic4Basis, setIsic4Basis] = useState(null);
  const [isic4Method, setIsic4Method] = useState(null);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [isic4Status, setIsic4Status] = useState('idle'); // idle | loading | error | no_data | ready
  const isic4RequestCountry = useRef(null);
  const unidoRequestCountry = useRef(null);

  // Historique détaillé (2018-2024, tous indicateurs) par code ISIC4, affiché au clic sur une ligne
  const [expandedIsic4, setExpandedIsic4] = useState(null);
  const [isic4Timeseries, setIsic4Timeseries] = useState({}); // { [isic4code]: { status, series, isic_description } }
  const isic4DetailRef = useRef(null);

  // Translations

  useEffect(() => {
    fetchUnidoStats();
    fetchMvaRanking();
  }, []);

  useEffect(() => {
    if (selectedCountry) {
      fetchUnidoData(selectedCountry);
    }
  }, [selectedCountry]);

  const fetchUnidoStats = async () => {
    try {
      const response = await axios.get(`${API}/production/unido/statistics`);
      setUnidoStats(response.data);
    } catch (error) {
      console.error('Error fetching UNIDO statistics:', error);
    }
  };

  const fetchMvaRanking = async () => {
    try {
      const response = await axios.get(`${API}/production/unido/ranking`);
      setMvaRanking(response.data.ranking || []);
    } catch (error) {
      console.error('Error fetching MVA ranking:', error);
    }
  };

  const fetchUnidoData = async (countryIso3) => {
    const requestedCountry = countryIso3;
    unidoRequestCountry.current = requestedCountry;
    setLoading(true);
    setExpandedIsic4(null);
    setIsic4Timeseries({});
    try {
      const response = await axios.get(`${API}/production/unido/${countryIso3}`);
      // Une réponse tardive d'un pays qu'on a quitté doit être jetée, pas
      // affichée. Sans ce garde, un changement de pays rapide appariait les
      // classes ISIC4 du pays courant aux parts de MVA d'un autre pays : les
      // encadrés auraient porté un classement faux sans rien signaler.
      if (unidoRequestCountry.current !== requestedCountry) return;
      setUnidoData(response.data);
    } catch (error) {
      if (unidoRequestCountry.current !== requestedCountry) return;
      console.error('Error fetching UNIDO data:', error);
      setUnidoData(null);
    } finally {
      if (unidoRequestCountry.current === requestedCountry) setLoading(false);
    }
  };

  // Table ISIC4 complète (tous les secteurs manufacturiers réels du pays,
  // via UNIDO IDSB/INDSTAT — /api/production/isic4/{country}), pas juste
  // les "top_sectors" agrégés qu'utilise l'aperçu ci-dessus.
  const fetchIsic4Sectors = async (countryIso3) => {
    const requestedCountry = countryIso3;
    isic4RequestCountry.current = requestedCountry;
    setIsic4Status('loading');
    setIsic4Sectors([]);
    setIsic4DataQuality(null);
    setIsic4Basis(null);
    setIsic4Method(null);
    try {
      const response = await axios.get(`${API}/production/isic4/${requestedCountry}`);
      if (isic4RequestCountry.current !== requestedCountry) return; // stale, country changed since
      setIsic4Sectors(response.data.sectors || []);
      setIsic4DataQuality(response.data.data_quality || null);
      setIsic4Basis(response.data.data_basis || null);
      setIsic4Method({
        methodology: response.data.methodology || null,
        coverage: response.data.coverage || null,
        source: response.data.source || null,
        years: response.data.years_covered || null,
      });
      setIsic4Status('ready');
    } catch (error) {
      if (isic4RequestCountry.current !== requestedCountry) return;
      if (error?.response?.status === 404) {
        setIsic4Status('no_data');
        return;
      }
      console.error('Error fetching ISIC4 sectors:', error);
      setIsic4Status('error');
    }
  };

  useEffect(() => {
    if (selectedCountry) {
      fetchIsic4Sectors(selectedCountry);
    }
  }, [selectedCountry]);

  // Historique complet (2018-2024, tous indicateurs IDSB+INDSTAT) pour une
  // classe ISIC4 donnée, chargé et mis en cache au premier clic sur la ligne.
  const fetchIsic4Timeseries = async (isic4Code) => {
    const requestedCountry = selectedCountry;
    setIsic4Timeseries((prev) => ({
      ...prev,
      [isic4Code]: { ...(prev[isic4Code] || {}), status: 'loading' },
    }));
    try {
      const response = await axios.get(`${API}/production/isic4/${requestedCountry}/${isic4Code}`);
      if (requestedCountry !== selectedCountry) return; // country changed while loading
      setIsic4Timeseries((prev) => ({
        ...prev,
        [isic4Code]: {
          status: 'ready',
          series: response.data.series || {},
          isicDescription: response.data.isic_description,
        },
      }));
    } catch (error) {
      if (requestedCountry !== selectedCountry) return;
      console.error('Error fetching ISIC4 timeseries:', error);
      setIsic4Timeseries((prev) => ({
        ...prev,
        [isic4Code]: { ...(prev[isic4Code] || {}), status: 'error' },
      }));
    }
  };

  const selectIsic4Class = (isic4Code) => {
    if (expandedIsic4 === isic4Code) {
      setExpandedIsic4(null);
      return;
    }
    setExpandedIsic4(isic4Code);
    // Le détail s'affiche sous la grille : sans ce recentrage, un clic sur une
    // carte du haut ne montrerait rien à l'écran.
    requestAnimationFrame(() => {
      isic4DetailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    // Les pays servis par estimation n'ont aucune série temporelle : appeler la
    // route ferait un 404 et afficherait une erreur là où il n'y a qu'une
    // absence de donnée, ce qui n'est pas la même chose.
    if (isic4Basis === 'ESTIMATED_FROM_ISIC2') return;
    const existing = isic4Timeseries[isic4Code];
    if (existing && (existing.status === 'ready' || existing.status === 'loading')) return;
    fetchIsic4Timeseries(isic4Code);
  };

  // Regroupe les secteurs ISIC4 par division 2 chiffres (ex. "10", "21", ...)
  // pour reconstituer les "encadrés ISIC2" — chacun affichant TOUTES ses
  // lignes ISIC4, pas seulement un sous-ensemble.
  const groupIsic4ByDivision = () => {
    const groups = {};
    for (const sector of isic4Sectors) {
      const division = sector.isic4?.slice(0, 2);
      if (!division) continue;
      if (!groups[division]) groups[division] = [];
      groups[division].push(sector);
    }

    // Part de MVA de la division, rattachée depuis le jeu ISIC2 du pays. C'est
    // le chiffre qui donne l'ordre d'importance des secteurs, et il est réel
    // pour les 54 pays — y compris ceux dont le niveau classe est estimé.
    const divisionStats = {};
    // Entrée recalculée sur un office national (Algérie) : ses branches 2024
    // ne sont pas des divisions CITI ; le détail par classe, lui, vient
    // d'INDSTAT. Les parts de division suivent le même millésime.
    for (const s of unidoData?.structure_indstat_2015 || unidoData?.top_sectors || []) {
      if (!s?.isic) continue;
      divisionStats[String(s.isic).padStart(2, '0')] = {
        shareMva: s.share_mva ?? null,
        valueMlnUsd: s.value_mln_usd ?? null,
        sourceName: s.name || null,
      };
    }

    return Object.keys(groups)
      .map((division) => {
        const stats = divisionStats[division] || {};
        return {
          division,
          label: t(`production.manufacturing.isicDivision.${division}`, {
            defaultValue: stats.sourceName || division,
          }),
          shareMva: stats.shareMva ?? null,
          valueMlnUsd: stats.valueMlnUsd ?? null,
          sectors: groups[division].sort((a, b) => a.isic4.localeCompare(b.isic4)),
        };
      })
      // Ordre d'importance décroissant. Une division sans part publiée n'est
      // pas une division à part nulle : elle passe après les divisions
      // chiffrées, dans l'ordre des codes, plutôt qu'en tête ou en queue par
      // un zéro inventé.
      .sort((a, b) => {
        if (a.shareMva == null && b.shareMva == null) return a.division.localeCompare(b.division);
        if (a.shareMva == null) return 1;
        if (b.shareMva == null) return -1;
        return b.shareMva - a.shareMva;
      });
  };

  const formatNumber = (num) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num?.toLocaleString() || '0';
  };

  // Montants : « 12,3 Md $ » en français, « $12.3B » en anglais — mêmes
  // paliers et même précision que formatNumber.
  const formatUsd = (num) =>
    num >= 1000 ? montantCompact(num, language, { B: 1, M: 1, K: 0 }) : montant(num ?? 0, language, 3);

  // Export PDF : le rapport reprend les encadrés ISIC2 tels qu'affichés, et
  // porte la nature de la donnée — un tableau détaché de l'écran doit dire
  // lui-même s'il est mesuré ou estimé.
  const exportIsic4Pdf = async () => {
    setPdfBusy(true);
    try {
      // Le détail par classe n'est chargé à l'écran qu'au clic, une classe à la
      // fois. Le PDF le veut en entier : une seule requête groupée plutôt que
      // 130 appels. Un échec ici ne doit pas priver du rapport — on produit
      // alors la vue d'ensemble seule, et le document le dit.
      let timeseries = null;
      let detailUnavailable = false;
      if (isic4Basis === 'UNIDO_MEASURED') {
        try {
          const res = await axios.get(`${API}/production/isic4/${selectedCountry}/timeseries`);
          timeseries = res.data?.classes || null;
          detailUnavailable = !timeseries;
        } catch (error) {
          console.error('Détail ISIC4 indisponible pour le PDF:', error);
          // Le document le dira : un export amputé qui se tait est indiscernable
          // d'un export complet.
          detailUnavailable = true;
        }
      }
      const doc = buildProductionPdf({
        countryIso3: selectedCountry,
        // unidoData vient d'une requête distincte, sans garde contre une
        // réponse périmée : si la table ISIC4 arrive la première après un
        // changement de pays, le PDF porterait le nom du pays précédent.
        // On ne s'en sert que si la charge utile désigne bien le pays courant.
        countryName:
          (unidoData?.country_iso3 || unidoData?.country_code) === selectedCountry
            ? unidoData?.country_name || selectedCountry
            : selectedCountry,
        language,
        dataBasis: isic4Basis,
        divisions: groupIsic4ByDivision(),
        source: isic4Method?.source,
        formatIndicatorValue,
        indicatorLabels: ISIC4_INDICATOR_LABELS[language] || ISIC4_INDICATOR_LABELS.fr,
        headlineOrder: HEADLINE_INDICATORS,
        indicatorOrder: ISIC4_INDICATOR_ORDER,
        timeseries,
        detailUnavailable,
      });
      doc.save(`${productionPdfFilename(selectedCountry, isic4Basis)}.pdf`);
    } finally {
      setPdfBusy(false);
    }
  };

  const formatIndicatorValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    if (PERCENT_INDICATORS.has(field)) return `${value.toLocaleString()} %`;
    return USD_INDICATORS.has(field) ? formatUsd(value) : value.toLocaleString();
  };

  // Pourcentage au format de la langue, décimales plafonnées : « 9,12 % »,
  // « +2,2 % » ; en anglais « 9.12% », « +2.2% ».
  const pct = (v, signe = false, decimales = 1) =>
    t('production.manufacturing.panel.percentValue', {
      value: `${signe && v > 0 ? '+' : ''}${nombre(v, language, decimales)}`,
    });
  // Libellé anglais quand l'entrée le porte (branches d'un office national).
  const nomBranche = (sector) => (language === 'en' && sector.name_en) || sector.name;

  const secteursPlies = () => (unidoData?.top_sectors?.length || 0) > MAX_PARTS_CAMEMBERT;
  const couleurBranche = (index) =>
    secteursPlies() && index >= PARTS_NOMMEES ? 'var(--afcfta-muted)' : couleurSecteur(index);

  const prepareSectorPieData = () => {
    if (!unidoData?.top_sectors) return [];
    const parts = unidoData.top_sectors.map((sector, index) => ({
      name: nomBranche(sector),
      value: sector.share_mva,
      fill: couleurSecteur(index)
    }));
    if (!secteursPlies()) return parts;
    const reste = parts.slice(PARTS_NOMMEES);
    return [
      ...parts.slice(0, PARTS_NOMMEES),
      {
        name: t('production.manufacturing.panel.sectorsOthers'),
        value: Math.round(reste.reduce((somme, p) => somme + (p.value || 0), 0) * 10) / 10,
        fill: 'var(--afcfta-muted)',
      },
    ];
  };

  const prepareSectorBarData = () => {
    if (!unidoData?.top_sectors) return [];
    
    return unidoData.top_sectors.map((sector) => ({
      name: nomBranche(sector).length > 20 ? nomBranche(sector).substring(0, 20) + '...' : nomBranche(sector),
      fullName: nomBranche(sector),
      value: sector.value_mln_usd || 0,
      share: sector.share_mva
    }));
  };

  const prepareRankingBarData = () => {
    return mvaRanking.slice(0, 10).map((country) => ({
      name: country.country_name.length > 15 ? country.country_name.substring(0, 15) + '...' : country.country_name,
      fullName: country.country_name,
      mva: country.mva_2023_mln_usd,
      isSelected: country.country_iso3 === selectedCountry
    }));
  };

  const getCountryRank = () => {
    const index = mvaRanking.findIndex(c => c.country_iso3 === selectedCountry);
    return index >= 0 ? index + 1 : null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-[image:var(--card-grad)] border-[var(--afcfta-border)] text-[var(--text)] shadow-xl overflow-hidden">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl font-bold flex items-center gap-3">
                <Factory className="w-8 h-8" />
                {t('production.manufacturing.panel.title')}
              </CardTitle>
              <CardDescription className="text-[var(--info)] text-lg mt-2">
                {t('production.manufacturing.panel.subtitle')}
              </CardDescription>
            </div>
            {unidoStats && (
              <div className="text-right">
                <Badge className="bg-[var(--overlay)] text-[var(--text)] hover:bg-[var(--overlay)]">
                  {montantUnite(unidoStats.total_mva_bln_usd, 'B', language)} {t('production.manufacturing.panel.totalMva')}
                </Badge>
                <p className="text-xs text-[var(--info)] mt-1">{unidoStats.total_countries} {t('production.manufacturing.panel.countries')}</p>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Enhanced Country Selector */}
      <div style={{ position: 'relative', zIndex: 100 }}>
        <Card className="border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] shadow-lg" style={{ overflow: 'visible' }}>
          <CardContent className="pt-6" style={{ overflow: 'visible' }}>
            <EnhancedCountrySelector
              value={selectedCountry}
              onChange={setSelectedCountry}
              label={t('production.manufacturing.panel.selectAnAfricanCountry')}
              variant="prominent"
              language={language}
            />
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {loading && (
        <Card className="animate-pulse">
          <CardContent className="flex items-center justify-center h-48">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-[var(--info)] mx-auto" />
              <p className="mt-4 text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.loading')}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data State */}
      {!loading && (!unidoData || unidoData.message) && (
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertTriangle className="w-12 h-12 text-[var(--gold)]" />
            <div>
              <h3 className="font-bold text-lg text-[var(--text)]">{t('production.manufacturing.panel.noData')}</h3>
              <p className="text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.noDataDesc')}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      {!loading && unidoData && !unidoData.message && (
        <>
          {/* Key Metrics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] border-l-4 border-l-[var(--info)]">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[var(--info)] text-sm">{t('production.manufacturing.panel.mvaLabel')}</p>
                    <p className="text-3xl font-bold">{formatUsd(unidoData.mva_2023_mln_usd * 1000000)}</p>
                    <NatureValeur nature={unidoData.natures?.mva_2023_mln_usd} t={t} />
                    {unidoData.natures?.mva_2024_mln_usd && (
                      <p className="text-sm text-[var(--text-soft)] mt-2" data-testid="manufacture-mva-2024">
                        {t('production.manufacturing.panel.yearValue', { year: 2024, value: formatUsd(unidoData.mva_2024_mln_usd * 1000000) })}
                      </p>
                    )}
                  </div>
                  <DollarSign className="w-10 h-10 text-[var(--info)]" />
                </div>
                {getCountryRank() && (
                  <Badge className="mt-3 bg-[var(--overlay)] text-[var(--text)]">
                    #{getCountryRank()} {t('production.manufacturing.panel.inAfrica')}
                  </Badge>
                )}
              </CardContent>
            </Card>

            <Card className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-l-4 border-l-[var(--success)]">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[var(--success)] text-sm">{t('production.manufacturing.panel.mvaGdp')}</p>
                    <p className="text-3xl font-bold">{pct(unidoData.mva_gdp_percent, false, 2)}</p>
                    <NatureValeur nature={unidoData.natures?.mva_gdp_percent} t={t} />
                  </div>
                  <TrendingUp className="w-10 h-10 text-[var(--success)]" />
                </div>
                <p className="text-sm text-[var(--success)] mt-2">{t('production.manufacturing.panel.industrialShare')}</p>
              </CardContent>
            </Card>

            <Card className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] border-l-4 border-l-[var(--violet)]">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[var(--violet)] text-sm">{t('production.manufacturing.panel.mvaPerCapita')}</p>
                    <p className="text-3xl font-bold">{montantUnite(unidoData.mva_per_capita_usd, null, language)}</p>
                    <NatureValeur nature={unidoData.natures?.mva_per_capita_usd} t={t} />
                  </div>
                  <Users className="w-10 h-10 text-[var(--violet)]" />
                </div>
                <p className="text-sm text-[var(--violet)] mt-2">{t('production.manufacturing.panel.industrialization')}</p>
              </CardContent>
            </Card>

            <Card className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] border-l-4 border-l-[var(--gold)]">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[var(--gold)] text-sm">{t('production.manufacturing.panel.growth2023')}</p>
                    <p className="text-3xl font-bold">{pct(unidoData.growth_rate_2023, true)}</p>
                    <NatureValeur nature={unidoData.natures?.growth_rate_2023} t={t} />
                    {unidoData.natures?.growth_rate_2024 && (
                      <p className="text-sm text-[var(--text-soft)] mt-2" data-testid="manufacture-croissance-2024">
                        {t('production.manufacturing.panel.yearValue', { year: 2024, value: pct(unidoData.growth_rate_2024, true) })}
                      </p>
                    )}
                  </div>
                  <TrendingUp className="w-10 h-10 text-[var(--gold)]" />
                </div>
                <p className="text-sm text-[var(--gold)] mt-2">{t('production.manufacturing.panel.annualGrowth')}</p>
              </CardContent>
            </Card>
          </div>

          {/* Estimation de l'année en cours (entrée recalculée sur un office
              national) : jamais lue comme une mesure — valeur centrale,
              fourchette, confiance et méthode. */}
          {unidoData.estimation_2025 && (
            <Card
              data-testid="manufacture-estimation"
              className="border-l-4 border-l-[var(--warning)] bg-[color-mix(in_srgb,var(--warning)_8%,var(--afcfta-card))]"
            >
              <CardContent className="pt-5">
                <div className="flex flex-wrap items-start justify-between gap-6">
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)] flex items-center gap-2 flex-wrap">
                      {t('production.manufacturing.panel.estimate2025Title')}
                      <NatureValeur nature="estimation" t={t} />
                    </p>
                    <p className="text-3xl font-bold mt-1">
                      {formatUsd(unidoData.estimation_2025.va_mln_usd.central * 1000000)}
                    </p>
                    <p className="text-sm text-[var(--text-soft)]">
                      {t('production.manufacturing.panel.estimateRange', {
                        bas: formatUsd(unidoData.estimation_2025.va_mln_usd.bas * 1000000),
                        haut: formatUsd(unidoData.estimation_2025.va_mln_usd.haut * 1000000),
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.estimateVolumeGrowth')}</p>
                    <p className="text-xl font-bold">
                      {pct(unidoData.estimation_2025.croissance_volume_pct.central, true)}
                      <span className="text-sm font-normal text-[var(--text-soft)]">
                        {' '}{t('production.manufacturing.panel.estimateGrowthRange', {
                          bas: chiffres(unidoData.estimation_2025.croissance_volume_pct.bas, language, 1),
                          haut: chiffres(unidoData.estimation_2025.croissance_volume_pct.haut, language, 1),
                        })}
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.estimateConfidence')}</p>
                    <p className="text-sm font-semibold" data-testid="manufacture-confiance">
                      {Object.entries(unidoData.estimation_2025.confiance_part_va_pct || {})
                        .map(([grade, share]) => t('production.manufacturing.panel.estimateConfidenceShare', { grade, share: chiffres(share, language, 1) }))
                        .join(' · ')}
                    </p>
                  </div>
                </div>
                <details className="mt-3 text-xs text-[var(--text-soft)]">
                  <summary className="cursor-pointer">{t('production.manufacturing.panel.estimateMethod')}</summary>
                  <p className="mt-2 leading-relaxed">{unidoData.estimation_2025.methode}</p>
                  <p className="mt-1">{unidoData.estimation_2025.note} — {unidoData.estimation_2025.base_prix}</p>
                </details>
              </CardContent>
            </Card>
          )}

          {/* Country Overview */}
          <Card className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
            <CardHeader className="pb-2">
              <CardTitle className="text-2xl text-[var(--info)] flex items-center gap-3">
                <Building2 className="w-7 h-7" />
                {unidoData.country_name}
              </CardTitle>
              <CardDescription className="text-[var(--info)] flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="border-[color-mix(in_srgb,var(--info)_30%,transparent)] text-[var(--info)]">{unidoData.region}</Badge>
                <Badge variant="outline" className="border-[color-mix(in_srgb,var(--info)_30%,transparent)] text-[var(--info)]">{t('production.manufacturing.panel.data')} {unidoData.data_year}</Badge>
                {unidoData.industrial_zones && (
                  <Badge variant="outline" className="border-[color-mix(in_srgb,var(--info)_30%,transparent)] text-[var(--info)]">
                    <Building2 className="w-3 h-3 mr-1" /> {unidoData.industrial_zones} {t('production.manufacturing.panel.industrialZones')}
                  </Badge>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Additional Info */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                {unidoData.industry_employment && (
                  <div className="bg-[var(--afcfta-card)] p-4 rounded-xl shadow-sm border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.industrialJobs')}</p>
                    <p className="text-2xl font-bold text-[var(--info)]">{formatNumber(unidoData.industry_employment)}</p>
                    <NatureValeur nature={unidoData.natures?.industry_employment} t={t} />
                  </div>
                )}
                {unidoData.exports_manuf_mln_usd && (
                  <div className="bg-[var(--afcfta-card)] p-4 rounded-xl shadow-sm border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.manufExports')}</p>
                    <p className="text-2xl font-bold text-[var(--success)]">{formatUsd(unidoData.exports_manuf_mln_usd * 1000000)}</p>
                    <NatureValeur nature={unidoData.natures?.exports_manuf_mln_usd} t={t} />
                  </div>
                )}
                {unidoData.top_sectors && (
                  <div className="bg-[var(--afcfta-card)] p-4 rounded-xl shadow-sm border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.keySectors')}</p>
                    <p className="text-2xl font-bold text-[var(--info)]">{unidoData.top_sectors.length}</p>
                  </div>
                )}
                {unidoData.special_economic_zones && (
                  <div className="bg-[var(--afcfta-card)] p-4 rounded-xl shadow-sm border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <p className="text-xs text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.specialZones')}</p>
                    <p className="text-2xl font-bold text-[var(--violet)]">{unidoData.special_economic_zones}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Sector Analysis Charts */}
          {unidoData.top_sectors && unidoData.top_sectors.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-[var(--text)] flex items-center gap-2">
                    <Package className="w-5 h-5" /> {t('production.manufacturing.panel.sectorDistribution')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={prepareSectorPieData()}
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        dataKey="value"
                      >
                        {prepareSectorPieData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} stroke="var(--afcfta-card)" strokeWidth={2} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => value + '% ' + t('production.manufacturing.panel.mva')} />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* Légende en HTML : un libellé long (branche d'un office
                      national) passe à la ligne au lieu de déborder de la
                      carte, et l'ordre suit les parts, pas l'alphabet. */}
                  <ul className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1.5 text-sm text-[var(--text)]" data-testid="manufacture-legende-camembert">
                    {prepareSectorPieData().map((part) => (
                      <li key={part.name} className="flex items-center gap-1.5">
                        <span aria-hidden="true" className="w-3 h-3 rounded-sm shrink-0" style={{ background: part.fill }} />
                        <span>{part.name}</span>
                        {part.value != null && <span className="text-[var(--afcfta-muted)] tabular-nums">{pct(part.value)}</span>}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Bar Chart */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-[var(--text)] flex items-center gap-2">
                    <Factory className="w-5 h-5" /> {t('production.manufacturing.panel.sectorValue')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={Math.max(300, prepareSectorBarData().length * 34)}>
                    <BarChart data={prepareSectorBarData()} layout="vertical" margin={{ top: 5, right: 28, bottom: 5, left: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tickFormatter={(v) => formatUsd(v * 1000000)} />
                      <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} interval={0} />
                      <Tooltip 
                        formatter={(value) => [formatUsd(value * 1000000), t('production.manufacturing.panel.value')]}
                        labelFormatter={(label) => prepareSectorBarData().find(d => d.name === label)?.fullName || label}
                      />
                      {/* Même couleur par secteur que le camembert voisin. */}
                      <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={24}>
                        {prepareSectorBarData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={couleurBranche(index)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}

          {unidoData.top_sectors?.length > 0 && unidoData.natures?.top_sectors && (
            <p className="text-xs text-[var(--afcfta-muted)] -mt-3 flex items-center gap-2 flex-wrap" data-testid="manufacture-structure-source">
              <NatureValeur nature={unidoData.natures.top_sectors} t={t} />
              {t('production.manufacturing.panel.structureSource', {
                year: unidoData.data_year,
                source: [unidoData.source_institution, unidoData.source_dataset].filter(Boolean).join(', '),
              })}
            </p>
          )}

          {/* ISIC4 Detail Table — vraies données UNIDO IDSB/INDSTAT, toutes les
              classes ISIC4 groupées par division ISIC2, historique complet au clic */}
          <Card className="shadow-lg">
            <CardHeader className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <CardTitle className="text-xl text-[var(--info)] flex items-center gap-2">
                  <Award className="w-5 h-5" /> {t('production.manufacturing.panel.mainIndustrialSectors')}
                </CardTitle>
                {isic4Status === 'ready' && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs">
                      {isic4Sectors.length} {t('production.manufacturing.panel.isic4DigitClasses')}
                    </Badge>
                    {/* Trois natures distinctes, jamais deux pastilles à la fois :
                        structure estimée hors couverture, estimations dérivées
                        UNIDO, ou statistiques mesurées. Afficher « Mesuré » à côté
                        de « estimations dérivées » présentait de l'estimé comme du
                        mesuré. */}
                    {isic4Basis === 'ESTIMATED_FROM_ISIC2' ? (
                      <Badge className="text-xs bg-[var(--gold)] hover:bg-[var(--gold)] text-[var(--bg)]">
                        {t('production.manufacturing.panel.estimatedStructure')}
                      </Badge>
                    ) : isic4DataQuality?.is_fully_estimated ? (
                      <Badge className="text-xs bg-[var(--info)] hover:bg-[var(--info)] text-[var(--bg)]">
                        {t('production.manufacturing.panel.unidoDerivedEstimates')}
                      </Badge>
                    ) : (
                      <Badge className="text-xs bg-[var(--success)] hover:bg-[var(--success)] text-[var(--bg)]">
                        {t('production.manufacturing.panel.measuredUnido')}
                      </Badge>
                    )}
                    <button
                      type="button"
                      onClick={exportIsic4Pdf}
                      disabled={pdfBusy}
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md border border-[color-mix(in_srgb,var(--info)_30%,transparent)] text-[var(--info)] hover:bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] transition disabled:opacity-60 disabled:cursor-wait"
                    >
                      {pdfBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                      {pdfBusy
                        ? t('production.manufacturing.panel.generating')
                        : t('production.manufacturing.panel.exportPdf')}
                    </button>
                  </div>
                )}
              </div>
              <CardDescription className="text-[var(--info)] text-xs mt-1">
                {isic4Method?.years
                  ? t('production.manufacturing.panel.sourceUnidoStatisticsDataYears', { years: isic4Method.years })
                  : t('production.manufacturing.panel.sourceUnidoStatisticsData')}
                {unidoData.structure_indstat_2015?.length > 0 && (
                  <> {t('production.manufacturing.panel.divisionSharesIndstat', { year: 2015 })}</>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {isic4Status === 'loading' && (
                <p className="text-sm text-[var(--afcfta-muted)] py-6 text-center">
                  <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
                  {t('production.manufacturing.panel.loadingShort')}
                </p>
              )}
              {isic4Status === 'error' && (
                <div className="text-sm text-[var(--danger)] flex items-center justify-between gap-2 py-4">
                  <span>{t('production.manufacturing.panel.failedLoadIsic4Data')}</span>
                  <button type="button" className="underline hover:no-underline" onClick={() => fetchIsic4Sectors(selectedCountry)}>
                    {t('production.manufacturing.panel.retry')}
                  </button>
                </div>
              )}
              {isic4Status === 'no_data' && (
                <p className="text-sm text-[var(--afcfta-muted)] py-4 flex items-center gap-2">
                  <Info className="w-4 h-4 shrink-0" />
                  {t('production.manufacturing.panel.noUnidoIdsbIndstat')}
                </p>
              )}
              {isic4Status === 'ready' && isic4Sectors.length === 0 && (
                <p className="text-sm text-[var(--afcfta-muted)] py-4">
                  {t('production.manufacturing.panel.noIsic4SectorFor')}
                </p>
              )}
              {isic4Status === 'ready' && isic4Basis === 'ESTIMATED_FROM_ISIC2' && (
                <div className="mb-5 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] px-4 py-3">
                  <p className="text-sm font-semibold text-[var(--gold)] flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {t('production.manufacturing.panel.theseFiguresAreStructural')}
                  </p>
                  <ul className="text-xs text-[var(--gold)] mt-2 space-y-1 list-disc list-inside">
                    <li>
                      {t('production.manufacturing.panel.unidoPublishesNoIsic')}
                    </li>
                    <li>
                      {t('production.manufacturing.panel.everyClassWithinDivision')}
                    </li>
                    <li>
                      {t('production.manufacturing.panel.onlyCountryU2019sMain')}
                    </li>
                    <li>
                      {t('production.manufacturing.panel.noTimeSeriesExists')}
                    </li>
                  </ul>
                  {isic4Method?.source && (
                    <p className="text-[11px] text-[var(--gold)] mt-2">
                      {t('production.manufacturing.panel.sourcePrefix')}{isic4Method.source}
                    </p>
                  )}
                </div>
              )}
              {isic4Status === 'ready' && isic4Sectors.length > 0 && (
                <>
                  {/* Encadrés carrés : une division ISIC2 par carte, classées
                      par part de MVA décroissante — l'ordre d'importance du
                      secteur se lit sans rien calculer. */}
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 items-start">
                    {groupIsic4ByDivision().map(({ division, label, shareMva, valueMlnUsd, sectors }, rank) => (
                      <IsicDivisionCard
                        key={division}
                        rank={rank + 1}
                        division={division}
                        label={label}
                        shareMva={shareMva}
                        valueMlnUsd={valueMlnUsd}
                        annee={unidoData.structure_indstat_2015?.length ? 2015 : null}
                        language={language}
                        sectors={sectors}
                        selectedIsic4={expandedIsic4}
                        onSelect={selectIsic4Class}
                      />
                    ))}
                  </div>

                  {/* Détail de la classe sélectionnée, affiché plus bas : deux
                      tableaux distincts, INDSTAT officiel puis IDSB dérivé,
                      jamais mélangés. */}
                  <div ref={isic4DetailRef} className="scroll-mt-4">
                    {expandedIsic4 && (
                      <Isic4DetailPanel
                        sector={isic4Sectors.find((s) => s.isic4 === expandedIsic4)}
                        timeseries={isic4Timeseries[expandedIsic4]}
                        dataBasis={isic4Basis}
                        formatIndicatorValue={formatIndicatorValue}
                        onRetry={() => fetchIsic4Timeseries(expandedIsic4)}
                        onClose={() => setExpandedIsic4(null)}
                      />
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Key Products */}
          {unidoData.key_products && unidoData.key_products.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl text-[var(--text)] flex items-center gap-2">
                  <Package className="w-5 h-5" /> {t('production.manufacturing.panel.keyProducts')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {unidoData.key_products.map((product, index) => (
                    <Badge 
                      key={index} 
                      className="text-sm py-2 px-4 bg-[var(--afcfta-card2)] text-[var(--text)] border border-[var(--afcfta-border)] hover:bg-[var(--afcfta-card2)]"
                    >
                      {product}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* African MVA Ranking */}
          {mvaRanking.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]">
                <CardTitle className="text-xl text-[var(--gold)] flex items-center gap-2">
                  <Award className="w-5 h-5" /> {t('production.manufacturing.panel.top10Africa')}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={prepareRankingBarData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(v) => formatUsd(v * 1000000)} width={80} />
                    <Tooltip 
                      formatter={(value) => [formatUsd(value * 1000000), 'MVA 2023']}
                      labelFormatter={(label) => prepareRankingBarData().find(d => d.name === label)?.fullName || label}
                    />
                    <Bar 
                      dataKey="mva" 
                      radius={[4, 4, 0, 0]}
                      maxBarSize={24}
                    >
                      {prepareRankingBarData().map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.isSelected ? RANG_CHOISI : RANG_AUTRES} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ background: RANG_AUTRES }} />
                    <span className="text-sm text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.otherCountries')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ background: RANG_CHOISI }} />
                    <span className="text-sm text-[var(--afcfta-muted)]">{t('production.manufacturing.panel.selectedCountry')}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Source Information */}
          <Card className="bg-[var(--afcfta-card2)] border-[var(--afcfta-border)]">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-[var(--afcfta-muted)] mt-0.5" />
                <div className="text-sm text-[var(--afcfta-muted)]">
                  <p><strong>{t('production.manufacturing.panel.source')}</strong> {unidoData.source}</p>
                  <p className="mt-1">
                    {unidoData.source_institution
                      ? t('production.manufacturing.panel.sourceNoteNational')
                      : t('production.manufacturing.panel.sourceNote')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

// Familles d'indicateurs, tenues séparées à l'affichage : INDSTAT publie des
// statistiques officielles, IDSB des estimations dérivées. Les fondre dans un
// seul tableau ferait lire les secondes comme les premières.
export const INDSTAT_FIELDS = [
  'output_usd_official', 'value_added_usd', 'establishments', 'employees',
  'female_employees', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
];
export const IDSB_FIELDS = [
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
];

// Part des femmes dans l'emploi d'une classe, pour une année. Rapport de deux
// séries mesurées — calculé, donc annoncé comme calculé. Rend null dès qu'une
// des deux valeurs manque ou que l'effectif total est nul : un ratio sans
// dénominateur n'est pas zéro, et zéro salarié ne fait pas 0 % de femmes.
export function femaleSharePct(series, year) {
  const total = series?.employees?.find((pt) => pt.year === year)?.value;
  const female = series?.female_employees?.find((pt) => pt.year === year)?.value;
  if (total == null || female == null || total === 0) return null;
  return (female / total) * 100;
}

// Encadré carré d'une division ISIC 2 chiffres : intitulé, code, part de MVA
// chiffrée, puis la liste de ses classes ISIC 4 en liens cliquables.
function IsicDivisionCard({ rank, division, label, shareMva, valueMlnUsd, annee, sectors, selectedIsic4, onSelect, language }) {
  const { t } = useTranslation();
  return (
    <div className="bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] rounded-xl shadow-sm flex flex-col">
      <div className="px-4 pt-4 pb-3 border-b border-[var(--afcfta-border)]">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <span className="inline-flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[var(--afcfta-muted)]">#{rank}</span>
              <span className="font-mono text-sm font-bold text-[var(--info)]">ISIC {division}</span>
            </span>
            {/* Intitulé complet, jamais tronqué : il passe à la ligne. */}
            <h4 className="font-bold text-[var(--text)] leading-snug mt-1 break-words">{label}</h4>
          </div>
          <div className="text-right shrink-0">
            {shareMva != null ? (
              <>
                <div className="text-2xl font-bold text-[var(--text)] tabular-nums leading-none">
                  {shareMva.toLocaleString()} %
                </div>
                <div className="text-[11px] text-[var(--afcfta-muted)] mt-1">
                  {annee
                    ? t('production.manufacturing.panel.mvaYear', { year: annee })
                    : t('production.manufacturing.panel.mva')}
                </div>
              </>
            ) : (
              <div className="text-sm text-[var(--afcfta-muted)]" title={t('production.manufacturing.panel.shareNotPublishedFor')}>
                —
              </div>
            )}
          </div>
        </div>
        {valueMlnUsd != null && (
          <p className="text-xs text-[var(--afcfta-muted)] mt-2 tabular-nums">
            {montantUnite(valueMlnUsd, 'M', language, 3, { max: true })}{' '}
            {annee
              ? t('production.manufacturing.panel.mUsdValueAddedYear', { year: annee })
              : t('production.manufacturing.panel.mUsdValueAdded')}
          </p>
        )}
      </div>

      <ul
        className={`px-2 py-2 flex-1 ${
          // Au-delà de six classes, la liste passe sur deux colonnes. Les
          // divisions vont de 1 à 16 classes : sur une seule colonne, la
          // division 28 ferait seize fois la hauteur de la division 12. Deux
          // colonnes rapprochent les encadrés d'une forme carrée SANS rien
          // masquer — l'inverse d'une hauteur imposée, qui mettrait les
          // longues listes derrière un ascenseur interne.
          sectors.length > 6 ? 'sm:columns-2 sm:gap-x-2 [&>li]:break-inside-avoid' : 'space-y-0.5'
        }`}
      >
        {sectors.map((sector) => {
          const isSelected = selectedIsic4 === sector.isic4;
          return (
            <li key={sector.isic4}>
              <button
                type="button"
                onClick={() => onSelect(sector.isic4)}
                aria-pressed={isSelected}
                className={`w-full text-left rounded-lg px-2 py-1.5 flex gap-2 items-baseline transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                  isSelected ? 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]' : 'hover:bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]'
                }`}
              >
                <span className="font-mono text-xs font-semibold text-[var(--info)] underline decoration-dotted underline-offset-2 shrink-0">
                  {sector.isic4}
                </span>
                <span className="text-sm text-[var(--text)] leading-snug break-words min-w-0">
                  {sector.isic_description || sector.description || (
                    <span className="text-[var(--afcfta-muted)] italic">
                      {t('production.manufacturing.panel.labelNotPublished')}
                    </span>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      <div className="px-4 pb-3 text-[11px] text-[var(--afcfta-muted)]">
        {sectors.length} {t('production.manufacturing.panel.isic4Classes')}
      </div>
    </div>
  );
}

// Tableau années × indicateurs d'une famille. Dimensionné pour tout montrer :
// aucune troncature de libellé, et c'est le conteneur qui défile si la série
// est longue, jamais le contenu qui est coupé.
function YearMatrix({ title, subtitle, fields, series, years, formatIndicatorValue, accent, extraRows = [] }) {
  const { t } = useTranslation();
  const present = fields.filter((f) => series[f]?.length);
  if (!present.length && !extraRows.length) return null;

  const valueAt = (field, year) => {
    const point = series[field]?.find((pt) => pt.year === year);
    return point ? formatIndicatorValue(field, point.value) : '—';
  };

  return (
    <div className="mt-4">
      <h5 className={`text-sm font-bold ${accent.text} flex items-baseline gap-2 flex-wrap`}>
        {title}
        <span className="text-xs font-normal text-[var(--afcfta-muted)]">{subtitle}</span>
      </h5>
      <div className="mt-2 overflow-x-auto rounded-lg border border-[var(--afcfta-border)] bg-[var(--afcfta-card)]">
        <table className="text-sm border-collapse min-w-full">
          <thead>
            <tr className={accent.head}>
              <th className="text-left font-semibold px-4 py-2.5 whitespace-nowrap sticky left-0 z-10 bg-inherit">
                {t('production.manufacturing.panel.indicator')}
              </th>
              {years.map((year) => (
                <th key={year} className="text-right font-semibold px-4 py-2.5 whitespace-nowrap tabular-nums">
                  {year}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {present.map((field, i) => (
              <tr key={field} className={i % 2 ? 'bg-gray-50/60' : 'bg-[var(--afcfta-card)]'}>
                <th scope="row" className="text-left font-medium text-[var(--text)] px-4 py-2 whitespace-nowrap sticky left-0 z-10 bg-inherit">
                  {t(`production.manufacturing.isicIndicator.${field}`, { defaultValue: field })}
                </th>
                {years.map((year) => (
                  <td key={year} className="text-right px-4 py-2 whitespace-nowrap tabular-nums text-[var(--text)]">
                    {valueAt(field, year)}
                  </td>
                ))}
              </tr>
            ))}
            {extraRows.map((row, i) => (
              <tr key={row.key} className={(present.length + i) % 2 ? 'bg-gray-50/60' : 'bg-[var(--afcfta-card)]'}>
                <th scope="row" className="text-left font-medium text-[var(--text)] px-4 py-2 whitespace-nowrap sticky left-0 z-10 bg-inherit">
                  {row.label}
                </th>
                {years.map((year) => (
                  <td key={year} className="text-right px-4 py-2 whitespace-nowrap tabular-nums text-[var(--text)]">
                    {row.valueAt(year)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Détail d'une classe ISIC 4, affiché sous la grille.
function Isic4DetailPanel({ sector, timeseries, dataBasis, formatIndicatorValue, onRetry, onClose }) {
  const { t } = useTranslation();
  const isEstimatedCountry = dataBasis === 'ESTIMATED_FROM_ISIC2';
  const status = timeseries?.status;
  const series = timeseries?.series || {};

  const years = Array.from(
    new Set(ISIC4_INDICATOR_ORDER.filter((f) => series[f]?.length).flatMap((f) => series[f].map((pt) => pt.year)))
  ).sort((a, b) => a - b);

  // Part des femmes : rapport de deux séries mesurées, calculé ici et annoncé
  // comme calculé. Émis seulement quand les deux valeurs existent pour l'année
  // et que l'effectif total n'est pas nul — sinon la case reste vide.
  const femaleShareRow = series.employees?.length && series.female_employees?.length
    ? [{
        key: 'female_share_pct',
        label: t('production.manufacturing.panel.femaleShareComputed'),
        valueAt: (year) => {
          const pct = femaleSharePct(series, year);
          return pct == null ? '—' : `${pct.toFixed(1)} %`;
        },
      }]
    : [];

  return (
    <div className="mt-6 rounded-xl border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[var(--afcfta-card2)] px-5 py-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <h4 className="font-bold text-[var(--text)] leading-snug break-words">
            <span className="font-mono text-[var(--info)]">{sector?.isic4}</span>
            <span className="text-[var(--afcfta-muted)] mx-2">·</span>
            {sector?.isic_description || sector?.description}
          </h4>
          {sector?.division_name && (
            <p className="text-xs text-[var(--afcfta-muted)] mt-0.5">{sector.division_name}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-sm text-[var(--info)] hover:underline shrink-0"
        >
          {t('production.manufacturing.panel.close')}
        </button>
      </div>

      {isEstimatedCountry ? (
        <EstimatedDetail
          indicators={sector?.indicators || {}}
          formatIndicatorValue={formatIndicatorValue}
        />
      ) : (
        <>
          {status === 'loading' && (
            <p className="text-sm text-[var(--afcfta-muted)] py-3">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
              {t('production.manufacturing.panel.loadingShort')}
            </p>
          )}
          {status === 'error' && (
            <div className="text-sm text-[var(--danger)] flex items-center justify-between gap-2 py-2">
              <span>{t('production.manufacturing.panel.failedLoadHistory')}</span>
              <button type="button" className="underline hover:no-underline" onClick={onRetry}>
                {t('production.manufacturing.panel.retry')}
              </button>
            </div>
          )}
          {status === 'ready' && years.length === 0 && (
            <p className="text-sm text-[var(--afcfta-muted)] py-2">
              {t('production.manufacturing.panel.noTimeSeriesAvailable')}
            </p>
          )}
          {status === 'ready' && years.length > 0 && (
            <>
              <YearMatrix
                title={t('production.manufacturing.panel.indstatOfficialStatistics')}
                subtitle={t('production.manufacturing.panel.outputEmploymentWagesValue')}
                fields={INDSTAT_FIELDS}
                series={series}
                years={years}
                formatIndicatorValue={formatIndicatorValue}
                accent={{ text: 'text-[var(--success)]', head: 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-b-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)]' }}
                extraRows={femaleShareRow}
              />
              <YearMatrix
                title={t('production.manufacturing.panel.idsbDerivedEstimates')}
                subtitle={t('production.manufacturing.panel.outputImportsExportsApparent')}
                fields={IDSB_FIELDS}
                series={series}
                years={years}
                formatIndicatorValue={formatIndicatorValue}
                accent={{ text: 'text-[var(--info)]', head: 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-b-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)]' }}
              />
              <p className="text-[11px] text-[var(--afcfta-muted)] mt-3">
                {t('production.manufacturing.panel.twoTablesAreKept')}
              </p>
            </>
          )}
        </>
      )}
    </div>
  );
}

function EstimatedDetail({ indicators, formatIndicatorValue }) {
  const { t } = useTranslation();
  const fields = ISIC4_INDICATOR_ORDER.filter((f) => indicators[f]?.value !== undefined && indicators[f]?.value !== null);
  if (fields.length === 0) {
    return (
      <p className="text-sm text-[var(--afcfta-muted)] py-2">
        {t('production.manufacturing.panel.noEstimatedValueFor')}
      </p>
    );
  }
  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-[var(--afcfta-border)] bg-[var(--afcfta-card)]">
        <table className="text-sm border-collapse w-full">
          <thead>
            <tr className="bg-[var(--afcfta-card2)] text-[var(--text)]">
              <th className="py-2 px-3 font-semibold text-left">{t('production.manufacturing.panel.indicator')}</th>
              <th className="py-2 px-3 font-semibold text-right">{t('production.manufacturing.panel.estimatedValue')}</th>
              <th className="py-2 px-3 font-semibold text-left">{t('production.manufacturing.panel.nature')}</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field, i) => (
              <tr key={field} className={i % 2 ? 'bg-slate-50/60' : 'bg-[var(--afcfta-card)]'}>
                <td className="py-2 px-3 text-[var(--text)]">{labels[field] || field}</td>
                <td className="py-2 px-3 text-right text-[var(--text)] font-semibold tabular-nums whitespace-nowrap">
                  {formatIndicatorValue(field, indicators[field].value)}
                </td>
                <td className="py-2 px-3">
                  <span className="rounded bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] px-2 py-0.5 text-xs font-medium text-[var(--gold)]">
                    {t('production.manufacturing.panel.structuralEstimate')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[var(--gold)] italic pt-3">
        {t('production.manufacturing.panel.valueObtainedByDividing')}
      </p>
    </>
  );
}


export default ProductionManufacturing;
