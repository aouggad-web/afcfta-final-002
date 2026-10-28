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

const API = (import.meta.env.VITE_BACKEND_URL || '') + '/api';

const DEVISE_NATIONALE = { TUN: 'TND', CIV: 'XOF', MDG: 'MGA', GHA: 'GHS', SEN: 'XOF', ZMB: 'ZMW', MLI: 'XOF', KEN: 'KES', TZA: 'TZS', ZAF: 'ZAR', CMR: 'XAF' };

const STATUTS = {
  CALCULE: { fr: 'Calculé', en: 'Calculated' },
  QUANTITE_REQUISE: { fr: 'Quantité requise', en: 'Quantity required' },
  TAUX_DE_CHANGE_REQUIS: { fr: 'Taux de change requis', en: 'Exchange rate required' },
  ASSIETTE_INDISPONIBLE: { fr: 'Assiette non établie', en: 'Basis not established' },
  ASSIETTE_INCOMPLETE: { fr: 'Assiette incomplète', en: 'Incomplete basis' },
  TAUX_INDISPONIBLE: { fr: 'Taux non établi', en: 'Rate not established' },
};

/** Statut d'une ligne ; une quantité réclamée dit dans quelle unité. */
function statut(ligne, fr) {
  const libelle = STATUTS[ligne.statut]?.[fr ? 'fr' : 'en'] || ligne.statut;
  return ligne.statut === 'QUANTITE_REQUISE' && ligne.unite_quantite ? `${libelle} (${ligne.unite_quantite})` : libelle;
}

const ETATS = {
  COMPLET: { fr: 'Complet', en: 'Complete' },
  PARTIEL: { fr: 'Partiel : des droits ne sont pas chiffrés', en: 'Partial: some duties are not quantified' },
  INDISPONIBLE: { fr: 'Non chiffrable', en: 'Not quantifiable' },
  AUCUN_DROIT_PUBLIE: { fr: 'Aucun droit de sortie au tarif collecté pour cette position', en: 'No export duty in the collected tariff for this position' },
};

function detailErreur(e, fr) {
  const detail = e?.response?.data?.detail;
  if (detail?.code === 'POSITION_NATIONALE_REQUISE') {
    return fr ? 'Position nationale requise : choisissez la position complète.' : 'National position required: choose the full position.';
  }
  if (typeof detail === 'string') return detail;
  return fr ? 'Calcul impossible' : 'Calculation failed';
}

export default function ExportCalculator({ language = 'fr' }) {
  const fr = language !== 'en';
  const [pays, setPays] = useState({});
  // Ce que le texte fait déclarer à l'exportateur (Madagascar : DTSPM du Code
  // minier ; Cameroun : produit fini ou non), servi par l'API, par pays, avec
  // le champ de la demande qui porte la réponse.
  const [questions, setQuestions] = useState({});
  const [reponse, setReponse] = useState(null);
  const [transforme, setTransforme] = useState(false);
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
      .catch(() => setErreur(fr ? 'Pays couverts indisponibles' : 'Covered countries unavailable'));
  }, [fr]);

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
      if (demandee === version.current) setErreur(detailErreur(e, fr));
    } finally {
      setChargement(false);
    }
  };

  const export_ = resultat?.export;
  const etat = export_ && (ETATS[export_.etat]?.[fr ? 'fr' : 'en'] || export_.etat);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{fr ? 'Droits et taxes à l’exportation' : 'Export duties and taxes'}</CardTitle>
        <CardDescription>
          {fr
            ? 'Droits de sortie publiés au tarif du pays d’exportation. Seuls les pays dont le tarif publie ces droits sont proposés.'
            : 'Export duties published in the exporting country’s tariff. Only countries whose tariff publishes them are offered.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="export-pays">{fr ? 'Pays d’exportation' : 'Exporting country'}</Label>
            <Select value={iso3} onValueChange={choisirPays}>
              <SelectTrigger id="export-pays" data-testid="export-pays">
                <SelectValue placeholder={fr ? 'Choisir' : 'Choose'} />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(pays).map(([iso, n]) => (
                  <SelectItem key={iso} value={iso}>
                    {iso} — {n
                      ? `${n} ${fr ? 'positions avec droit de sortie' : 'positions with export duty'}`
                      : (fr ? 'taxe de sortie hors tarif' : 'export levy outside the tariff')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="export-code">{fr ? 'Position nationale' : 'National position'}</Label>
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
            <Label htmlFor="export-valeur">{fr ? 'Valeur en douane' : 'Customs value'}</Label>
            <Input id="export-valeur" type="number" min="0" value={valeur} onChange={(e) => setValeur(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="export-devise">{fr ? 'Devise' : 'Currency'}</Label>
            <Input id="export-devise" value={devise} onChange={(e) => setDevise(e.target.value.toUpperCase())} />
          </div>
          <div>
            <Label htmlFor="export-quantite">{fr ? 'Quantité (unité du droit)' : 'Quantity (unit of the duty)'}</Label>
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
              {fr ? question.question : question.question_en}
            </legend>
            <div className="flex gap-4 text-sm">
              <label><input type="radio" name="reponse-exportateur" checked={reponse === true} onChange={() => setReponse(true)} /> {fr ? 'Oui' : 'Yes'}</label>
              <label><input type="radio" name="reponse-exportateur" checked={reponse === false} onChange={() => setReponse(false)} /> {fr ? 'Non' : 'No'}</label>
            </div>
            {reponse && question.question_transformation && (
              <label className="flex gap-2 text-sm">
                <input type="checkbox" checked={transforme} onChange={(e) => setTransforme(e.target.checked)} />
                {fr ? question.question_transformation : question.question_transformation_en}
              </label>
            )}
          </fieldset>
        )}

        <Button
          onClick={calculer}
          disabled={!iso3 || !code || valeur === '' || changeInvalide || (question && reponse === null) || chargement}
          data-testid="export-calculer"
        >
          {fr ? 'Calculer les droits de sortie' : 'Calculate export duties'}
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
                    <th>{fr ? 'Droit' : 'Duty'}</th>
                    <th>{fr ? 'Montant' : 'Amount'}</th>
                    <th>{fr ? 'Statut' : 'Status'}</th>
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
                      <td>{statut(ligne, fr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {/* Aucun total quand rien n'est chiffré : « 0 » se lirait « rien à payer ». */}
            {export_.lignes.some((ligne) => ligne.statut === 'CALCULE') && (
              <p className="font-semibold">
                {fr ? 'Droits de sortie chiffrés' : 'Quantified export duties'} : {chiffres(export_.total_droits, language, 2)} {resultat.devise}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
