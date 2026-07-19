/**
 * Générateur PDF générique du module Opportunités — un seul bâtisseur pour
 * tous les sous-modules (Substitution, Simulateur, Comparateur, Vue
 * d'ensemble, Chaînes de valeur, Par produit, Comparaison, Analyse IA).
 *
 * Même langage graphique que utils/tradeReportPdf.js (bandeau, cartes KPI,
 * tableau à en-tête foncé, pied de page paginé) et mêmes thèmes clair/sombre
 * issus de la palette réelle de l'appli — les thèmes sont importés du module
 * de référence pour qu'un ajustement de charte se propage partout.
 *
 * Spécification déclarative : chaque sous-module décrit son rapport en
 * données (titre, KPIs, sections tableau / clé-valeur / paragraphes) et le
 * bâtisseur s'occupe de la mise en page et de la pagination.
 */
import jsPDF from 'jspdf';
import { THEME_LIGHT, THEME_DARK } from './tradeReportPdf';

const MM = { pageW: 210, pageH: 297, margin: 13 };

const I18N = {
  fr: { page: 'Page', source: 'SOURCE', consulted: 'Consultation', module: 'MODULE OPPORTUNITÉS' },
  en: { page: 'Page', source: 'SOURCE', consulted: 'Consulted', module: 'OPPORTUNITIES MODULE' },
};

const ACCENTS = { green: 'green', red: 'red', gold: 'gold', terra: 'terra' };

function paintPage(doc, theme) {
  doc.setFillColor(...theme.page);
  doc.rect(0, 0, MM.pageW, MM.pageH, 'F');
}

function drawMasthead(doc, theme, { badge, title, subtitle, language }) {
  const t = I18N[language] || I18N.fr;
  const bandH = 30;
  doc.setFillColor(...theme.headerBandFrom);
  doc.rect(0, 0, MM.pageW, bandH, 'F');
  doc.setFillColor(...theme.gold);
  doc.rect(0, bandH - 0.9, MM.pageW, 0.9, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(...theme.onBand);
  const wordmark = 'AFCFTA / ZLECAf';
  doc.text(wordmark, MM.margin, 8);
  const wordmarkWidth = doc.getTextWidth(wordmark);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.2);
  doc.setTextColor(...theme.gold);
  doc.text(t.module, MM.margin + wordmarkWidth + 3, 8);

  if (badge) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.2);
    const padX = 2.8;
    const w = doc.getTextWidth(badge) + padX * 2;
    doc.setFillColor(...theme.terra);
    doc.roundedRect(MM.margin, 11.5, w, 5.4, 2.7, 2.7, 'F');
    doc.setTextColor(...theme.onBand);
    doc.text(badge, MM.margin + padX, 15.2);
  }

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15.5);
  doc.setTextColor(...theme.onBand);
  doc.text(title || '', MM.margin, 23, { maxWidth: MM.pageW - 2 * MM.margin });

  if (subtitle) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...theme.gold);
    doc.text(subtitle, MM.margin, 27.6, { maxWidth: MM.pageW - 2 * MM.margin });
  }
  return bandH + 6;
}

function drawKpis(doc, theme, kpis, y) {
  const gap = 3;
  const h = 17;
  const perRow = Math.min(kpis.length, 4);
  const w = (MM.pageW - 2 * MM.margin - (perRow - 1) * gap) / perRow;
  kpis.slice(0, 8).forEach((kpi, i) => {
    const row = Math.floor(i / perRow);
    const col = i % perRow;
    const x = MM.margin + col * (w + gap);
    const yy = y + row * (h + gap);
    doc.setFillColor(...theme.surface);
    doc.roundedRect(x, yy, w, h, 1.4, 1.4, 'F');
    doc.setFillColor(...theme[ACCENTS[kpi.accent] || 'gold']);
    doc.rect(x, yy, 1.2, h, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.2);
    doc.setTextColor(...theme.muted);
    doc.text(String(kpi.label || '').toUpperCase(), x + 3.5, yy + 4.8, { maxWidth: w - 5 });
    doc.setFontSize(11.5);
    doc.setTextColor(...theme.text);
    doc.text(String(kpi.value ?? '—'), x + 3.5, yy + 11, { maxWidth: w - 5 });
    if (kpi.sub) {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(5.8);
      doc.setTextColor(...theme.muted);
      doc.text(String(kpi.sub), x + 3.5, yy + h - 2, { maxWidth: w - 5 });
    }
  });
  const rows = Math.ceil(Math.min(kpis.length, 8) / perRow);
  return y + rows * (h + gap) + 3;
}

function sectionTitle(doc, theme, title, y) {
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(...theme.text);
  doc.text(title, MM.margin, y);
  return y + 4.5;
}

function ensureRoom(doc, theme, y, needed) {
  if (y + needed > MM.pageH - 16) {
    doc.addPage();
    paintPage(doc, theme);
    return MM.margin + 4;
  }
  return y;
}

function drawTable(doc, theme, table, startY) {
  const cols = table.columns || [];
  if (!cols.length) return startY;
  const totalW = MM.pageW - 2 * MM.margin;
  const weights = cols.map((c) => c.width || 1);
  const weightSum = weights.reduce((s, v) => s + v, 0);
  const widths = weights.map((v) => (v / weightSum) * totalW);
  const rowH = 6.2;

  const header = (yy) => {
    doc.setFillColor(...theme.headerBandFrom);
    doc.rect(MM.margin, yy, totalW, 6.6, 'F');
    let cx = MM.margin;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.8);
    doc.setTextColor(...theme.onBand);
    cols.forEach((c, i) => {
      doc.text(String(c.label || c.key), c.align === 'right' ? cx + widths[i] - 2 : cx + 2, yy + 4.3, {
        align: c.align === 'right' ? 'right' : 'left',
        maxWidth: widths[i] - 4,
      });
      cx += widths[i];
    });
    return yy + 6.6;
  };

  let y = ensureRoom(doc, theme, startY, 6.6 + rowH);
  y = header(y);

  (table.rows || []).forEach((row, idx) => {
    if (y + rowH > MM.pageH - 16) {
      doc.addPage();
      paintPage(doc, theme);
      y = header(MM.margin + 4);
    }
    doc.setFillColor(...(idx % 2 === 0 ? theme.surface : theme.page));
    doc.rect(MM.margin, y, totalW, rowH, 'F');
    let cx = MM.margin;
    cols.forEach((c, i) => {
      const raw = row[c.key];
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7);
      if (c.color === 'signed' && typeof raw === 'number') {
        doc.setTextColor(...(raw < 0 ? theme.danger : theme.green));
      } else {
        doc.setTextColor(...theme.text);
      }
      const text = c.fmt ? c.fmt(raw, row) : String(raw ?? '—');
      doc.text(text, c.align === 'right' ? cx + widths[i] - 2 : cx + 2, y + 4.2, {
        align: c.align === 'right' ? 'right' : 'left',
        maxWidth: widths[i] - 4,
      });
      cx += widths[i];
    });
    y += rowH;
  });
  return y + 4;
}

function drawKeyValues(doc, theme, keyValues, startY) {
  let y = startY;
  keyValues.forEach(({ label, value }) => {
    y = ensureRoom(doc, theme, y, 6);
    doc.setFillColor(...theme.surface);
    doc.roundedRect(MM.margin, y, MM.pageW - 2 * MM.margin, 5.6, 1, 1, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.8);
    doc.setTextColor(...theme.muted);
    doc.text(String(label), MM.margin + 2.5, y + 3.8);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.2);
    doc.setTextColor(...theme.text);
    doc.text(String(value ?? '—'), MM.pageW - MM.margin - 2.5, y + 3.8, {
      align: 'right',
      maxWidth: (MM.pageW - 2 * MM.margin) * 0.6,
    });
    y += 6.6;
  });
  return y + 2;
}

function drawParagraphs(doc, theme, paragraphs, startY) {
  let y = startY;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.6);
  doc.setTextColor(...theme.text);
  paragraphs.forEach((p) => {
    const lines = doc.splitTextToSize(String(p), MM.pageW - 2 * MM.margin);
    y = ensureRoom(doc, theme, y, lines.length * 3.6 + 2);
    doc.text(lines, MM.margin, y);
    y += lines.length * 3.6 + 2.5;
  });
  return y + 1;
}

function drawFooters(doc, theme, { language, source }) {
  const t = I18N[language] || I18N.fr;
  const consulted = new Date().toLocaleDateString(language === 'fr' ? 'fr-FR' : 'en-US');
  const total = doc.internal.getNumberOfPages();
  for (let i = 1; i <= total; i++) {
    doc.setPage(i);
    const y = MM.pageH - 10;
    doc.setDrawColor(...theme.gold);
    doc.setLineWidth(0.4);
    doc.line(MM.margin, y, MM.pageW - MM.margin, y);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.2);
    doc.setTextColor(...theme.muted);
    doc.text(t.source, MM.margin, y + 3.8);
    const labelW = doc.getTextWidth(t.source);
    doc.setFont('helvetica', 'normal');
    doc.text(`${source || '—'} • ${t.consulted}: ${consulted}`, MM.margin + labelW + 2, y + 3.8, {
      maxWidth: MM.pageW - 2 * MM.margin - labelW - 22,
    });
    doc.setFont('helvetica', 'bold');
    doc.text(`${t.page} ${i}/${total}`, MM.pageW - MM.margin, y + 3.8, { align: 'right' });
  }
}

/**
 * Construit le document (l'appelant fait `.save(filename)`).
 *
 * @param {object} spec
 * @param {string} spec.title
 * @param {string} [spec.subtitle]
 * @param {string} [spec.badge]      Pastille sous le wordmark (nom du sous-module)
 * @param {'fr'|'en'} [spec.language]
 * @param {'light'|'dark'} [spec.theme]
 * @param {Array}  [spec.kpis]       [{label, value, sub, accent}]
 * @param {Array}  [spec.sections]   [{title, table}|{title, keyValues}|{title, paragraphs}, ...]
 * @param {string} [spec.source]
 */
export function buildOpportunityPdf(spec) {
  const theme = spec.theme === 'dark' ? THEME_DARK : THEME_LIGHT;
  const language = spec.language || 'fr';
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  paintPage(doc, theme);

  let y = drawMasthead(doc, theme, { ...spec, language });
  if (spec.kpis?.length) y = drawKpis(doc, theme, spec.kpis, y);

  (spec.sections || []).forEach((section) => {
    y = ensureRoom(doc, theme, y, 14);
    if (section.title) y = sectionTitle(doc, theme, section.title, y + 2);
    if (section.table) y = drawTable(doc, theme, section.table, y);
    else if (section.keyValues?.length) y = drawKeyValues(doc, theme, section.keyValues, y);
    else if (section.paragraphs?.length) y = drawParagraphs(doc, theme, section.paragraphs, y);
  });

  drawFooters(doc, theme, { language, source: spec.source });
  return doc;
}

export function opportunityPdfFilename(moduleName, extra = '') {
  const date = new Date().toISOString().split('T')[0];
  const safe = (s) => String(s || '').trim().replace(/[\\/:*?"<>|\s]+/g, '_');
  return ['ZLECAf_Opportunites', safe(moduleName), safe(extra), date].filter(Boolean).join('_');
}
