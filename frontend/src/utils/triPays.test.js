import { describe, it, expect } from 'vitest';
import { trierPays } from './triPays';
import { getCountriesByRegion, getAllCountries } from './translations';

const nom = (p) => p.nom;

describe('trierPays', () => {
  it('range les accents avec leur lettre (français)', () => {
    const liste = ['Éthiopie', 'Zambie', 'Égypte', 'Algérie', "Côte d'Ivoire", 'Cameroun', 'Eswatini'].map(
      (n) => ({ nom: n })
    );
    expect(trierPays(liste, nom, 'fr').map(nom)).toEqual([
      'Algérie',
      'Cameroun',
      "Côte d'Ivoire",
      'Égypte',
      'Eswatini',
      'Éthiopie',
      'Zambie',
    ]);
  });

  it('trie en arabe selon l’ordre arabe', () => {
    const liste = ['مصر', 'الجزائر', 'تونس'].map((n) => ({ nom: n }));
    expect(trierPays(liste, nom, 'ar').map(nom)).toEqual(['الجزائر', 'تونس', 'مصر']);
  });

  it('ne modifie pas la liste reçue et accepte une liste vide', () => {
    const liste = [{ nom: 'Togo' }, { nom: 'Bénin' }];
    trierPays(liste, nom, 'fr');
    expect(liste.map(nom)).toEqual(['Togo', 'Bénin']);
    expect(trierPays(undefined, nom, 'fr')).toEqual([]);
  });
});

describe('listes de pays du module Production', () => {
  it.each(['fr', 'en', 'ar'])('sont dans l’ordre alphabétique (%s)', (langue) => {
    const c = new Intl.Collator(langue, { sensitivity: 'base', ignorePunctuation: true });
    const enOrdre = (liste) => liste.every((p, i) => i === 0 || c.compare(liste[i - 1].name, p.name) <= 0);
    Object.values(getCountriesByRegion(langue)).forEach((region) => expect(enOrdre(region)).toBe(true));
    expect(enOrdre(getAllCountries(langue))).toBe(true);
  });
});
