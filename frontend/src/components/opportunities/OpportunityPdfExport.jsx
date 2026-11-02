/**
 * Boutons d'export PDF (clair / sombre) partagés par les sous-modules du
 * module Opportunités. Chaque sous-module fournit `getSpec()` qui décrit son
 * rapport en données (voir utils/opportunityPdf.js) ; le rendu, la palette
 * et la pagination sont communs — même langage graphique que l'export du
 * module Statistiques.
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FileDown, Moon, Loader2 } from 'lucide-react';
import { buildOpportunityPdf, opportunityPdfFilename } from '../../utils/opportunityPdf';

export default function OpportunityPdfExport({ getSpec, disabled = false, language = 'fr' }) {
  const { t, i18n } = useTranslation();
  // jsPDF ne sait pas écrire l'arabe : en arabe, le PDF est produit en
  // français. `getSpec(t, langue)` reçoit le `t` et la langue du PDF.
  const pdfLang = String(language).startsWith('ar') ? 'fr' : language;
  const [exporting, setExporting] = useState(null); // null | 'light' | 'dark'

  const run = (theme) => {
    if (disabled || exporting) return;
    setExporting(theme);
    try {
      const spec = getSpec(pdfLang === language ? t : i18n.getFixedT(pdfLang), pdfLang);
      if (!spec) return;
      const doc = buildOpportunityPdf({ ...spec, theme, language: pdfLang });
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
    border: '1px solid color-mix(in srgb, var(--gold) 45%, transparent)',
    background: 'var(--goldSoft)',
    color: 'var(--gold)',
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
        title={t('opportunities.opportunityPdfExport.lightPdfPrintOptimized')}
        data-testid="opportunity-pdf-light"
      >
        {exporting === 'light' ? <Loader2 size={13} className="animate-spin" /> : <FileDown size={13} />}
        {t('opportunities.opportunityPdfExport.pdfLight')}
      </button>
      <button
        type="button"
        onClick={() => run('dark')}
        disabled={disabled || exporting != null}
        style={btnStyle}
        title={t('opportunities.opportunityPdfExport.darkPdfOnScreen')}
        data-testid="opportunity-pdf-dark"
      >
        {exporting === 'dark' ? <Loader2 size={13} className="animate-spin" /> : <Moon size={13} />}
        {t('opportunities.opportunityPdfExport.pdfDark')}
      </button>
    </div>
  );
}
