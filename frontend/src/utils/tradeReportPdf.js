/**
 * Rapport PDF "Fiche Pays-Produit" — commerce bilatéral par pays + code SH.
 *
 * Dessin natif jsPDF (pas de html2canvas) : le graphique est tracé
 * vectoriellement, donc net à n'importe quelle résolution/zoom d'impression,
 * ne dépend pas d'un DOM déjà rendu, et produit un fichier plus léger qu'une
 * capture d'écran rasterisée.
 *
 * Palette reprise de src/styles/theme.css / theme-light.css (thème "Afrique
 * Moderne" de l'application) — deux variantes du même bâtisseur : claire
 * (fond parchemin, optimisée impression) et sombre (nuit africaine, aligné
 * sur le rendu à l'écran de l'appli).
 */
import jsPDF from 'jspdf';

const THEME_LIGHT = {
  name: 'light',
  printNote: { fr: 'Optimisé pour impression.', en: 'Optimized for printing.' },
  page: [250, 246, 238], // --bg (light) FAF6EE
  surface: [255, 255, 255], // --surface FFFFFF
  card2: [245, 239, 227], // --afcfta-card2 F5EFE3
  headerBandFrom: [31, 42, 54], // masthead : encre foncée pour contraste sur fond clair
  headerBandTo: [46, 61, 46],
  terra: [176, 70, 26], // B0461A
  gold: [184, 118, 26], // B8761A
  green: [21, 106, 64], // 156A40
  red: [178, 34, 34], // B22222
  text: [31, 42, 54], // 1F2A36
  muted: [92, 107, 128], // 5C6B80
  danger: [184, 48, 48], // B83030
  onBand: [250, 246, 238], // texte clair sur le bandeau d'en-tête foncé
};

const THEME_DARK = {
  name: 'dark',
  printNote: { fr: 'Optimisé pour lecture à l’écran.', en: 'Optimized for on-screen reading.' },
  page: [12, 18, 25], // --bg 0C1219 nuit africaine
  surface: [17, 24, 32], // --surface 111820
  card2: [24, 32, 48], // --afcfta-card 182030
  headerBandFrom: [19, 27, 40], // --afcfta-card2 131B28
  headerBandTo: [12, 18, 25],
  terra: [200, 83, 26], // C8531A
  gold: [212, 137, 26], // D4891A
  green: [26, 122, 74], // 1A7A4A
  red: [198, 43, 43], // C62B2B
  text: [234, 224, 208], // EAE0D0 parchemin
  muted: [142, 155, 174], // 8E9BAE
  danger: [224, 64, 64], // E04040
  onBand: [234, 224, 208],
};

const I18N = {
  fr: {
    tag: 'INTELLIGENCE COMMERCIALE',
    badge: 'FICHE PAYS-PRODUIT',
    period: 'Période analysée',
    match: 'Correspondance',
    exportsAcc: 'EXPORTS CUMULÉS',
    importsAcc: 'IMPORTATIONS CUMULÉES',
    balanceAcc: 'BALANCE CUMULÉE',
    cagrExports: 'TCAM DES EXPORTS',
    cagrImports: 'TCAM DES IMPORTS',
    deficit: 'déficit',
    surplus: 'excédent',
    dynamics: 'DYNAMIQUE DES ÉCHANGES',
    amountsIn: 'Montants en USD',
    scaleNote: 'Échelle distincte pour préserver la lisibilité',
    signal: 'SIGNAL',
    coverage: 'Taux de couverture (exports/imports)',
    detail: 'DÉTAIL ANNUEL',
    roundedValues: 'Valeurs arrondies',
    year: 'Année', exports: 'Exportations', volExp: 'Volume exporté',
    imports: 'Importations', volImp: 'Volume importé', balance: 'Balance commerciale',
    source: 'SOURCE', consulted: 'Consultation', page: 'Page',
    footerNote: 'Montants et volumes arrondis. Les deux graphiques utilisent des échelles distinctes.',
    volLabel: 'Volume (tonnes)', legendBalance: 'Balance', legendValue: 'Valeur',
  },
  en: {
    tag: 'TRADE INTELLIGENCE',
    badge: 'COUNTRY-PRODUCT SHEET',
    period: 'Period analysed',
    match: 'Match',
    exportsAcc: 'CUMULATIVE EXPORTS',
    importsAcc: 'CUMULATIVE IMPORTS',
    balanceAcc: 'CUMULATIVE BALANCE',
    cagrExports: 'EXPORTS CAGR',
    cagrImports: 'IMPORTS CAGR',
    deficit: 'deficit',
    surplus: 'surplus',
    dynamics: 'TRADE DYNAMICS',
    amountsIn: 'Amounts in USD',
    scaleNote: 'Separate scale to preserve readability',
    signal: 'SIGNAL',
    coverage: 'Coverage ratio (exports/imports)',
    detail: 'ANNUAL DETAIL',
    roundedValues: 'Rounded values',
    year: 'Year', exports: 'Exports', volExp: 'Export vol.',
    imports: 'Imports', volImp: 'Import vol.', balance: 'Trade balance',
    source: 'SOURCE', consulted: 'Consulted', page: 'Page',
    footerNote: 'Amounts and volumes are rounded. Both charts use separate scales.',
    volLabel: 'Volume (tonnes)', legendBalance: 'Balance', legendValue: 'Value',
  },
};

const MM = { pageW: 210, pageH: 297, margin: 13 };

function starPoints(cx, cy, outerR, innerR, points, rotationDeg) {
  const pts = [];
  const step = Math.PI / points;
  const rot = (rotationDeg * Math.PI) / 180;
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const a = i * step - Math.PI / 2 + rot;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return pts;
}

function cagrOf(rows, key) {
  if (!rows.length) return null;
  const first = rows[0]?.[key] || 0;
  const last = rows[rows.length - 1]?.[key] || 0;
  if (first <= 0 || last <= 0) return null;
  const years = Math.max(1, rows.length - 1);
  return (Math.pow(last / first, 1 / years) - 1) * 100;
}

function drawEmblem(doc, cx, cy, size, theme) {
  // Insigne "étoile Najm" (motif zellige de Tlemcen documenté dans le design
  // system de l'appli) plutôt qu'un clip-art de silhouette continentale —
  // fidèle au vocabulaire visuel du projet et net en tracé vectoriel simple.
  const r = size / 2;
  doc.setFillColor(...theme.headerBandTo);
  doc.setDrawColor(...theme.gold);
  doc.setLineWidth(0.5);
  doc.roundedRect(cx - r, cy - r, size, size, 1.5, 1.5, 'FD');
  const pts = starPoints(cx, cy, r * 0.62, r * 0.28, 8, 0);
  doc.setDrawColor(...theme.gold);
  doc.setLineWidth(0.35);
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[(i + 1) % pts.length];
    doc.line(x1, y1, x2, y2);
  }
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(5.2);
  doc.setTextColor(...theme.gold);
  doc.text('ZLECAf', cx, cy + r + 3.2, { align: 'center' });
}

function pillBadge(doc, x, y, text, theme) {
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  const padX = 3;
  const w = doc.getTextWidth(text) + padX * 2;
  doc.setFillColor(...theme.terra);
  doc.roundedRect(x, y, w, 6, 3, 3, 'F');
  doc.setTextColor(...theme.onBand);
  doc.text(text, x + padX, y + 4.2);
  return w;
}

function axisUnit(maxAbs, language) {
  if (maxAbs >= 1e6) return { divisor: 1e6, suffix: language === 'fr' ? ' M$' : ' M$' };
  if (maxAbs >= 1e3) return { divisor: 1e3, suffix: language === 'fr' ? ' k$' : ' k$' };
  return { divisor: 1, suffix: '$' };
}

/**
 * Un panneau graphique : barres de valeur (+ étiquette volume optionnelle
 * au-dessus) et, en option, une ligne de balance superposée sur la MÊME
 * échelle. Utilisé deux fois (flux dominant à gauche avec balance, flux
 * mineur à droite sans) — reproduit la lecture "double échelle" du modèle
 * de référence, nécessaire dès que les deux flux diffèrent de plusieurs
 * ordres de grandeur (un flux minoritaire serait sinon invisible sur
 * l'échelle du flux dominant).
 */
function drawFlowPanel(doc, opts) {
  const { x, y, w, h, title, unitCaption, rows, valueKey, qtyKey, barColor, lineValues, lineColor, theme, language, fmtQty } = opts;
  const t = I18N[language] || I18N.fr;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(...theme.text);
  doc.text(title, x, y + 3.5);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.8);
  doc.setTextColor(...theme.muted);
  doc.text(unitCaption, x + w, y + 3.5, { align: 'right' });

  const showLine = Array.isArray(lineValues);
  const values = rows.map((r) => Number(r[valueKey]) || 0);
  const hasQty = qtyKey && rows.some((r) => (r[qtyKey] || 0) > 0);
  const headroomFactor = hasQty ? 1.32 : 1.18;
  const rawMax = Math.max(0, ...values, ...(showLine ? lineValues.map(Math.abs) : []));
  const rawMin = showLine ? Math.min(0, ...lineValues) : 0;
  const maxVal = (rawMax || 1) * headroomFactor;
  const minVal = rawMin < 0 ? rawMin * 1.15 : 0;

  const plotX = x + 11;
  const plotTop = y + 8;
  const plotBottom = y + h - 11;
  const plotW = w - 11 - 2;
  const plotH = plotBottom - plotTop;
  const scale = plotH / (maxVal - minVal || 1);
  const zeroY = plotBottom - (0 - minVal) * scale;

  const { divisor, suffix } = axisUnit(Math.max(Math.abs(maxVal), Math.abs(minVal)), language);
  const glCount = 4;
  doc.setDrawColor(...theme.muted);
  doc.setLineWidth(0.1);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.3);
  for (let i = 0; i <= glCount; i++) {
    const v = minVal + ((maxVal - minVal) * i) / glCount;
    const gy = plotBottom - (v - minVal) * scale;
    doc.setDrawColor(...theme.muted);
    doc.setLineWidth(v === 0 && minVal < 0 ? 0.3 : 0.08);
    doc.line(plotX, gy, plotX + plotW, gy);
    doc.setTextColor(...theme.muted);
    const label = (v / divisor).toFixed(Math.abs(v / divisor) < 10 && v !== 0 ? 1 : 0).replace('.', ',');
    doc.text(`${label}${suffix}`, plotX - 1.5, gy + 1.2, { align: 'right' });
  }

  const n = rows.length;
  const slot = plotW / Math.max(n, 1);
  const barW = Math.min(slot * 0.5, 9);
  const points = [];

  rows.forEach((row, i) => {
    const cx = plotX + i * slot + slot / 2;
    const val = values[i];
    const barH = Math.abs(val) * scale;
    const barY = val >= 0 ? zeroY - barH : zeroY;
    doc.setFillColor(...barColor);
    doc.roundedRect(cx - barW / 2, barY, barW, Math.max(barH, 0.2), 0.6, 0.6, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.6);
    doc.setTextColor(...theme.text);
    const valLabel = (val / divisor).toLocaleString(language === 'fr' ? 'fr-FR' : 'en-US', {
      maximumFractionDigits: Math.abs(val / divisor) < 10 ? 1 : 0,
    });
    doc.text(valLabel, cx, barY - (hasQty ? 5.2 : 1.6), { align: 'center' });
    if (hasQty) {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(5.6);
      doc.setTextColor(...theme.muted);
      doc.text(fmtQty(row[qtyKey]), cx, barY - 1.4, { align: 'center' });
    }

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.8);
    doc.setTextColor(...theme.muted);
    doc.text(String(row.year), cx, plotBottom + 4.5, { align: 'center' });

    if (showLine) points.push([cx, zeroY - lineValues[i] * scale]);
  });

  if (showLine && points.length > 1) {
    doc.setDrawColor(...lineColor);
    doc.setLineWidth(0.6);
    for (let i = 0; i < points.length - 1; i++) {
      doc.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]);
    }
    points.forEach(([px, py]) => {
      doc.setFillColor(...lineColor);
      doc.circle(px, py, 0.9, 'F');
    });
  }

  // Légende
  let lx = x;
  const ly = y + h - 2.5;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.5);
  doc.setFillColor(...barColor);
  doc.rect(lx, ly - 2, 2.6, 2.6, 'F');
  doc.setTextColor(...theme.muted);
  doc.text(t.legendValue, lx + 3.4, ly);
  lx += 3.4 + doc.getTextWidth(t.legendValue) + 5;
  if (showLine) {
    doc.setDrawColor(...lineColor);
    doc.setLineWidth(0.6);
    doc.line(lx, ly - 0.8, lx + 3, ly - 0.8);
    doc.setFillColor(...lineColor);
    doc.circle(lx + 1.5, ly - 0.8, 0.7, 'F');
    doc.text(t.legendBalance, lx + 4.4, ly);
  }
}

function kpiCard(doc, { x, y, w, h, label, value, sub, accent, theme }) {
  doc.setFillColor(...theme.surface);
  doc.roundedRect(x, y, w, h, 1.4, 1.4, 'F');
  doc.setFillColor(...accent);
  doc.rect(x, y, 1.3, h, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.6);
  doc.setTextColor(...theme.muted);
  doc.text(label, x + 4, y + 5.5, { maxWidth: w - 6 });
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13.5);
  doc.setTextColor(...theme.text);
  doc.text(value, x + 4, y + 13, { maxWidth: w - 6 });
  if (sub) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.4);
    doc.setTextColor(...theme.muted);
    doc.text(sub, x + 4, y + h - 2.2);
  }
}

function drawFooter(doc, { theme, t, source, consultedDate, language, pageNum, totalPages, printNote }) {
  const y = MM.pageH - 11;
  doc.setDrawColor(...theme.gold);
  doc.setLineWidth(0.4);
  doc.line(MM.margin, y, MM.pageW - MM.margin, y);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.6);
  doc.setTextColor(...theme.muted);
  doc.text(t.source, MM.margin, y + 4);
  const sourceLabelWidth = doc.getTextWidth(t.source); // mesurée avant setFont('normal') — voir wordmark plus haut
  doc.setFont('helvetica', 'normal');
  doc.text(`${source} • ${t.consulted}: ${consultedDate}`, MM.margin + sourceLabelWidth + 2, y + 4);
  doc.setFontSize(6.2);
  doc.text(`${t.footerNote} ${printNote[language] || ''}`, MM.margin, y + 7.6, { maxWidth: MM.pageW - 2 * MM.margin - 22 });
  doc.setFont('helvetica', 'bold');
  doc.text(`${t.page} ${pageNum}/${totalPages}`, MM.pageW - MM.margin, y + 4, { align: 'right' });
}

/**
 * Construit le document jsPDF (ne l'enregistre pas — l'appelant fait `.save()`).
 *
 * @param {object} p
 * @param {object} p.data       Réponse OEC (country_name, hs_code, hs_labels, chart_rows, source, currency)
 * @param {object} p.totals     { exports, imports, balance, cagr }
 * @param {'fr'|'en'} p.language
 * @param {number} p.levelLen   6 | 4 | 2 (longueur du code SH recherché)
 * @param {string} p.matchLevelLabel  Libellé déjà résolu (SH6 exact, Agrégat SH4…)
 * @param {(v:number)=>string} p.fmtUSD
 * @param {(v:number)=>string} p.fmtTonnes
 * @param {'light'|'dark'} [p.theme]
 */
export function buildTradeReportPdf(p) {
  const { data, totals, language, levelLen, matchLevelLabel, fmtUSD, fmtTonnes, theme: themeName } = p;
  const theme = themeName === 'dark' ? THEME_DARK : THEME_LIGHT;
  const t = I18N[language] || I18N.fr;
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const rows = data.chart_rows || [];
  const years = rows.map((r) => r.year);
  const period = years.length ? `${years[0]}-${years[years.length - 1]}` : '—';

  const paint = () => {
    doc.setFillColor(...theme.page);
    doc.rect(0, 0, MM.pageW, MM.pageH, 'F');
  };
  paint();

  // ── Bandeau d'en-tête ──────────────────────────────────────────────
  const bandH = 40;
  doc.setFillColor(...theme.headerBandFrom);
  doc.rect(0, 0, MM.pageW, bandH, 'F');
  doc.setFillColor(...theme.gold);
  doc.rect(0, bandH - 0.9, MM.pageW, 0.9, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.setTextColor(...theme.onBand);
  const wordmark = 'AFCFTA / ZLECAf';
  doc.text(wordmark, MM.margin, 9);
  // Largeur mesurée AVANT de changer de police : getTextWidth() lit la police
  // actuellement active, pas celle utilisée pour dessiner le texte mesuré —
  // mesurer après le setFont('normal', 6.6) sous-évaluait l'espacement et
  // faisait chevaucher le tag sur le wordmark.
  const wordmarkWidth = doc.getTextWidth(wordmark);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.6);
  doc.setTextColor(...theme.gold);
  doc.text(t.tag, MM.margin + wordmarkWidth + 3, 9);

  pillBadge(doc, MM.margin, 14, t.badge, theme);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(19);
  doc.setTextColor(...theme.onBand);
  const title = language === 'fr' ? `Commerce extérieur — ${data.country_name}` : `Foreign trade — ${data.country_name}`;
  doc.text(title, MM.margin, 27, { maxWidth: MM.pageW - 2 * MM.margin - 24 });

  const productLabel = data.hs_labels?.[0]?.label || '';
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9.5);
  doc.setTextColor(...theme.gold);
  doc.text(`SH${levelLen} ${data.hs_code}  |  ${productLabel}`, MM.margin, 33, { maxWidth: MM.pageW - 2 * MM.margin - 24 });

  doc.setFontSize(7.2);
  doc.setTextColor(...theme.onBand);
  doc.text(`${t.period}: ${period}   •   ${t.match}: ${matchLevelLabel}`, MM.margin, 37.5);

  drawEmblem(doc, MM.pageW - MM.margin - 8, bandH / 2, 15, theme);

  // ── KPI ────────────────────────────────────────────────────────────
  const kpiY = bandH + 6;
  const kpiH = 20;
  const gap = 3;
  const kpiW = (MM.pageW - 2 * MM.margin - 3 * gap) / 4;
  const balanceIsDeficit = (totals?.balance || 0) < 0;
  const dominantIsImports = (totals?.imports || 0) >= (totals?.exports || 0);
  const cagrLabel = dominantIsImports ? t.cagrImports : t.cagrExports;
  const cagrValue = cagrOf(rows, dominantIsImports ? 'imports' : 'exports');

  kpiCard(doc, { x: MM.margin, y: kpiY, w: kpiW, h: kpiH, label: t.exportsAcc, value: fmtUSD(totals?.exports), sub: period, accent: theme.green, theme });
  kpiCard(doc, { x: MM.margin + (kpiW + gap), y: kpiY, w: kpiW, h: kpiH, label: t.importsAcc, value: fmtUSD(totals?.imports), sub: period, accent: theme.red, theme });
  kpiCard(doc, { x: MM.margin + 2 * (kpiW + gap), y: kpiY, w: kpiW, h: kpiH, label: t.balanceAcc, value: fmtUSD(totals?.balance), sub: balanceIsDeficit ? t.deficit : t.surplus, accent: theme.gold, theme });
  kpiCard(doc, { x: MM.margin + 3 * (kpiW + gap), y: kpiY, w: kpiW, h: kpiH, label: cagrLabel, value: cagrValue != null ? `${cagrValue.toFixed(1)}%` : '—', sub: period, accent: theme.gold, theme });

  // ── Graphiques : deux panneaux, chacun sur SA PROPRE échelle ────────
  // Superposer exports et imports sur un même repère quand leurs ordres de
  // grandeur diffèrent (le cas le plus fréquent : un pays africain importe
  // souvent 10-100x ce qu'il exporte d'un même code SH) rend le flux mineur
  // invisible. Deux panneaux à échelle indépendante restent lisibles dans
  // TOUS les cas — flux proches ou très éloignés — donc toujours utilisés ;
  // seul le message d'avertissement "échelle distincte" est conditionnel,
  // pour ne pas alarmer inutilement quand les deux flux sont déjà proches.
  const chartsY = kpiY + kpiH + 8;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.setTextColor(...theme.text);
  doc.text(t.dynamics, MM.margin, chartsY);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(...theme.muted);
  doc.text(`${t.amountsIn} • ${period}`, MM.pageW - MM.margin, chartsY, { align: 'right' });

  const panelsY = chartsY + 4;
  const panelH = 62;
  const maxExp = Math.max(0, ...rows.map((r) => r.exports || 0));
  const maxImp = Math.max(0, ...rows.map((r) => r.imports || 0));
  const domIsImports = maxImp >= maxExp;
  const ratio = domIsImports ? (maxImp || 1) / (maxExp || 1) : (maxExp || 1) / (maxImp || 1);
  const balanceValues = rows.map((r) => r.balance || 0);

  const panelW = (MM.pageW - 2 * MM.margin - 5) / 2;
  doc.setFillColor(...theme.surface);
  doc.roundedRect(MM.margin, panelsY, panelW, panelH, 1.6, 1.6, 'F');
  doc.roundedRect(MM.margin + panelW + 5, panelsY, panelW, panelH, 1.6, 1.6, 'F');

  drawFlowPanel(doc, {
    x: MM.margin + 3, y: panelsY + 3, w: panelW - 6, h: panelH - 5,
    title: domIsImports ? t.imports.toUpperCase() : t.exports.toUpperCase(),
    unitCaption: `USD / ${t.volLabel.toLowerCase()}`,
    rows, valueKey: domIsImports ? 'imports' : 'exports', qtyKey: domIsImports ? 'imports_quantity' : 'exports_quantity',
    barColor: domIsImports ? theme.red : theme.green,
    lineValues: balanceValues, lineColor: theme.gold,
    theme, language, fmtQty: fmtTonnes,
  });
  drawFlowPanel(doc, {
    x: MM.margin + panelW + 5 + 3, y: panelsY + 3, w: panelW - 6, h: panelH - 5,
    title: domIsImports ? t.exports.toUpperCase() : t.imports.toUpperCase(),
    unitCaption: 'USD',
    rows, valueKey: domIsImports ? 'exports' : 'imports', qtyKey: null,
    barColor: domIsImports ? theme.green : theme.red,
    lineValues: null, lineColor: theme.gold,
    theme, language, fmtQty: fmtTonnes,
  });
  if (ratio >= 4) {
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(6.4);
    doc.setTextColor(...theme.muted);
    doc.text(t.scaleNote, MM.pageW - MM.margin, panelsY + panelH + 4, { align: 'right' });
  }

  // ── Signal dynamique ─────────────────────────────────────────────
  const signalY = panelsY + panelH + (ratio >= 4 ? 10 : 6);
  const lastRow = rows[rows.length - 1];
  const coveragePct = lastRow && lastRow.imports > 0 ? (lastRow.exports / lastRow.imports) * 100 : null;
  const signalText =
    lastRow
      ? language === 'fr'
        ? `En ${lastRow.year}, les importations atteignent ${fmtUSD(lastRow.imports)} contre ${fmtUSD(lastRow.exports)} d'exportations.`
        : `In ${lastRow.year}, imports reach ${fmtUSD(lastRow.imports)} against ${fmtUSD(lastRow.exports)} of exports.`
      : '';
  doc.setFillColor(...theme.card2);
  doc.roundedRect(MM.margin, signalY, MM.pageW - 2 * MM.margin, 15, 1.6, 1.6, 'F');
  doc.setFillColor(...theme.green);
  doc.rect(MM.margin, signalY, 1.3, 15, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.6);
  doc.setTextColor(...theme.muted);
  doc.text(`${t.signal} ${lastRow?.year || ''}`, MM.margin + 4, signalY + 5);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(...theme.text);
  doc.text(signalText, MM.margin + 4, signalY + 10.5, { maxWidth: MM.pageW - 2 * MM.margin - 60 });
  if (coveragePct != null) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.4);
    doc.setTextColor(...theme.muted);
    doc.text(t.coverage, MM.pageW - MM.margin - 4, signalY + 5.5, { align: 'right' });
    doc.setFontSize(11);
    doc.setTextColor(...(coveragePct < 20 ? theme.danger : theme.green));
    doc.text(`${coveragePct.toFixed(coveragePct < 1 ? 3 : 1)}%`, MM.pageW - MM.margin - 4, signalY + 11.5, { align: 'right' });
  }

  // ── Tableau détaillé ─────────────────────────────────────────────
  let y = signalY + 21;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.setTextColor(...theme.text);
  doc.text(t.detail, MM.margin, y);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);
  doc.setTextColor(...theme.muted);
  doc.text(t.roundedValues, MM.pageW - MM.margin, y, { align: 'right' });
  y += 5;

  const cols = [
    { key: 'year', label: t.year, w: 20, align: 'left' },
    { key: 'exports', label: t.exports, w: 30, align: 'right', fmt: fmtUSD },
    { key: 'exports_quantity', label: t.volExp, w: 27, align: 'right', fmt: fmtTonnes },
    { key: 'imports', label: t.imports, w: 30, align: 'right', fmt: fmtUSD },
    { key: 'imports_quantity', label: t.volImp, w: 27, align: 'right', fmt: fmtTonnes },
    { key: 'balance', label: t.balance, w: 30, align: 'right', fmt: fmtUSD },
  ];
  const tableW = cols.reduce((s, c) => s + c.w, 0);
  const tableX = MM.margin + (MM.pageW - 2 * MM.margin - tableW) / 2;

  const drawTableHeader = (yy) => {
    doc.setFillColor(...theme.headerBandFrom);
    doc.rect(tableX, yy, tableW, 7, 'F');
    let cx = tableX;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.4);
    doc.setTextColor(...theme.onBand);
    cols.forEach((c) => {
      doc.text(c.label, c.align === 'right' ? cx + c.w - 2 : cx + 2, yy + 4.6, { align: c.align === 'right' ? 'right' : 'left' });
      cx += c.w;
    });
    return yy + 7;
  };

  const rowH = 6.4;
  y = drawTableHeader(y);
  const consultedDate = new Date().toLocaleDateString(language === 'fr' ? 'fr-FR' : 'en-US');

  rows.forEach((row, idx) => {
    if (y + rowH > MM.pageH - 18) {
      doc.addPage();
      paint();
      y = MM.margin;
      y = drawTableHeader(y);
    }
    const isLast = idx === rows.length - 1;
    doc.setFillColor(...(isLast ? theme.card2 : idx % 2 === 0 ? theme.surface : theme.page));
    doc.rect(tableX, y, tableW, rowH, 'F');
    let cx = tableX;
    cols.forEach((c) => {
      const raw = row[c.key];
      const val = c.fmt ? c.fmt(raw) : String(raw);
      doc.setFont('helvetica', isLast ? 'bold' : 'normal');
      doc.setFontSize(7.6);
      if (c.key === 'balance') {
        doc.setTextColor(...(raw < 0 ? theme.danger : theme.green));
      } else {
        doc.setTextColor(...theme.text);
      }
      doc.text(val, c.align === 'right' ? cx + c.w - 2 : cx + 2, y + 4.4, { align: c.align === 'right' ? 'right' : 'left' });
      cx += c.w;
    });
    y += rowH;
  });
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    drawFooter(doc, {
      theme, t, source: data.source || '', consultedDate, language,
      pageNum: i, totalPages, printNote: theme.printNote,
    });
  }

  return doc;
}

export function tradeReportFilename(data) {
  const years = (data.chart_rows || []).map((r) => r.year);
  const period = years.length ? `${years[0]}-${years[years.length - 1]}` : '';
  // Seuls les caractères réellement invalides pour un nom de fichier (et les
  // espaces, par lisibilité) sont remplacés — les accents (Algérie, Côte
  // d'Ivoire...) sont conservés, les navigateurs les gèrent sans problème
  // dans un téléchargement.
  const country = (data.country_name || 'pays').trim().replace(/[\\/:*?"<>|\s]+/g, '_');
  return `ZLECAf_${country}_SH${data.hs_code}_${period}`;
}

export { THEME_LIGHT, THEME_DARK };
