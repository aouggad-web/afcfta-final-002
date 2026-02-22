/**
 * Tax Breakdown Chart Component
 * Displays all taxes with their names in visual charts
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

// African-inspired color palette
const COLORS = {
  dd: '#dc2626',      // Red - Customs Duties
  vat: '#f59e0b',     // Amber - VAT
  tpi: '#8b5cf6',     // Purple - TPI
  cedeao: '#10b981',  // Emerald - CEDEAO
  pcs: '#3b82f6',     // Blue - PCS
  rs: '#06b6d4',      // Cyan - RS
  ciss: '#ec4899',    // Pink - CISS
  tcs: '#14b8a6',     // Teal - TCS
  prct: '#f97316',    // Orange - PRCT
  other: '#6b7280',   // Gray - Other
  cif: '#475569',     // Slate - CIF Value
  savings: '#22c55e'  // Green - Savings
};

// Get color for tax code
const getTaxColor = (taxCode) => {
  const code = taxCode?.toLowerCase().replace(/[.\s]/g, '') || '';
  if (code.includes('dd') || code.includes('douane')) return COLORS.dd;
  if (code.includes('tva') || code.includes('vat')) return COLORS.vat;
  if (code.includes('tpi')) return COLORS.tpi;
  if (code.includes('cedeao') || code.includes('ecowas')) return COLORS.cedeao;
  if (code.includes('pcs')) return COLORS.pcs;
  if (code.includes('rs') || code.includes('redevance')) return COLORS.rs;
  if (code.includes('ciss')) return COLORS.ciss;
  if (code.includes('tcs')) return COLORS.tcs;
  if (code.includes('prct')) return COLORS.prct;
  return COLORS.other;
};

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#1B232C', padding: '12px', borderRadius: '8px', border: '1px solid rgba(212,175,55,0.3)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}>
        <p style={{ fontWeight: '600', color: '#F5F5F5', marginBottom: '8px' }}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ fontSize: '14px', color: entry.color }}>
            {entry.name}: {formatCurrency(entry.value)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Pie chart tooltip
const PieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{ background: '#1B232C', padding: '12px', borderRadius: '8px', border: '1px solid rgba(212,175,55,0.3)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}>
        <p style={{ fontWeight: '600', color: '#F5F5F5' }}>{data.name}</p>
        <p style={{ fontSize: '14px', color: '#A0AAB4' }}>{data.fullName}</p>
        <p style={{ fontWeight: 'bold', marginTop: '4px', color: data.fill }}>
          {formatCurrency(data.value)} ({data.percentage}%)
        </p>
      </div>
    );
  }
  return null;
};

/**
 * Stacked Bar Chart comparing NPF vs ZLECAf
 */
export function TaxComparisonBarChart({ npfTaxes, zlecafTaxes, cifValue, language = 'fr' }) {
  // Build data for chart
  const allTaxCodes = new Set();
  npfTaxes.forEach(t => allTaxCodes.add(t.tax));
  zlecafTaxes.forEach(t => allTaxCodes.add(t.tax));
  
  const npfData = { name: language === 'fr' ? 'Régime NPF' : 'MFN Regime' };
  const zlecafData = { name: language === 'fr' ? 'Régime ZLECAf' : 'AfCFTA Regime' };
  
  // Add CIF as base
  npfData['Valeur CIF'] = cifValue;
  zlecafData['Valeur CIF'] = cifValue;
  
  // Add each tax
  npfTaxes.forEach(t => {
    const amount = cifValue * (t.rate / 100);
    npfData[t.tax] = amount;
  });
  
  zlecafTaxes.forEach(t => {
    // DD is exempt under ZLECAf
    const isDD = t.tax.toLowerCase().includes('d.d') || t.tax.toLowerCase().includes('douane');
    const amount = isDD ? 0 : cifValue * (t.rate / 100);
    zlecafData[t.tax] = amount;
  });
  
  const chartData = [npfData, zlecafData];
  
  // Build bars dynamically
  const taxBars = Array.from(allTaxCodes).map(taxCode => ({
    key: taxCode,
    color: getTaxColor(taxCode)
  }));
  
  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl">📊</span>
          {language === 'fr' ? 'Comparaison des Coûts Totaux' : 'Total Cost Comparison'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="Valeur CIF" stackId="a" fill={COLORS.cif} name="Valeur CIF" />
            {taxBars.map(({ key, color }) => (
              <Bar key={key} dataKey={key} stackId="a" fill={color} name={key} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

/**
 * Donut/Pie Chart showing tax distribution
 */
export function TaxDistributionPieChart({ taxes, cifValue, regime, language = 'fr' }) {
  // Calculate tax amounts
  const totalTaxes = taxes.reduce((sum, t) => sum + (cifValue * t.rate / 100), 0);
  
  const pieData = taxes.map(t => {
    const amount = cifValue * (t.rate / 100);
    return {
      name: t.tax,
      fullName: t.observation || t.tax,
      value: amount,
      percentage: totalTaxes > 0 ? ((amount / totalTaxes) * 100).toFixed(1) : 0,
      fill: getTaxColor(t.tax)
    };
  }).filter(d => d.value > 0);
  
  const regimeLabel = regime === 'npf' 
    ? (language === 'fr' ? 'Régime NPF' : 'MFN Regime')
    : (language === 'fr' ? 'Régime ZLECAf' : 'AfCFTA Regime');
  
  const regimeColor = regime === 'npf' ? '#EF4444' : '#10b981';
  
  return (
    <Card className="shadow-lg" style={{ background: '#1B232C' }}>
      <CardHeader className="pb-2" style={{ background: `rgba(${regime === 'npf' ? '239,68,68' : '16,185,129'},0.1)` }}>
        <CardTitle className="text-lg flex items-center gap-2" style={{ color: regimeColor }}>
          <span className="text-2xl">🥧</span>
          {language === 'fr' ? 'Répartition des Taxes' : 'Tax Distribution'} - {regimeLabel}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row items-center gap-4">
          <div className="w-full lg:w-1/2">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percentage }) => `${name}: ${percentage}%`}
                  labelLine={false}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<PieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="w-full lg:w-1/2 space-y-2">
            <p className="font-semibold mb-3" style={{ color: '#A0AAB4' }}>
              {language === 'fr' ? 'Total des taxes:' : 'Total taxes:'} 
              <span className="text-xl ml-2" style={{ color: regimeColor }}>{formatCurrency(totalTaxes)}</span>
            </p>
            {pieData.map((tax, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <div className="flex items-center gap-2">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: tax.fill }}
                  />
                  <span className="font-medium text-sm" style={{ color: '#F5F5F5' }}>{tax.name}</span>
                  {tax.fullName !== tax.name && (
                    <span className="text-xs" style={{ color: '#A0AAB4' }}>({tax.fullName})</span>
                  )}
                </div>
                <div className="text-right">
                  <span className="font-bold text-sm" style={{ color: '#F5F5F5' }}>{formatCurrency(tax.value)}</span>
                  <span className="text-xs ml-1" style={{ color: '#A0AAB4' }}>({tax.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Detailed Tax Table with all tax names
 */
export function DetailedTaxTable({ taxes, cifValue, regime, language = 'fr', isZlecaf = false }) {
  const regimeLabel = regime === 'npf' 
    ? (language === 'fr' ? 'Régime NPF (Normale)' : 'MFN Regime (Normal)')
    : (language === 'fr' ? 'Régime ZLECAf (Préférentiel)' : 'AfCFTA Regime (Preferential)');
  
  const regimeColor = isZlecaf ? '#10b981' : '#3B82F6';
  
  let runningTotal = cifValue;
  const taxRows = taxes.map(t => {
    const isDD = t.tax.toLowerCase().includes('d.d') || t.tax.toLowerCase().includes('douane');
    const isExempt = isZlecaf && isDD;
    const rate = isExempt ? 0 : t.rate;
    const amount = cifValue * (rate / 100);
    runningTotal += amount;
    
    return {
      code: t.tax,
      name: t.observation || t.tax,
      rate: t.rate,
      effectiveRate: rate,
      amount: amount,
      cumulative: runningTotal,
      isExempt: isExempt,
      color: getTaxColor(t.tax)
    };
  });
  
  const totalTaxes = taxRows.reduce((sum, t) => sum + t.amount, 0);
  
  return (
    <Card className="shadow-lg" style={{ background: '#1B232C', border: `1px solid ${isZlecaf ? 'rgba(16,185,129,0.3)' : 'rgba(59,130,246,0.3)'}` }}>
      <CardHeader className="pb-2" style={{ background: `rgba(${isZlecaf ? '16,185,129' : '59,130,246'},0.1)` }}>
        <CardTitle className="text-lg flex items-center gap-2" style={{ color: regimeColor }}>
          {isZlecaf ? '✓' : '📋'} {regimeLabel}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: `rgba(${isZlecaf ? '16,185,129' : '59,130,246'},0.15)` }}>
                <th className="text-left p-2 font-semibold" style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'Code Taxe' : 'Tax Code'}
                </th>
                <th className="text-left p-2 font-semibold" style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'Intitulé' : 'Description'}
                </th>
                <th className="text-center p-2 font-semibold" style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'Taux' : 'Rate'}
                </th>
                <th className="text-right p-2 font-semibold" style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'Montant' : 'Amount'}
                </th>
                <th className="text-right p-2 font-semibold" style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'Cumulatif' : 'Cumulative'}
                </th>
              </tr>
            </thead>
            <tbody>
              {/* CIF Row */}
              <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                <td className="p-2 font-semibold" style={{ color: '#F5F5F5' }}>CIF</td>
                <td className="p-2 font-semibold" style={{ color: '#F5F5F5' }}>{language === 'fr' ? 'Valeur en douane' : 'Customs Value'}</td>
                <td className="text-center p-2" style={{ color: '#A0AAB4' }}>-</td>
                <td className="text-right p-2" style={{ color: '#F5F5F5' }}>{formatCurrency(cifValue)}</td>
                <td className="text-right p-2" style={{ color: '#F5F5F5' }}>{formatCurrency(cifValue)}</td>
              </tr>
              
              {/* Tax Rows */}
              {taxRows.map((tax, idx) => (
                <tr 
                  key={idx} 
                  style={{ 
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    background: tax.isExempt ? 'rgba(16,185,129,0.1)' : 'transparent'
                  }}
                >
                  <td className="p-2">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: tax.color }}
                      />
                      <span className="font-mono font-medium" style={{ color: '#F5F5F5' }}>{tax.code}</span>
                    </div>
                  </td>
                  <td className="p-2">
                    <span style={{ color: tax.isExempt ? '#10b981' : '#F5F5F5' }}>
                      {tax.name}
                    </span>
                    {tax.isExempt && (
                      <Badge className="ml-2 text-xs" style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>
                        {language === 'fr' ? 'Exonéré ZLECAf' : 'AfCFTA Exempt'}
                      </Badge>
                    )}
                  </td>
                  <td className="text-center p-2">
                    <span style={{ textDecoration: tax.isExempt ? 'line-through' : 'none', color: tax.isExempt ? '#6B7280' : '#F5F5F5' }}>
                      {tax.rate}%
                    </span>
                    {tax.isExempt && (
                      <span className="ml-1 font-bold" style={{ color: '#10b981' }}>→ 0%</span>
                    )}
                  </td>
                  <td className="text-right p-2 font-mono" style={{ color: tax.isExempt ? '#10b981' : '#F5F5F5' }}>
                    {formatCurrency(tax.amount)}
                  </td>
                  <td className="text-right p-2 font-mono" style={{ color: '#A0AAB4' }}>
                    {formatCurrency(tax.cumulative)}
                  </td>
                </tr>
              ))}
              
              {/* Total Row */}
              <tr className="font-bold" style={{ background: `rgba(${isZlecaf ? '16,185,129' : '59,130,246'},0.15)` }}>
                <td className="p-2" colSpan={2} style={{ color: '#F5F5F5' }}>
                  {language === 'fr' ? 'TOTAL À PAYER' : 'TOTAL TO PAY'}
                </td>
                <td className="text-center p-2" style={{ color: '#F5F5F5' }}>
                  {((totalTaxes / cifValue) * 100).toFixed(1)}%
                </td>
                <td className="text-right p-2 text-lg" style={{ color: '#F5F5F5' }}>
                  {formatCurrency(totalTaxes)}
                </td>
                <td className="text-right p-2 text-lg" style={{ color: regimeColor }}>
                  {formatCurrency(cifValue + totalTaxes)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Savings Highlight Card
 */
export function SavingsHighlight({ npfTotal, zlecafTotal, language = 'fr' }) {
  const savings = npfTotal - zlecafTotal;
  const savingsPercent = ((savings / npfTotal) * 100).toFixed(1);
  
  return (
    <Card className="bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 text-white shadow-xl">
      <CardContent className="py-6">
        <div className="text-center">
          <p className="text-lg opacity-90 mb-2">
            {language === 'fr' ? '💰 Économies avec ZLECAf' : '💰 Savings with AfCFTA'}
          </p>
          <p className="text-5xl font-bold mb-3">{formatCurrency(savings)}</p>
          <div className="flex justify-center gap-6 text-sm opacity-90">
            <div>
              <span className="opacity-70">{language === 'fr' ? 'Coût NPF:' : 'MFN Cost:'}</span>
              <span className="ml-2 font-semibold line-through">{formatCurrency(npfTotal)}</span>
            </div>
            <div>
              <span className="opacity-70">{language === 'fr' ? 'Coût ZLECAf:' : 'AfCFTA Cost:'}</span>
              <span className="ml-2 font-semibold">{formatCurrency(zlecafTotal)}</span>
            </div>
          </div>
          <Badge className="mt-4 bg-white/20 text-white text-lg px-4 py-1">
            -{savingsPercent}% {language === 'fr' ? 'd\'économie' : 'savings'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

export default {
  TaxComparisonBarChart,
  TaxDistributionPieChart,
  DetailedTaxTable,
  SavingsHighlight
};
