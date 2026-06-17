import React, { useEffect, useState } from 'react';

const STATUS_CONFIG = {
  VERIFIED: {
    bg: 'bg-green-50 border-green-200',
    icon: '✓',
    iconColor: 'text-green-600',
    title: 'Données vérifiées',
    titleColor: 'text-green-800',
    textColor: 'text-green-700',
  },
  PARTIAL: {
    bg: 'bg-yellow-50 border-yellow-200',
    icon: '⚠',
    iconColor: 'text-yellow-600',
    title: 'Données partiellement vérifiées',
    titleColor: 'text-yellow-800',
    textColor: 'text-yellow-700',
  },
  SYNTHETIC: {
    bg: 'bg-orange-50 border-orange-200',
    icon: '!',
    iconColor: 'text-orange-600',
    title: 'Données indicatives non vérifiées',
    titleColor: 'text-orange-800',
    textColor: 'text-orange-700',
  },
};

const DEFAULT_MESSAGE = {
  VERIFIED: null,
  PARTIAL:
    'Ces données sont partiellement vérifiées. Certains taux ou formalités ' +
    'peuvent ne pas refléter la réglementation en vigueur.',
  SYNTHETIC:
    "Ces données sont générées par modèle et n'ont pas été vérifiées auprès " +
    "des sources officielles. Ne pas les utiliser pour des décisions commerciales " +
    "réelles. Consultez les tarifs douaniers officiels du pays importateur.",
};

/**
 * Bandeau d'avertissement sur la qualité des données tarifaires.
 *
 * Props:
 *   status        — "VERIFIED" | "PARTIAL" | "SYNTHETIC"
 *                   (prend le pas sur countryIso3 si fourni)
 *   disclaimer    — message personnalisé (remplace le message par défaut)
 *   countryIso3   — charge automatiquement le statut depuis DATA_STATUS.json
 *   className     — classes Tailwind additionnelles
 *   compact       — affichage condensé (icône + titre seulement)
 */
export default function DataStatusBanner({
  status: statusProp,
  disclaimer,
  countryIso3,
  className = '',
  compact = false,
}) {
  const [status, setStatus] = useState(statusProp || null);
  const [message, setMessage] = useState(disclaimer || null);

  useEffect(() => {
    if (statusProp) {
      setStatus(statusProp);
      setMessage(disclaimer || DEFAULT_MESSAGE[statusProp]);
      return;
    }
    if (!countryIso3) return;

    fetch('/data/DATA_STATUS.json')
      .then((r) => r.json())
      .then((doc) => {
        const entry = doc?.countries?.[countryIso3.toUpperCase()];
        if (entry) {
          setStatus(entry.data_status);
          setMessage(disclaimer || entry.disclaimer || DEFAULT_MESSAGE[entry.data_status]);
        }
      })
      .catch(() => {
        setStatus('SYNTHETIC');
        setMessage(disclaimer || DEFAULT_MESSAGE['SYNTHETIC']);
      });
  }, [statusProp, disclaimer, countryIso3]);

  if (!status || status === 'VERIFIED') return null;

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['SYNTHETIC'];

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${cfg.bg} ${className}`}
      role="status"
      aria-live="polite"
    >
      <span
        className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border-2 font-bold ${cfg.iconColor} border-current`}
        aria-hidden="true"
      >
        {cfg.icon}
      </span>
      <div className="min-w-0">
        <span className={`font-semibold ${cfg.titleColor}`}>{cfg.title}</span>
        {!compact && message && (
          <p className={`mt-0.5 ${cfg.textColor}`}>{message}</p>
        )}
      </div>
    </div>
  );
}
