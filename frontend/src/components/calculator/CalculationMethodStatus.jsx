import React from "react";
import { AlertTriangle, CheckCircle2, Scale } from "lucide-react";

export default function CalculationMethodStatus({
  status,
  legalSource,
  language = "fr",
}) {
  if (!status && !legalSource) return null;

  const fr = language === "fr";
  const isCountrySpecific = status === "country_specific";
  const title = isCountrySpecific
    ? fr
      ? "Méthode nationale appliquée"
      : "Country-specific method applied"
    : fr
      ? "Méthode générique à confirmer"
      : "Generic method to be confirmed";
  const description = isCountrySpecific
    ? fr
      ? "Les assiettes et l’ordre des taxes suivent le profil du pays de destination."
      : "Tax bases and ordering follow the destination country profile."
    : fr
      ? "Aucune méthode nationale validée n’est encore enregistrée pour ce pays. Le résultat utilise provisoirement TVA = CIF + DD."
      : "No validated country method is registered yet. The result provisionally uses VAT = CIF + customs duty.";
  const Icon = isCountrySpecific ? CheckCircle2 : AlertTriangle;

  return (
    <div
      role={isCountrySpecific ? "status" : "alert"}
      data-testid="calculation-method-status"
      className={`rounded-xl border p-4 ${
        isCountrySpecific
          ? "border-[color-mix(in_srgb,var(--success)_30%,transparent)] bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))]"
          : "border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))]"
      }`}
    >
      <div className="flex items-start gap-3">
        <Icon
          className={`mt-0.5 h-5 w-5 shrink-0 ${isCountrySpecific ? "text-[var(--success)]" : "text-[var(--gold)]"}`}
        />
        <div>
          <p
            className={`font-semibold ${isCountrySpecific ? "text-[var(--success)]" : "text-[var(--gold)]"}`}
          >
            {title}
          </p>
          <p className="mt-1 text-sm text-[var(--text)]">{description}</p>
          {legalSource && (
            <p className="mt-2 flex items-start gap-1.5 text-xs text-[var(--afcfta-muted)]">
              <Scale className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                {fr ? "Référence" : "Reference"} : {legalSource}
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
