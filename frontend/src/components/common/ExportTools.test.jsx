import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CSVExportButton, JSONExportButton } from './ExportTools';

// Capture le contenu CSV directement via le constructeur Blob (jsdom n'expose
// pas Blob.text() de façon fiable). On neutralise aussi createObjectURL et le
// click() de l'ancre (jsdom ne sait pas naviguer).
let csvContent = '';
const RealBlob = global.Blob;
const originalCreate = URL.createObjectURL;
const originalRevoke = URL.revokeObjectURL;
let clickSpy;

beforeEach(() => {
  csvContent = '';
  global.Blob = vi.fn((parts) => {
    csvContent = (parts || []).join('');
    return { type: 'text/csv' };
  });
  URL.createObjectURL = vi.fn(() => 'blob:mock');
  URL.revokeObjectURL = vi.fn();
  clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
});

afterEach(() => {
  global.Blob = RealBlob;
  URL.createObjectURL = originalCreate;
  URL.revokeObjectURL = originalRevoke;
  clickSpy.mockRestore();
});

const columns = [
  { key: 'country', label: 'Pays' },
  { key: 'exports', label: 'Exports' },
];

describe('CSVExportButton', () => {
  it('est désactivé sans données', () => {
    render(<CSVExportButton rows={[]} columns={columns} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('affiche le libellé localisé', () => {
    const { rerender } = render(<CSVExportButton rows={[{ country: 'X' }]} columns={columns} language="fr" />);
    expect(screen.getByRole('button')).toHaveTextContent('Exporter CSV');
    rerender(<CSVExportButton rows={[{ country: 'X' }]} columns={columns} language="en" />);
    expect(screen.getByRole('button')).toHaveTextContent('Export CSV');
  });

  it('génère un CSV avec BOM UTF-8, en-têtes et lignes', async () => {
    const rows = [
      { country: 'Nigéria', exports: 9.7 },
      { country: 'Égypte', exports: 7.2 },
    ];
    render(<CSVExportButton rows={rows} columns={columns} />);
    await userEvent.click(screen.getByRole('button'));

    // Préfixe BOM pour qu'Excel reconnaisse l'UTF-8 (accents)
    expect(csvContent.charCodeAt(0)).toBe(0xfeff);
    const lines = csvContent.replace(/^﻿/, '').split('\n');
    expect(lines[0]).toBe('Pays,Exports');
    expect(lines[1]).toBe('Nigéria,9.7');
    expect(lines[2]).toBe('Égypte,7.2');
  });

  it('échappe les cellules contenant virgule, guillemets ou retour ligne', async () => {
    const rows = [
      { country: 'Congo, Rép. dém.', exports: 'a "b"' },
    ];
    render(<CSVExportButton rows={rows} columns={columns} />);
    await userEvent.click(screen.getByRole('button'));

    const body = csvContent.replace(/^﻿/, '').split('\n')[1];
    expect(body).toBe('"Congo, Rép. dém.","a ""b"""');
  });

  it('traite les valeurs nulles/undefined comme cellules vides', async () => {
    const rows = [{ country: null, exports: undefined }];
    render(<CSVExportButton rows={rows} columns={columns} />);
    await userEvent.click(screen.getByRole('button'));

    const body = csvContent.replace(/^﻿/, '').split('\n')[1];
    expect(body).toBe(',');
  });

  it('ajoute la notice et les métadonnées informatives lorsqu’elles sont fournies', async () => {
    render(<CSVExportButton
      rows={[{ country: 'KEN' }]}
      columns={[{ key: 'country', label: 'Pays' }]}
      exportMetadata={{
        simulation_generated_at: '2026-07-24T12:00:00Z',
        importer_country: 'KEN',
        exporter_country: 'UGA',
        product_code: '10019910',
        assumptions: 'CIF déclaré',
        scope: 'CET + taxes disponibles',
        sources: 'Kenya Law',
        known_data_gaps: 'Gazettes EAC',
      }}
    />);
    await userEvent.click(screen.getByRole('button'));
    expect(csvContent).toContain('Simulation informative des droits et taxes à l’importation');
    expect(csvContent).toContain('Simulation informative — non opposable à l’administration douanière.');
    expect(csvContent).toContain('2026-07-24T12:00:00Z');
  });

  it('neutralise les cellules texte commençant par = + - @ (injection de formules)', async () => {
    const rows = [
      { country: '=1+1', exports: -5 },
      { country: '+cmd', exports: '@SUM(A1)' },
      { country: '-', exports: '- Autres' },
    ];
    render(<CSVExportButton rows={rows} columns={columns} />);
    await userEvent.click(screen.getByRole('button'));

    const lines = csvContent.replace(/^﻿/, '').split('\n');
    // Le nombre négatif reste un nombre, le tiret seul reste tel quel.
    expect(lines[1]).toBe("'=1+1,-5");
    expect(lines[2]).toBe("'+cmd,'@SUM(A1)");
    expect(lines[3]).toBe("-,'- Autres");
  });

  it('neutralise aussi une valeur tableau dont le texte commence par =', async () => {
    render(<CSVExportButton rows={[{ country: ['=1+1'], exports: -5 }]} columns={columns} />);
    await userEvent.click(screen.getByRole('button'));

    expect(csvContent.replace(/^﻿/, '').split('\n')[1]).toBe("'=1+1,-5");
  });

  it('neutralise aussi les métadonnées d’export', async () => {
    render(<CSVExportButton
      rows={[{ country: 'KEN' }]}
      columns={[{ key: 'country', label: 'Pays' }]}
      exportMetadata={{ exporter_country: '@SUM(1)' }}
    />);
    await userEvent.click(screen.getByRole('button'));

    expect(csvContent).toContain("Pays exportateur,'@SUM(1)");
  });

});

describe('JSONExportButton', () => {
  it('est désactivé sans données', () => {
    render(<JSONExportButton data={null} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('est désactivé pour un tableau vide', () => {
    render(<JSONExportButton data={[]} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('affiche le libellé localisé', () => {
    const { rerender } = render(<JSONExportButton data={{ a: 1 }} language="fr" />);
    expect(screen.getByRole('button')).toHaveTextContent('Exporter JSON');
    rerender(<JSONExportButton data={{ a: 1 }} language="en" />);
    expect(screen.getByRole('button')).toHaveTextContent('Export JSON');
  });

  it('sérialise les données en JSON indenté', async () => {
    const data = { country: 'CIV', measures: [{ record_id: 'CIV-GUCE-SINGLE-WINDOW' }] };
    render(<JSONExportButton data={data} />);
    await userEvent.click(screen.getByRole('button'));

    expect(JSON.parse(csvContent)).toEqual(data);
  });
});
