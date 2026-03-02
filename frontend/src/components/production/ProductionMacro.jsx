import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function ProductionMacro({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('ZAF');
  const [macroData, setMacroData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Translations
  const texts = {
    fr: {
      title: "Valeur Ajoutée Macro (World Bank / IMF)",
      subtitle: "Structure sectorielle du PIB des économies africaines (2021-2024)",
      records: "enregistrements",
      sectors: "secteurs",
      loading: "Chargement des données macro...",
      noData: "Aucune donnée disponible pour ce pays.",
      evolutionTitle: "Évolution de la Valeur Ajoutée par Secteur (% du PIB)",
      comparisonTitle: "Comparaison Sectorielle par Année",
      detailsTitle: "Données Détaillées",
      gdpPercent: "% du PIB",
      year: "Année"
    },
    en: {
      title: "Macro Value Added (World Bank / IMF)",
      subtitle: "Sectoral structure of GDP for African economies (2021-2024)",
      records: "records",
      sectors: "sectors",
      loading: "Loading macro data...",
      noData: "No data available for this country.",
      evolutionTitle: "Value Added Evolution by Sector (% of GDP)",
      comparisonTitle: "Sectoral Comparison by Year",
      detailsTitle: "Detailed Data",
      gdpPercent: "% of GDP",
      year: "Year"
    }
  };
  const t = texts[language] || texts.fr;

  useEffect(() => {
    if (selectedCountry) {
      fetchMacroData(selectedCountry);
    }
  }, [selectedCountry]);

  const fetchMacroData = async (countryIso3) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/production/macro/${countryIso3}`);
      const d = response.data;
      setMacroData(typeof d === 'object' && d !== null && !Array.isArray(d) ? d : null);
    } catch (error) {
      console.error('Error fetching macro data:', error);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!macroData || !macroData.data_by_sector) return [];

    const years = [2021, 2022, 2023, 2024];
    return years.map(year => {
      const dataPoint = { year };
      
      Object.entries(macroData.data_by_sector).forEach(([sectorName, records]) => {
        const yearRecord = records.find(r => r.year === year);
        if (yearRecord) {
          dataPoint[sectorName] = yearRecord.value;
        }
      });
      
      return dataPoint;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-3xl font-bold flex items-center gap-3">
            <span>📊</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="text-purple-100 text-lg">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Country Selector */}
      <Card className="overflow-visible">
        <CardContent className="pt-6 overflow-visible">
          <EnhancedCountrySelector
            value={selectedCountry}
            onChange={setSelectedCountry}
            label={language === 'en' ? "Country" : "Pays"}
            language={language}
          />
          {macroData && (
            <div className="mt-3">
              <Badge variant="outline" className="text-sm">
                {macroData.total_records} {t.records} • {Object.keys(macroData.data_by_sector).length} {t.sectors}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts */}
      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : macroData && macroData.data_by_sector ? (
        <>
          {/* Line Chart: Evolution temporelle */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
              <CardTitle className="text-xl text-purple-700">
                📈 {t.evolutionTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={prepareChartData()} margin={{ left: 50, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis label={{ value: t.gdpPercent, angle: -90, position: 'insideLeft', offset: -10, style: { fontSize: 11 } }} />
                  <Tooltip />
                  <Legend />
                  {Object.keys(macroData.data_by_sector).map((sector, index) => (
                    <Line 
                      key={sector}
                      type="monotone" 
                      dataKey={sector} 
                      stroke={['#8b5cf6', '#3b82f6', '#10b981'][index % 3]}
                      strokeWidth={2}
                      dot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Bar Chart: Comparison par année */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-indigo-50 to-blue-50">
              <CardTitle className="text-xl text-indigo-700">
                📊 {t.comparisonTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={prepareChartData()} margin={{ left: 50, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis label={{ value: t.gdpPercent, angle: -90, position: 'insideLeft', offset: -10, style: { fontSize: 11 } }} />
                  <Tooltip />
                  <Legend />
                  {Object.keys(macroData.data_by_sector).map((sector, index) => (
                    <Bar 
                      key={sector}
                      dataKey={sector} 
                      fill={['#8b5cf6', '#3b82f6', '#10b981'][index % 3]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Details Table */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50">
              <CardTitle className="text-xl text-gray-700">
                📋 {t.detailsTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {Object.entries(macroData.data_by_sector).map(([sectorName, records]) => (
                  <div key={sectorName} className="border-l-4 border-purple-500 pl-4 py-2 bg-purple-50 rounded">
                    <h4 className="font-bold text-purple-700 mb-2">{sectorName}</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {records.map(record => (
                        <div key={record.year} className="bg-white p-2 rounded shadow-sm">
                          <p className="text-xs text-gray-600">{t.year} {record.year}</p>
                          <p className="text-lg font-bold text-purple-600">{record.value}%</p>
                          <Badge variant="outline" className="text-xs mt-1">
                            {record.indicator_label.split(',')[0]}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="text-center py-12 text-gray-500">
            {t.noData}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ProductionMacro;
