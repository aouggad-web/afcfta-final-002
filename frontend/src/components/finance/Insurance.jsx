import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { montant } from '../../utils/nombres';
import { pick } from '../../i18n/lang';
import { trDonnee } from '../../i18n/donnees';
import { trierPays } from '../../utils/triPays';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const PRODUCT_TYPES = [
  { value: 'export_credit', fr: 'Crédit export', en: 'Export credit', ar: 'ائتمان الصادرات' },
  { value: 'political_risk', fr: 'Risque politique', en: 'Political risk', ar: 'المخاطر السياسية' },
  { value: 'performance_guarantee', fr: 'Garantie de performance', en: 'Performance guarantee', ar: 'ضمان حسن التنفيذ' },
  { value: 'advance_payment', fr: 'Garantie de restitution', en: 'Advance payment', ar: 'ضمان استرداد الدفعة المقدمة' },
  { value: 'tender', fr: "Garantie d'appel d'offres", en: 'Tender guarantee', ar: 'ضمان المناقصة' },
  { value: 'transport', fr: 'Assurance transport', en: 'Transport insurance', ar: 'تأمين النقل' },
];

// Niveaux de risque renvoyés par l'API (codes anglais) → arabe.
const RISK_LEVEL_AR = {
  very_low: 'منخفض جدًا',
  low: 'منخفض',
  moderate: 'متوسط',
  high: 'مرتفع',
  very_high: 'مرتفع جدًا',
};

const texts = {
  fr: {
    title: '🛡️ Assurance Commerce Extérieur',
    subtitle: 'Estimation indicative des primes et assureurs à contacter',
    countryLabel: 'Pays acheteur',
    amountLabel: 'Valeur du contrat (USD)',
    productLabel: 'Produit',
    sectorLabel: 'Secteur (optionnel)',
    submit: 'Estimer la prime',
    submitBatch: 'Comparer tous les produits',
    loading: 'Calcul en cours…',
    error: 'Erreur',
    profile: 'Profil pays',
    riskLevel: 'Niveau de risque',
    insurers: 'Assureurs à contacter',
    products: 'Produits disponibles',
    quote: 'Estimation indicative de prime',
    basePremium: 'Prime de base',
    finalPremium: 'Prime finale',
    coverage: 'Couverture',
    deductible: 'Franchise',
    adjustment: 'Ajustement risque',
    notes: 'Notes',
    comparison: 'Comparaison des produits (estimations)',
    avertissement:
      "Estimation calculée par la plateforme à partir du risque du pays acheteur. Seul un assureur établit un devis : contactez-le avec les coordonnées ci-dessous.",
    siteWeb: 'Site web',
    roles: {
      eca: "Agence publique d'assurance-crédit à l'export",
      assureur_credit: 'Assureur-crédit',
      multilateral: 'Assureur multilatéral (risque politique et crédit)',
      assureur_general: 'Assureur',
    },
    souscriptionPays: 'Pour les entreprises établies : {pays}',
    souscriptionMembres: 'Opérations liées à ses États membres (liste sur son site)',
    souscriptionOuverte: 'Entreprises de tous pays, par ses implantations',
    country: 'Pays',
    noProfile: 'Aucun profil assurance disponible pour ce pays.',
  },
  en: {
    title: '🛡️ Trade Insurance',
    subtitle: 'Indicative premium estimates and insurers to contact',
    countryLabel: 'Buyer country',
    amountLabel: 'Contract value (USD)',
    productLabel: 'Product',
    sectorLabel: 'Sector (optional)',
    submit: 'Estimate the premium',
    submitBatch: 'Compare all products',
    loading: 'Calculating…',
    error: 'Error',
    profile: 'Country profile',
    riskLevel: 'Risk level',
    insurers: 'Insurers to contact',
    products: 'Available products',
    quote: 'Indicative premium estimate',
    basePremium: 'Base premium',
    finalPremium: 'Final premium',
    coverage: 'Coverage',
    deductible: 'Deductible',
    adjustment: 'Risk adjustment',
    notes: 'Notes',
    comparison: 'Product comparison (estimates)',
    avertissement:
      'Estimate computed by the platform from the buyer country risk. Only an insurer issues a quote: contact one with the details below.',
    siteWeb: 'Website',
    roles: {
      eca: 'Public export credit insurer',
      assureur_credit: 'Credit insurer',
      multilateral: 'Multilateral insurer (political and credit risk)',
      assureur_general: 'Insurer',
    },
    souscriptionPays: 'For companies based in: {pays}',
    souscriptionMembres: 'Transactions involving its member states (list on its website)',
    souscriptionOuverte: 'Companies from any country, through its local offices',
    country: 'Country',
    noProfile: 'No insurance profile available for this country.',
  },
  ar: {
    title: '🛡️ تأمين التجارة الخارجية',
    subtitle: 'تقدير إرشادي للأقساط وشركات التأمين للاتصال بها',
    countryLabel: 'بلد المشتري',
    amountLabel: 'قيمة العقد (USD)',
    productLabel: 'المنتج',
    sectorLabel: 'القطاع (اختياري)',
    submit: 'تقدير القسط',
    submitBatch: 'مقارنة جميع المنتجات',
    loading: 'جارٍ الحساب…',
    error: 'خطأ',
    profile: 'ملف البلد',
    riskLevel: 'مستوى المخاطر',
    insurers: 'شركات التأمين للاتصال بها',
    products: 'المنتجات المتاحة',
    quote: 'تقدير إرشادي للقسط',
    basePremium: 'القسط الأساسي',
    finalPremium: 'القسط النهائي',
    coverage: 'التغطية',
    deductible: 'مبلغ التحمل',
    adjustment: 'تعديل المخاطر',
    notes: 'ملاحظات',
    comparison: 'مقارنة المنتجات (تقديرات)',
    avertissement:
      'تقدير تحسبه المنصة انطلاقاً من مخاطر بلد المشتري. وحدها شركة التأمين تُصدر عرض سعر: تواصلوا معها عبر البيانات أدناه.',
    siteWeb: 'الموقع الإلكتروني',
    roles: {
      eca: 'هيئة عمومية لتأمين ائتمان الصادرات',
      assureur_credit: 'شركة تأمين الائتمان',
      multilateral: 'مؤسسة تأمين متعددة الأطراف (المخاطر السياسية والائتمانية)',
      assureur_general: 'شركة تأمين',
    },
    souscriptionPays: 'للشركات المقيمة في: {pays}',
    souscriptionMembres: 'العمليات المرتبطة بدوله الأعضاء (القائمة على موقعه)',
    souscriptionOuverte: 'الشركات من جميع البلدان، عبر فروعه',
    country: 'البلد',
    noProfile: 'لا يتوفر ملف تأمين لهذا البلد.',
  },
};

export default function Insurance({ language = 'en' }) {
  const t = texts[language] || texts.en;
  // Qui peut souscrire auprès de l'assureur (registre : souscription, souscripteurs).
  const nomPays = (code) => {
    try {
      return new Intl.DisplayNames([language], { type: 'region' }).of(code) || code;
    } catch (e) {
      return code;
    }
  };
  const souscription = (ins) => {
    if (ins.souscription === 'pays' && ins.souscripteurs?.length) {
      return t.souscriptionPays.replace('{pays}', ins.souscripteurs.map(nomPays).join(', '));
    }
    if (ins.souscription === 'etats_membres') return t.souscriptionMembres;
    if (ins.souscription === 'ouvert') return t.souscriptionOuverte;
    return null;
  };
  // Lien externe : http(s) seulement.
  const lienSur = (url) => typeof url === 'string' && /^https?:\/\//i.test(url);
  // « 12 345 $ » en français, « $12,345 » en anglais.
  const usd = (v) => (v == null ? '—' : montant(v, language, 3));
  const [countryCode, setCountryCode] = useState('DZ');
  const [amount, setAmount] = useState(500000);
  const [productType, setProductType] = useState('export_credit');
  const [sector, setSector] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profileNotFound, setProfileNotFound] = useState(false);
  const [quote, setQuote] = useState(null);
  const [batch, setBatch] = useState(null);
  const [countries, setCountries] = useState([]);

  useEffect(() => {
    let cancelled = false;
    axios
      .get(`${API}/insurance/countries`)
      .then((res) => {
        if (!cancelled && res.data.success) {
          setCountries(res.data.countries);
        }
      })
      .catch(() => {
        // selector falls back to the default DZ value if the list can't load
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const invalidAmountMessage = {
    fr: 'Veuillez saisir un montant valide supérieur à 0.',
    en: 'Please enter a valid amount greater than 0.',
    ar: 'يرجى إدخال مبلغ صالح أكبر من 0.',
  };

  const parseAmount = () => {
    const value = parseFloat(amount);
    if (!Number.isFinite(value) || value <= 0) {
      return null;
    }
    return value;
  };

  const fetchProfile = async (code) => {
    try {
      const res = await axios.get(`${API}/insurance/countries/${code.toUpperCase()}/profile`);
      if (res.data.success) {
        setProfile(res.data.profile);
        setProfileNotFound(false);
      } else {
        setProfile(null);
        setProfileNotFound(true);
      }
    } catch (err) {
      // profile is best-effort context; quote errors surface separately
      setProfile(null);
      setProfileNotFound(err.response?.status === 404);
    }
  };

  const handleQuote = async (e) => {
    e.preventDefault();
    setError(null);
    setQuote(null);
    setBatch(null);

    const value = parseAmount();
    if (value === null) {
      setError(invalidAmountMessage[language] || invalidAmountMessage.en);
      return;
    }

    setLoading(true);
    try {
      await fetchProfile(countryCode);
      const res = await axios.post(`${API}/insurance/quote`, {
        country_code: countryCode.toUpperCase(),
        product_type: productType,
        contract_value_usd: value,
        sector: sector || null,
      });
      if (res.data.success) {
        setQuote(res.data.quote);
      } else {
        setError(res.data.detail || t.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBatch = async () => {
    setError(null);
    setQuote(null);
    setBatch(null);

    const value = parseAmount();
    if (value === null) {
      setError(invalidAmountMessage[language] || invalidAmountMessage.en);
      return;
    }

    setLoading(true);
    try {
      await fetchProfile(countryCode);
      const res = await axios.post(`${API}/insurance/quotes/batch`, {
        country_code: countryCode.toUpperCase(),
        contract_value_usd: value,
      });
      if (res.data.success) {
        setBatch(res.data.quotes);
      } else {
        setError(res.data.detail || t.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{t.title}</CardTitle>
          <p className="text-sm text-[var(--afcfta-muted)]">{t.subtitle}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleQuote} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">{t.countryLabel}</label>
                {countries.length > 0 ? (
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className="w-full px-3 py-2 border rounded"
                  >
                    {trierPays(countries, (c) => trDonnee(c.country_name, language), language).map((c) => (
                      <option key={c.country_code} value={c.country_code}>
                        {trDonnee(c.country_name, language)} ({c.country_code})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    maxLength="2"
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 border rounded"
                    placeholder="DZ"
                  />
                )}
              </div>
              <div>
                <label className="block text-sm font-medium">{t.amountLabel}</label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">{t.productLabel}</label>
                <select
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                >
                  {PRODUCT_TYPES.map((p) => (
                    <option key={p.value} value={p.value}>
                      {pick(language, p.fr, p.en, p.ar)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium">{t.sectorLabel}</label>
                <input
                  type="text"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="manufacturing…"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? t.loading : t.submit}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={loading}
                onClick={handleBatch}
                className="flex-1"
              >
                {t.submitBatch}
              </Button>
            </div>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--danger)_30%,transparent)] rounded">
              <p className="text-[var(--danger)]">
                {t.error}: {error}
              </p>
            </div>
          )}

          {profile && (
            <Card className="mt-6 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {t.profile}
                  <Badge variant="outline">
                    {profile.country_code} — {trDonnee(profile.country_name, language)}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>{t.riskLevel}:</span>
                  <Badge className="capitalize">{pick(language, profile.risk_level, profile.risk_level, RISK_LEVEL_AR[profile.risk_level] || profile.risk_level)}</Badge>
                </div>
                <div>
                  {t.insurers}: {profile.available_insurers?.length || 0}
                </div>
                <div>
                  {t.products}: {profile.available_products?.length || 0}
                </div>
                {profile.available_insurers?.length > 0 && (
                  <ul className="mt-2 space-y-3" data-testid="assureurs">
                    {profile.available_insurers.map((ins) => (
                      <li key={ins.abbreviation || ins.name} className="text-xs text-[var(--text)]">
                        <div className="font-semibold">
                          {ins.name}
                          {ins.abbreviation ? ` (${ins.abbreviation})` : ''}
                        </div>
                        {t.roles[ins.role] && (
                          <div className="text-[var(--afcfta-muted)]">{t.roles[ins.role]}</div>
                        )}
                        {souscription(ins) && <div className="italic">{souscription(ins)}</div>}
                        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-0.5">
                          {lienSur(ins.website) && (
                            <a href={ins.website} target="_blank" rel="noopener noreferrer" className="underline">
                              {t.siteWeb}
                            </a>
                          )}
                          {ins.email && (
                            <a href={`mailto:${ins.email}`} className="underline" dir="ltr">
                              {ins.email}
                            </a>
                          )}
                          {ins.phone && (
                            <a href={`tel:${ins.phone.replace(/[^+\d]/g, '')}`} dir="ltr">
                              {ins.phone}
                            </a>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          )}

          {!profile && profileNotFound && !error && (
            <div className="mt-6 p-3 bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded text-sm text-[var(--gold)]">
              {t.country} {countryCode.toUpperCase()}: {t.noProfile}
            </div>
          )}

          {quote && (
            <Card className="mt-4 bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
              <CardHeader>
                <CardTitle className="text-base">{t.quote}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="text-xs italic text-[var(--afcfta-muted)]">{t.avertissement}</p>
                <div className="flex justify-between">
                  <span>{t.basePremium}:</span>
                  <strong>{usd(quote.base_premium_usd)}</strong>
                </div>
                <div className="flex justify-between">
                  <span>{t.finalPremium}:</span>
                  <strong>{usd(quote.final_premium_usd)}</strong>
                </div>
                <div className="flex justify-between">
                  <span>{t.coverage}:</span>
                  <span>{usd(quote.coverage_usd)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t.deductible}:</span>
                  <span>{usd(quote.deductible_usd)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t.adjustment}:</span>
                  <span>{quote.risk_adjustment_percent}%</span>
                </div>
                {quote.notes && (
                  <p className="text-xs text-[var(--afcfta-muted)] mt-2 italic">{quote.notes}</p>
                )}
              </CardContent>
            </Card>
          )}

          {batch && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-base">{t.comparison}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-xs italic text-[var(--afcfta-muted)]">{t.avertissement}</p>
                {Object.entries(batch)
                  .sort((a, b) => a[1].final_premium_usd - b[1].final_premium_usd)
                  .map(([type, q], i) => (
                    <div
                      key={type}
                      className={`p-2 rounded text-sm ${i === 0 ? 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]' : 'bg-[var(--afcfta-card2)]'}`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium capitalize">
                          {pick(
                            language,
                            type.replace('_', ' '),
                            type.replace('_', ' '),
                            PRODUCT_TYPES.find((p) => p.value === type)?.ar || type.replace('_', ' ')
                          )}
                        </span>
                        <Badge variant={i === 0 ? 'default' : 'outline'}>
                          {usd(q.final_premium_usd)}
                        </Badge>
                      </div>
                      <div className="text-xs text-[var(--afcfta-muted)] mt-1">
                        {t.coverage}: {usd(q.coverage_usd)}
                      </div>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
