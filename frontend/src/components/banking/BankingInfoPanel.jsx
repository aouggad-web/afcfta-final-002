import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

const texts = {
  fr: {
    title: '🏦 Financement du commerce & banque',
    subtitle: 'Panorama des instruments de financement disponibles pour vos échanges ZLECAf',
    instrumentsTitle: 'Instruments de financement',
    instruments: [
      { name: 'Lettre de crédit (LC)', desc: 'Garantie de paiement émise par la banque de l’importateur.' },
      { name: 'Garantie bancaire', desc: 'Engagement de la banque en cas de défaut de l’une des parties.' },
      { name: 'Affacturage (factoring)', desc: 'Cession des créances commerciales pour un financement immédiat.' },
      { name: 'Assurance-crédit export', desc: 'Couverture du risque d’impayé sur les ventes à l’international.' },
      { name: 'Financement pré-expédition', desc: 'Avance de trésorerie pour produire avant l’expédition.' },
    ],
    partnersTitle: 'Pays partenaires couverts',
    noCountries: 'Aucun pays sélectionné',
    note: 'Informations indicatives — rapprochez-vous de votre banque pour les conditions réelles.',
  },
  en: {
    title: '🏦 Trade finance & banking',
    subtitle: 'Overview of financing instruments available for your AfCFTA trade',
    instrumentsTitle: 'Financing instruments',
    instruments: [
      { name: 'Letter of Credit (LC)', desc: "Payment guarantee issued by the importer's bank." },
      { name: 'Bank guarantee', desc: 'Bank commitment in case either party defaults.' },
      { name: 'Factoring', desc: 'Assignment of trade receivables for immediate financing.' },
      { name: 'Export credit insurance', desc: 'Coverage against non-payment risk on international sales.' },
      { name: 'Pre-shipment financing', desc: 'Cash advance to produce before shipment.' },
    ],
    partnersTitle: 'Covered partner countries',
    noCountries: 'No country selected',
    note: 'Indicative information — contact your bank for actual terms.',
  },
};

export default function BankingInfoPanel({ language = 'fr', countries = [] }) {
  const t = texts[language === 'en' ? 'en' : 'fr'];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">{t.title}</CardTitle>
        <p className="text-sm text-muted-foreground">{t.subtitle}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        <div>
          <h3 className="font-semibold mb-2">{t.instrumentsTitle}</h3>
          <ul className="space-y-2">
            {t.instruments.map((inst) => (
              <li key={inst.name} className="text-sm">
                <span className="font-medium">{inst.name}</span> — {inst.desc}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="font-semibold mb-2">{t.partnersTitle}</h3>
          {countries && countries.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {countries.map((c) => {
                const code = typeof c === 'string' ? c : c.iso3 || c.code || String(c);
                const label = typeof c === 'string' ? c : c.name || code;
                return (
                  <Badge key={code} variant="secondary">
                    {label}
                  </Badge>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t.noCountries}</p>
          )}
        </div>

        <p className="text-xs text-muted-foreground italic">{t.note}</p>
      </CardContent>
    </Card>
  );
}
