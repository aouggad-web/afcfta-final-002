/**
 * Droits et taxes à l'exportation : un écran à part, car c'est un autre impôt
 * sur une autre opération. Les droits de sortie sont lus au socle et liquidés
 * par POST /calcul/export ; une ligne que la source ne permet pas de chiffrer
 * est montrée avec sa raison, jamais comme un zéro.
 */
import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import ProductKeywordSearch from './ProductKeywordSearch';
import { chiffres } from '../../utils/nombres';
import { pick } from '../../i18n/lang';

const API = (import.meta.env.VITE_BACKEND_URL || '') + '/api';

const DEVISE_NATIONALE = { TUN: 'TND', CIV: 'XOF', MDG: 'MGA', GHA: 'GHS', SEN: 'XOF', ZMB: 'ZMW', MLI: 'XOF', KEN: 'KES', TZA: 'TZS', ZAF: 'ZAR', CMR: 'XAF', EGY: 'EGP', COG: 'XAF', GAB: 'XAF', COD: 'CDF' };

const STATUTS = {
  CALCULE: { fr: 'Calculé', en: 'Calculated', ar: 'محسوب' },
  QUANTITE_REQUISE: { fr: 'Quantité requise', en: 'Quantity required', ar: 'الكمية مطلوبة' },
  TAUX_DE_CHANGE_REQUIS: { fr: 'Taux de change requis', en: 'Exchange rate required', ar: 'سعر الصرف مطلوب' },
  ASSIETTE_INDISPONIBLE: { fr: 'Assiette non établie', en: 'Basis not established', ar: 'الوعاء غير محدد' },
  ASSIETTE_INCOMPLETE: { fr: 'Assiette incomplète', en: 'Incomplete basis', ar: 'الوعاء غير مكتمل' },
  TAUX_INDISPONIBLE: { fr: 'Taux non établi', en: 'Rate not established', ar: 'المعدل غير محدد' },
};

/** Statut d'une ligne ; une quantité réclamée dit dans quelle unité. */
function statut(ligne, language) {
  const libelle = STATUTS[ligne.statut]?.[pick(language, 'fr', 'en', 'ar')] || ligne.statut;
  return ligne.statut === 'QUANTITE_REQUISE' && ligne.unite_quantite ? `${libelle} (${ligne.unite_quantite})` : libelle;
}

const ETATS = {
  COMPLET: { fr: 'Complet', en: 'Complete', ar: 'كامل' },
  PARTIEL: { fr: 'Partiel : des droits ne sont pas chiffrés', en: 'Partial: some duties are not quantified', ar: 'جزئي: بعض الرسوم غير محتسبة' },
  INDISPONIBLE: { fr: 'Non chiffrable', en: 'Not quantifiable', ar: 'غير قابل للاحتساب' },
  AUCUN_DROIT_PUBLIE: { fr: 'Aucun droit de sortie au tarif collecté pour cette position', en: 'No export duty in the collected tariff for this position', ar: 'لا يوجد رسم تصدير في التعريفة المجمَّعة لهذا البند' },
};

function detailErreur(e, language) {
  const detail = e?.response?.data?.detail;
  if (detail?.code === 'POSITION_NATIONALE_REQUISE') {
    return pick(language, 'Position nationale requise : choisissez la position complète.', 'National position required: choose the full position.', 'البند الوطني مطلوب: اختر البند كاملًا.');
  }
  if (typeof detail === 'string') return detail;
  return pick(language, 'Calcul impossible', 'Calculation failed', 'تعذّر الحساب');
}

export default function ExportCalculator({ language = 'fr' }) {
  const [pays, setPays] = useState({});
  // Ce que le texte fait déclarer à l'exportateur (Madagascar : DTSPM du Code
  // minier ; Cameroun : produit fini ou non), servi par l'API, par pays, avec
  // le champ de la demande qui porte la réponse.
  const [questions, setQuestions] = useState({});
  const [reponse, setReponse] = useState(null);
  const [transforme, setTransforme] = useState(false);
  const [transformeAilleurs, setTransformeAilleurs] = useState(null);
  const [iso3, setIso3] = useState('');
  const [code, setCode] = useState('');
  const [valeur, setValeur] = useState('');
  const [devise, setDevise] = useState('');
  const [quantite, setQuantite] = useState('');
  const [tauxDeChange, setTauxDeChange] = useState('');
  // La paire de devises qu'un droit attend, dite par l'API (`change_requis`) :
  // jamais devinée, un droit pouvant être publié en USD (Ghana) et non dans la
  // monnaie du tarif.
  const [paire, setPaire] = useState(null);
  const [resultat, setResultat] = useState(null);
  const [erreur, setErreur] = useState('');
  const [chargement, setChargement] = useState(false);

  useEffect(() => {
    axios.get(`${API}/calcul/export/pays`)
      .then((res) => {
        setPays(res.data.pays || {});
        setQuestions(res.data.questions || {});
      })
      .catch(() => setErreur(pick(language, 'Pays couverts indisponibles', 'Covered countries unavailable', 'البلدان المشمولة غير متاحة')));
  }, [language]);

  // Une autre position ou une autre devise appelle une autre paire ; la réponse
  // d'un calcul lancé avant le changement ne vaut plus pour elles.
  const version = useRef(0);
  useEffect(() => {
    version.current += 1;
    setPaire(null);
    setTauxDeChange('');
  }, [iso3, code, devise]);

  const choisirPays = (valeurPays) => {
    setIso3(valeurPays);
    setDevise(DEVISE_NATIONALE[valeurPays] || '');
    setCode('');
    setReponse(null);
    setTransforme(false);
    setTransformeAilleurs(null);
    setResultat(null);
  };

  const nationale = DEVISE_NATIONALE[iso3] || '';
  // Le moteur attend des unités de la devise de la valeur pour UNE unité de la
  // devise du droit. Droit dans la monnaie du tarif : demandé comme on le lit
  // (« 1 USD = ? TND ») et inversé ; droit publié en USD/EUR : « 1 USD = ? GHS »,
  // envoyé tel quel.
  const changeRequis = Boolean(paire);
  const inverse = Boolean(paire && paire.devise_droit === nationale && paire.devise_valeur !== nationale);
  const libelleChange = !paire ? '' : inverse
    ? `1 ${paire.devise_valeur} = ? ${paire.devise_droit}`
    : `1 ${paire.devise_droit} = ? ${paire.devise_valeur}`;
  const changeInvalide = changeRequis && tauxDeChange !== '' && !(parseFloat(tauxDeChange) > 0);
  const question = questions[iso3];

  const calculer = async () => {
    setChargement(true);
    setErreur('');
    setResultat(null);
    const corps = { pays: iso3, code_sh: code, valeur: parseFloat(valeur) };
    if (devise) corps.devise = devise;
    if (quantite !== '') corps.quantite = parseFloat(quantite);
    if (changeRequis && tauxDeChange !== '') {
      corps.taux_de_change = inverse ? 1 / parseFloat(tauxDeChange) : parseFloat(tauxDeChange);
    }
    if (question && reponse !== null) {
      corps[question.champ] = reponse;
      if (reponse && question.question_transformation) corps.produit_minier_transforme = transforme;
      if (reponse === false && question.champ_si_non && transformeAilleurs !== null) {
        corps[question.champ_si_non] = transformeAilleurs;
      }
    }
    const demandee = version.current;
    try {
      const res = await axios.post(`${API}/calcul/export`, corps);
      if (demandee !== version.current) return;
      // Les montants sont dans la devise envoyée, pas dans celle du champ
      // si on la modifie ensuite ; sans devise, dans la monnaie du tarif.
      setResultat({ ...res.data, devise: devise || res.data.provenance?.devise_nationale || '' });
      const requise = (res.data.change_requis || [])[0];
      if (requise) setPaire(requise);
    } catch (e) {
      if (demandee === version.current) setErreur(detailErreur(e, language));
    } finally {
      setChargement(false);
    }
  };

  const export_ = resultat?.export;
  const etat = export_ && (ETATS[export_.etat]?.[pick(language, 'fr', 'en', 'ar')] || export_.etat);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{pick(language, 'Droits et taxes à l’exportation', 'Export duties and taxes', 'رسوم وضرائب التصدير')}</CardTitle>
        <CardDescription>
          {pick(language, 'Droits de sortie publiés au tarif du pays d’exportation. Seuls les pays dont le tarif publie ces droits sont proposés.', 'Export duties published in the exporting country’s tariff. Only countries whose tariff publishes them are offered.', 'رسوم التصدير المنشورة في تعريفة بلد التصدير. لا تُعرض إلا البلدان التي تنشر تعريفتُها هذه الرسوم.')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="export-pays">{pick(language, 'Pays d’exportation', 'Exporting country', 'بلد التصدير')}</Label>
            <Select value={iso3} onValueChange={choisirPays}>
              <SelectTrigger id="export-pays" data-testid="export-pays">
                <SelectValue placeholder={pick(language, 'Choisir', 'Choose', 'اختر')} />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(pays).map(([iso, n]) => (
                  <SelectItem key={iso} value={iso}>
                    {iso} — {n
                      ? `${n} ${pick(language, 'positions avec droit de sortie', 'positions with export duty', 'بندًا خاضعًا لرسم التصدير')}`
                      : (pick(language, 'taxe de sortie hors tarif', 'export levy outside the tariff', 'رسم تصدير خارج التعريفة'))}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="export-code">{pick(language, 'Position nationale', 'National position', 'البند الوطني')}</Label>
            <Input id="export-code" value={code} onChange={(e) => setCode(e.target.value)} />
          </div>
        </div>

        {iso3 && (
          <ProductKeywordSearch
            destinationCountry={iso3}
            language={language}
            sansDroitImport
            onSelect={(choisi) => setCode(choisi)}
          />
        )}

        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <Label htmlFor="export-valeur">{pick(language, 'Valeur en douane', 'Customs value', 'القيمة الجمركية')}</Label>
            <Input id="export-valeur" type="number" min="0" value={valeur} onChange={(e) => setValeur(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="export-devise">{pick(language, 'Devise', 'Currency', 'العملة')}</Label>
            <Input id="export-devise" value={devise} onChange={(e) => setDevise(e.target.value.toUpperCase())} />
          </div>
          <div>
            <Label htmlFor="export-quantite">{pick(language, 'Quantité (unité du droit)', 'Quantity (unit of the duty)', 'الكمية (وحدة الرسم)')}</Label>
            <Input id="export-quantite" type="number" min="0" value={quantite} onChange={(e) => setQuantite(e.target.value)} />
          </div>
          {changeRequis && (
            <div>
              <Label htmlFor="export-change">
                {libelleChange}
              </Label>
              <Input id="export-change" type="number" min="0" value={tauxDeChange} onChange={(e) => setTauxDeChange(e.target.value)} />
            </div>
          )}
        </div>

        {question && (
          <fieldset className="space-y-2" data-testid="export-question-hors-tarif">
            <legend className="text-sm">
              {pick(language, question.question, question.question_en, question.question)}
            </legend>
            <div className="flex gap-4 text-sm">
              <label><input type="radio" name="reponse-exportateur" checked={reponse === true} onChange={() => setReponse(true)} /> {pick(language, 'Oui', 'Yes', 'نعم')}</label>
              <label><input type="radio" name="reponse-exportateur" checked={reponse === false} onChange={() => setReponse(false)} /> {pick(language, 'Non', 'No', 'لا')}</label>
            </div>
            {reponse === false && question.question_si_non && (
              <div className="space-y-1" data-testid="export-question-si-non">
                <p className="text-sm">{pick(language, question.question_si_non, question.question_si_non_en, question.question_si_non)}</p>
                <div className="flex gap-4 text-sm">
                  <label><input type="radio" name="transforme-ailleurs" checked={transformeAilleurs === true} onChange={() => setTransformeAilleurs(true)} /> {pick(language, 'Oui', 'Yes', 'نعم')}</label>
                  <label><input type="radio" name="transforme-ailleurs" checked={transformeAilleurs === false} onChange={() => setTransformeAilleurs(false)} /> {pick(language, 'Non', 'No', 'لا')}</label>
                </div>
              </div>
            )}
            {reponse && question.question_transformation && (
              <label className="flex gap-2 text-sm">
                <input type="checkbox" checked={transforme} onChange={(e) => setTransforme(e.target.checked)} />
                {pick(language, question.question_transformation, question.question_transformation_en, question.question_transformation)}
              </label>
            )}
          </fieldset>
        )}

        <Button
          onClick={calculer}
          disabled={!iso3 || !code || valeur === '' || changeInvalide || (question && reponse === null)
            || (question && question.question_si_non && reponse === false && transformeAilleurs === null) || chargement}
          data-testid="export-calculer"
        >
          {pick(language, 'Calculer les droits de sortie', 'Calculate export duties', 'احتساب رسوم التصدير')}
        </Button>

        {erreur && <p className="text-sm text-red-600" role="alert">{erreur}</p>}

        {resultat && (
          <div className="space-y-3" data-testid="export-resultat">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono">{resultat.pays} {code}</span>
              <span>{resultat.position?.designation}</span>
              <Badge variant="outline">{etat}</Badge>
            </div>
            {export_.lignes.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left">
                    <th>{pick(language, 'Droit', 'Duty', 'الرسم')}</th>
                    <th>{pick(language, 'Montant', 'Amount', 'المبلغ')}</th>
                    <th>{pick(language, 'Statut', 'Status', 'الحالة')}</th>
                  </tr>
                </thead>
                <tbody>
                  {export_.lignes.map((ligne) => (
                    <tr key={ligne.code} className="align-top border-t">
                      <td>
                        <div>{ligne.libelle || ligne.code}</div>
                        {/* Un droit spécifique se lit avec son unité : kg net, centaine, nombre… */}
                        {ligne.specifique && (
                          <div className="text-xs">
                            {ligne.specifique}{ligne.unite_quantite ? ` / ${ligne.unite_quantite}` : ''}
                          </div>
                        )}
                        {ligne.note && <div className="text-xs text-[var(--afcfta-muted)]">{ligne.note}</div>}
                      </td>
                      <td className="tabular-nums">
                        {ligne.montant == null ? '—' : `${chiffres(ligne.montant, language, 2)} ${resultat.devise}`}
                      </td>
                      <td>{statut(ligne, language)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {/* Aucun total quand rien n'est chiffré : « 0 » se lirait « rien à payer ». */}
            {export_.lignes.some((ligne) => ligne.statut === 'CALCULE') && (
              <p className="font-semibold">
                {pick(language, 'Droits de sortie chiffrés', 'Quantified export duties', 'رسوم التصدير المحتسبة')} : {chiffres(export_.total_droits, language, 2)} {resultat.devise}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
