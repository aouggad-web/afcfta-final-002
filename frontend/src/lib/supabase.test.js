/**
 * Client Supabase (audit M6) : flux PKCE, jamais le flux « implicit » par
 * défaut qui ramène la session dans l'URL.
 */
import { afterEach, expect, it, vi } from 'vitest';

vi.mock('@supabase/supabase-js', () => ({ createClient: vi.fn(() => ({ auth: {} })) }));

afterEach(() => {
  vi.unstubAllEnvs();
  vi.clearAllMocks();
  vi.resetModules();
});

it('crée le client en flux PKCE quand le projet est configuré', async () => {
  vi.stubEnv('VITE_SUPABASE_URL', 'https://projet.supabase.co');
  vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test');
  vi.resetModules();
  const { createClient } = await import('@supabase/supabase-js');
  const { supabase } = await import('./supabase');

  expect(supabase).not.toBeNull();
  expect(createClient).toHaveBeenCalledWith('https://projet.supabase.co', 'sb_publishable_test', {
    auth: expect.objectContaining({ flowType: 'pkce', detectSessionInUrl: true }),
  });
});

it("n'en crée aucun sans configuration", async () => {
  vi.stubEnv('VITE_SUPABASE_URL', '');
  vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', '');
  vi.resetModules();
  const { createClient } = await import('@supabase/supabase-js');
  const { supabase } = await import('./supabase');

  expect(supabase).toBeNull();
  expect(createClient).not.toHaveBeenCalled();
});

it('crée le client de vérification des liens sans stockage ni rafraîchissement', async () => {
  vi.stubEnv('VITE_SUPABASE_URL', 'https://projet.supabase.co');
  vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test');
  vi.resetModules();
  const { createClient } = await import('@supabase/supabase-js');
  const { creerClientVerification } = await import('./supabase');
  createClient.mockClear();

  creerClientVerification();

  expect(createClient).toHaveBeenCalledWith('https://projet.supabase.co', 'sb_publishable_test', {
    auth: expect.objectContaining({ persistSession: false, autoRefreshToken: false, detectSessionInUrl: false }),
  });
});
