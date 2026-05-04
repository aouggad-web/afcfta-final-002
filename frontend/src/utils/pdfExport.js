import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * Export a DOM element to PDF
 * @param {HTMLElement} element - The DOM element to export
 * @param {string} filename - The name of the PDF file
 * @param {object} options - Additional options
 */
export const exportToPDF = async (element, filename = 'report.pdf', options = {}) => {
  const {
    scale = 2,
    orientation = 'portrait',
    format = 'a4',
    margin = 10,
    title = '',
    subtitle = '',
    showDate = true,
    language = 'fr'
  } = options;

  try {
    // Create canvas from element
    const canvas = await html2canvas(element, {
      scale: scale,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: orientation,
      unit: 'mm',
      format: format
    });

    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();

    // Add header if title provided
    let yOffset = margin;
    if (title) {
      pdf.setFontSize(18);
      pdf.setTextColor(30, 64, 175); // Blue color
      pdf.text(title, margin, yOffset + 10);
      yOffset += 15;

      if (subtitle) {
        pdf.setFontSize(12);
        pdf.setTextColor(100, 100, 100);
        pdf.text(subtitle, margin, yOffset + 5);
        yOffset += 10;
      }

      // Add date
      if (showDate) {
        pdf.setFontSize(10);
        pdf.setTextColor(150, 150, 150);
        const dateText = language === 'fr' 
          ? `Généré le ${new Date().toLocaleDateString('fr-FR')}`
          : `Generated on ${new Date().toLocaleDateString('en-US')}`;
        pdf.text(dateText, margin, yOffset + 5);
        yOffset += 10;
      }

      // Add separator line
      pdf.setDrawColor(200, 200, 200);
      pdf.line(margin, yOffset, pageWidth - margin, yOffset);
      yOffset += 5;
    }

    // Calculate image dimensions
    const imgWidth = pageWidth - (margin * 2);
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    // Check if we need multiple pages
    const availableHeight = pageHeight - yOffset - margin;

    if (imgHeight <= availableHeight) {
      // Single page
      pdf.addImage(imgData, 'PNG', margin, yOffset, imgWidth, imgHeight);
    } else {
      // Multiple pages
      let remainingHeight = imgHeight;
      let sourceY = 0;
      let pageNum = 0;

      while (remainingHeight > 0) {
        if (pageNum > 0) {
          pdf.addPage();
          yOffset = margin;
        }

        const currentHeight = Math.min(availableHeight, remainingHeight);
        const sourceHeight = (currentHeight / imgWidth) * canvas.width;

        // Create a temporary canvas for this page section
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = canvas.width;
        tempCanvas.height = sourceHeight;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(
          canvas,
          0, sourceY, canvas.width, sourceHeight,
          0, 0, canvas.width, sourceHeight
        );

        const tempImgData = tempCanvas.toDataURL('image/png');
        pdf.addImage(tempImgData, 'PNG', margin, yOffset, imgWidth, currentHeight);

        sourceY += sourceHeight;
        remainingHeight -= currentHeight;
        pageNum++;
      }
    }

    // Add footer with page numbers
    const totalPages = pdf.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setTextColor(150, 150, 150);
      const footerText = language === 'fr' 
        ? `Page ${i} sur ${totalPages} - ZLECAf Analytics`
        : `Page ${i} of ${totalPages} - AfCFTA Analytics`;
      pdf.text(footerText, pageWidth / 2, pageHeight - 5, { align: 'center' });
    }

    // Save PDF
    pdf.save(filename);
    return { success: true };
  } catch (error) {
    console.error('PDF export error:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Export specific tab content to PDF
 * @param {string} tabId - The ID of the tab content to export
 * @param {string} tabName - The name of the tab for the filename
 * @param {string} language - Current language ('fr' or 'en')
 */
export const exportTabToPDF = async (tabId, tabName, language = 'fr') => {
  const element = document.getElementById(tabId);
  if (!element) {
    console.error(`Element with id "${tabId}" not found`);
    return { success: false, error: 'Element not found' };
  }

  const titles = {
    fr: {
      calculator: 'Calculateur ZLECAf',
      statistics: 'Statistiques Commerciales',
      production: 'Capacité de Production',
      logistics: 'Plateforme Logistique',
      tools: 'Outils ZLECAf',
      rules: "Règles d'Origine",
      profiles: 'Profils Pays'
    },
    en: {
      calculator: 'AfCFTA Calculator',
      statistics: 'Trade Statistics',
      production: 'Production Capacity',
      logistics: 'Logistics Platform',
      tools: 'AfCFTA Tools',
      rules: 'Rules of Origin',
      profiles: 'Country Profiles'
    }
  };

  const subtitles = {
    fr: 'Rapport généré depuis la plateforme ZLECAf Analytics',
    en: 'Report generated from the AfCFTA Analytics platform'
  };

  const title = titles[language]?.[tabName] || tabName;
  const filename = `${tabName}_${language}_${new Date().toISOString().split('T')[0]}.pdf`;

  return exportToPDF(element, filename, {
    title,
    subtitle: subtitles[language],
    language,
    showDate: true
  });
};

export default { exportToPDF, exportTabToPDF };
