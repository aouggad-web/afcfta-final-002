import React, { useRef } from 'react';
import { Card, CardContent } from '../ui/card';
import { PDFExportButton } from './ExportTools';

/**
 * TabWrapper - Wrapper pour les onglets avec fonctionnalité d'export PDF
 */
export default function TabWrapper({ 
  children, 
  title,
  filename,
  language = 'fr',
  showExport = true,
  className = ''
}) {
  const contentRef = useRef(null);

  const texts = {
    fr: { exportHint: 'Exporter cette section en PDF' },
    en: { exportHint: 'Export this section to PDF' }
  };
  const t = texts[language];

  return (
    <div className={className}>
      {/* Export Button Header */}
      {showExport && (
        <div className="flex justify-end mb-4">
          <PDFExportButton
            targetRef={contentRef}
            filename={filename}
            title={title}
            language={language}
          />
        </div>
      )}

      {/* Content */}
      <div ref={contentRef} id={`tab-content-${filename}`}>
        {children}
      </div>
    </div>
  );
}
