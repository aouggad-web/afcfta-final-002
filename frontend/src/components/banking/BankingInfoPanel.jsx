import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

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
    forex: 'Change & Domiciliation',
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
    instruments: 'Instruments Recommandés',
    coverage: 'Couverture',
    paymentSystems: 'Systèmes de Paiement',
    compliance: 'Conformité (KYC/AML)',
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
    forex: 'Forex & Domiciliation',
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
    instruments: 'Recommended Instruments',
    coverage: 'Coverage',
    paymentSystems: 'Payment Systems',
    compliance: 'Compliance (KYC/AML)',
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
  },
};

// ── Small helpers ────────────────────────────────────────────────────────────

function AlertBadge({ level }) {
  const colorMap = { green: 'bg-green-100 text-green-800', orange: 'bg-orange-100 text-orange-800', red: 'bg-red-100 text-red-800' };
  return <span className={`px-2 py-1 rounded text-xs font-semibold ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>{level?.toUpperCase()}</span>;
}

function RiskBadge({ level }) {
  const colorMap = { low: 'bg-green-100 text-green-800', moderate: 'bg-yellow-100 text-yellow-800', high: 'bg-orange-100 text-orange-800', very_high: 'bg-red-100 text-red-800' };
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>{level?.replace('_', ' ').toUpperCase()}</span>;
}

function RegulationBadge({ level }) {
  const colorMap = { strict: 'bg-red-100 text-red-800', moderate: 'bg-yellow-100 text-yellow-800', liberal: 'bg-green-100 text-green-800' };
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorMap[level] || 'bg-gray-100 text-gray-700'}`}>{level?.toUpperCase()}</span>;
}

// ── Tab navigation ────────────────────────────────────────────────────────────

const TABS = ['banks', 'forex', 'risk', 'instruments', 'paymentSystems', 'compliance'];

function TabBar({ activeTab, onChange, t }) {
  return (
    <div className="flex gap-1 flex-wrap border-b mb-4">
      {TABS.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={`px-3 py-1.5 text-sm font-medium rounded-t transition-colors ${
            activeTab === tab
              ? 'bg-white border-b-2 border-blue-600 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {t[tab]}
        </button>
      ))}
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
          </div>
          {central_bank?.website && (
            <a href={central_bank.website} target="_blank" rel="noreferrer" className="text-blue-600 text-xs underline">
              {central_bank.website}
            </a>
          )}
        </CardContent>
      </Card>

      {/* Commercial Banks */}
      {commercial_banks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.commercialBanks}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border px-2 py-1 text-left">Nom</th>
                    <th className="border px-2 py-1">{t.swiftCode}</th>
                    <th className="border px-2 py-1">{t.tradeFinance}</th>
                    <th className="border px-2 py-1 text-left">{t.services}</th>
                  </tr>
                </thead>
                <tbody>
                  {commercial_banks.map((bank, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="border px-2 py-1 font-medium">{bank.name}</td>
                      <td className="border px-2 py-1 text-center font-mono">{bank.swift_code || '—'}</td>
                      <td className="border px-2 py-1 text-center">
                        {bank.trade_finance ? <span className="text-green-700 font-bold">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
                      <td className="border px-2 py-1">
                        <div className="flex flex-wrap gap-0.5">
                          {bank.services?.slice(0, 3).map((s) => (
                            <span key={s} className="bg-blue-50 text-blue-700 px-1 rounded text-xs">{s}</span>
                          ))}
                          {bank.services?.length > 3 && <span className="text-gray-400 text-xs">+{bank.services.length - 3}</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
            <div className="flex flex-wrap gap-2">
              {regional_banks.map((rb, i) => (
                <div key={i} className="border rounded p-2 text-xs bg-gray-50 min-w-40">
                  <div className="font-semibold">{rb.abbreviation}</div>
                  <div className="text-gray-600 text-xs">{rb.headquarters}</div>
                  {rb.website && <a href={rb.website} target="_blank" rel="noreferrer" className="text-blue-500 underline text-xs">{t.website}</a>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Forex Tab ─────────────────────────────────────────────────────────────────

function ForexTab({ data, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;
  const { domiciliation, forex_regulation } = data;

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

// ── Risk Tab ──────────────────────────────────────────────────────────────────

function RiskTab({ data, t }) {
  if (!data) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t.risk} – {data.country_name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-2xl">{data.overall_risk_rating}</span>
          <AlertBadge level={data.alert_level} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div><span className="text-gray-500">{t.forexRisk} :</span> <RiskBadge level={data.forex_risk} /></div>
          <div><span className="text-gray-500">{t.politicalRisk} :</span> <RiskBadge level={data.political_risk} /></div>
          <div><span className="text-gray-500">{t.transferRisk} :</span> <RiskBadge level={data.transfer_risk} /></div>
          <div><span className="text-gray-500">{t.riskScore} :</span> <strong>{data.risk_score}/10</strong></div>
        </div>
        {data.max_recommended_exposure_usd && (
          <p className="text-xs text-gray-600">
            {t.maxExposure} : <strong>{data.max_recommended_exposure_usd.toLocaleString()} USD</strong>
          </p>
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
        {data.notes && <p className="text-gray-600 text-xs italic">{data.notes}</p>}
      </CardContent>
    </Card>
  );
}

// ── Instruments Tab ───────────────────────────────────────────────────────────

function InstrumentsTab({ instruments, t }) {
  if (!instruments?.length) return <p className="text-gray-500 text-sm">{t.noData}</p>;

  return (
    <div className="space-y-3">
      {instruments.map((inst) => (
        <Card key={inst.code}>
          <CardHeader className="pb-1">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle className="text-sm">{inst.name_fr}</CardTitle>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${inst.risk_coverage === 'full' ? 'bg-green-100 text-green-800' : inst.risk_coverage === 'partial' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-700'}`}>
                {t.coverage} : {inst.risk_coverage}
              </span>
              {inst.typical_cost_pct != null && (
                <span className="text-xs text-gray-500">~{inst.typical_cost_pct}%</span>
              )}
            </div>
          </CardHeader>
          <CardContent className="text-xs text-gray-600">{inst.description}</CardContent>
        </Card>
      ))}
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

  // Load country list once
  useEffect(() => {
    axios.get(`${API}/banking/countries`)
      .then((r) => setCountries(r.data || []))
      .catch(() => setCountries([]));

    // Load instruments (independent of country)
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
    setActiveTab('banks');
  };

  return (
    <div className="p-4 space-y-4 max-w-4xl mx-auto">
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
              {c.country_name} ({c.country_code})
            </option>
          ))}
        </select>
      </div>

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
          <TabBar activeTab={activeTab} onChange={setActiveTab} t={t} />

          {activeTab === 'banks' && <BanksTab data={bankData} t={t} />}
          {activeTab === 'forex' && <ForexTab data={forexData} t={t} />}
          {activeTab === 'risk' && <RiskTab data={riskData} t={t} />}
          {activeTab === 'instruments' && <InstrumentsTab instruments={instruments} t={t} />}
          {activeTab === 'paymentSystems' && <PaymentSystemsTab systems={paymentSystems} t={t} />}
          {activeTab === 'compliance' && <ComplianceTab data={complianceData} t={t} />}
        </>
      )}
    </div>
  );
}
