"""Génère un rapport sectoriel ZLECAf en PDF.

    python reports/generateur/generer.py pharma                       # focus Algérie (défaut)
    python reports/generateur/generer.py chimie --pays-focus SEN      # chapitre focus générique Sénégal
    python reports/generateur/generer.py agri --etapes pdf            # réassembler le PDF seulement
    python reports/generateur/generer.py agri --edition producteurs   # plan d'action par profil (agri : producteurs,
                                                                      # industriels, negoce, intrants ; « toutes » pour les 4)

Chaque secteur est une suite de scripts (extraction des données du SaaS, graphiques, PDF)
exécutés dans un dossier de travail _travail/<secteur>/ où sont copiés les scripts et les
données figées (figees/). Les chemins passent par les variables d'environnement RG_*.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
REPO = RACINE.parents[1]

# (script, dossier d'exécution, étape) — l'ordre compte : chaque script lit les sorties des précédents.
PIPELINES = {
    'agri': [('analyze.py', 'repo', 'extraction'), ('analyze2.py', 'repo', 'extraction'), ('targets.py', 'backend', 'extraction'),
             ('scan.py', 'backend', 'extraction'), ('escal.py', 'repo', 'extraction'), ('dza_tax.py', 'repo', 'extraction'),
             ('cibles.py', 'backend', 'extraction'),
             ('charts.py', 'repo', 'graphiques'), ('charts_sec.py', 'repo', 'graphiques'), ('chart_served.py', 'repo', 'graphiques'),
             ('charts_dza.py', 'repo', 'graphiques'), ('charts_log.py', 'repo', 'graphiques'), ('corridors.py', 'repo', 'graphiques')],
    'pharma': [('analyze.py', 'repo', 'extraction'), ('served.py', 'backend', 'extraction'), ('cases.py', 'backend', 'extraction'),
               ('charts1.py', 'repo', 'graphiques'), ('charts2.py', 'repo', 'graphiques'), ('charts3.py', 'repo', 'graphiques'),
               ('charts4.py', 'repo', 'graphiques')],
    'chimie': [('analyze.py', 'repo', 'extraction'), ('served.py', 'backend', 'extraction'), ('cases.py', 'backend', 'extraction'),
               ('charts.py', 'repo', 'graphiques')],
}
TITRES = {'agri': 'Agriculture_Agroalimentaire', 'pharma': 'Pharmaceutique_Sante', 'chimie': 'Chimie_Cosmetiques_Hygiene'}
EDITION = 'T3-2026'
EDITIONS_PROFIL = {'agri': ['producteurs', 'industriels', 'negoce', 'intrants']}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('secteur', choices=sorted(PIPELINES))
    ap.add_argument('--pays-focus', default='DZA', help='code ISO3 du pays focus (défaut : DZA, module approfondi)')
    ap.add_argument('--etapes', default='extraction,graphiques,pdf', help='sous-ensemble de extraction,graphiques,pdf')
    ap.add_argument('--edition', help='plan d\'action par profil (agri) : producteurs, industriels, negoce, intrants ou toutes')
    ap.add_argument('--sortie', type=Path, help='chemin du PDF (défaut : reports/sectoriels/Rapport_<secteur>_ZLECAf_<édition>[_<pays>].pdf)')
    a = ap.parse_args()
    etapes = set(a.etapes.split(','))
    pays = a.pays_focus.upper()
    editions = [None]
    if a.edition:
        permises = EDITIONS_PROFIL.get(a.secteur, [])
        editions = permises if a.edition == 'toutes' else [a.edition]
        if not permises:
            ap.error(f'--edition : aucune édition par profil pour {a.secteur} (disponible : agri)')
        if not set(editions) <= set(permises):
            ap.error(f'--edition : {a.edition} non disponible pour {a.secteur} (choix : {", ".join(permises) or "aucun"}, toutes)')
        if a.sortie and len(editions) > 1:
            ap.error('--sortie ne peut désigner qu\'un seul PDF : préciser une édition')

    sys.path.insert(0, str(RACINE / 'commun'))
    from polices import preparer
    travail = RACINE / '_travail' / a.secteur
    travail.mkdir(parents=True, exist_ok=True)
    src = RACINE / 'secteurs' / a.secteur
    (travail / 'charts').mkdir(exist_ok=True)
    for f in list(src.glob('*.py')) + list((src / 'figees').glob('*')):
        # figees/ : données et graphiques non régénérables (repris d'un autre secteur ou saisis à la main)
        shutil.copy2(f, travail / ('charts' if f.suffix == '.png' else '') / f.name)

    env = dict(os.environ, RG_DIR=str(travail), RG_RACINE=str(RACINE), RG_REPO=str(REPO), RG_PAYS_FOCUS=pays,
               RG_POLICES=str(preparer(RACINE / '_cache' / 'polices')), MPLBACKEND='Agg',
               PYTHONPATH=os.pathsep.join([str(travail), str(RACINE / 'commun'), str(REPO / 'backend'), os.environ.get('PYTHONPATH', '')]))
    cwd = {'repo': REPO, 'backend': REPO / 'backend'}

    for script, ou, etape in PIPELINES[a.secteur]:
        if etape in etapes:
            print(f'[{etape}] {script}', flush=True)
            subprocess.run([sys.executable, str(travail / script)], cwd=cwd[ou], env=env, check=True, stdout=subprocess.DEVNULL)
    if 'pdf' in etapes:
        suffixe = '' if pays == 'DZA' else f'_{pays}'
        for ed in editions:
            titre = TITRES[a.secteur] + (f'_Plan_{ed.capitalize()}' if ed else '')
            sortie = a.sortie or REPO / 'reports' / 'sectoriels' / f'Rapport_{titre}_ZLECAf_{EDITION}{suffixe}.pdf'
            sortie.parent.mkdir(parents=True, exist_ok=True)
            env_ed = dict(env, RG_EDITION=ed) if ed else env
            subprocess.run([sys.executable, str(travail / 'build.py'), str(sortie)], cwd=REPO, env=env_ed, check=True)
            print('PDF :', sortie)


if __name__ == '__main__':
    main()
