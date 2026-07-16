import React from 'react';
import { AlertTriangle, CheckCircle2, Scale } from 'lucide-react';

export default function CalculationMethodStatus({ status, legalSource, language = 'fr' }) {
  if (!status && !legalSource) return null;

  const fr = language === 'fr';
  const isCountrySpecific = status === 'country_specific';
  const title = isCountrySpecific
    ? (fr ? 'Méthode nationale appliquée' : 'Country-specific method applied')
    : (fr ? 'Méthode générique à confirmer' : 'Generic method to be confirmed');
  const description = isCountrySpecific
    ? (fr
      ? 'Les assiettes et l’ordre des taxes suivent le profil du pays de destination.'
      : 'Tax bases and ordering follow the destination country profile.')
    : (fr
      ? 'Aucune méthode nationale validée n’est encore enregistrée pour ce pays. Le résultat utilise provisoirement TVA = CIF + DD.'
      : 'No validated country method is registered yet. The result provisionally uses VAT = CIF + customs duty.');
  const Icon = isCountrySpecific ? CheckCircle2 : AlertTriangle;

  return (
    <div
      role={isCountrySpecific ? 'status' : 'alert'}
      data-testid="calculation-method-status"
      className={`rounded-xl border p-4 ${
        isCountrySpecific
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-amber-500/40 bg-amber-500/10'
      }`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${isCountrySpecific ? 'text-emerald-400' : 'text-amber-400'}`} />
        <div>
          <p className={`font-semibold ${isCountrySpecific ? 'text-emerald-300' : 'text-amber-300'}`}>
            {title}
          </p>
          <p className="mt-1 text-sm text-slate-300">{description}</p>
          {legalSource && (
            <p className="mt-2 flex items-start gap-1.5 text-xs text-slate-400">
              <Scale className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{fr ? 'Référence' : 'Reference'} : {legalSource}</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
