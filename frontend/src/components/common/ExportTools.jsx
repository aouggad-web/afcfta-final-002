import React from 'react';
import jsPDF from 'jspdf';

/**
 * Boutons d'export (CSV / JSON / PDF) réutilisables.
 *
 * - CSVExportButton : rows + columns ({key,label}) -> CSV UTF-8 (BOM), cellules
 *   échappées, bloc de métadonnées informatives optionnel.
 * - JSONExportButton : data -> JSON indenté.
 * - PDFExportButton : rows + columns -> PDF tabulaire simple (jsPDF).
 */

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function escapeCsvCell(value) {
  if (value === null || value === undefined) return '';
  const s = String(value);
  if (/[",\n]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function buildMetadataBlock(meta) {
  if (!meta) return '';
  const lines = [
    'Simulation informative des droits et taxes à l’importation',
    'Simulation informative — non opposable à l’administration douanière.',
  ];
  const labels = {
    simulation_generated_at: 'Généré le',
    importer_country: 'Pays importateur',
    exporter_country: 'Pays exportateur',
    product_code: 'Code produit',
    assumptions: 'Hypothèses',
    scope: 'Portée',
    sources: 'Sources',
    known_data_gaps: 'Lacunes connues',
  };
  for (const [key, value] of Object.entries(meta)) {
    if (value === null || value === undefined || value === '') continue;
    const label = labels[key] || key;
    lines.push(`${escapeCsvCell(label)},${escapeCsvCell(value)}`);
  }
  return lines.join('\n') + '\n\n';
}

export function CSVExportButton({
  rows,
  columns,
  language = 'fr',
  filename = 'export.csv',
  exportMetadata = null,
  className,
}) {
  const isFr = language !== 'en';
  const disabled = !rows || rows.length === 0;
  const label = isFr ? 'Exporter CSV' : 'Export CSV';

  const handleExport = () => {
    if (disabled) return;
    const header = columns.map((c) => escapeCsvCell(c.label)).join(',');
    const body = rows
      .map((row) => columns.map((c) => escapeCsvCell(row[c.key])).join(','))
      .join('\n');
    const csv = '﻿' + buildMetadataBlock(exportMetadata) + header + '\n' + body;
    triggerDownload(new Blob([csv], { type: 'text/csv;charset=utf-8;' }), filename);
  };

  return (
    <button type="button" onClick={handleExport} disabled={disabled} className={className}>
      ⬇ {label}
    </button>
  );
}

export function JSONExportButton({ data, language = 'fr', filename = 'export.json', className }) {
  const isFr = language !== 'en';
  const disabled = !data || (Array.isArray(data) && data.length === 0);
  const label = isFr ? 'Exporter JSON' : 'Export JSON';

  const handleExport = () => {
    if (disabled) return;
    const json = JSON.stringify(data, null, 2);
    triggerDownload(new Blob([json], { type: 'application/json' }), filename);
  };

  return (
    <button type="button" onClick={handleExport} disabled={disabled} className={className}>
      ⬇ {label}
    </button>
  );
}

export function PDFExportButton({
  rows,
  columns,
  language = 'fr',
  filename = 'export.pdf',
  title,
  className,
}) {
  const isFr = language !== 'en';
  const disabled = !rows || rows.length === 0;
  const label = isFr ? 'Exporter PDF' : 'Export PDF';

  const handleExport = () => {
    if (disabled) return;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'pt' });
    let y = 40;
    if (title) {
      doc.setFontSize ? doc.setFontSize(14) : null;
      doc.text(String(title), 40, y);
      y += 24;
    }
    doc.setFontSize && doc.setFontSize(9);
    const header = columns.map((c) => c.label).join('   |   ');
    doc.text(header, 40, y);
    y += 16;
    rows.forEach((row) => {
      const line = columns.map((c) => (row[c.key] ?? '')).join('   |   ');
      doc.text(String(line).slice(0, 180), 40, y);
      y += 14;
      if (y > 540) {
        doc.addPage();
        y = 40;
      }
    });
    doc.save(filename);
  };

  return (
    <button type="button" onClick={handleExport} disabled={disabled} className={className}>
      ⬇ {label}
    </button>
  );
}

export default { CSVExportButton, JSONExportButton, PDFExportButton };
