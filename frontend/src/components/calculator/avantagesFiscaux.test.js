/**
 * Ce que ces tests tiennent — et pourquoi.
 *
 * La carte visée est celle que voit un client pendant une démonstration. Le
 * défaut corrigé n'était pas un détail d'affichage : le tarif tunisien publie
 * dix-sept colonnes préférentielles par position, et l'interface les servait
 * toutes sous « Avantages ZLECAf », coche vert et taux masqué. Un opérateur
 * ghanéen y lisait le Koweït et la Palestine comme des avantages ZLECAf.
 */

import { describe, expect, it } from 'vitest';
import { normaliserNom, partenaireDeLAvantage, tauxDeLAvantage, trierAvantages } from './avantagesFiscaux';

// Une position tunisienne réelle : huile moteur 27101981100, droit NPF 0 %.
const AVANTAGES_TUN = [
  { tax: 'DD', rate: 0.0, condition_fr: 'Taux préférentiel — pays partenaire : PALESTINE' },
  { tax: 'DD', rate: 50.0, condition_fr: 'Taux préférentiel — pays partenaire : GHANA' },
  { tax: 'DD', rate: 50.0, condition_fr: 'Taux préférentiel — pays partenaire : KENYA' },
  { tax: 'DD', rate: 0.0, condition_fr: 'Taux préférentiel — pays partenaire : KOWEIT' },
  { tax: 'DD', rate: 0.0, condition_fr: 'Taux préférentiel — pays partenaire : RUANDA' },
];

describe('normaliserNom', () => {
  it('rejoint deux écritures d’un même nom', () => {
    expect(normaliserNom('Égypte')).toBe(normaliserNom('EGYPTE'));
    expect(normaliserNom("Côte d'Ivoire")).toBe(normaliserNom('COTE D IVOIRE'));
  });
});

describe('partenaireDeLAvantage', () => {
  it('lit le partenaire nommé dans la condition', () => {
    expect(partenaireDeLAvantage(AVANTAGES_TUN[1])).toBe('GHANA');
  });

  it('rend null quand aucun partenaire n’est nommé', () => {
    // L'exonération ZLECAf algérienne ne nomme pas de partenaire : elle reste
    // un avantage général, et doit continuer de s'afficher.
    expect(
      partenaireDeLAvantage({
        condition_fr: "Certificat d'Origine dans le cadre ZLECAf - Exonération DD",
      }),
    ).toBeNull();
  });
});

describe('tauxDeLAvantage', () => {
  it('lit un nombre comme une chaîne, et refuse ce qui n’en est pas un', () => {
    expect(tauxDeLAvantage({ rate: 50.0 })).toBe(50);
    expect(tauxDeLAvantage({ rate: '0 %' })).toBe(0);
    expect(tauxDeLAvantage({ rate: 'sur contingent' })).toBeNull();
    expect(tauxDeLAvantage({})).toBeNull();
  });
});

describe('trierAvantages', () => {
  it('ne retient que la colonne au nom de l’origine choisie', () => {
    const tri = trierAvantages(AVANTAGES_TUN, 'GHA', 0);
    expect(tri.pourLOrigine.map((e) => e.partenaire)).toEqual(['GHANA']);
    expect(tri.autresPartenaires).toBe(4);
  });

  it('N’AFFICHE NI LE KOWEÏT NI LA PALESTINE : c’est le défaut corrigé', () => {
    const tri = trierAvantages(AVANTAGES_TUN, 'GHA', 0);
    const affiches = [...tri.pourLOrigine, ...tri.generaux]
      .map((e) => e.libelle)
      .join(' ');
    expect(affiches).not.toMatch(/KOWEIT|PALESTINE/);
  });

  it('dit qu’une colonne à 50 % ne réduit pas un droit NPF de 0 %', () => {
    // Le cœur du défaut : un coche vert annonçait un « avantage » qui, appliqué,
    // coûterait 50 % de la valeur CIF là où le tarif laisse la franchise.
    const tri = trierAvantages(AVANTAGES_TUN, 'GHA', 0);
    expect(tri.pourLOrigine[0].taux).toBe(50);
    expect(tri.pourLOrigine[0].reduitLeDroit).toBe(false);
  });

  it('reconnaît une réduction réelle', () => {
    const tri = trierAvantages(AVANTAGES_TUN, 'KEN', 60);
    expect(tri.pourLOrigine[0].reduitLeDroit).toBe(true);
  });

  it('laisse le rapport au droit INDÉTERMINÉ quand le droit NPF est inconnu', () => {
    // Un droit absent ne vaut pas zéro : comparer contre un zéro de repli
    // ferait passer toute colonne non nulle pour un désavantage.
    const tri = trierAvantages(AVANTAGES_TUN, 'GHA', null);
    expect(tri.pourLOrigine[0].reduitLeDroit).toBeNull();
  });

  it('rapproche une graphie du tarif du nom courant du pays', () => {
    // « RUANDA » est l'écriture de douane.gov.tn ; le pays s'appelle Rwanda.
    const tri = trierAvantages(AVANTAGES_TUN, 'RWA', 0);
    expect(tri.pourLOrigine.map((e) => e.partenaire)).toEqual(['RUANDA']);
  });

  it('compte dans le résidu un partenaire qu’il ne sait pas rapprocher', () => {
    // Contrôle négatif : une graphie inconnue ne doit PAS être attribuée au
    // hasard à l'origine choisie.
    const tri = trierAvantages(
      [{ rate: 0, condition_fr: 'Taux préférentiel — pays partenaire : SYLDAVIE' }],
      'GHA',
      0,
    );
    expect(tri.pourLOrigine).toEqual([]);
    expect(tri.autresPartenaires).toBe(1);
  });

  it('conserve un avantage qui ne nomme aucun partenaire', () => {
    const tri = trierAvantages(
      [{ condition_fr: "Certificat d'Origine dans le cadre ZLECAf - Exonération DD" }],
      'GHA',
      30,
    );
    expect(tri.generaux).toHaveLength(1);
    expect(tri.pourLOrigine).toEqual([]);
  });

  it('accepte une liste absente sans rien inventer', () => {
    const tri = trierAvantages(undefined, 'GHA', 0);
    expect(tri).toEqual({ pourLOrigine: [], generaux: [], autresPartenaires: 0 });
  });
});
