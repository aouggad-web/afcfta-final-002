import React, { useState, useRef } from 'react';
import { Button } from '../ui/button';
import { Download, Loader2, ZoomIn, ZoomOut, Image } from 'lucide-react';
import { exportToPDF } from '../../utils/pdfExport';
import html2canvas from 'html2canvas';

/**
 * PDFExportButton - Bouton d'export PDF réutilisable
 */
export function PDFExportButton({ 
  targetRef, 
  filename = 'report', 
  title = '', 
  subtitle = '',
  language = 'fr',
  informationalNotice = true,
  className = '',
  ...buttonProps
}) {
  const [exporting, setExporting] = useState(false);

  const texts = {
    fr: { export: 'Exporter PDF', exporting: 'Export...' },
    en: { export: 'Export PDF', exporting: 'Exporting...' }
  };
  const t = texts[language];

  const handleExport = async () => {
    if (!targetRef?.current) return;
    
    setExporting(true);
    try {
      const result = await exportToPDF(targetRef.current, `${filename}_${new Date().toISOString().split('T')[0]}.pdf`, {
        title,
        subtitle: subtitle || (language === 'fr' ? 'Rapport ZLECAf Analytics' : 'AfCFTA Analytics Report'),
        language,
        showDate: true,
        informationalNotice
      });
      
      if (!result.success) {
        console.error('PDF export failed:', result.error);
      }
    } catch (error) {
      console.error('PDF export error:', error);
    } finally {
      setExporting(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      disabled={exporting}
      variant="outline"
      size="sm"
      className={`gap-2 ${className}`}
      {...buttonProps}
    >
      {exporting ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          {t.exporting}
        </>
      ) : (
        <>
          <Download className="w-4 h-4" />
          {t.export}
        </>
      )}
    </Button>
  );
}

/**
 * CSVExportButton - Export client-side d'un tableau de données en CSV
 * (ouvrable dans Excel, sans dépendance externe).
 *
 * Props:
 *   - rows: tableau d'objets
 *   - columns: [{ key, label }] (ordre + en-têtes des colonnes)
 *   - filename: nom de base du fichier (sans extension)
 *   - language: 'fr' | 'en'
 */
export function CSVExportButton({
  rows = [],
  columns = [],
  filename = 'export',
  language = 'fr',
  exportMetadata = null,
  className = '',
  ...buttonProps
}) {
  const texts = {
    fr: { export: 'Exporter CSV' },
    en: { export: 'Export CSV' },
  };
  const t = texts[language] || texts.fr;

  const escapeCell = (val) => {
    if (val == null) return '';
    const s = String(val);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };

  const handleExport = () => {
    if (!rows.length || !columns.length) return;
    const header = columns.map((c) => escapeCell(c.label ?? c.key)).join(',');
    const body = rows
      .map((r) => columns.map((c) => escapeCell(r[c.key])).join(','))
      .join('\n');
    const metadataRows = exportMetadata
      ? [
          ['Simulation informative des droits et taxes à l’importation', ''],
          ['Date et heure de simulation', exportMetadata.simulation_generated_at || new Date().toISOString()],
          ['Pays importateur', exportMetadata.importer_country || ''],
          ['Pays exportateur', exportMetadata.exporter_country || ''],
          ['Produit et code utilisé', exportMetadata.product_code || ''],
          ['Hypothèses', exportMetadata.assumptions || ''],
          ['Périmètre couvert', exportMetadata.scope || ''],
          ['Sources', exportMetadata.sources || ''],
          ['Lacunes', exportMetadata.known_data_gaps || ''],
          ['Mention', 'Simulation informative — non opposable à l’administration douanière.'],
          [],
        ].map((row) => row.map(escapeCell).join(','))
      : [];
    // BOM pour qu'Excel reconnaisse l'UTF-8 (accents)
    const csv = `\uFEFF${metadataRows.length ? `${metadataRows.join('\n')}\n` : ''}${header}\n${body}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // Différé au tick suivant : révoquer immédiatement peut interrompre le
    // téléchargement sur certains navigateurs avant qu'il n'ait démarré.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <Button
      onClick={handleExport}
      disabled={!rows.length || !columns.length}
      variant="outline"
      size="sm"
      className={`gap-2 ${className}`}
      {...buttonProps}
    >
      <Download className="w-4 h-4" />
      {t.export}
    </Button>
  );
}

/**
 * JSONExportButton - Export client-side d'un objet/tableau de données en JSON.
 *
 * Props:
 *   - data: objet ou tableau sérialisable en JSON
 *   - filename: nom de base du fichier (sans extension)
 *   - language: 'fr' | 'en'
 */
export function JSONExportButton({
  data,
  filename = 'export',
  language = 'fr',
  className = '',
  ...buttonProps
}) {
  const texts = {
    fr: { export: 'Exporter JSON' },
    en: { export: 'Export JSON' },
  };
  const t = texts[language] || texts.fr;

  const isEmpty = data == null || (Array.isArray(data) && data.length === 0);

  const handleExport = () => {
    if (isEmpty) return;
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // Différé au tick suivant : révoquer immédiatement peut interrompre le
    // téléchargement sur certains navigateurs avant qu'il n'ait démarré.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <Button
      onClick={handleExport}
      disabled={isEmpty}
      variant="outline"
      size="sm"
      className={`gap-2 ${className}`}
      {...buttonProps}
    >
      <Download className="w-4 h-4" />
      {t.export}
    </Button>
  );
}

/**
 * ChartExportButton - Bouton pour exporter un graphique en image
 */
export function ChartExportButton({ 
  chartRef, 
  filename = 'chart',
  language = 'fr',
  className = ''
}) {
  const [exporting, setExporting] = useState(false);

  const texts = {
    fr: { export: 'Image' },
    en: { export: 'Image' }
  };
  const t = texts[language];

  const handleExport = async () => {
    if (!chartRef?.current) return;
    
    setExporting(true);
    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: 2,
        backgroundColor: '#ffffff'
      });
      
      const link = document.createElement('a');
      link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Chart export error:', error);
    } finally {
      setExporting(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      disabled={exporting}
      variant="ghost"
      size="sm"
      className={`gap-1 text-xs ${className}`}
    >
      {exporting ? (
        <Loader2 className="w-3 h-3 animate-spin" />
      ) : (
        <>
          <Image className="w-3 h-3" />
          {t.export}
        </>
      )}
    </Button>
  );
}

/**
 * ZoomableChart - Wrapper pour graphiques avec zoom
 */
export function ZoomableChart({ children, className = '' }) {
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef(null);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.6));
  const handleReset = () => setZoom(1);

  return (
    <div className={`relative ${className}`}>
      {/* Zoom Controls */}
      <div className="absolute top-2 right-2 z-10 flex gap-1 bg-white/90 rounded-lg shadow-sm p-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          disabled={zoom <= 0.6}
          className="h-7 w-7 p-0"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          className="h-7 px-2 text-xs"
        >
          {Math.round(zoom * 100)}%
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          disabled={zoom >= 2}
          className="h-7 w-7 p-0"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
      </div>

      {/* Chart Container */}
      <div 
        ref={containerRef}
        className="overflow-auto"
        style={{ 
          transform: `scale(${zoom})`,
          transformOrigin: 'top left',
          transition: 'transform 0.2s ease'
        }}
      >
        {children}
      </div>
    </div>
  );
}

/**
 * ExportToolbar - Barre d'outils complète pour export
 */
export function ExportToolbar({ 
  targetRef,
  chartRef,
  title,
  filename,
  language = 'fr',
  showPDF = true,
  showImage = true,
  className = ''
}) {
  return (
    <div className={`flex gap-2 items-center ${className}`}>
      {showPDF && (
        <PDFExportButton
          targetRef={targetRef}
          filename={filename}
          title={title}
          language={language}
        />
      )}
      {showImage && chartRef && (
        <ChartExportButton
          chartRef={chartRef}
          filename={`${filename}_chart`}
          language={language}
        />
      )}
    </div>
  );
}

export default {
  PDFExportButton,
  CSVExportButton,
  JSONExportButton,
  ChartExportButton,
  ZoomableChart,
  ExportToolbar,
};
