import * as React from 'react';
import { cn } from '@/lib/utils';

/**
 * DataFreshnessIndicator — petit badge indiquant la fraîcheur des données.
 * Tolérant à la forme de `freshness` : accepte une chaîne ou un objet
 * ({ status, label, last_updated, updated_at, year }). Ne casse jamais le
 * rendu si le champ est absent ou partiel.
 */
export function DataFreshnessIndicator({ freshness, language = 'fr', className }) {
  if (!freshness) return null;

  const isFr = language !== 'en';

  if (typeof freshness === 'string') {
    return <span className={cn('data-freshness', className)}>🕒 {freshness}</span>;
  }

  const status = freshness.status || freshness.level || 'unknown';
  const when =
    freshness.last_updated ||
    freshness.updated_at ||
    freshness.year ||
    freshness.date ||
    null;
  const label =
    freshness.label ||
    (isFr ? 'Fraîcheur des données' : 'Data freshness');

  const tone =
    status === 'fresh' || status === 'current'
      ? '#155724'
      : status === 'stale' || status === 'outdated'
      ? '#856404'
      : '#383d41';

  return (
    <span
      className={cn('data-freshness', className)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        fontSize: '0.75em',
        color: tone,
      }}
      title={label}
    >
      🕒 {label}
      {when ? ` — ${when}` : ''}
    </span>
  );
}

export default DataFreshnessIndicator;
