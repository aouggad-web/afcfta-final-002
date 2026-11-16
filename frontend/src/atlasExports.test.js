/**
 * Atlas Business (page statique /tools/afcfta_business_atlas.html) : export
 * CSV réservé à l'administrateur (demande du 06/11/2026). Les boutons « ↓ CSV »,
 * masqués dans la page, n'apparaissent que pour une session qui a le format CSV
 * (`export_formats` de GET /api/auth/me).
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

const dossier = path.resolve(__dirname, '../public/tools');
const page = readFileSync(path.join(dossier, 'afcfta_business_atlas.html'), 'utf8');
const script = readFileSync(path.join(dossier, 'afcfta_business_atlas.js'), 'utf8');

const boutons = () => [...document.querySelectorAll('[data-export]')];

function ouvrirAtlas(me) {
  document.body.innerHTML = new DOMParser().parseFromString(page, 'text/html').body.innerHTML;
  vi.stubGlobal('Chart', class { destroy() {} });
  vi.stubGlobal(
    'fetch',
    vi.fn((url) =>
      Promise.resolve(
        url === '/api/auth/me' && me ? { ok: true, json: () => Promise.resolve(me) } : { ok: false },
      ),
    ),
  );
  window.eval(script);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('les boutons CSV sont masqués dans la page avant toute réponse', () => {
  document.body.innerHTML = new DOMParser().parseFromString(page, 'text/html').body.innerHTML;
  expect(boutons()).toHaveLength(3);
  expect(boutons().every((b) => b.hidden)).toBe(true);
});

it.each([
  ['un visiteur sans session', null],
  ['un abonné Business', { role: 'user', export_formats: ['pdf'] }],
])('les boutons CSV restent masqués pour %s', async (_, me) => {
  ouvrirAtlas(me);
  await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/auth/me', { credentials: 'include' }));
  await new Promise((fin) => setTimeout(fin, 0));
  expect(boutons().every((b) => b.hidden)).toBe(true);
});

it('les boutons CSV apparaissent pour l’administrateur', async () => {
  ouvrirAtlas({ role: 'admin', export_formats: ['csv', 'excel', 'pdf'] });
  await waitFor(() => expect(boutons().every((b) => !b.hidden)).toBe(true));
});
