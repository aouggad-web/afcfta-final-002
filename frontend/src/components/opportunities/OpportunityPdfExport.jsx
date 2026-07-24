/**
 * Boutons d'export PDF (clair / sombre) partagés par les sous-modules du
 * module Opportunités. Chaque sous-module fournit `getSpec()` qui décrit son
 * rapport en données (voir utils/opportunityPdf.js) ; le rendu, la palette
 * et la pagination sont communs — même langage graphique que l'export du
 * module Statistiques.
 */
import React, { useState } from 'react';
import { FileDown, Moon, Loader2 } from 'lucide-react';
import { buildOpportunityPdf, opportunityPdfFilename } from '../../utils/opportunityPdf';

export default function OpportunityPdfExport({ getSpec, disabled = false, language = 'fr' }) {
  const [exporting, setExporting] = useState(null); // null | 'light' | 'dark'

  const run = (theme) => {
    if (disabled || exporting) return;
    setExporting(theme);
    try {
      const spec = getSpec();
      if (!spec) return;
      const doc = buildOpportunityPdf({ ...spec, theme, language });
      doc.save(`${spec.filename || opportunityPdfFilename(spec.badge || 'rapport')}_${theme}.pdf`);
    } catch (err) {
      console.error('Opportunity PDF export failed:', err);
    } finally {
      setExporting(null);
    }
  };

  const btnStyle = {
    padding: '6px 12px',
    borderRadius: 8,
    border: '1px solid rgba(212,175,55,0.45)',
    background: 'rgba(212,175,55,0.12)',
    color: 'rgba(212,175,55,0.95)',
    fontWeight: 700,
    fontSize: 12,
    cursor: disabled || exporting ? 'not-allowed' : 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    opacity: disabled || exporting ? 0.55 : 1,
  };

  return (
    <div style={{ display: 'inline-flex', gap: 8 }} data-testid="opportunity-pdf-export">
      <button
        type="button"
        onClick={() => run('light')}
        disabled={disabled || exporting != null}
        style={btnStyle}
        title={language === 'en' ? 'Light PDF — print-optimized' : 'PDF clair — optimisé impression'}
        data-testid="opportunity-pdf-light"
      >
        {exporting === 'light' ? <Loader2 size={13} className="animate-spin" /> : <FileDown size={13} />}
        {language === 'en' ? 'PDF · Light' : 'PDF · Clair'}
      </button>
      <button
        type="button"
        onClick={() => run('dark')}
        disabled={disabled || exporting != null}
        style={btnStyle}
        title={language === 'en' ? 'Dark PDF — on-screen look' : 'PDF sombre — rendu écran'}
        data-testid="opportunity-pdf-dark"
      >
        {exporting === 'dark' ? <Loader2 size={13} className="animate-spin" /> : <Moon size={13} />}
        {language === 'en' ? 'PDF · Dark' : 'PDF · Sombre'}
      </button>
    </div>
  );
}
