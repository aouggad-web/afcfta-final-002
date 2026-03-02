import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function ProductionMining({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('ZAF');
  const [miningData, setMiningData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Translations
  const texts = {
    fr: {
      title: "Production Minière (USGS)",
      subtitle: "Production de minerais et métaux par pays africain (2021-2024)",
      records: "enregistrements",
      minerals: "minerais",
      loading: "Chargement des données minières...",
      noData: "Aucune donnée minière disponible pour ce pays.",
      evolutionTitle: "Évolution de la Production Minière",
      comparisonTitle: "Production par Minerai et Année",
      detailsTitle: "Données Détaillées par Minerai",
      production: "Production",
      year: "Année"
    },
    en: {
      title: "Mining Production (USGS)",
      subtitle: "Mineral and metal production by African country (2021-2024)",
      records: "records",
      minerals: "minerals",
      loading: "Loading mining data...",
      noData: "No mining data available for this country.",
      evolutionTitle: "Mining Production Evolution",
      comparisonTitle: "Production by Mineral and Year",
      detailsTitle: "Detailed Data by Mineral",
      production: "Production",
      year: "Year"
    }
  };
  const t = texts[language] || texts.fr;

  useEffect(() => {
    if (selectedCountry) {
      fetchMiningData(selectedCountry);
    }
  }, [selectedCountry]);

  const fetchMiningData = async (countryIso3) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/production/mining/${countryIso3}`);
      setMiningData(response.data);
    } catch (error) {
      console.error('Error fetching mining data:', error);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!miningData || !miningData.data_by_commodity) return [];

    const years = [2021, 2022, 2023, 2024];
    return years.map(year => {
      const dataPoint = { year };
      
      Object.entries(miningData.data_by_commodity).forEach(([commodity, records]) => {
        const yearRecord = records.find(r => r.year === year);
        if (yearRecord) {
          dataPoint[commodity] = yearRecord.value;
        }
      });
      
      return dataPoint;
    });
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-3xl font-bold flex items-center gap-3">
            <span>⛏️</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="text-amber-100 text-lg">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Country Selector */}
      <Card>
        <CardContent className="pt-6">
          <EnhancedCountrySelector
            value={selectedCountry}
            onChange={setSelectedCountry}
            label={language === 'en' ? "Country" : "Pays"}
            language={language}
          />
          {miningData && (
            <div className="mt-3">
              <Badge variant="outline" className="text-sm">
                {miningData.total_records} {t.records} • {Object.keys(miningData.data_by_commodity).length} {t.minerals}
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
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : miningData && miningData.data_by_commodity ? (
        <>
          {/* Line Chart: Evolution Production */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-amber-50 to-orange-50">
              <CardTitle className="text-xl text-amber-700">
                📈 {t.evolutionTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={prepareChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis 
                    label={{ value: t.production, angle: -90, position: 'insideLeft' }}
                    tickFormatter={formatNumber}
                  />
                  <Tooltip 
                    formatter={(value, name, props) => {
                      const unit = Object.values(miningData.data_by_commodity)[0]?.[0]?.unit || '';
                      return `${value.toLocaleString()} ${unit}`;
                    }}
                  />
                  <Legend />
                  {Object.keys(miningData.data_by_commodity).map((commodity, index) => (
                    <Line 
                      key={commodity}
                      type="monotone" 
                      dataKey={commodity} 
                      stroke={['#f59e0b', '#ea580c', '#dc2626'][index % 3]}
                      strokeWidth={2}
                      dot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Bar Chart: Comparison */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50">
              <CardTitle className="text-xl text-orange-700">
                📊 {t.comparisonTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={prepareChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis 
                    label={{ value: t.production, angle: -90, position: 'insideLeft' }}
                    tickFormatter={formatNumber}
                  />
                  <Tooltip 
                    formatter={(value, name, props) => {
                      const unit = Object.values(miningData.data_by_commodity)[0]?.[0]?.unit || '';
                      return `${value.toLocaleString()} ${unit}`;
                    }}
                  />
                  <Legend />
                  {Object.keys(miningData.data_by_commodity).map((commodity, index) => (
                    <Bar 
                      key={commodity}
                      dataKey={commodity} 
                      fill={['#f59e0b', '#ea580c', '#dc2626'][index % 3]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Details Cards */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50">
              <CardTitle className="text-xl text-gray-700">
                ⛏️ {t.detailsTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(miningData.data_by_commodity).map(([commodity, records]) => (
                  <div key={commodity} className="border-l-4 border-amber-500 pl-4 py-3 bg-amber-50 rounded-lg">
                    <h4 className="font-bold text-amber-700 text-lg mb-3 flex items-center gap-2">
                      💎 {commodity}
                    </h4>
                    <div className="space-y-2">
                      {records.map(record => (
                        <div key={record.year} className="bg-white p-3 rounded shadow-sm flex justify-between items-center">
                          <div>
                            <p className="text-sm text-gray-600">{t.year} {record.year}</p>
                            <p className="text-xs text-gray-500">
                              {record.commodity_code} - {record.usgs_table_name}
                            </p>
                            <Badge variant="outline" className="text-xs mt-1">
                              {record.source_dataset}
                            </Badge>
                          </div>
                          <div className="text-right">
                            <p className="text-xl font-bold text-amber-600">
                              {record.value.toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500">{record.unit}</p>
                          </div>
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

export default ProductionMining;
