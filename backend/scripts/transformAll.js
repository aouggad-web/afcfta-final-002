const fs = require('fs');
const crypto = require('crypto');
const path = require('path');
const { tarifSchema } = require('../../src/schemas/tarifSchema');

// Configuration des sources par pays
const COUNTRY_CONFIG = {
  ZMB: {
    reference: "Tarif douanier Zambien 2026",
    lien: "https://www.zra.org.zm/tariff",
    date_mise_a_jour: "2026-08-15",
  },
  DZA: {
    reference: "Tarif des Douanes Algérien 2026",
    lien: "https://www.douane.dz/tarif",
    date_mise_a_jour: "2026-07-01",
  },
  EGY: {
    reference: "Egyptian Custom Tariff 2026",
    lien: "https://www.customs.gov.eg/tariff",
    date_mise_a_jour: "2026-06-30",
  },
  // Ajouter les autres pays ici selon le même modèle
};

// Mécanisme d'extension pour les formats spécifiques
const COUNTRY_TRANSFORMERS = {
  // Transformateur par défaut
  default: rawEntry => ({
    pays: rawEntry.iso,
    sous_position: rawEntry.hs_code,
    intitule: rawEntry.description,
    droits: (rawEntry.taxes || []).map(tax => ({
      type: tax.name,
      taux: tax.rate,
      unite: tax.unit,
      calcul: tax.formula
    })),
    formalites: (rawEntry.documents || []).map(doc => ({
      document: doc.name,
      autorite: doc.issuing_authority,
      delivrance: doc.timing
    })),
    npf: {
      statut: rawEntry.npf_applicable ? "Applicable" : "Non applicable",
      reference: rawEntry.npf_reference || ""
    },
    avantages_fta: (rawEntry.fta_benefits || []).map(benefit => ({
      accord: benefit.agreement,
      reduction: benefit.reduction_rate,
      condition: benefit.conditions
    }))
  }),
  
  // Transformateurs spécifiques par pays
  ZMB: rawEntry => {
    const base = COUNTRY_TRANSFORMERS.default(rawEntry);
    return {
      ...base,
      // Transformations spécifiques pour la Zambie
    };
  }
};

// Fonction principale de transformation
function transformCountryData(countryCode) {
  const config = COUNTRY_CONFIG[countryCode] || {};
  const transform = COUNTRY_TRANSFORMERS[countryCode] || COUNTRY_TRANSFORMERS.default;
  
  const rawPath = `./data/crawled/${countryCode}_tariffs.json`;
  const outPath = `./data/structured/${countryCode}_v2.json`;
  
  try {
    const rawData = JSON.parse(fs.readFileSync(rawPath));
    const transformedData = rawData.map(entry => {
      const transformed = transform(entry);
      
      // Ajouter la source et l'empreinte cryptographique
      transformed.source = {
        ...config,
        empreinte_crypto: generateHash(entry)
      };
      
      return transformed;
    });

    // Valider le schéma
    const { error } = tarifSchema.validate(transformedData);
    if (error) {
      console.error(`[${countryCode}] Validation error:`, error.details);
    } else {
      fs.writeFileSync(outPath, JSON.stringify(transformedData, null, 2));
      console.log(`[${countryCode}] Transformation successful!`);
      return true;
    }
  } catch (err) {
    console.error(`[${countryCode}] Error: ${err.message}`);
    return false;
  }
}

// Génération de l'empreinte cryptographique
function generateHash(data) {
  const hash = crypto.createHash('sha256');
  hash.update(JSON.stringify(data));
  return 'sha256:' + hash.digest('hex');
}

// Exécution pour tous les pays
const africanCountries = Object.keys(COUNTRY_CONFIG);
const results = {};

for (const country of africanCountries) {
  results[country] = transformCountryData(country);
}

// Enregistrer le rapport global
fs.writeFileSync(
  './transformation_report.json', 
  JSON.stringify({
    timestamp: new Date().toISOString(),
    results
  }, null, 2)
);

console.log('Transformation complète terminée!');