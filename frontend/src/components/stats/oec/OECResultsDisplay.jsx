/**
 * OEC Results Display Component
 * Displays charts and tables for trade data results
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie, Legend } from 'recharts';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { getCountryFlag } from '../../../utils/countryCodes';
import { COLORS, formatValue, formatQuantity } from './utils';

/**
 * Prepare chart data from API response
 */
export const prepareChartData = (data, type) => {
  if (!data) return [];
  
  let items = [];
  if (type === 'country') {
    items = data.products?.slice(0, 8) || [];
    return items.map((item, index) => ({
      name: (item.product_name_short || item.product_name || item.hs_code || '').slice(0, 15),
      fullName: item.product_name || item.hs_code,
      value: item.trade_value || item.value || 0,
      volume: item.quantity || 0,
      fill: COLORS[index % COLORS.length]
    }));
  } else if (type === 'product') {
    items = data.countries?.slice(0, 8) || data.data?.slice(0, 8) || [];
    return items.map((item, index) => ({
      name: (item.country_name || item.partner_name || item.iso3 || '').slice(0, 12),
      fullName: item.country_name || item.partner_name || item.iso3,
      value: item.trade_value || item.value || 0,
      volume: item.quantity || 0,
      fill: COLORS[index % COLORS.length]
    }));
  } else if (type === 'bilateral') {
    items = data.products?.slice(0, 8) || [];
    return items.map((item, index) => ({
      name: (item.product_name || item.hs_code || '').slice(0, 15),
      fullName: item.product_name || item.hs_code,
      value: item.trade_value || item.value || 0,
      volume: item.quantity || 0,
      fill: COLORS[index % COLORS.length]
    }));
  }
  return [];
};

/**
 * Country Trade Results Display
 */
export function CountryResultsDisplay({ data, selectedFlow, selectedYear, t }) {
  if (!data) return null;
  
  const chartData = prepareChartData(data, 'country');
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Summary Card with Chart */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-50 to-cyan-50 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-slate-800">
              {selectedFlow === 'exports' ? t.exports : t.imports} - {data.country?.name_fr || data.country?.name_en}
            </CardTitle>
            <Badge variant="outline" className="text-emerald-700 border-emerald-300">
              {t.dataYear} {selectedYear}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center p-3 bg-emerald-50 rounded-lg">
              <p className="text-xs text-emerald-600 mb-1">{t.totalValue}</p>
              <p className="text-2xl font-bold text-emerald-800">{formatValue(data.total_value || 0)}</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
              <p className="text-2xl font-bold text-blue-800">
                {formatQuantity(data.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span>
              </p>
            </div>
          </div>
          <p className="text-sm text-slate-500 text-center mb-4">{data.total_products} {t.topProducts}</p>
          
          {/* Bar Chart */}
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical">
                <XAxis type="number" tickFormatter={(v) => formatValue(v)} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} />
                <Tooltip 
                  formatter={(v) => formatValue(v)} 
                  labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card className="shadow-lg">
        <CardHeader className="border-b">
          <CardTitle className="text-lg font-semibold">{t.topProducts}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-80 overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-50">
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>{t.product} (Code HS)</TableHead>
                  <TableHead className="text-right">{t.value}</TableHead>
                  <TableHead className="text-right">{t.volume}</TableHead>
                  <TableHead className="text-right">{t.share}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.products?.slice(0, 15).map((item, index) => (
                  <TableRow key={index} className="hover:bg-slate-50">
                    <TableCell className="font-medium text-slate-500">{index + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-start gap-2">
                        <Badge variant="secondary" className="bg-slate-100 text-slate-700 font-mono text-xs px-1.5 py-0.5 shrink-0">
                          {item.hs_code}
                        </Badge>
                        <span className="font-medium text-sm">{item.product_name_short || item.product_name || '-'}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-semibold text-emerald-700">
                      {formatValue(item.trade_value || item.value || 0)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {item.quantity ? formatQuantity(item.quantity) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="font-mono">
                        {item.share ? `${item.share.toFixed(1)}%` : '-'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Product Trade Results Display
 */
export function ProductResultsDisplay({ data, hsCode, hsCodeName, selectedYear, t }) {
  if (!data) return null;
  
  const chartData = prepareChartData(data, 'product');
  const displayCountries = data.countries || data.data || [];
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Summary Card */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 border-b">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold text-slate-800">
                HS {hsCode}
              </CardTitle>
              {hsCodeName && (
                <p className="text-sm text-slate-600 mt-1">{hsCodeName}</p>
              )}
            </div>
            <Badge variant="outline" className="text-purple-700 border-purple-300">
              {t.dataYear} {selectedYear}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <p className="text-xs text-purple-600 mb-1">{t.totalValue}</p>
              <p className="text-2xl font-bold text-purple-800">{formatValue(data.total_value || 0)}</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
              <p className="text-2xl font-bold text-blue-800">
                {formatQuantity(data.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span>
              </p>
            </div>
          </div>
          
          {/* Pie Chart */}
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => formatValue(v)} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Countries Table */}
      <Card className="shadow-lg">
        <CardHeader className="border-b">
          <CardTitle className="text-lg font-semibold">{t.africanExporters}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-80 overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-50">
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>{t.country}</TableHead>
                  <TableHead className="text-right">{t.value}</TableHead>
                  <TableHead className="text-right">{t.volume}</TableHead>
                  <TableHead className="text-right">{t.share}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayCountries.slice(0, 15).map((item, index) => (
                  <TableRow key={index} className="hover:bg-slate-50">
                    <TableCell className="font-medium text-slate-500">{index + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{getCountryFlag(item.iso3 || item.country_code)}</span>
                        <span className="font-medium">{item.country_name || item.partner_name || item.iso3}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-semibold text-purple-700">
                      {formatValue(item.trade_value || item.value || 0)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {item.quantity ? formatQuantity(item.quantity) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="font-mono">
                        {item.share ? `${item.share.toFixed(1)}%` : '-'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Bilateral Trade Results Display
 */
export function BilateralResultsDisplay({ data, selectedYear, t }) {
  if (!data) return null;
  
  const chartData = prepareChartData(data, 'bilateral');
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Summary Card */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-amber-50 to-orange-50 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-slate-800">
              {t.bilateralTitle}
            </CardTitle>
            <Badge variant="outline" className="text-amber-700 border-amber-300">
              {t.dataYear} {selectedYear}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Trade Flow Info */}
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="text-center">
              <span className="text-2xl">{getCountryFlag(data.exporter_iso3)}</span>
              <p className="text-sm font-medium">{data.exporter_name}</p>
              <p className="text-xs text-slate-500">{t.exporter}</p>
            </div>
            <ArrowUpRight className="w-8 h-8 text-emerald-500" />
            <div className="text-center">
              <span className="text-2xl">{getCountryFlag(data.importer_iso3)}</span>
              <p className="text-sm font-medium">{data.importer_name}</p>
              <p className="text-xs text-slate-500">{t.importer}</p>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <p className="text-xs text-amber-600 mb-1">{t.totalValue}</p>
              <p className="text-2xl font-bold text-amber-800">{formatValue(data.total_value || 0)}</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
              <p className="text-2xl font-bold text-blue-800">
                {formatQuantity(data.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span>
              </p>
            </div>
          </div>
          
          {/* Bar Chart */}
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical">
                <XAxis type="number" tickFormatter={(v) => formatValue(v)} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => formatValue(v)} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card className="shadow-lg">
        <CardHeader className="border-b">
          <CardTitle className="text-lg font-semibold">{t.topProducts}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-80 overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-50">
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>{t.product} (Code HS)</TableHead>
                  <TableHead className="text-right">{t.value}</TableHead>
                  <TableHead className="text-right">{t.share}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.products?.slice(0, 15).map((item, index) => (
                  <TableRow key={index} className="hover:bg-slate-50">
                    <TableCell className="font-medium text-slate-500">{index + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-start gap-2">
                        <Badge variant="secondary" className="bg-amber-100 text-amber-700 font-mono text-xs px-1.5 py-0.5 shrink-0">
                          {item.hs_code}
                        </Badge>
                        <span className="font-medium text-sm">{item.product_name || '-'}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-semibold text-amber-700">
                      {formatValue(item.trade_value || item.value || 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="font-mono">
                        {item.share ? `${item.share.toFixed(1)}%` : '-'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
