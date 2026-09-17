/**
 * Adaptateur du moteur unique (`POST /calcul`, chantier L3) vers la forme
 * historique déjà consommée par `CalculatorTab` et ses composants d'affichage.
 *
 * Ce module remplace le second chemin de calcul du frontend — l'appel de
 * repli `/calculate-tariff` (`routes/calculator.py`, l'une des « trois
 * cascades » recensées par `docs/PLAN_CALCULATEUR_UNIQUE.md` §1.1) — sans
 * toucher au chemin `/authentic-tariffs/calculate`, qui reste pour l'instant
 * seul à fournir les avantages fiscaux, les formalités administratives et
 * les frais réglementaires : le moteur unifié ne les calcule pas encore.
 *
 * Règle tenue ici comme dans le moteur : un montant INDISPONIBLE ne devient
 * jamais un zéro affiché. Une ligne que le moteur n'a pas pu liquider est
 * exclue du tableau comparatif NPF/ZLECAf (qui n'est pas construit pour
 * afficher un manque ligne par ligne), mais reste motivée dans `_manques_npf`
 * et se reflète dans `confidence_level` / `duty_status`.
 */

const FAMILLE_CATEGORIE = { droit: 'droit_douane', tva: 'tva' };
const categorieDe = (famille) => FAMILLE_CATEGORIE[famille] || 'autre_taxe';

const estCalculee = (ligne) => ligne?.statut === 'CALCULE' && typeof ligne.montant === 'number';
const pctToFraction = (pct) => (typeof pct === 'number' ? pct / 100 : null);
const sommePositive = (valeur) => (typeof valeur === 'number' && valeur > 0 ? valeur : null);

function ligneParCode(lignes) {
  const map = new Map();
  (lignes || []).forEach((l) => map.set(l.code, l));
  return map;
}

/**
 * Sommer les lignes calculées d'une famille — sans jamais faire disparaître
 * dans un total silencieux ni une ligne qui a échoué, ni une famille que la
 * source ne trace pas du tout.
 *
 * Filtrer puis réduire (comme le faisait cette fonction) traite ces deux cas
 * exactement comme « rien à additionner » : leur `reduce` de départ à `0`
 * devient le total affiché, indiscernable d'un pays qui exonère réellement
 * la famille. Les deux se distinguent donc avant la somme : une ligne
 * présente mais non liquidée invalide le total (`null`, pas une somme
 * amputée) ; une famille absente des lignes ET absente à la source
 * (`manques`, motif `NON_TRACEE_A_LA_SOURCE` — la dégradation que
 * `services/calcul.py` applique déjà à `etat`) rend `null` plutôt que `0`.
 */
function familleNonTracee(manques, famille) {
  return (manques || []).some(
    (m) => m.code === famille.toUpperCase() && m.motif === 'NON_TRACEE_A_LA_SOURCE'
  );
}

function sommeFamille(lignes, famille, excluCode, manques) {
  const correspondantes = (lignes || []).filter(
    (l) => l.famille === famille && l.code !== excluCode
  );
  if (correspondantes.some((l) => !estCalculee(l))) return null;
  if (correspondantes.length === 0) return familleNonTracee(manques, famille) ? null : 0;
  return correspondantes.reduce((total, l) => total + l.montant, 0);
}

function sommeAutres(lignes, excluCode) {
  const correspondantes = (lignes || []).filter(
    (l) => l.famille !== 'tva' && l.code !== excluCode
  );
  if (correspondantes.some((l) => !estCalculee(l))) return null;
  return correspondantes.reduce((total, l) => total + l.montant, 0);
}

/**
 * Statut ZLECAf dans le vocabulaire déjà compris par `zlecafAvailability.js`
 * et `CalculatorTab` : `DOCUMENTED` quand un taux a réellement été appliqué ;
 * `OFFER_ONLY` / `PARTNER_NOTICE_REQUIRED` transmis tels quels — ce sont les
 * mêmes noms que `zlecaf_implementation_registry.py`, le registre reste seul
 * à en décider ; sinon `NOT_AVAILABLE`, qu'il s'agisse d'un couloir non
 * autorisé ou d'un couloir autorisé sans taux tracé (`PREFERENCE_NON_TRACEE`).
 */
function zlecafStatusLegacy(preferenceZlecaf) {
  if (preferenceZlecaf?.applique) return 'DOCUMENTED';
  const { statut } = preferenceZlecaf || {};
  return statut === 'OFFER_ONLY' || statut === 'PARTNER_NOTICE_REQUIRED'
    ? statut
    : 'NOT_AVAILABLE';
}

export function buildCalculRequestBody({ destinationISO3, originISO3, hsCode, cifValue }) {
  const body = { destination: destinationISO3, code_sh: hsCode, valeur_cif: cifValue };
  if (originISO3) body.origine = originISO3;
  return body;
}

function buildJournal(cifValue, lignes) {
  const journal = [
    { step: 1, component: 'Valeur CIF', base: cifValue, rate: '-', amount: cifValue,
      cumulative: cifValue, legal_ref: 'Incoterms 2020' },
  ];
  let cumulative = cifValue;
  (lignes || []).forEach((l, i) => {
    if (!estCalculee(l)) {
      journal.push({
        step: i + 2, component: l.libelle, base: null, rate: '-', amount: null,
        cumulative, legal_ref: l.assiette_non_traduite || l.statut,
      });
      return;
    }
    cumulative += l.montant;
    // Un droit spécifique (« 8c/kg ») n'a pas de taux pourcentuel : `taux_pct`
    // y est `null`, et l'afficher tel quel écrirait « null% ». Le moteur porte
    // alors `specifique` (le libellé brut publié) — l'utiliser à sa place.
    const taux = l.montant_unitaire != null ? l.specifique : `${l.taux_pct}%`;
    journal.push({
      step: i + 2, component: l.libelle, base: l.base, base_formula: l.assiette,
      rate: taux, amount: l.montant, cumulative, legal_ref: l.source || '',
    });
  });
  return journal;
}

/**
 * Transformer la réponse de `POST /calcul` dans la forme historique.
 *
 * @param {object} calcul   Corps de la réponse de `POST /calcul`.
 * @param {object} contexte `{ originCountry, destinationCountry, hsCode, cifValue }`
 *                           tels que saisis dans le formulaire (codes bruts,
 *                           pas nécessairement ISO3 — conservés pour l'affichage).
 */
export function mapCalculToLegacyResult(calcul, { originCountry, destinationCountry, hsCode, cifValue }) {
  const npf = calcul.npf || { lignes: [], etat: 'INDISPONIBLE', manques: [] };
  const pref = calcul.preference || null;

  const regime = calcul.regime_commercial || {};
  const complements = calcul.complements_nationaux || [];
  const unionDouaniere = regime.regime === 'UNION_DOUANIERE' ? regime : null;

  // Deux drapeaux, parce que deux questions distinctes se posent.
  //
  // `hasPreference` — un régime préférentiel a-t-il joué ? Il commande les
  // MONTANTS de la colonne préférentielle. Le chemin historique fait de même
  // pour une union douanière : il retire le droit de la cascade
  // (`zlecaf_taxes.pop("DD")`, authentic_tariff_service). Ne pas le suivre
  // ferait répondre aux deux chemins des montants différents sur la même
  // importation — l'écart que le chantier L4 existe pour supprimer.
  //
  // `hasZlecaf` — ce régime est-il la ZLECAf ? Il commande tout ce qui porte
  // son NOM : `zlecaf_eligible`, `zlecaf_preference_applied`, `zlecaf_status`.
  // Une franchise d'union douanière n'y touche pas : l'y déclarer ferait lire
  // un régime pour un autre, la faute même qu'une colonne COMESA prise pour
  // un taux ZLECAf.
  const hasZlecaf = !!(pref && calcul.preference_zlecaf?.applique);
  const hasPreference = !!(pref && (regime.regime ? regime.applique : hasZlecaf));

  const npfLignes = npf.lignes || [];
  const prefLignes = pref?.lignes || [];
  const prefParCode = ligneParCode(prefLignes);

  const dd = npfLignes.find((l) => l.code === 'DD');
  const ddPref = prefParCode.get('DD');
  const dutyAmount = estCalculee(dd) ? dd.montant : null;
  const zlecafDutyAmount = hasPreference && estCalculee(ddPref) ? ddPref.montant : null;

  const vatAmount = sommeFamille(npfLignes, 'tva', null, npf.manques);
  const otherAmount = sommeAutres(npfLignes, 'DD');
  const zlecafVatAmount = hasPreference ? sommeFamille(prefLignes, 'tva', null, pref.manques) : null;
  const zlecafOtherAmount = hasPreference ? sommeAutres(prefLignes, 'DD') : null;

  // Le tableau comparatif ligne à ligne (TaxBreakdownDual) n'a pas de
  // représentation pour un manque : il n'affiche que ce qui a été liquidé.
  // Le manque, lui, reste visible dans le détail des taxes ci-dessous et
  // dans le bandeau de statut (`confidence_level`, `duty_status`).
  const breakdown = npfLignes.filter(estCalculee).map((l) => {
    const p = hasPreference ? prefParCode.get(l.code) : null;
    const pCalculee = estCalculee(p);
    return {
      code: l.code,
      name: l.libelle,
      category: categorieDe(l.famille),
      base_expr: l.assiette,
      amount_npf: l.montant,
      rate_npf_pct: l.taux_pct,
      amount_zlecaf: pCalculee ? p.montant : null,
      rate_zlecaf_pct: pCalculee ? p.taux_pct : null,
      affected_by_zlecaf: pCalculee && p.regime_applique === 'preference',
    };
  });

  const economie = hasPreference && typeof calcul.economie === 'number' ? calcul.economie : null;
  const totalDroitsNpf = sommePositive(npf.total_droits);
  const pctEconomie = economie !== null && totalDroitsNpf
    ? Math.round((economie / totalDroitsNpf) * 10000) / 100
    : null;

  const summary = {
    npf: {
      droit_douane: dutyAmount, tva: vatAmount, autres_taxes: otherAmount,
      cout_total: npf.total_a_payer ?? null,
    },
    zlecaf: hasPreference ? {
      droit_douane: zlecafDutyAmount, tva: zlecafVatAmount, autres_taxes: zlecafOtherAmount,
      cout_total: pref.total_a_payer ?? null,
    } : null,
    economie_totale: economie,
  };

  const taxesDetailSource = npfLignes.map((l) => ({
    code: l.code, tax: l.code, rate: l.taux_pct ?? null, observation: l.libelle,
  }));

  const provenance = calcul.provenance || {};
  const referenceLegale = provenance.assiettes?.reference_legale
    || provenance.source?.nom || null;
  const npfComplet = npf.etat === 'COMPLET';

  return {
    origin_country: originCountry,
    destination_country: destinationCountry,
    hs_code: hsCode,
    hs6_code: (hsCode || '').slice(0, 6),
    value: cifValue,
    description: calcul.position?.designation || null,

    normal_tariff_rate: pctToFraction(dd?.taux_pct),
    normal_tariff_amount: dutyAmount,
    zlecaf_tariff_rate: hasPreference ? pctToFraction(ddPref?.taux_pct) : null,
    zlecaf_tariff_amount: zlecafDutyAmount,

    // Plusieurs taux de TVA peuvent coexister sur une même position (rare,
    // mais réel) : aucun taux unique n'est affirmé, seul le montant l'est.
    normal_vat_rate: null,
    normal_vat_amount: vatAmount,
    normal_statistical_fee: 0,
    normal_community_levy: 0,
    normal_ecowas_levy: 0,
    normal_other_taxes_total: otherAmount,
    normal_total_cost: npf.total_a_payer ?? null,

    zlecaf_vat_rate: null,
    zlecaf_vat_amount: zlecafVatAmount,
    zlecaf_statistical_fee: 0,
    zlecaf_community_levy: 0,
    zlecaf_ecowas_levy: 0,
    zlecaf_other_taxes_total: zlecafOtherAmount,
    zlecaf_total_cost: hasPreference ? (pref.total_a_payer ?? null) : null,

    savings: economie,
    savings_percentage: pctEconomie,
    total_savings_with_taxes: economie,
    total_savings_percentage: pctEconomie,

    total_taxes_npf: npf.taux_effectif_pct ?? null,
    total_taxes_zlecaf: hasPreference ? (pref.taux_effectif_pct ?? null) : null,

    taxes_breakdown: breakdown,
    taxes_summary: summary,
    // Normalisé par `normalizeTaxesDetail` à l'appel, comme le chemin
    // authentique : même fonction, même garantie (jamais de taux fabriqué).
    taxes_detail: taxesDetailSource,
    currency: null, // conversion de devise hors périmètre du moteur de calcul

    data_source: 'socle_unifie',
    tariff_precision: provenance.niveau === 'national' ? 'sub_position' : 'hs6_country',
    calculation_profile_status: 'country_specific',
    cascade_legal_source: referenceLegale,

    // Le régime affiché est celui qui a réellement joué. Écrire « ZLECAF »
    // dès qu'une préférence s'applique ferait passer une franchise d'union
    // douanière pour une préférence continentale.
    // Même vocabulaire que le chemin historique (`authentic_tariff_service`) :
    // `trade_regime` nomme le régime, `trade_regime_code` le bloc. Diverger
    // ici obligerait l'interface à comprendre deux dialectes pour un seul fait.
    trade_regime: unionDouaniere ? 'CUSTOMS_UNION' : hasZlecaf ? 'ZLECAF' : 'NPF',
    trade_regime_code: unionDouaniere ? unionDouaniere.code_bloc : hasZlecaf ? 'ZLECAF' : 'NPF',
    trade_regime_note: regime.note || null,
    preferential_regime_applied: hasPreference,

    // Union douanière : le bloc, son libellé et la raison. `null` quand les
    // deux pays n'en partagent pas — l'interface n'affiche alors rien.
    customs_union: unionDouaniere
      ? {
          code: unionDouaniere.code_bloc,
          label: unionDouaniere.libelle_bloc,
          note: unionDouaniere.note,
        }
      : null,
    zlecaf_eligible: hasZlecaf,
    zlecaf_preference_applied: hasZlecaf,
    zlecaf_note: calcul.preference_zlecaf?.note || null,
    plancher_npf: null,
    zlecaf_status: zlecafStatusLegacy(calcul.preference_zlecaf),
    zlecaf_rate_expression: null,
    zlecaf_rate_source: null,
    zlecaf_rate_calculation_status: null,
    zlecaf_offer_rate_pct: null,
    zlecaf_offer_rate_expression: null,

    // Le moteur unifié ne calcule pas encore ces trois blocs (chantier
    // distinct de L1-L3) : listes vides et objets nuls, jamais une valeur
    // inventée à leur place.
    fiscal_advantages: [],
    administrative_formalities: [],
    has_sub_positions: false,
    sub_position_count: 0,
    sub_position: null,
    // Frais des prestataires que la douane délègue. La route les sert depuis
    // le point d'entrée commun à tous les chemins de calcul ; les remettre à
    // `null` ici les jetait, et faisait répondre au chemin unifié autre chose
    // qu'au chemin historique sur la même importation. Ils restent hors du
    // coût douanier, que le backend calcule sans eux.
    regulatory_compliance: calcul.regulatory_compliance ?? null,
    regulatory_cost: calcul.regulatory_cost ?? null,
    regulatory_reported: calcul.regulatory_reported ?? null,
    national_legal_calculation: null,
    generic_legal_calculation: null,
    kenya_legal_calculation: null,

    rules_of_origin: {
      rule: 'ZLECAf Rules of Origin',
      requirement: null,
      regional_content: 40,
    },

    normal_calculation_journal: buildJournal(cifValue, npfLignes),
    zlecaf_calculation_journal: hasPreference ? buildJournal(cifValue, prefLignes) : [],
    computation_order_ref: `Socle unifié — ${provenance.source?.nom || destinationCountry}`,
    last_verified: provenance.source?.collecte ? String(provenance.source.collecte).slice(0, 10) : null,
    // Un complément national est un taux standard de pays, pas une donnée de
    // ligne : il rend le calcul complet sans le rendre certain — un bien
    // détaxé y recevrait le taux plein. La confiance reste donc « partielle »
    // même quand rien ne manque.
    confidence_level: npfComplet && !complements.length ? 'very_high' : 'partial',
    complements_nationaux: complements,

    // État honnête propre au moteur unique, jamais réductible à un booléen :
    // `_npf_etat`/`_manques_npf` permettent d'afficher un motif, pas un 0.
    duty_status: dutyAmount === null ? 'UNAVAILABLE' : 'PAYABLE',
    duty_notice: dutyAmount === null
      ? (npf.manques || []).find((m) => m.code === 'DD')?.motif || null
      : null,
    dd_available: dutyAmount !== null,
    _npf_etat: npf.etat,
    _zlecaf_etat: hasPreference ? pref.etat : null,
    _manques_npf: npf.manques || [],
  };
}
