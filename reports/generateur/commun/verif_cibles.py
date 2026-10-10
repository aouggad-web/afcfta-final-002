"""Vérification des cibles d'export : un taux préférentiel ne suffit pas, il faut un marché.

Chaque cible (origine, destination, SH6) est confrontée aux flux réels OEC/BACI (moyenne
2023-2024) et reçoit un verdict explicite :

  (toutes les lignes nationales à 8-10 chiffres sont évaluées ; une préférence qui ne couvre
   qu'une partie des lignes est signalée — cas des pâtes au Maroc : seules les lignes à 2,5 % sont
   libéralisées, celles à 40 % restent au NPF)
  RETENUE      marge servie > 0, marché importateur réel, offre de l'origine réelle
  CRÉNEAU      destination exportatrice nette du produit : niche (contre-saison, gamme), pas un débouché
  REJETÉE      pas de marge servie, marché trop petit, ou origine sans capacité d'export

Le motif « pourquoi maintenant » est calculé à partir du calendrier (taux servi en 2026),
jamais saisi à la main. Cas d'école : Égypte → Maroc, oranges (0805.10) — marge de 40 points,
mais le Maroc n'en importe que ~1,4 M$ par an (et en exporte ~51 M$) : REJETÉE (marché trop petit).
"""
import os
import statistics as stt

import oec

ANNEES = [int(a) for a in os.environ.get('RG_ANNEES_OEC', '2023,2024').split(',')]
SEUIL_MARCHE = float(os.environ.get('RG_SEUIL_MARCHE', 5e6))     # importations mondiales de la destination (USD/an)
SEUIL_OFFRE = float(os.environ.get('RG_SEUIL_OFFRE', 5e6))       # exportations mondiales de l'origine (USD/an)
AGRI = [f'{i:02d}' for i in range(1, 25)]


def _moy(dicts):
    cles = set().union(*dicts)
    return {k: stt.mean(d.get(k, 0) for d in dicts) for k in cles}


def _par_hs6(rows):
    return {str(r['HS6 ID'])[-6:]: r['Trade Value'] for r in rows}


def importations_hs6(iso3, chapitres=AGRI):
    ids = ','.join(oec.hs_id(c) for c in chapitres)
    return _moy([_par_hs6(oec.requete(drilldowns='HS6', **{'Importer Country': oec.pays_id(iso3), 'HS2': ids, 'Year': a})) for a in ANNEES])


def exportations_hs6(iso3, chapitres=AGRI):
    ids = ','.join(oec.hs_id(c) for c in chapitres)
    return _moy([_par_hs6(oec.requete(drilldowns='HS6', **{'Exporter Country': oec.pays_id(iso3), 'HS2': ids, 'Year': a})) for a in ANNEES])


def flux_bilateral_hs6(origine, dest, chapitres=AGRI):
    ids = ','.join(oec.hs_id(c) for c in chapitres)
    return _moy([_par_hs6(oec.requete(drilldowns='HS6', **{'Exporter Country': oec.pays_id(origine), 'Importer Country': oec.pays_id(dest),
                                                           'HS2': ids, 'Year': a})) for a in ANNEES])


class Marches:
    """Cache des flux OEC par pays (une requête par pays et par sens)."""

    def __init__(self, chapitres=AGRI):
        self.ch = chapitres
        self._imp, self._exp, self._bil = {}, {}, {}

    def imp(self, iso3):
        if iso3 not in self._imp:
            self._imp[iso3] = importations_hs6(iso3, self.ch)
        return self._imp[iso3]

    def exp(self, iso3):
        if iso3 not in self._exp:
            self._exp[iso3] = exportations_hs6(iso3, self.ch)
        return self._exp[iso3]

    def bil(self, o, d):
        if (o, d) not in self._bil:
            self._bil[(o, d)] = flux_bilateral_hs6(o, d, self.ch)
        return self._bil[(o, d)]


def verdict(o, d, hs6, npf, pref, m: Marches, couverture=None):
    """Retourne (verdict, motifs, indicateurs)."""
    hs6 = hs6.replace('.', '')[:6]
    imp_d, exp_d = m.imp(d).get(hs6, 0), m.exp(d).get(hs6, 0)
    exp_o, deja = m.exp(o).get(hs6, 0), m.bil(o, d).get(hs6, 0)
    imp_o = m.imp(o).get(hs6, 0)
    ind = dict(imp_dest=imp_d, exp_dest=exp_d, exp_orig=exp_o, imp_orig=imp_o, bilat=deja,
               marge=(npf - pref) if npf is not None and pref is not None else None)
    motifs = []
    if ind['marge'] is None or ind['marge'] <= 0:
        motifs.append('aucune marge servie en 2026')
    if imp_d < SEUIL_MARCHE:
        motifs.append(f'marché trop petit ({imp_d / 1e6:.1f} M$ importés)')
    if exp_o < SEUIL_OFFRE:
        motifs.append(f"offre d'origine insuffisante ({exp_o / 1e6:.1f} M$ exportés)")
    if motifs:
        return 'REJETÉE', motifs, ind
    note = []
    if imp_o > 0.5 * exp_o:
        note.append(f"réexportation possible : l'origine importe {imp_o / 1e6:.0f} M$ pour {exp_o / 1e6:.0f} M$ exportés (vérifier la règle d'origine)")
    if couverture and 0 < couverture[0] < couverture[1]:
        note += [f'préférence partielle : {couverture[0]} ligne(s) nationale(s) sur {couverture[1]} réduite(s), les autres restent au NPF']
    if exp_d > imp_d:
        return 'CRÉNEAU', [f'destination exportatrice nette ({exp_d / 1e6:.0f} M$ exportés vs {imp_d / 1e6:.0f} M$ importés)'] + note, ind
    return 'RETENUE', note, ind


def score(ind):
    """Valeur annuelle de la marge sur le marché accessible : min(demande, offre) × marge."""
    return min(ind['imp_dest'], ind['exp_orig']) * ind['marge'] / 100
