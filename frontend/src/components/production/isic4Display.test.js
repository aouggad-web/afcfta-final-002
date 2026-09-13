import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { INDSTAT_FIELDS, IDSB_FIELDS, femaleSharePct } from './ProductionManufacturing';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '../../../..');

describe('familles d’indicateurs ISIC4', () => {
  it('INDSTAT et IDSB sont disjoints', () => {
    const overlap = INDSTAT_FIELDS.filter((f) => IDSB_FIELDS.includes(f));
    expect(overlap).toEqual([]);
  });

  // Un indicateur ajouté côté backend et oublié ici disparaîtrait de l'écran
  // sans que rien n'échoue : les deux tableaux n'affichent QUE les champs de
  // leur liste. Ce test lit la source de vérité plutôt qu'une copie.
  it('couvrent tous les indicateurs que le backend peut émettre', () => {
    const py = readFileSync(resolve(repoRoot, 'backend/etl/isic4_idsb_data.py'), 'utf8');
    const block = (name) => py.slice(py.indexOf(`${name} = {`), py.indexOf('}', py.indexOf(`${name} = {`)));
    const fieldsOf = (name) => Array.from(block(name).matchAll(/:\s*"([a-z0-9_]+)"/g)).map((m) => m[1]);

    const idsb = fieldsOf('_IDSB_INDICATORS');
    const indstat = fieldsOf('_INDSTAT_INDICATORS');
    expect(idsb.length).toBeGreaterThan(0);
    expect(indstat.length).toBeGreaterThan(0);

    expect([...IDSB_FIELDS].sort()).toEqual([...idsb].sort());
    expect([...INDSTAT_FIELDS].sort()).toEqual([...indstat].sort());
  });
});

describe('part des femmes', () => {
  const series = (employees, female) => ({
    employees: employees.map(([year, value]) => ({ year, value })),
    female_employees: female.map(([year, value]) => ({ year, value })),
  });

  it('calcule le rapport quand les deux valeurs existent', () => {
    expect(femaleSharePct(series([[2020, 1000]], [[2020, 350]]), 2020)).toBeCloseTo(35);
  });

  it('ne conclut pas si une des deux séries manque pour l’année', () => {
    expect(femaleSharePct(series([[2020, 1000]], [[2019, 350]]), 2020)).toBeNull();
    expect(femaleSharePct(series([[2019, 1000]], [[2020, 350]]), 2020)).toBeNull();
  });

  // Zéro salarié ne fait pas « 0 % de femmes » : c'est une division par zéro.
  it('ne divise pas par un effectif nul', () => {
    expect(femaleSharePct(series([[2020, 0]], [[2020, 0]]), 2020)).toBeNull();
  });

  it('ne prend pas une absence pour un zéro', () => {
    expect(femaleSharePct({ employees: [{ year: 2020, value: 1000 }] }, 2020)).toBeNull();
    expect(femaleSharePct(series([[2020, null]], [[2020, 350]]), 2020)).toBeNull();
  });
});
