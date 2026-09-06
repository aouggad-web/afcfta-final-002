const fs = require('fs');
const crypto = require('crypto');
const { tarifSchema } = require('../src/schemas/tarifSchema');

// Charger les données existantes
const rawData = JSON.parse(fs.readFileSync('./data/crawled/ZMB_tariffs.json'));

// Configuration des sources officielles
const SOURCE_ZMB = {
  reference: "Tarif douanier Zambien 2026",
  lien: "https://www.zra.org.zm/tariff",
  date_mise_a_jour: "2026-08-15"
};

// Fonction de transformation
function transformEntry(rawEntry) {
  return {
    pays: "ZMB",
    sous_position: rawEntry.hs_code,
    intitule: rawEntry.description,
    droits: [{
      type: "Droit de douane",
      taux: rawEntry.customs_duty,
      unite: "%",
      calcul: "Valeur CAF * taux"
    }, ...rawEntry.other_taxes.map(tax => ({
      type: tax.name,
      taux: tax.rate,
      unite: tax.unit,
      calcul: tax.calculation
    }))],
    formalites: rawEntry.required_documents.map(doc => ({
      document: doc.name,
      autorite: doc.issuing_authority,
      delivrance: doc.timing
    })),
    npf: {
      statut: rawEntry.npf_applicable ? "Applicable" : "Non applicable",
      reference: rawEntry.npf_reference
    },
    avantages_fta: rawEntry.fta_benefits.map(benefit => ({
      accord: benefit.agreement,
      reduction: benefit.reduction_rate,
      condition: benefit.conditions
    })),
    source: {
      ...SOURCE_ZMB,
      empreinte_crypto: generateHash(rawEntry)
    }
  };
}

// Générer l'empreinte cryptographique
function generateHash(entry) {
  const hash = crypto.createHash('sha256');
  hash.update(JSON.stringify(entry));
  return 'sha256:' + hash.digest('hex');
}

// Transformation complète
const transformedData = rawData.map(transformEntry);

// Validation
const { error } = tarifSchema.validate(transformedData);
if (error) {
  console.error("Validation error:", error.details);
} else {
  // Sauvegarder
  fs.writeFileSync(
    './data/structured/ZMB_tariffs_v2.json', 
    JSON.stringify(transformedData, null, 2)
  );
  console.log("Transformation successful!");
}