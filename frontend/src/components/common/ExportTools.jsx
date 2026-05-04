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
  className = ''
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
        subtitle: language === 'fr' ? 'Rapport ZLECAf Analytics' : 'AfCFTA Analytics Report',
        language,
        showDate: true
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

export default { PDFExportButton, ChartExportButton, ZoomableChart, ExportToolbar };
