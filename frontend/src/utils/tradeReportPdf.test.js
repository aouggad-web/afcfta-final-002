import { describe, it, expect } from 'vitest';
import { buildTradeReportPdf, tradeReportFilename } from './tradeReportPdf';

const fmtUSD = (v) => {
  if (v == null || isNaN(v)) return '—';
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};
const fmtTonnes = (v) => {
  if (v == null || isNaN(v) || v <= 0) return '—';
  if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M t`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K t`;
  return `${v.toFixed(v < 10 ? 1 : 0)} t`;
};

// Reproduit le cas de référence : Algérie / SH 901832, imports >> exports
// (coefficient de couverture proche de 0) — le cas le plus exigeant pour
// l'échelle du graphique double-panneau.
const dominantImportsData = {
  country_name: 'Algérie',
  hs_code: '901832',
  currency: 'USD',
  source: 'OEC / BACI (SH rév. 2017)',
  hs_labels: [{ label: 'Aiguilles tubulaires en métal et aiguilles de suture' }],
  chart_rows: [
    { year: 2020, exports: 300, exports_quantity: 7.8, imports: 6_100_000, imports_quantity: 387, balance: -6_099_700 },
    { year: 2021, exports: 48_000, exports_quantity: 2.0, imports: 6_900_000, imports_quantity: 414, balance: -6_852_000 },
    { year: 2022, exports: 7_000, exports_quantity: 0.2, imports: 8_600_000, imports_quantity: 610, balance: -8_593_000 },
    { year: 2023, exports: 20_000, exports_quantity: 1.2, imports: 6_700_000, imports_quantity: 450, balance: -6_680_000 },
    { year: 2024, exports: 100, exports_quantity: 0, imports: 10_200_000, imports_quantity: 682, balance: -10_199_900 },
  ],
};

const dominantExportsData = {
  country_name: 'Côte d\'Ivoire',
  hs_code: '180100',
  currency: 'USD',
  source: 'OEC / BACI (SH rév. 2017)',
  hs_labels: [{ label: 'Cacao en fèves' }],
  chart_rows: [
    { year: 2020, exports: 2_000_000_000, exports_quantity: 900_000, imports: 5_000_000, imports_quantity: 200, balance: 1_995_000_000 },
    { year: 2021, exports: 2_400_000_000, exports_quantity: 950_000, imports: 6_000_000, imports_quantity: 220, balance: 2_394_000_000 },
  ],
};

const closeScaleData = {
  country_name: 'Maroc',
  hs_code: '870323',
  currency: 'USD',
  source: 'OEC / BACI (SH rév. 2017)',
  hs_labels: [{ label: 'Voitures de tourisme' }],
  chart_rows: [
    { year: 2023, exports: 900_000_000, exports_quantity: 40_000, imports: 800_000_000, imports_quantity: 35_000, balance: 100_000_000 },
    { year: 2024, exports: 950_000_000, exports_quantity: 42_000, imports: 1_000_000_000, imports_quantity: 44_000, balance: -50_000_000 },
  ],
};

function totalsOf(data) {
  const rows = data.chart_rows;
  const exp = rows.reduce((s, r) => s + r.exports, 0);
  const imp = rows.reduce((s, r) => s + r.imports, 0);
  return { exports: exp, imports: imp, balance: exp - imp };
}

describe('buildTradeReportPdf', () => {
  const baseParams = (data, overrides = {}) => ({
    data,
    totals: totalsOf(data),
    language: 'fr',
    levelLen: 6,
    matchLevelLabel: 'SH6 exact',
    fmtUSD,
    fmtTonnes,
    ...overrides,
  });

  it('builds a light-theme doc without throwing (dominant imports, extreme scale gap)', () => {
    const doc = buildTradeReportPdf(baseParams(dominantImportsData, { theme: 'light' }));
    expect(doc).toBeDefined();
    const bytes = doc.output('arraybuffer');
    expect(bytes.byteLength).toBeGreaterThan(1000);
  });

  it('builds a dark-theme doc without throwing (dominant imports, extreme scale gap)', () => {
    const doc = buildTradeReportPdf(baseParams(dominantImportsData, { theme: 'dark' }));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles a dominant-exports country (surplus) without throwing', () => {
    const doc = buildTradeReportPdf(baseParams(dominantExportsData, { theme: 'light' }));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles close-scale flows (deficit flips sign across years) without throwing', () => {
    const doc = buildTradeReportPdf(baseParams(closeScaleData, { theme: 'light' }));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles English language without throwing', () => {
    const doc = buildTradeReportPdf(baseParams(dominantImportsData, { language: 'en', theme: 'dark' }));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles a single-year series (CAGR undefined) without throwing', () => {
    const single = { ...dominantImportsData, chart_rows: [dominantImportsData.chart_rows[0]] };
    const doc = buildTradeReportPdf(baseParams(single));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles an all-zero series without throwing (no NaN/Infinity in geometry)', () => {
    const zeroed = {
      ...dominantImportsData,
      chart_rows: dominantImportsData.chart_rows.map((r) => ({
        ...r, exports: 0, exports_quantity: 0, imports: 0, imports_quantity: 0, balance: 0,
      })),
    };
    const doc = buildTradeReportPdf(baseParams(zeroed));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('handles a long series that forces table pagination (10 years)', () => {
    const many = {
      ...dominantImportsData,
      chart_rows: Array.from({ length: 10 }, (_, i) => ({
        year: 2015 + i,
        exports: 1000 * (i + 1),
        exports_quantity: i + 1,
        imports: 5_000_000 * (i + 1),
        imports_quantity: 300 + i * 10,
        balance: 1000 * (i + 1) - 5_000_000 * (i + 1),
      })),
    };
    const doc = buildTradeReportPdf(baseParams(many));
    expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(1);
  });

  it('missing hs_labels / no product title does not throw', () => {
    const noLabel = { ...dominantImportsData, hs_labels: [] };
    const doc = buildTradeReportPdf(baseParams(noLabel));
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });
});

describe('tradeReportFilename', () => {
  it('produces a stable, filesystem-safe filename', () => {
    const name = tradeReportFilename(dominantImportsData);
    expect(name).toBe('ZLECAf_Algérie_SH901832_2020-2024');
    expect(name).not.toMatch(/[/\\]/);
  });

  it('handles missing chart_rows gracefully', () => {
    const name = tradeReportFilename({ country_name: 'Kenya', hs_code: '090111' });
    expect(name).toBe('ZLECAf_Kenya_SH090111_');
  });
});
