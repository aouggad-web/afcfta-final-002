"""Polices du générateur : DM Sans et Fraunces (licence SIL OFL 1.1).

Les fichiers variables sont téléchargés depuis le dépôt google/fonts (via jsDelivr),
puis figés en instances statiques. Chaque instance reçoit un nom interne propre :
sans cela, toutes les graisses portent le même nom PostScript et le lecteur PDF
n'affiche jamais le gras.
"""
import os
import urllib.request
from pathlib import Path

BASE = 'https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/'
SOURCES = {
    'DMSans-VF.ttf': 'dmsans/DMSans%5Bopsz,wght%5D.ttf',
    'DMSans-VF-Italic.ttf': 'dmsans/DMSans-Italic%5Bopsz,wght%5D.ttf',
    'Fraunces-VF.ttf': 'fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf',
    'Fraunces-VF-Italic.ttf': 'fraunces/Fraunces-Italic%5BSOFT,WONK,opsz,wght%5D.ttf',
}
INSTANCES = [
    ('DMSans-VF.ttf', 'DMSans-Regular', {'wght': 400, 'opsz': 14}),
    ('DMSans-VF.ttf', 'DMSans-Medium', {'wght': 500, 'opsz': 14}),
    ('DMSans-VF.ttf', 'DMSans-Bold', {'wght': 700, 'opsz': 14}),
    ('DMSans-VF.ttf', 'DMSans-Light', {'wght': 300, 'opsz': 14}),
    ('DMSans-VF-Italic.ttf', 'DMSans-Italic', {'wght': 400, 'opsz': 14}),
    ('Fraunces-VF.ttf', 'Fraunces-SemiBold', {'wght': 600, 'opsz': 72, 'SOFT': 0, 'WONK': 0}),
    ('Fraunces-VF.ttf', 'Fraunces-Bold', {'wght': 700, 'opsz': 72, 'SOFT': 0, 'WONK': 0}),
    ('Fraunces-VF.ttf', 'Fraunces-Regular', {'wght': 400, 'opsz': 36, 'SOFT': 0, 'WONK': 0}),
    ('Fraunces-VF-Italic.ttf', 'Fraunces-Italic', {'wght': 400, 'opsz': 36, 'SOFT': 0, 'WONK': 0}),
]


def preparer(dossier: Path) -> Path:
    """Télécharge et instancie les polices si besoin ; renvoie le dossier."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    dossier.mkdir(parents=True, exist_ok=True)
    if all((dossier / f'{nom}.ttf').exists() for _, nom, _ in INSTANCES):
        return dossier
    for fichier, chemin in SOURCES.items():
        cible = dossier / fichier
        if not cible.exists():
            urllib.request.urlretrieve(BASE + chemin, cible)
    for src, nom, loc in INSTANCES:
        vf = TTFont(dossier / src)
        axes = {a.axisTag for a in vf['fvar'].axes}
        inst = instancer.instantiateVariableFont(vf, {k: v for k, v in loc.items() if k in axes})
        famille, style = nom.split('-')
        table = inst['name']
        table.names = [r for r in table.names if r.nameID not in (16, 17) and r.platformID != 1]
        for nid, val in ((1, famille), (2, style), (3, nom), (4, f'{famille} {style}'), (6, nom)):
            table.setName(val, nid, 3, 1, 0x409)
        inst.save(dossier / f'{nom}.ttf')
    return dossier


if __name__ == '__main__':
    print(preparer(Path(os.environ.get('RG_POLICES', Path(__file__).resolve().parents[1] / '_cache' / 'polices'))))
