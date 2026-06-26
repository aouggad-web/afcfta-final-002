import { describe, it, expect } from 'vitest';
import {
  AFRICAN_COUNTRIES,
  ISO2_TO_ISO3,
  ISO3_TO_ISO2,
  getCountryFlag,
  getISO3FromISO2,
  getISO2FromISO3,
  getCountryInfo,
  getAllCountries,
  getCountriesByRegion,
  ECONOMIC_COMMUNITIES,
} from './countryCodes';

describe('countryCodes — couverture du référentiel', () => {
  it('contient les 55 entrées (54 pays + RASD/ESH)', () => {
    expect(Object.keys(AFRICAN_COUNTRIES)).toHaveLength(55);
    expect(AFRICAN_COUNTRIES.ESH).toBeDefined();
  });

  it('marque correctement les cas particuliers (Érythrée non-signataire, RASD sans données)', () => {
    expect(AFRICAN_COUNTRIES.ERI.zlecafSignatory).toBe(false);
    expect(AFRICAN_COUNTRIES.ESH.hasTradeData).toBe(false);
  });

  it('construit des mappings inversés cohérents et bijectifs', () => {
    expect(ISO3_TO_ISO2.DZA).toBe('DZ');
    expect(ISO2_TO_ISO3.DZ).toBe('DZA');
    // Chaque pays doit faire un aller-retour ISO3 -> ISO2 -> ISO3
    for (const iso3 of Object.keys(AFRICAN_COUNTRIES)) {
      expect(ISO2_TO_ISO3[ISO3_TO_ISO2[iso3]]).toBe(iso3);
    }
  });
});

describe('getCountryFlag', () => {
  it('retourne le drapeau pour un code ISO3', () => {
    expect(getCountryFlag('NGA')).toBe('🇳🇬');
  });
  it('retourne le drapeau pour un code ISO2', () => {
    expect(getCountryFlag('NG')).toBe('🇳🇬');
  });
  it('est insensible à la casse', () => {
    expect(getCountryFlag('za')).toBe('🇿🇦');
  });
  it('retourne le globe par défaut pour code inconnu ou vide', () => {
    expect(getCountryFlag('XXX')).toBe('🌍');
    expect(getCountryFlag('')).toBe('🌍');
    expect(getCountryFlag(null)).toBe('🌍');
  });
});

describe('conversions ISO2 <-> ISO3', () => {
  it('convertit ISO2 -> ISO3', () => {
    expect(getISO3FromISO2('ma')).toBe('MAR');
    expect(getISO3FromISO2('ZZ')).toBeNull();
  });
  it('convertit ISO3 -> ISO2', () => {
    expect(getISO2FromISO3('mar')).toBe('MA');
    expect(getISO2FromISO3('ZZZ')).toBeNull();
  });
});

describe('getCountryInfo', () => {
  it('résout depuis ISO3 et ISO2 avec le champ iso3 ajouté', () => {
    expect(getCountryInfo('KEN')).toMatchObject({ iso3: 'KEN', iso2: 'KE', name_en: 'Kenya' });
    expect(getCountryInfo('KE')).toMatchObject({ iso3: 'KEN', iso2: 'KE' });
  });
  it('retourne null pour un code invalide', () => {
    expect(getCountryInfo('ZZ')).toBeNull();
    expect(getCountryInfo(null)).toBeNull();
  });
});

describe('getAllCountries', () => {
  it('retourne 55 entrées triées par nom localisé', () => {
    const fr = getAllCountries('fr');
    expect(fr).toHaveLength(55);
    const names = fr.map((c) => c.name);
    const sorted = [...names].sort((a, b) => a.localeCompare(b));
    expect(names).toEqual(sorted);
  });
  it('utilise le nom anglais quand lang=en', () => {
    const en = getAllCountries('en');
    const za = en.find((c) => c.iso3 === 'ZAF');
    expect(za.name).toBe('South Africa');
  });
});

describe('getCountriesByRegion', () => {
  it('filtre par région', () => {
    const north = getCountriesByRegion('North Africa', 'en');
    const isos = north.map((c) => c.iso3);
    expect(isos).toContain('DZA');
    expect(isos).toContain('EGY');
    expect(isos).not.toContain('NGA');
  });
});

describe('ECONOMIC_COMMUNITIES', () => {
  it('ne référence que des codes ISO3 connus', () => {
    for (const [bloc, members] of Object.entries(ECONOMIC_COMMUNITIES)) {
      for (const iso3 of members) {
        expect(AFRICAN_COUNTRIES[iso3], `${bloc} -> ${iso3}`).toBeDefined();
      }
    }
  });
  it('CEMAC contient ses 6 membres', () => {
    expect(ECONOMIC_COMMUNITIES.CEMAC).toHaveLength(6);
    expect(ECONOMIC_COMMUNITIES.CEMAC).toContain('GAB');
  });
});
