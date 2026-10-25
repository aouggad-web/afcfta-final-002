"""Chapitre « pays focus » générique, paramétré par le code ISO3 du pays demandé.

L'Algérie (DZA) dispose d'un module approfondi propre à chaque secteur (ch_algeria.py) ;
pour tout autre pays, ce chapitre est construit à partir des données du SaaS et de l'OEC,
et se termine par la liste des recherches documentaires à mener avant diffusion.
S'importe depuis le build d'un secteur (layout.py doit être sur le chemin).
"""
import importlib
import json
import os
import statistics as stt

from layout import *  # noqa: F401,F403 (styles et composants du secteur)
from services.oec_trade_service import AFRICAN_COUNTRIES_OEC
from services.official_preferential_rates import ISO3_TO_ISO2

import oec

PAYS = os.environ.get('RG_PAYS_FOCUS', 'DZA').upper()
ANNEE_OEC = int(os.environ.get('RG_ANNEE_OEC', '2023'))
LIBELLES = {'ADOPTE_ET_DIRECTIVE': 'Offre adoptée', 'ADOPTE_PROVISOIREMENT': 'Adoptée à titre provisoire',
            'LISTE_PROVISOIRE_DIRECTIVE': 'Liste provisoire', 'SOUMIS': 'Offre soumise', 'AUTRE_DECLARATION': 'Autre situation'}
STATUTS = json.load(open(os.environ['RG_REPO'] + '/backend/data/official_preferential/afcfta_status_matrix_2026-09-13.json'))['pays']


def nom(iso3):
    return AFRICAN_COUNTRIES_OEC.get(iso3, {}).get('name_fr', iso3)


def _fr(x, d=1):
    return f'{x:,.{d}f}'.replace(',', ' ').replace('.', ',')


def _md(x):
    return _fr(x / 1e6, 0) + ' M$'


def perimetre(saas):
    """Segments (id, libellé, préfixes SH) et chapitres SH2 du secteur, lus dans le fichier d'analyse SaaS."""
    segs = saas.get('groups') or saas.get('sectors_def')
    return segs, sorted({p[:2] for _, _, pre in segs for p in pre})


def profil_npf(saas, iso3):
    """NPF moyen par segment pour le pays, comparé à la médiane des barèmes du SaaS."""
    segs, _ = perimetre(saas)
    pays = saas['countries']

    def val(c, g):
        v = c.get('groups', {}).get(g) if 'groups' in c else c.get('sectors', {}).get(g)
        return v['avg'] if isinstance(v, dict) else v
    rows = []
    for g, lab, _ in segs:
        tous = [val(c, g) for c in pays.values() if val(c, g) is not None]
        mien = val(pays[iso3], g) if iso3 in pays else None
        if tous:
            rows.append((lab, mien, stt.median(tous)))
    return rows


def taux_servis(served, iso3):
    """Moyennes NPF → ZLECAf servies au pays focus, pondérées par le nombre de lignes."""
    out = []
    for k, grp in served.items():
        d, o = k.split('|')
        if o != iso3:
            continue
        n = sum(v['n'] for v in grp.values())
        if n:
            out.append((nom(d), sum(v['npf'] * v['n'] for v in grp.values()) / n, sum(v['pref'] * v['n'] for v in grp.values()) / n, n))
    return sorted(out, key=lambda x: x[1] - x[2], reverse=True)


def chapitre_focus(num, saas_fichier, served_fichier=None):
    iso2 = ISO3_TO_ISO2.get(PAYS, '')
    st_pays = next((p for p in STATUTS if p['code_iso2'] == iso2), None)
    saas = json.load(open(S + saas_fichier))
    _, chap = perimetre(saas)
    npf = profil_npf(saas, PAYS)
    fl = [chapter(num, f'Focus {nom(PAYS)}'),
          P(f"Ce chapitre est généré pour le pays focus demandé ({nom(PAYS)}, {PAYS}) à partir des données du SaaS et de l'OEC. "
            "Il donne la position tarifaire du pays, les préférences qui lui sont servies et ses flux sur le périmètre du rapport ; "
            "l'analyse qualitative (régime d'importation, base productive, presse, contexte politique) est à compléter selon la liste en fin de chapitre.", LEAD)]
    try:
        imp = oec.importations(PAYS, chap, ANNEE_OEC)
        exp = oec.exportations(PAYS, chap, ANNEE_OEC)
        afr = oec.importateurs_africains(chap, ANNEE_OEC)
    except Exception as e:  # réseau indisponible : le chapitre reste générable
        print('OEC indisponible :', e)
        imp = exp = afr = {}
    mien = [m for _, m, _ in npf if m is not None]
    fl.append(kpis([(LIBELLES.get(st_pays['statut_declare'], st_pays['statut_declare']) if st_pays else 'n.d.', 'offre tarifaire ZLECAf (statut déclaré)', 'Matrice des statuts, 13/09/2026'),
                    (_fr(stt.mean(mien)) + ' %' if mien else 'n.d.', 'droit NPF moyen des segments du rapport', 'Barème SaaS'),
                    (_md(sum(imp.values())) if imp else 'n.d.', f'importations {ANNEE_OEC} sur le périmètre', 'OEC / BACI'),
                    (_md(sum(exp.values())) if exp else 'n.d.', f'exportations {ANNEE_OEC} sur le périmètre', 'OEC / BACI')], cols=4))

    fl.append(h2(f'{num}.1 Protection tarifaire par segment'))
    if mien:
        rows = [['Segment', f'NPF {PAYS} (%)', 'Médiane africaine (%)', 'Écart (pts)']]
        rows += [[lab, _fr(m), _fr(md), _fr(m - md)] for lab, m, md in npf if m is not None]
        fl.append(table(rows, [80 * mm, 30 * mm, 34 * mm, 30 * mm], align_right_from=1))
        fl.append(Paragraph('Source : barèmes NPF du SaaS (moyennes simples des lignes nationales), 40 pays.', SRC))
    else:
        fl.append(P(f"Le barème de {nom(PAYS)} n'est pas encore intégré au SaaS : protection tarifaire à documenter (profil OMC, tarif national)."))

    if served_fichier and os.path.exists(S + served_fichier):
        serv = taux_servis(json.load(open(S + served_fichier)), PAYS)
        fl.append(h2(f'{num}.2 Préférences servies aux produits originaires de {nom(PAYS)}'))
        if serv:
            rows = [['Destination', 'NPF moyen (%)', 'Taux ZLECAf servi (%)', 'Lignes']]
            rows += [[d, _fr(a), _fr(b), str(n)] for d, a, b, n in serv]
            fl.append(table(rows, [60 * mm, 36 * mm, 42 * mm, 36 * mm], align_right_from=1))
            fl.append(Paragraph('Source : calculateurs du SaaS (DZA, EGY, KEN, MAR, ZAF) ; taux 2026, moyennes pondérées par le nombre de lignes.', SRC))
        else:
            fl.append(P(f"Aucun des calculateurs appliqués du SaaS ne sert encore de taux à l'origine {nom(PAYS)} sur ce périmètre."))

    if imp or afr:
        fl.append(h2(f'{num}.3 Flux commerciaux et débouchés africains'))
        rows = [['Chapitre SH', f'Importations {ANNEE_OEC}', f'Exportations {ANNEE_OEC}']]
        rows += [[c, _md(imp.get(c, 0)), _md(exp.get(c, 0))] for c in chap if imp.get(c) or exp.get(c)]
        fl.append(table(rows, [60 * mm, 57 * mm, 57 * mm], align_right_from=1))
        top = [(k, v) for k, v in sorted(afr.items(), key=lambda x: -x[1]) if k != PAYS][:10]
        if top:
            fl.append(Paragraph(f'Premiers importateurs africains du périmètre, {ANNEE_OEC}', CAP))
            fl.append(table([['Pays', 'Importations']] + [[nom(k), _md(v)] for k, v in top], [100 * mm, 74 * mm], align_right_from=1))
        fl.append(Paragraph('Source : OEC / BACI (HS 2017), API tesseract, même source que le module Statistiques du SaaS.', SRC))

    fl.append(callout('Recherches à compléter avant diffusion', [
        "Régime d'importation : licences, autorisations, programmes d'importation, contrôle de conformité.",
        "Fiscalité à l'import au-delà du droit de douane (taxes intérieures, redevances) et son traitement sous la ZLECAf.",
        'Base productive : principaux groupes, capacités, investissements annoncés, zones économiques spéciales.',
        'Presse économique récente, contexte politique et relations régionales, intégrés dans l\'analyse et datés.',
        'Change, rapatriement des recettes et statut GAFI.',
        f"Modèle : le module Algérie (ch_algeria.py) de ce secteur ; créer secteurs/&lt;secteur&gt;/ch_{PAYS.lower()}.py (fonction chapitre(num)) pour un focus approfondi."]))
    return fl


def chapitre(num, saas_fichier, served_fichier=None):
    """Module approfondi du pays s'il existe dans le secteur (ch_algeria pour DZA, ch_<iso3>.py sinon), à défaut chapitre générique."""
    if PAYS == 'DZA':
        from ch_algeria import ch_algeria
        return ch_algeria()
    try:
        module = importlib.import_module(f'ch_{PAYS.lower()}')
    except ModuleNotFoundError:
        return chapitre_focus(num, saas_fichier, served_fichier)
    return module.chapitre(num)
