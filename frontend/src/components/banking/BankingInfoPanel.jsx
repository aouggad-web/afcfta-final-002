import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// ── Country flags (ISO2 → emoji) ─────────────────────────────────────────────
const COUNTRY_FLAGS = {
  DZ:'🇩🇿', MA:'🇲🇦', TN:'🇹🇳', EG:'🇪🇬', LY:'🇱🇾', MR:'🇲🇷', SD:'🇸🇩',
  NG:'🇳🇬', GH:'🇬🇭', CI:'🇨🇮', SN:'🇸🇳', ML:'🇲🇱', BF:'🇧🇫', NE:'🇳🇪',
  TG:'🇹🇬', BJ:'🇧🇯', GN:'🇬🇳', GM:'🇬🇲', GW:'🇬🇼', LR:'🇱🇷', SL:'🇸🇱',
  CV:'🇨🇻', KE:'🇰🇪', TZ:'🇹🇿', UG:'🇺🇬', RW:'🇷🇼', BI:'🇧🇮', SO:'🇸🇴',
  DJ:'🇩🇯', ER:'🇪🇷', ET:'🇪🇹', SS:'🇸🇸', ZA:'🇿🇦', ZW:'🇿🇼', ZM:'🇿🇲',
  MZ:'🇲🇿', MW:'🇲🇼', BW:'🇧🇼', NA:'🇳🇦', LS:'🇱🇸', SZ:'🇸🇿', MG:'🇲🇬',
  MU:'🇲🇺', SC:'🇸🇨', KM:'🇰🇲', AO:'🇦🇴', CG:'🇨🇬', CD:'🇨🇩', CF:'🇨🇫',
  CM:'🇨🇲', GA:'🇬🇦', GQ:'🇬🇶', ST:'🇸🇹', TD:'🇹🇩',
};

// ── i18n texts ────────────────────────────────────────────────────────────────
const texts = {
  fr: {
    title: '🏦 Système Bancaire Africain – ZLECAf',
    subtitle: 'Réglementations de change, domiciliation et financement du commerce',
    selectCountry: 'Sélectionner un pays',
    selectCountryPrompt: 'Sélectionnez un pays pour afficher les informations bancaires, réglementaires et de risque.',
    banks: 'Banques',
    centralBank: 'Banque Centrale',
    commercialBanks: 'Banques Commerciales',
    regionalBanks: 'Banques Régionales',
    forex: 'Change',
    domiciliationRequired: 'Domiciliation Obligatoire',
    domiciliationConditional: 'Domiciliation Conditionnelle',
    domiciliationFree: 'Non Requise',
    threshold: 'Seuil',
    allOperations: 'Toutes opérations',
    timeline: 'Délai rapatriement',
    days: 'jours',
    regulation: 'Réglementation',
    strict: 'Stricte',
    moderate: 'Modérée',
    liberal: 'Libérale',
    risk: 'Risque Pays',
    riskRating: 'Notation',
    forexRisk: 'Risque Change',
    politicalRisk: 'Risque Politique',
    transferRisk: 'Risque Transfert',
    alertLevel: 'Niveau Alerte',
    riskScore: 'Score',
    maxExposure: 'Exposition max recommandée',
    exposureWarning: '⚠ Montant dépasse l\'exposition recommandée',
    priorAuthRequired: '⚠ Autorisation préalable requise',
    penalties: 'Sanctions',
    instruments: 'Instruments',
    coverage: 'Couverture',
    paymentSystems: 'Paiements',
    compliance: 'Conformité',
    amlFramework: 'Cadre AML',
    kycRequired: 'KYC requis',
    sanctionsScreening: 'Contrôle des sanctions',
    reportingRequirements: 'Obligations de déclaration',
    fiuLabel: 'Cellule FIU',
    loading: 'Chargement…',
    error: 'Erreur de chargement',
    noData: 'Données non disponibles',
    documents: 'Documents requis',
    currency: 'Devise',
    swiftCode: 'Code SWIFT',
    tradeFinance: 'Commerce Ext.',
    services: 'Services',
    yes: 'OUI',
    no: 'NON',
    website: 'Site web',
    mandatory_documents: 'Documents obligatoires',
    notes: 'Notes',
    address: 'Adresse',
    phone: 'Téléphone',
    email: 'E-mail',
    established: 'Fondée en',
    bankingAct: 'Loi bancaire',
    licenseType: 'Agrément',
    correspondents: 'Correspondants',
    register: 'Registre',
    regulations: 'Réglementations',
    registerTitle: 'Registre des Banques Africaines',
    registerSubtitle: 'Annuaire consultable – banques centrales, commerciales et régionales',
    searchPlaceholder: 'Rechercher (nom, sigle, pays…)',
    filterType: 'Type de banque',
    allTypes: 'Tous types',
    centralType: 'Banques centrales',
    commercialType: 'Banques commerciales',
    regionalType: 'Banques régionales',
    tradeFinanceOnly: 'Trade finance seulement',
    allCountries: 'Tous les pays',
    resultCount: 'résultat(s)',
    regulationsTitle: 'Réglementations de Change – Vue Comparative',
    regulationsSubtitle: 'Synthèse des contrôles de change pour les pays africains AfCFTA',
    filterRegulation: 'Niveau de réglementation',
    allLevels: 'Tous niveaux',
    domiciliation: 'Domiciliation',
    priorAuth: 'Autorisation',
    repatriation: 'Rapatriement',
    countryCol: 'Pays',
    bankCol: 'Banque centrale',
    currencyCol: 'Devise',
    regulationCol: 'Réglementation',
    domiciliationCol: 'Domiciliation',
    priorAuthCol: 'Autor. préalable',
    repatriationCol: 'Rapatriement',
    bankingActCol: 'Loi bancaire',
    contactCol: 'Contact',
    required: 'Obligatoire',
    conditional: 'Conditionnelle',
    free: 'Libre',
    notRequired: 'Non requis',
    memberCountries: 'Pays membres',
    focusAreas: 'Domaines',
    contact: 'Contact',
    // Converter
    converterTitle: 'Convertisseur de devises',
    amount: 'Montant',
    from: 'De',
    to: 'Vers',
    convert: 'Convertir',
    result: 'Résultat',
    rate: 'Taux',
    // Simulator
    simulatorTitle: 'Simulateur d\'instrument',
    txAmount: 'Montant transaction (USD)',
    txType: 'Type',
    txImport: 'Importation',
    txExport: 'Exportation',
    simulate: 'Recommander',
    recommendedFor: 'Instrument recommandé pour',
    // Regulations summary
    regSummary: 'Résumé par niveau',
    countries: 'pays',
  },
  en: {
    title: '🏦 African Banking System – AfCFTA',
    subtitle: 'Forex regulations, domiciliation and trade finance',
    selectCountry: 'Select a country',
    selectCountryPrompt: 'Select a country to display banking, regulatory and risk information.',
    banks: 'Banks',
    centralBank: 'Central Bank',
    commercialBanks: 'Commercial Banks',
    regionalBanks: 'Regional Banks',
    forex: 'Forex',
    domiciliationRequired: 'Domiciliation Required',
    domiciliationConditional: 'Conditional Domiciliation',
    domiciliationFree: 'Not Required',
    threshold: 'Threshold',
    allOperations: 'All operations',
    timeline: 'Repatriation deadline',
    days: 'days',
    regulation: 'Regulation',
    strict: 'Strict',
    moderate: 'Moderate',
    liberal: 'Liberal',
    risk: 'Country Risk',
    riskRating: 'Rating',
    forexRisk: 'Forex Risk',
    politicalRisk: 'Political Risk',
    transferRisk: 'Transfer Risk',
    alertLevel: 'Alert Level',
    riskScore: 'Score',
    maxExposure: 'Max recommended exposure',
    exposureWarning: '⚠ Amount exceeds recommended exposure',
    priorAuthRequired: '⚠ Prior authorization required',
    penalties: 'Penalties',
    instruments: 'Instruments',
    coverage: 'Coverage',
    paymentSystems: 'Payments',
    compliance: 'Compliance',
    amlFramework: 'AML Framework',
    kycRequired: 'KYC required',
    sanctionsScreening: 'Sanctions screening',
    reportingRequirements: 'Reporting requirements',
    fiuLabel: 'FIU',
    loading: 'Loading…',
    error: 'Loading error',
    noData: 'Data not available',
    documents: 'Required documents',
    currency: 'Currency',
    swiftCode: 'SWIFT Code',
    tradeFinance: 'Trade Finance',
    services: 'Services',
    yes: 'YES',
    no: 'NO',
    website: 'Website',
    mandatory_documents: 'Mandatory documents',
    notes: 'Notes',
    address: 'Address',
    phone: 'Phone',
    email: 'Email',
    established: 'Established',
    bankingAct: 'Banking Act',
    licenseType: 'License',
    correspondents: 'Correspondents',
    register: 'Register',
    regulations: 'Regulations',
    registerTitle: 'African Banks Register',
    registerSubtitle: 'Searchable directory – central, commercial and regional banks',
    searchPlaceholder: 'Search (name, code, country…)',
    filterType: 'Bank type',
    allTypes: 'All types',
    centralType: 'Central banks',
    commercialType: 'Commercial banks',
    regionalType: 'Regional banks',
    tradeFinanceOnly: 'Trade finance only',
    allCountries: 'All countries',
    resultCount: 'result(s)',
    regulationsTitle: 'Forex Regulations – Comparative View',
    regulationsSubtitle: 'Forex control summary for AfCFTA African countries',
    filterRegulation: 'Regulation level',
    allLevels: 'All levels',
    domiciliation: 'Domiciliation',
    priorAuth: 'Authorization',
    repatriation: 'Repatriation',
    countryCol: 'Country',
    bankCol: 'Central Bank',
    currencyCol: 'Currency',
    regulationCol: 'Regulation',
    domiciliationCol: 'Domiciliation',
    priorAuthCol: 'Prior auth.',
    repatriationCol: 'Repatriation',
    bankingActCol: 'Banking Act',
    contactCol: 'Contact',
    required: 'Required',
    conditional: 'Conditional',
    free: 'Free',
    notRequired: 'Not required',
    memberCountries: 'Member countries',
    focusAreas: 'Focus areas',
    contact: 'Contact',
    converterTitle: 'Currency Converter',
    amount: 'Amount',
    from: 'From',
    to: 'To',
    convert: 'Convert',
    result: 'Result',
    rate: 'Rate',
    simulatorTitle: 'Instrument Simulator',
    txAmount: 'Transaction Amount (USD)',
    txType: 'Type',
    txImport: 'Import',
    txExport: 'Export',
    simulate: 'Recommend',
    recommendedFor: 'Recommended instrument for',
    regSummary: 'Summary by level',
    countries: 'countries',
  },
};

// ── Small helpers ────────────────────────────────────────────────────────────

function AlertBadge({ level }) {
  const colorMap = {
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>
      {level?.toUpperCase()}
    </span>
  );
}

function RiskBadge({ level }) {
  const colorMap = {
    low: 'bg-green-100 text-green-800',
    moderate: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    very_high: 'bg-red-100 text-red-800',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>
      {level?.replace('_', ' ').toUpperCase()}
    </span>
  );
}

function RegulationBadge({ level }) {
  const colorMap = {
    strict: 'bg-red-100 text-red-800',
    moderate: 'bg-yellow-100 text-yellow-800',
    liberal: 'bg-green-100 text-green-800',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>
      {level?.toUpperCase()}
    </span>
  );
}

function ContactBlock({ contact, t }) {
  if (!contact) return null;
  return (
    <div className="mt-2 text-xs text-gray-600 space-y-0.5 border-t pt-2">
      {contact.address && <div className="flex gap-1"><span className="text-gray-400">📍</span>{contact.address}</div>}
      {contact.phone && (
        <div className="flex gap-1"><span className="text-gray-400">📞</span>
          <a href={`tel:${contact.phone}`} className="text-blue-600 hover:underline">{contact.phone}</a>
        </div>
      )}
      {contact.email && (
        <div className="flex gap-1"><span className="text-gray-400">✉</span>
          <a href={`mailto:${contact.email}`} className="text-blue-600 hover:underline">{contact.email}</a>
        </div>
      )}
      {contact.department && <div className="flex gap-1"><span className="text-gray-400">🏢</span><span className="italic">{contact.department}</span></div>}
    </div>
  );
}

// ── Quick Stats Bar (shown when a country is selected) ────────────────────────

function QuickStatsBar({ bankData, riskData, forexData, countryCode }) {
  const flag = COUNTRY_FLAGS[countryCode] || '🌍';
  const cb = bankData?.central_bank;
  const regLevel = cb?.forex_regulation || forexData?.forex_regulation?.regulation_level;
  const regColors = { strict: 'text-red-700 bg-red-50', moderate: 'text-yellow-700 bg-yellow-50', liberal: 'text-green-700 bg-green-50' };
  const alertColors = { green: 'text-green-700 bg-green-50', orange: 'text-orange-700 bg-orange-50', red: 'text-red-700 bg-red-50' };

  return (
    <div className="flex flex-wrap gap-2 px-3 py-2 bg-white border rounded-lg shadow-sm">
      {/* Flag + country */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-2xl">{flag}</span>
        <div className="min-w-0">
          <div className="font-semibold text-sm text-gray-900 truncate">{bankData?.country_name || forexData?.country_name || countryCode}</div>
          {cb?.name && <div className="text-xs text-gray-500 truncate">{cb.name}</div>}
        </div>
      </div>

      <div className="h-auto w-px bg-gray-200 self-stretch hidden sm:block" />

      {/* Currency */}
      {cb?.currency_code && (
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Devise</span>
          <span className="font-mono font-bold text-gray-800">{cb.currency_code}</span>
        </div>
      )}

      {/* Regulation */}
      {regLevel && (
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Réglementation</span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded mt-0.5 ${regColors[regLevel] || 'bg-gray-100 text-gray-700'}`}>
            {regLevel.toUpperCase()}
          </span>
        </div>
      )}

      {/* Risk rating */}
      {riskData?.overall_risk_rating && (
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Note risque</span>
          <span className="font-bold text-lg text-gray-800">{riskData.overall_risk_rating}</span>
        </div>
      )}

      {/* Alert level */}
      {riskData?.alert_level && (
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Alerte</span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded mt-0.5 ${alertColors[riskData.alert_level] || 'bg-gray-100 text-gray-700'}`}>
            {riskData.alert_level.toUpperCase()}
          </span>
        </div>
      )}

      {/* Domiciliation required */}
      {forexData?.domiciliation && (
        <div className="flex flex-col items-center justify-center px-2">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Domiciliation</span>
          <span className={`text-xs font-semibold mt-0.5 ${forexData.domiciliation.required ? 'text-red-600' : forexData.domiciliation.conditional ? 'text-yellow-600' : 'text-green-600'}`}>
            {forexData.domiciliation.required ? 'OBLIGATOIRE' : forexData.domiciliation.conditional ? 'CONDITIONNELLE' : 'LIBRE'}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Tab navigation ────────────────────────────────────────────────────────────

const COUNTRY_TABS = ['banks', 'forex', 'risk', 'instruments', 'paymentSystems', 'compliance'];
const GLOBAL_TABS = ['register', 'regulations'];
const ALL_TABS = [...COUNTRY_TABS, ...GLOBAL_TABS];

const TAB_ICONS = {
  banks: '🏛️',
  forex: '💱',
  risk: '⚠️',
  instruments: '📋',
  paymentSystems: '💳',
  compliance: '🔒',
  register: '📂',
  regulations: '📊',
};

function TabBar({ activeTab, onChange, t }) {
  return (
    <div className="flex gap-1 flex-wrap border-b mb-4">
      <div className="flex gap-1 flex-wrap">
        <span className="text-xs text-gray-400 self-center pr-1 border-r mr-1">Par pays</span>
        {COUNTRY_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => onChange(tab)}
            className={`px-3 py-1.5 text-sm font-medium rounded-t transition-colors flex items-center gap-1 ${
              activeTab === tab
                ? 'bg-white border-b-2 border-blue-600 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <span>{TAB_ICONS[tab]}</span>
            <span>{t[tab]}</span>
          </button>
        ))}
      </div>
      <div className="flex gap-1 flex-wrap ml-2">
        <span className="text-xs text-gray-400 self-center pr-1 border-r mr-1">Global</span>
        {GLOBAL_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => onChange(tab)}
            className={`px-3 py-1.5 text-sm font-medium rounded-t transition-colors flex items-center gap-1 ${
              activeTab === tab
                ? 'bg-white border-b-2 border-emerald-600 text-emerald-700'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <span>{TAB_ICONS[tab]}</span>
            <span>{t[tab]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Banks Tab ────────────────────────────────────────────────────────────────

function BanksTab({ data, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;
  const { central_bank, commercial_banks = [], regional_banks = [] } = data;

  return (
    <div className="space-y-4">
      {/* Central Bank */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.centralBank}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="font-semibold text-lg">{central_bank?.name}</div>
          <div className="grid grid-cols-2 gap-2 text-gray-600">
            <span>{t.currency}: <strong>{central_bank?.currency_code} – {central_bank?.currency_name}</strong></span>
            <span>{t.swiftCode}: <strong>{central_bank?.swift_code || '—'}</strong></span>
            <span>{t.regulation}: <RegulationBadge level={central_bank?.forex_regulation} /></span>
            {central_bank?.established_year && (
              <span>{t.established}: <strong>{central_bank.established_year}</strong></span>
            )}
          </div>
          {central_bank?.banking_act && (
            <p className="text-xs text-gray-500 italic">{t.bankingAct}: {central_bank.banking_act}</p>
          )}
          {central_bank?.website && (
            <a href={central_bank.website} target="_blank" rel="noreferrer" className="text-blue-600 text-xs underline">
              {central_bank.website}
            </a>
          )}
          {central_bank?.contact && <ContactBlock contact={central_bank.contact} t={t} />}
        </CardContent>
      </Card>

      {/* Commercial Banks */}
      {commercial_banks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.commercialBanks}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {commercial_banks.map((bank, i) => (
                <div key={i} className="border rounded p-3 text-sm hover:bg-gray-50">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                      <span className="font-semibold">{bank.name}</span>
                      {bank.abbreviation && <span className="ml-1 text-gray-500 text-xs">({bank.abbreviation})</span>}
                      {bank.license_type && <span className="ml-2 bg-gray-100 text-gray-600 text-xs px-1.5 py-0.5 rounded">{bank.license_type}</span>}
                    </div>
                    <div className="flex gap-1 items-center">
                      {bank.trade_finance && <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded font-medium">Trade Finance ✓</span>}
                      {bank.swift_code && <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{bank.swift_code}</span>}
                    </div>
                  </div>
                  {bank.services?.length > 0 && (
                    <div className="flex flex-wrap gap-0.5 mt-1.5">
                      {bank.services.map((s) => (
                        <span key={s} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">{s}</span>
                      ))}
                    </div>
                  )}
                  {bank.contact && <ContactBlock contact={bank.contact} t={t} />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Regional Banks */}
      {regional_banks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.regionalBanks}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {regional_banks.map((rb, i) => (
                <div key={i} className="border rounded p-3 text-sm bg-gray-50">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                      <span className="font-semibold">{rb.abbreviation}</span>
                      <span className="ml-2 text-gray-600 text-xs">{rb.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">{rb.headquarters}</span>
                  </div>
                  <div className="flex flex-wrap gap-0.5 mt-1">
                    {rb.focus_areas?.map((f) => (
                      <span key={f} className="bg-emerald-50 text-emerald-700 text-xs px-1.5 py-0.5 rounded">{f}</span>
                    ))}
                  </div>
                  {rb.contact && <ContactBlock contact={rb.contact} t={t} />}
                  {rb.website && !rb.contact && (
                    <a href={rb.website} target="_blank" rel="noreferrer" className="text-blue-500 underline text-xs mt-1 block">{rb.website}</a>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Forex Converter ────────────────────────────────────────────────────────────

const SOURCE_CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'AED', 'SAR', 'CHF', 'JPY'];

function ForexConverter({ countryCode, countryCurrencyCode, countryName, t }) {
  const [amount, setAmount] = useState('1000');
  const [fromCurrency, setFromCurrency] = useState('USD');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Reset when country changes
  useEffect(() => {
    setResult(null);
    setError(null);
  }, [countryCode]);

  const doConvert = async () => {
    const parsed = parseFloat(amount);
    if (!parsed || parsed <= 0 || !countryCode) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.get(`${API}/banking/forex/convert`, {
        params: {
          country_code: countryCode,
          from_currency: fromCurrency,
          amount: parsed,
        },
      });
      setResult(res.data);
    } catch (e) {
      const detail = e.response?.data?.detail;
      if (typeof detail === 'string' && detail.includes('indisponible')) {
        setError(`Taux non disponible pour ${countryCurrencyCode || 'cette devise'} (non cotée sur les marchés internationaux accessibles)`);
      } else {
        setError('Conversion indisponible pour cette paire de devises');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <span>💱</span> {t.converterTitle}
          {countryCurrencyCode && (
            <span className="text-xs font-normal text-gray-500 ml-1">→ {countryCurrencyCode}</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[100px]">
            <label className="text-xs text-gray-500 block mb-1">{t.amount}</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => { setAmount(e.target.value); setResult(null); }}
              onKeyDown={(e) => e.key === 'Enter' && doConvert()}
              className="border rounded px-3 py-1.5 text-sm bg-white w-full"
              min="0"
            />
          </div>
          <div className="min-w-[90px]">
            <label className="text-xs text-gray-500 block mb-1">{t.from}</label>
            <select
              value={fromCurrency}
              onChange={(e) => { setFromCurrency(e.target.value); setResult(null); }}
              className="border rounded px-2 py-1.5 text-sm bg-white w-full"
            >
              {SOURCE_CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="flex items-end pb-1.5 text-gray-400 text-sm">→</div>
          <div className="min-w-[90px] flex flex-col justify-end">
            <label className="text-xs text-gray-500 block mb-1">{t.to}</label>
            <div className="border rounded px-3 py-1.5 text-sm bg-gray-50 font-mono font-semibold text-gray-700">
              {countryCurrencyCode || '—'}
            </div>
          </div>
          <button
            onClick={doConvert}
            disabled={loading || !countryCode}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '…' : t.convert}
          </button>
        </div>

        {error && (
          <p className="text-xs text-orange-700 bg-orange-50 border border-orange-200 px-3 py-2 rounded">
            ⚠ {error}
          </p>
        )}

        {result && (
          <div className="bg-white border border-blue-200 rounded px-4 py-3 flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="text-xl font-bold text-blue-800">
                {result.converted_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}{' '}
                <span className="text-base font-normal">{result.to_currency}</span>
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                {parseFloat(amount).toLocaleString()} {fromCurrency} → {result.currency_name || result.to_currency}
              </div>
            </div>
            <div className="text-xs text-gray-500 text-right space-y-0.5">
              {result.rate_display && <div className="font-medium text-gray-700">{result.rate_display}</div>}
              {result.source && <div className="text-gray-400">Source : {result.source}</div>}
              {result.disclaimer && <div className="text-gray-400 max-w-[180px] italic">{result.disclaimer}</div>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Forex Tab ─────────────────────────────────────────────────────────────────

function ForexTab({ data, countryCode, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;
  const { domiciliation, forex_regulation } = data;
  const currencyCode = data.currency_code || data.central_bank?.currency_code;

  const domLabel = domiciliation?.required
    ? t.domiciliationRequired
    : domiciliation?.conditional
    ? t.domiciliationConditional
    : t.domiciliationFree;

  const domColor = domiciliation?.required
    ? 'bg-red-50 border-red-200'
    : domiciliation?.conditional
    ? 'bg-yellow-50 border-yellow-200'
    : 'bg-green-50 border-green-200';

  return (
    <div className="space-y-4">
      {/* Converter */}
      <ForexConverter countryCode={countryCode} countryCurrencyCode={currencyCode} countryName={data.country_name} t={t} />

      <Card className={`border-2 ${domColor}`}>
        <CardHeader>
          <CardTitle className="text-base">{domLabel}</CardTitle>
          <CardDescription>{data.country_name} – {data.central_bank_name}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {domiciliation?.threshold_usd != null && (
            <p><strong>{t.threshold} :</strong> {domiciliation.threshold_usd === 0 ? t.allOperations : `${domiciliation.threshold_usd.toLocaleString()} USD`}</p>
          )}
          {domiciliation?.timeline_days && (
            <p><strong>{t.timeline} :</strong> {domiciliation.timeline_days} {t.days}</p>
          )}
          {domiciliation?.mandatory_documents?.length > 0 && (
            <div>
              <strong>{t.mandatory_documents} :</strong>
              <ul className="list-disc ml-4 mt-1 text-xs text-gray-700">
                {domiciliation.mandatory_documents.map((d) => <li key={d}>{d.replace(/_/g, ' ')}</li>)}
              </ul>
            </div>
          )}
          {domiciliation?.notes && <p className="text-gray-600 text-xs italic">{domiciliation.notes}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.regulation}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <RegulationBadge level={forex_regulation?.regulation_level} />
            {forex_regulation?.prior_authorization_required && (
              <span className="text-xs text-red-600">{t.priorAuthRequired}</span>
            )}
          </div>
          {forex_regulation?.repatriation_deadline_days && (
            <p><strong>{t.timeline} :</strong> {forex_regulation.repatriation_deadline_days} {t.days}</p>
          )}
          {forex_regulation?.penalties && (
            <p className="text-xs text-red-700 bg-red-50 p-2 rounded"><strong>{t.penalties} :</strong> {forex_regulation.penalties}</p>
          )}
          {forex_regulation?.notes && <p className="text-gray-600 text-xs italic">{forex_regulation.notes}</p>}
          {data.authorized_currencies?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {data.authorized_currencies.map((c) => <Badge key={c} variant="outline" className="text-xs">{c}</Badge>)}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Risk Gauge ────────────────────────────────────────────────────────────────

function RiskGauge({ score, maxScore = 10 }) {
  const pct = Math.min(100, Math.round((score / maxScore) * 100));
  const color = score <= 3 ? '#22c55e' : score <= 5 ? '#eab308' : score <= 7 ? '#f97316' : '#ef4444';
  const trackColor = score <= 3 ? 'bg-green-100' : score <= 5 ? 'bg-yellow-100' : score <= 7 ? 'bg-orange-100' : 'bg-red-100';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Score risque</span>
        <span className="font-bold text-base" style={{ color }}>{score}/{maxScore}</span>
      </div>
      <div className={`h-3 rounded-full ${trackColor} overflow-hidden`}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-300">
        <span>Faible</span>
        <span>Élevé</span>
      </div>
    </div>
  );
}

// ── Risk Tab ──────────────────────────────────────────────────────────────────

function RiskTab({ data, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  const riskRows = [
    { label: t.forexRisk, value: data.forex_risk },
    { label: t.politicalRisk, value: data.political_risk },
    { label: t.transferRisk, value: data.transfer_risk },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.risk} – {data.country_name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {/* Rating + alert */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex flex-col items-center justify-center bg-gray-50 border rounded-lg px-6 py-3">
              <span className="text-xs text-gray-400 uppercase tracking-wide mb-1">Notation</span>
              <span className="font-bold text-3xl text-gray-800">{data.overall_risk_rating}</span>
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 text-xs">Alerte :</span>
                <AlertBadge level={data.alert_level} />
              </div>
              {data.credit_insurance_available !== undefined && (
                <div className="text-xs text-gray-600">
                  Assurance crédit : {data.credit_insurance_available
                    ? <span className="text-green-600 font-medium">Disponible ✓</span>
                    : <span className="text-red-600 font-medium">Non disponible</span>}
                </div>
              )}
            </div>
          </div>

          {/* Gauge */}
          {data.risk_score != null && (
            <div className="bg-gray-50 rounded-lg p-3">
              <RiskGauge score={data.risk_score} />
            </div>
          )}

          {/* Risk breakdown */}
          <div className="grid grid-cols-1 gap-2">
            {riskRows.map(({ label, value }) => value && (
              <div key={label} className="flex items-center justify-between py-1 border-b last:border-b-0">
                <span className="text-gray-600 text-xs">{label}</span>
                <RiskBadge level={value} />
              </div>
            ))}
          </div>

          {data.max_recommended_exposure_usd && (
            <div className="bg-blue-50 border border-blue-100 rounded p-2 text-xs text-blue-700">
              {t.maxExposure} : <strong>{data.max_recommended_exposure_usd.toLocaleString()} USD</strong>
            </div>
          )}
          {data.exposure_warning && (
            <p className="text-xs text-red-700 bg-red-50 p-2 rounded">{t.exposureWarning}</p>
          )}
          {data.recommended_instruments?.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">{t.instruments} :</p>
              <div className="flex flex-wrap gap-1">
                {data.recommended_instruments.map((code) => (
                  <span key={code} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">{code}</span>
                ))}
              </div>
            </div>
          )}
          {data.notes && <p className="text-gray-600 text-xs italic border-t pt-2">{data.notes}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Instrument Simulator ──────────────────────────────────────────────────────

function InstrumentSimulator({ countryCode, t }) {
  const [txAmount, setTxAmount] = useState('50000');
  const [txType, setTxType] = useState('import');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const simulate = async () => {
    if (!countryCode) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.get(`${API}/banking/trade-finance/recommend`, {
        params: { country_code: countryCode, amount: parseFloat(txAmount) || 50000, transaction_type: txType },
      });
      setResult(res.data);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-emerald-200 bg-emerald-50/20">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <span>🎯</span> {t.simulatorTitle}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[120px]">
            <label className="text-xs text-gray-500 block mb-1">{t.txAmount}</label>
            <input
              type="number"
              value={txAmount}
              onChange={(e) => setTxAmount(e.target.value)}
              className="border rounded px-3 py-1.5 text-sm bg-white w-full"
              min="0"
            />
          </div>
          <div className="min-w-[120px]">
            <label className="text-xs text-gray-500 block mb-1">{t.txType}</label>
            <select value={txType} onChange={(e) => setTxType(e.target.value)} className="border rounded px-3 py-1.5 text-sm bg-white w-full">
              <option value="import">{t.txImport}</option>
              <option value="export">{t.txExport}</option>
            </select>
          </div>
          <button
            onClick={simulate}
            disabled={loading || !countryCode}
            className="px-4 py-1.5 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '…' : t.simulate}
          </button>
        </div>

        {result?.recommended_instruments?.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-600">
              {t.recommendedFor} {parseFloat(txAmount).toLocaleString()} USD ({txType}) :
            </p>
            <div className="flex flex-wrap gap-1">
              {result.recommended_instruments.map((inst) => (
                <span key={typeof inst === 'string' ? inst : inst.code} className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded text-xs font-medium">
                  {typeof inst === 'string' ? inst : (inst.name_fr || inst.name)}
                </span>
              ))}
            </div>
            {result.notes && <p className="text-xs text-gray-500 italic">{result.notes}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Instruments Tab ───────────────────────────────────────────────────────────

function InstrumentsTab({ instruments, countryCode, t }) {
  if (!instruments?.length) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  return (
    <div className="space-y-4">
      {/* Simulator */}
      <InstrumentSimulator countryCode={countryCode} t={t} />

      <div className="space-y-3">
        {instruments.map((inst) => (
          <Card key={inst.code}>
            <CardHeader className="pb-1">
              <div className="flex items-center gap-2 flex-wrap">
                <CardTitle className="text-sm">{inst.name_fr}</CardTitle>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  inst.risk_coverage === 'full' ? 'bg-green-100 text-green-800'
                  : inst.risk_coverage === 'partial' ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-700'
                }`}>
                  {t.coverage} : {inst.risk_coverage}
                </span>
                {inst.typical_cost_pct != null && (
                  <span className="text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded border">~{inst.typical_cost_pct}%</span>
                )}
              </div>
            </CardHeader>
            <CardContent className="text-xs text-gray-600">{inst.description}</CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Payment Systems Tab ───────────────────────────────────────────────────────

const PAYMENT_TYPE_ICONS = { swift: '🌐', regional: '🏛️', mobile_money: '📱', digital: '💻' };
const PAYMENT_TYPE_LABELS = { swift: 'SWIFT', regional: 'Régional', mobile_money: 'Mobile Money', digital: 'Digital' };

function PaymentSystemsTab({ systems, t }) {
  if (!systems?.length) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  const grouped = systems.reduce((acc, ps) => {
    const key = ps.type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(ps);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([type, list]) => (
        <div key={type}>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            {PAYMENT_TYPE_ICONS[type]} {PAYMENT_TYPE_LABELS[type] || type}
          </h4>
          <div className="space-y-2">
            {list.map((ps) => (
              <Card key={ps.code} className="border shadow-sm">
                <CardContent className="pt-3 pb-2">
                  <div className="flex items-start gap-2 justify-between">
                    <div>
                      <div className="font-medium text-sm">{ps.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{ps.region}</div>
                      {ps.notes && <div className="text-xs text-gray-600 mt-1">{ps.notes}</div>}
                    </div>
                    {ps.currency && <Badge variant="outline" className="text-xs shrink-0">{ps.currency}</Badge>}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Compliance Tab ────────────────────────────────────────────────────────────

function ComplianceTab({ data, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  return (
    <div className="space-y-3 text-sm">
      <Card>
        <CardHeader><CardTitle className="text-base">{t.compliance}</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div>
            <span className="font-medium">{t.amlFramework} :</span> {data.aml_framework}
          </div>
          {data.kyc_requirements?.length > 0 && (
            <div>
              <span className="font-medium">{t.kycRequired} :</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.kyc_requirements.map((r) => (
                  <span key={r} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">{r.replace(/_/g, ' ')}</span>
                ))}
              </div>
            </div>
          )}
          {data.sanctions_screening && (
            <div><span className="font-medium">{t.sanctionsScreening} :</span> {data.sanctions_screening}</div>
          )}
          {data.reporting_requirements && (
            <div className="bg-yellow-50 p-2 rounded text-xs">
              <div className="font-medium mb-1">{t.reportingRequirements} :</div>
              {Object.entries(data.reporting_requirements).map(([k, v]) => (
                <div key={k}>{k.replace(/_/g, ' ')} : <strong>{typeof v === 'number' ? v.toLocaleString() : v}</strong></div>
              ))}
            </div>
          )}
          {data.compliance_contacts && (
            <div className="text-xs text-gray-600 space-y-0.5">
              {data.compliance_contacts.fiu && <div>{t.fiuLabel} : <strong>{data.compliance_contacts.fiu}</strong></div>}
              {data.compliance_contacts.website && (
                <a href={data.compliance_contacts.website} target="_blank" rel="noreferrer" className="text-blue-500 underline">{data.compliance_contacts.website}</a>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Register Tab ──────────────────────────────────────────────────────────────

const TYPE_COLORS = {
  central: 'bg-blue-100 text-blue-800',
  commercial: 'bg-purple-100 text-purple-800',
  regional: 'bg-emerald-100 text-emerald-800',
};

const TYPE_ICONS = { central: '🏛️', commercial: '🏦', regional: '🌍' };

function RegisterTab({ t, countries }) {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [tradeOnly, setTradeOnly] = useState(false);
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);

  const fetchRegister = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (filterType) params.set('bank_type', filterType);
      if (filterCountry) params.set('country_code', filterCountry);
      if (tradeOnly) params.set('trade_finance_only', 'true');
      const res = await axios.get(`${API}/banking/register?${params}`);
      setResults(res.data.results || []);
      setTotal(res.data.total || 0);
    } catch {
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [search, filterType, filterCountry, tradeOnly]);

  useEffect(() => {
    fetchRegister();
  }, [fetchRegister]);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold text-gray-800">{t.registerTitle}</h3>
        <p className="text-xs text-gray-500">{t.registerSubtitle}</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t.searchPlaceholder}
          className="border rounded px-3 py-1.5 text-sm bg-white min-w-48 flex-1"
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">{t.allTypes}</option>
          <option value="central">{t.centralType}</option>
          <option value="commercial">{t.commercialType}</option>
          <option value="regional">{t.regionalType}</option>
        </select>
        <select
          value={filterCountry}
          onChange={(e) => setFilterCountry(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">{t.allCountries}</option>
          {countries.map((c) => (
            <option key={c.country_code} value={c.country_code}>
              {c.country_name} ({c.country_code})
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={tradeOnly}
            onChange={(e) => setTradeOnly(e.target.checked)}
            className="accent-blue-600"
          />
          {t.tradeFinanceOnly}
        </label>
      </div>

      <p className="text-xs text-gray-500">{total} {t.resultCount}</p>

      {loading && <div className="text-center py-6 text-gray-400">{t.loading}</div>}

      {!loading && (
        <div className="space-y-2">
          {results.map((bank, i) => {
            const isOpen = expanded === i;
            return (
              <div
                key={i}
                className="border rounded-lg overflow-hidden hover:border-blue-300 transition-colors"
              >
                <button
                  className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
                  onClick={() => setExpanded(isOpen ? null : i)}
                >
                  <div className="flex items-center gap-2 flex-wrap min-w-0">
                    <span className="text-base">{TYPE_ICONS[bank.type]}</span>
                    <div className="min-w-0">
                      <span className="font-medium text-sm">{bank.name}</span>
                      {bank.abbreviation && (
                        <span className="ml-1.5 text-gray-500 text-xs">({bank.abbreviation})</span>
                      )}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${TYPE_COLORS[bank.type]}`}>
                      {bank.country_code ? `${COUNTRY_FLAGS[bank.country_code] || ''} ${bank.country_name} · ${bank.country_code}` : bank.country_name}
                    </span>
                    {bank.trade_finance && (
                      <span className="bg-green-50 text-green-700 text-xs px-1.5 py-0.5 rounded">Trade ✓</span>
                    )}
                  </div>
                  <span className="text-gray-400 text-sm shrink-0 ml-2">{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pt-1 bg-white border-t text-sm space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-xs">
                      {bank.swift_code && (
                        <div><span className="text-gray-500">{t.swiftCode}: </span><span className="font-mono">{bank.swift_code}</span></div>
                      )}
                      {bank.currency_code && (
                        <div><span className="text-gray-500">{t.currency}: </span><strong>{bank.currency_code} – {bank.currency_name}</strong></div>
                      )}
                      {bank.forex_regulation && (
                        <div><span className="text-gray-500">{t.regulation}: </span><RegulationBadge level={bank.forex_regulation} /></div>
                      )}
                      {bank.established_year && (
                        <div><span className="text-gray-500">{t.established}: </span>{bank.established_year}</div>
                      )}
                      {bank.license_type && (
                        <div><span className="text-gray-500">{t.licenseType}: </span>{bank.license_type}</div>
                      )}
                      {bank.banking_act && (
                        <div className="md:col-span-2"><span className="text-gray-500">{t.bankingAct}: </span><span className="italic">{bank.banking_act}</span></div>
                      )}
                    </div>

                    {bank.services?.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500 block mb-1">{t.services}:</span>
                        <div className="flex flex-wrap gap-1">
                          {bank.services.map((s) => (
                            <span key={s} className="bg-blue-50 text-blue-700 text-xs px-1.5 py-0.5 rounded">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {bank.correspondent_banks?.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500">{t.correspondents}: </span>
                        <span className="text-xs">{bank.correspondent_banks.join(' · ')}</span>
                      </div>
                    )}

                    {bank.member_countries?.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-500">{t.memberCountries}: </span>
                        <div className="flex flex-wrap gap-0.5 mt-0.5">
                          {bank.member_countries.map((c) => (
                            <span key={c} className="bg-gray-100 text-gray-600 text-xs px-1.5 py-0.5 rounded">{c}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {(bank.contact?.address || bank.contact?.phone || bank.contact?.email || bank.website) && (
                      <div className="border-t pt-2 space-y-0.5 text-xs text-gray-600">
                        <div className="font-medium text-gray-700 mb-1">{t.contact}</div>
                        {bank.contact?.address && (
                          <div className="flex gap-1"><span className="text-gray-400">📍</span>{bank.contact.address}</div>
                        )}
                        {bank.contact?.phone && (
                          <div className="flex gap-1"><span className="text-gray-400">📞</span>
                            <a href={`tel:${bank.contact.phone}`} className="text-blue-600 hover:underline">{bank.contact.phone}</a>
                          </div>
                        )}
                        {bank.contact?.email && (
                          <div className="flex gap-1"><span className="text-gray-400">✉</span>
                            <a href={`mailto:${bank.contact.email}`} className="text-blue-600 hover:underline">{bank.contact.email}</a>
                          </div>
                        )}
                        {bank.contact?.department && (
                          <div className="flex gap-1"><span className="text-gray-400">🏢</span><span className="italic">{bank.contact.department}</span></div>
                        )}
                        {bank.website && (
                          <div className="flex gap-1"><span className="text-gray-400">🌐</span>
                            <a href={bank.website} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{bank.website}</a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {results.length === 0 && !loading && (
            <p className="text-center text-gray-400 text-sm py-8">{t.noData}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Regulations Summary Bar ────────────────────────────────────────────────────

function RegSummaryBar({ data, t }) {
  if (!data.length) return null;
  const counts = data.reduce((acc, r) => {
    const k = r.regulation_level || 'unknown';
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});
  const total = data.length;
  const levels = [
    { key: 'strict', label: t.strict, color: 'bg-red-400', textColor: 'text-red-700' },
    { key: 'moderate', label: t.moderate, color: 'bg-yellow-400', textColor: 'text-yellow-700' },
    { key: 'liberal', label: t.liberal, color: 'bg-green-400', textColor: 'text-green-700' },
  ];

  return (
    <div className="bg-gray-50 border rounded-lg p-3 space-y-2">
      <p className="text-xs font-medium text-gray-600">{t.regSummary}</p>
      {/* Bar */}
      <div className="h-4 rounded-full overflow-hidden flex">
        {levels.map(({ key, color }) => {
          const pct = Math.round(((counts[key] || 0) / total) * 100);
          return pct > 0 ? (
            <div key={key} className={`${color} h-full`} style={{ width: `${pct}%` }} title={`${key}: ${counts[key] || 0}`} />
          ) : null;
        })}
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {levels.map(({ key, label, color, textColor }) => (
          <div key={key} className="flex items-center gap-1.5 text-xs">
            <span className={`inline-block w-3 h-3 rounded-sm ${color}`} />
            <span className={`font-medium ${textColor}`}>{label}</span>
            <span className="text-gray-500">{counts[key] || 0} {t.countries}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Regulations Tab ───────────────────────────────────────────────────────────

const REG_COLORS = { strict: 'bg-red-100 text-red-800', moderate: 'bg-yellow-100 text-yellow-800', liberal: 'bg-green-100 text-green-800' };
const DOM_COLORS = { required: 'text-red-700 font-medium', conditional: 'text-yellow-700', free: 'text-green-700' };

function RegulationsTab({ t }) {
  const [data, setData] = useState([]);
  const [filterLevel, setFilterLevel] = useState('');
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/banking/regulations/summary`)
      .then((r) => setData(r.data.results || []))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filterLevel ? data.filter((d) => d.regulation_level === filterLevel) : data;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold text-gray-800">{t.regulationsTitle}</h3>
        <p className="text-xs text-gray-500">{t.regulationsSubtitle}</p>
      </div>

      {/* Summary bar */}
      {data.length > 0 && <RegSummaryBar data={data} t={t} />}

      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">{t.allLevels}</option>
          <option value="strict">{t.strict}</option>
          <option value="moderate">{t.moderate}</option>
          <option value="liberal">{t.liberal}</option>
        </select>
        <span className="text-xs text-gray-400">{filtered.length} {t.resultCount}</span>
      </div>

      {loading && <div className="text-center py-6 text-gray-400">{t.loading}</div>}

      {!loading && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse min-w-[600px]">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2 py-1.5 text-left">{t.countryCol}</th>
                <th className="border px-2 py-1.5 text-left">{t.bankCol}</th>
                <th className="border px-2 py-1.5">{t.currencyCol}</th>
                <th className="border px-2 py-1.5">{t.regulationCol}</th>
                <th className="border px-2 py-1.5">{t.domiciliationCol}</th>
                <th className="border px-2 py-1.5">{t.priorAuthCol}</th>
                <th className="border px-2 py-1.5">{t.repatriationCol}</th>
                <th className="border px-2 py-1.5">{t.contactCol}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => {
                const isOpen = expanded === i;
                const domText = row.domiciliation_required
                  ? t.required
                  : row.domiciliation_conditional
                  ? t.conditional
                  : t.free;
                const domKey = row.domiciliation_required ? 'required' : row.domiciliation_conditional ? 'conditional' : 'free';
                const flag = COUNTRY_FLAGS[row.country_code] || '';

                return (
                  <React.Fragment key={i}>
                    <tr
                      className="hover:bg-blue-50 cursor-pointer"
                      onClick={() => setExpanded(isOpen ? null : i)}
                    >
                      <td className="border px-2 py-1.5 font-medium">
                        <span className="mr-1">{isOpen ? '▼' : '▶'}</span>
                        {flag && <span className="mr-1">{flag}</span>}
                        {row.country_name}
                        <span className="ml-1 text-gray-400">({row.country_code})</span>
                      </td>
                      <td className="border px-2 py-1.5 text-gray-600">{row.central_bank}</td>
                      <td className="border px-2 py-1.5 text-center font-mono">{row.currency_code}</td>
                      <td className="border px-2 py-1.5 text-center">
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${REG_COLORS[row.regulation_level] || 'bg-gray-100'}`}>
                          {row.regulation_level?.toUpperCase()}
                        </span>
                      </td>
                      <td className={`border px-2 py-1.5 text-center ${DOM_COLORS[domKey]}`}>{domText}</td>
                      <td className="border px-2 py-1.5 text-center">
                        {row.prior_authorization
                          ? <span className="text-red-600 font-medium">{t.yes}</span>
                          : <span className="text-green-600">{t.no}</span>}
                      </td>
                      <td className="border px-2 py-1.5 text-center text-gray-600">
                        {row.repatriation_days ? `${row.repatriation_days}j` : '—'}
                      </td>
                      <td className="border px-2 py-1.5 text-center">
                        {(row.central_bank_phone || row.central_bank_email) ? (
                          <span className="text-blue-600">📋</span>
                        ) : '—'}
                      </td>
                    </tr>
                    {isOpen && (
                      <tr className="bg-blue-50">
                        <td colSpan={8} className="border px-4 py-3">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 text-xs">
                            <div className="space-y-1">
                              {row.threshold_usd != null && (
                                <div><span className="text-gray-500">{t.threshold}: </span>
                                  <strong>{row.threshold_usd === 0 ? t.allOperations : `${row.threshold_usd.toLocaleString()} USD`}</strong>
                                </div>
                              )}
                              {row.authorization_threshold_usd && (
                                <div><span className="text-gray-500">Seuil autorisation: </span>
                                  <strong>{row.authorization_threshold_usd.toLocaleString()} USD</strong>
                                </div>
                              )}
                              {row.declaration_threshold_usd && (
                                <div><span className="text-gray-500">Seuil déclaration: </span>
                                  <strong>{row.declaration_threshold_usd.toLocaleString()} USD</strong>
                                </div>
                              )}
                              {row.penalties && (
                                <div className="text-red-700 bg-red-50 p-1.5 rounded">
                                  <span className="font-medium">{t.penalties}: </span>{row.penalties}
                                </div>
                              )}
                              {row.banking_act && (
                                <div><span className="text-gray-500">{t.bankingAct}: </span><span className="italic">{row.banking_act}</span></div>
                              )}
                            </div>
                            <div className="space-y-1">
                              {row.central_bank_phone && (
                                <div className="flex gap-1"><span className="text-gray-400">📞</span>
                                  <a href={`tel:${row.central_bank_phone}`} className="text-blue-600 hover:underline">{row.central_bank_phone}</a>
                                </div>
                              )}
                              {row.central_bank_email && (
                                <div className="flex gap-1"><span className="text-gray-400">✉</span>
                                  <a href={`mailto:${row.central_bank_email}`} className="text-blue-600 hover:underline">{row.central_bank_email}</a>
                                </div>
                              )}
                              {row.central_bank_website && (
                                <div className="flex gap-1"><span className="text-gray-400">🌐</span>
                                  <a href={row.central_bank_website} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{row.central_bank_website}</a>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="border px-4 py-6 text-center text-gray-400">{t.noData}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function BankingInfoPanel({ language = 'fr', selectedCountry: propCountry }) {
  const t = texts[language] || texts.fr;

  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState(propCountry || '');
  const [activeTab, setActiveTab] = useState('banks');

  const [bankData, setBankData] = useState(null);
  const [forexData, setForexData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [instruments, setInstruments] = useState([]);
  const [paymentSystems, setPaymentSystems] = useState([]);
  const [complianceData, setComplianceData] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isGlobalTab = GLOBAL_TABS.includes(activeTab);

  // Load country list + instruments once
  useEffect(() => {
    axios.get(`${API}/banking/countries`)
      .then((r) => setCountries(r.data || []))
      .catch(() => setCountries([]));

    axios.get(`${API}/banking/trade-finance/instruments`)
      .then((r) => setInstruments(r.data || []))
      .catch(() => setInstruments([]));
  }, []);

  // Load country-specific data
  const loadCountryData = useCallback(async (code) => {
    if (!code) return;
    setLoading(true);
    setError(null);
    try {
      const [banks, forex, risk, payments, compliance] = await Promise.allSettled([
        axios.get(`${API}/banking/countries/${code}/banks`),
        axios.get(`${API}/banking/countries/${code}/regulations`),
        axios.get(`${API}/banking/countries/${code}/risk-assessment`),
        axios.get(`${API}/banking/payment-systems?country_code=${code}`),
        axios.get(`${API}/banking/compliance/${code}`),
      ]);

      setBankData(banks.status === 'fulfilled' ? banks.value.data : null);
      setForexData(forex.status === 'fulfilled' ? forex.value.data : null);
      setRiskData(risk.status === 'fulfilled' ? risk.value.data : null);
      setPaymentSystems(payments.status === 'fulfilled' ? payments.value.data : []);
      setComplianceData(compliance.status === 'fulfilled' ? compliance.value.data : null);
    } catch (e) {
      setError(t.error);
    } finally {
      setLoading(false);
    }
  }, [t.error]);

  useEffect(() => {
    if (selectedCountry) loadCountryData(selectedCountry);
  }, [selectedCountry, loadCountryData]);

  const handleCountryChange = (e) => {
    setSelectedCountry(e.target.value);
    if (GLOBAL_TABS.includes(activeTab)) return;
    setActiveTab('banks');
  };

  return (
    <div className="p-4 space-y-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{t.title}</h2>
          <p className="text-sm text-gray-500 mt-1">{t.subtitle}</p>
        </div>
        <select
          value={selectedCountry}
          onChange={handleCountryChange}
          className="border rounded px-3 py-1.5 text-sm bg-white min-w-48"
        >
          <option value="">{t.selectCountry}</option>
          {countries.map((c) => (
            <option key={c.country_code} value={c.country_code}>
              {COUNTRY_FLAGS[c.country_code] || ''} {c.country_name} ({c.country_code})
            </option>
          ))}
        </select>
      </div>

      {/* Quick stats banner — shown when country selected */}
      {selectedCountry && !loading && (bankData || riskData || forexData) && (
        <QuickStatsBar
          bankData={bankData}
          riskData={riskData}
          forexData={forexData}
          countryCode={selectedCountry}
        />
      )}

      {/* Tab bar - always visible */}
      <TabBar activeTab={activeTab} onChange={setActiveTab} t={t} />

      {/* Global tabs - no country needed */}
      {activeTab === 'register' && <RegisterTab t={t} countries={countries} />}
      {activeTab === 'regulations' && <RegulationsTab t={t} />}

      {/* Country-specific tabs */}
      {!isGlobalTab && (
        <>
          {!selectedCountry && (
            <div className="bg-blue-50 border border-blue-200 rounded p-4 text-sm text-blue-700">
              {t.selectCountryPrompt}
            </div>
          )}

          {loading && (
            <div className="text-center py-8 text-gray-500">{t.loading}</div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
          )}

          {selectedCountry && !loading && (
            <>
              {activeTab === 'banks' && <BanksTab data={bankData} t={t} />}
              {activeTab === 'forex' && <ForexTab data={forexData} countryCode={selectedCountry} t={t} />}
              {activeTab === 'risk' && <RiskTab data={riskData} t={t} />}
              {activeTab === 'instruments' && (
                <InstrumentsTab instruments={instruments} countryCode={selectedCountry} t={t} />
              )}
              {activeTab === 'paymentSystems' && <PaymentSystemsTab systems={paymentSystems} t={t} />}
              {activeTab === 'compliance' && <ComplianceTab data={complianceData} t={t} />}
            </>
          )}
        </>
      )}
    </div>
  );
}
