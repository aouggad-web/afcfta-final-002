import React from 'react';

const ACTIONS = [
  ['VALIDATE', 'Valider'],
  ['REJECT', 'Rejeter'],
  ['SELECT_OTHER_HS6', 'Sélectionner un autre SH6'],
];

export default function KenyaGazetteMappingReview({ mappings = [], onReview }) {
  return (
    <section aria-labelledby="kenya-mapping-review-title">
      <h2 id="kenya-mapping-review-title">Revue des rattachements SH6 — gazettes Kenya</h2>
      {mappings.map((mapping) => (
        <article key={mapping.mapping_id} className="card" data-testid="gazette-mapping-card">
          <h3>{mapping.gazette_product_text}</h3>
          <p>{mapping.gazette_reference}</p>
          <dl>
            <dt>Résultats de l’index existant</dt>
            <dd>{mapping.wco_index_matches?.length ? JSON.stringify(mapping.wco_index_matches) : 'Aucun résultat validé'}</dd>
            <dt>Candidats SH6</dt>
            <dd>{mapping.hs6_candidates?.join(', ') || 'Aucun'}</dd>
            <dt>Notes contrôlées</dt>
            <dd>{[...(mapping.section_notes_checked || []), ...(mapping.chapter_notes_checked || [])].join('; ') || 'Non disponibles'}</dd>
            <dt>Taux CET / dérogatoire</dt>
            <dd>{mapping.base_cet_rate ?? 'À établir'} / {mapping.gazette_override_rate ?? 'Voir mesure'}</dd>
            <dt>Confiance</dt>
            <dd>{mapping.confidence_score}/100 — {mapping.classification_status}</dd>
          </dl>
          <div role="group" aria-label={`Décision pour ${mapping.mapping_id}`}>
            {ACTIONS.map(([action, label]) => (
              <button key={action} type="button" onClick={() => onReview?.(mapping, action)}>
                {label}
              </button>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
