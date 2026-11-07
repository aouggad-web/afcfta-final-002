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
import { THEME_LIGHT, THEME_DARK, espacesSimples } from './tradeReportPdf';
import { dessinerLogo, nomSaas } from './pdfMarque';

const MM = { pageW: 210, pageH: 297, margin: 13 };
// Logo du site, à droite du bandeau ; le titre s'arrête avant lui.
const LOGO = 22;
const TEXTE_BANDEAU = MM.pageW - 2 * MM.margin - LOGO - 4;

const I18N = {
  fr: { page: 'Page', source: 'SOURCE', consulted: 'Consultation', module: 'MODULE OPPORTUNITÉS' },
  en: { page: 'Page', source: 'SOURCE', consulted: 'Consulted', module: 'OPPORTUNITIES MODULE' },
};

const ACCENTS = { green: 'green', red: 'red', gold: 'gold', terra: 'terra' };

function paintPage(doc, theme) {
  doc.setFillColor(...theme.page);
  doc.rect(0, 0, MM.pageW, MM.pageH, 'F');
}

function drawMasthead(doc, theme, { badge, title, subtitle, language, moduleLabel }) {
  const t = I18N[language] || I18N.fr;
  const bandH = 30;
  doc.setFillColor(...theme.headerBandFrom);
  doc.rect(0, 0, MM.pageW, bandH, 'F');
  doc.setFillColor(...theme.gold);
  doc.rect(0, bandH - 0.9, MM.pageW, 0.9, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(...theme.onBand);
  const wordmark = nomSaas(language);
  doc.text(wordmark, MM.margin, 8);
  const wordmarkWidth = doc.getTextWidth(wordmark);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.2);
  doc.setTextColor(...theme.gold);
  // moduleLabel permet à un autre module de réutiliser ce bâtisseur sans
  // que son rapport s'annonce « MODULE OPPORTUNITÉS ».
  doc.text(moduleLabel || t.module, MM.margin + wordmarkWidth + 3, 8);

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
  doc.text(title || '', MM.margin, 23, { maxWidth: TEXTE_BANDEAU });

  if (subtitle) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...theme.gold);
    doc.text(subtitle, MM.margin, 27.6, { maxWidth: TEXTE_BANDEAU });
  }
  dessinerLogo(doc, MM.pageW - MM.margin - LOGO, (bandH - LOGO) / 2, LOGO);
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

  // Hauteur de ligne dynamique : un nom de produit/pays/partenaire plus large
  // que sa colonne est enroulé sur plusieurs lignes par `maxWidth`, mais une
  // hauteur de ligne FIXE ne le sait pas — la deuxième ligne se dessinait
  // dans la ligne suivante et pouvait l'écraser. On pré-calcule le texte
  // enroulé de chaque cellule, on prend la hauteur nécessaire au maximum sur
  // la ligne, et cette hauteur sert à la fois au fond et à la pagination.
  const LINE_H = 3.1;
  const TOP_PAD = 4.2;
  const BOTTOM_PAD = 2.0;

  let y = ensureRoom(doc, theme, startY, 6.6 + rowH);
  y = header(y);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7);

  // `fmt` est fourni par chaque sous-module et peut renvoyer n'importe quoi
  // (nombre, undefined...) — jsPDF (splitTextToSize/text) exige une chaîne
  // (ou un tableau de chaînes) et lève sinon. On coerce systématiquement,
  // en aplatissant un éventuel tableau plutôt que de planter dessus.
  const toCellText = (value) =>
    Array.isArray(value) ? value.map(String).join(', ') : String(value ?? '—');

  (table.rows || []).forEach((row, idx) => {
    const cellLines = cols.map((c, i) => {
      const raw = row[c.key];
      const text = toCellText(c.fmt ? c.fmt(raw, row) : raw);
      return doc.splitTextToSize(text, widths[i] - 4);
    });
    const lineCount = Math.max(1, ...cellLines.map((lines) => lines.length));
    const thisRowH = Math.max(rowH, TOP_PAD + (lineCount - 1) * LINE_H + BOTTOM_PAD);

    if (y + thisRowH > MM.pageH - 16) {
      doc.addPage();
      paintPage(doc, theme);
      y = header(MM.margin + 4);
    }
    doc.setFillColor(...(idx % 2 === 0 ? theme.surface : theme.page));
    doc.rect(MM.margin, y, totalW, thisRowH, 'F');
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
      const xPos = c.align === 'right' ? cx + widths[i] - 2 : cx + 2;
      cellLines[i].forEach((line, li) => {
        doc.text(line, xPos, y + TOP_PAD + li * LINE_H, { align: c.align === 'right' ? 'right' : 'left' });
      });
      cx += widths[i];
    });
    y += thisRowH;
  });
  return y + 4;
}

function drawKeyValues(doc, theme, keyValues, startY) {
  // Une valeur longue (désignation, référence légale) s'enroule sur
  // plusieurs lignes : la hauteur de la ligne suit le texte, sinon la
  // deuxième ligne déborderait sur la suivante.
  const totalW = MM.pageW - 2 * MM.margin;
  const labelW = totalW * 0.36;
  const valueW = totalW - labelW - 5;
  let y = startY;
  keyValues.forEach(({ label, value }) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.8);
    const labelLines = doc.splitTextToSize(String(label), labelW);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.2);
    const valueLines = doc.splitTextToSize(String(value ?? '—'), valueW);
    const lines = Math.max(labelLines.length, valueLines.length);
    const h = 5.6 + (lines - 1) * 3.1;
    y = ensureRoom(doc, theme, y, h + 1);
    doc.setFillColor(...theme.surface);
    doc.roundedRect(MM.margin, y, totalW, h, 1, 1, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.8);
    doc.setTextColor(...theme.muted);
    doc.text(labelLines, MM.margin + 2.5, y + 3.8);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.2);
    doc.setTextColor(...theme.text);
    // Une ligne : alignée à droite ; plusieurs : un paragraphe aligné à gauche.
    if (valueLines.length > 1) doc.text(valueLines, MM.pageW - MM.margin - 2.5 - valueW, y + 3.8);
    else doc.text(valueLines, MM.pageW - MM.margin - 2.5, y + 3.8, { align: 'right' });
    y += h + 1;
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

/**
 * Encadré « à savoir » : fond teinté, filet doré à gauche. Sert aux réserves
 * qui doivent se lire même en survolant le document (simulation non
 * opposable, montant indicatif, donnée manquante).
 */
function drawNotice(doc, theme, paragraphs, startY) {
  const totalW = MM.pageW - 2 * MM.margin;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.4);
  const blocs = paragraphs.map((p) => doc.splitTextToSize(String(p), totalW - 8));
  const h = blocs.reduce((sum, lines) => sum + lines.length * 3.5 + 1.6, 0) + 3;
  let y = ensureRoom(doc, theme, startY, Math.min(h, 120));
  doc.setFillColor(...theme.card2);
  doc.roundedRect(MM.margin, y, totalW, h, 1.4, 1.4, 'F');
  doc.setFillColor(...theme.gold);
  doc.rect(MM.margin, y, 1.2, h, 'F');
  doc.setTextColor(...theme.text);
  let yy = y + 4.6;
  blocs.forEach((lines) => {
    doc.text(lines, MM.margin + 4.5, yy);
    yy += lines.length * 3.5 + 1.6;
  });
  return y + h + 3;
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
 * @param {Array}  [spec.sections]   [{title, table}|{title, keyValues}|{title, paragraphs}|{title, notice}, ...]
 * @param {string} [spec.source]
 * @param {string} [spec.moduleLabel] Libellé du module dans le bandeau (défaut : Opportunités)
 */
export function buildOpportunityPdf(spec) {
  const theme = spec.theme === 'dark' ? THEME_DARK : THEME_LIGHT;
  const language = spec.language || 'fr';
  const doc = espacesSimples(new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' }));
  paintPage(doc, theme);

  let y = drawMasthead(doc, theme, { ...spec, language });
  if (spec.kpis?.length) y = drawKpis(doc, theme, spec.kpis, y);

  (spec.sections || []).forEach((section) => {
    y = ensureRoom(doc, theme, y, 14);
    if (section.title) y = sectionTitle(doc, theme, section.title, y + 2);
    if (section.table) y = drawTable(doc, theme, section.table, y);
    else if (section.keyValues?.length) y = drawKeyValues(doc, theme, section.keyValues, y);
    else if (section.paragraphs?.length) y = drawParagraphs(doc, theme, section.paragraphs, y);
    else if (section.notice?.length) y = drawNotice(doc, theme, section.notice, y);
  });

  drawFooters(doc, theme, { language, source: spec.source });
  return doc;
}

export function opportunityPdfFilename(moduleName, extra = '') {
  const date = new Date().toISOString().split('T')[0];
  const safe = (s) => String(s || '').trim().replace(/[\\/:*?"<>|\s]+/g, '_');
  return ['ZLECAf_Opportunites', safe(moduleName), safe(extra), date].filter(Boolean).join('_');
}
