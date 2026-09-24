import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const srcDir = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(resolve(srcDir, p), 'utf8');

// Garde de câblage, pas de rendu. L'application complète a déjà vécu dans le
// dépôt sans être montée par personne : index.js recréait un App() local avec
// cinq modules en placeholder, et App.js — les onze modules, le thème, l'i18n —
// n'était importé nulle part. Aucun test de composant n'aurait vu le défaut,
// puisque chaque composant pris isolément fonctionnait.
describe('point d’entrée du frontend', () => {
  const html = read('../index.html');
  const index = read('./index.js');

  it('index.html charge bien src/index.js', () => {
    expect(html).toContain('/src/index.js');
  });

  it('index.js monte le composant App du dépôt', () => {
    expect(index).toMatch(/import App from '\.\/App'/);
    expect(index).toMatch(/createRoot\([\s\S]*\)\.render\(\s*<App\s*\/>\s*\)/);
  });

  it('index.js ne redéfinit pas sa propre application', () => {
    expect(index).not.toMatch(/function App\s*\(/);
    expect(index).not.toContain('ModulePlaceholder');
    expect(index).not.toContain('Module en développement');
  });

  it("l'intercepteur CSRF est installé dès le point d'entrée", () => {
    // Sans lui, chaque POST axios part sans X-CSRF-Token et le serveur répond
    // 403 « CSRF token missing » — le calcul de la Tunisie en premier.
    expect(index).toContain("import './services/csrf'");
    expect(index.indexOf("import './services/csrf'")).toBeLessThan(index.indexOf('import App'));
  });

  it('i18next est initialisé avant le rendu, car App.js appelle useTranslation', () => {
    expect(index).toContain("import './i18n'");
    expect(read('./App.js')).toContain('useTranslation');
  });

  it('App.js expose les onze modules réels, aucun placeholder', () => {
    const app = read('./App.js');
    for (const tab of [
      'dashboard', 'calculator', 'statistics', 'production', 'logistics',
      'banking', 'tools', 'rules', 'profiles', 'reports', 'contact',
    ]) {
      expect(app).toContain(`case '${tab}'`);
    }
    expect(app).not.toContain('Module en développement');
  });
});
