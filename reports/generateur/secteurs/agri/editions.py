"""Quatre éditions par profil d'opérateur (plan d'action sectoriel) à partir d'un tronc commun.

    RG_EDITION = producteurs | industriels | negoce | intrants

Les chapitres réutilisés portent leur numéro d'origine (1 à 10), les chapitres propres aux éditions un identifiant > 100
(pour ne pas être confondus avec les chapitres SH cités dans le texte) ; renumeroter() les renumérote dans l'ordre
de l'édition et met à jour les titres de sections, les légendes (Figure/Tableau N.M) et les renvois
« chapitre N ».
"""
import copy
import math
import re

from layout import *
from reportlab.platypus import KeepTogether

EDITIONS = {
    'producteurs': dict(num='01-A', titre=['Production agricole', 'brute'], sous_titre=['Cultures, élevage, pêche : exporter et sourcer', 'dans la Zone de libre-échange continentale africaine'],
                        public='producteurs, coopératives, fermes commerciales et exploitations d\'amont',
                        lignes=['Filières brutes : SH 01 à 14 (animaux, pêche, lait, horticulture, légumes, fruits, café-thé, céréales, oléagineux)',
                                'Cibles vérifiées : taux servis ligne par ligne × marché réel (OEC 2023-2024) × formalités',
                                'Chaîne du froid, semences, focus pays et feuille de route 2026-2027'],
                        running='ZLECAf · Agriculture — Plan d\'action Producteurs'),
    'industriels': dict(num='01-B', titre=['Industrie agroalimentaire', '& transformation'], sous_titre=['Escalade tarifaire, origine et investissement', 'dans la Zone de libre-échange continentale africaine'],
                        public='transformateurs industriels, agro-industries et unités de conditionnement',
                        lignes=['Produits transformés : SH 15 à 24 (huiles, sucre, cacao, céréales transformées, conserves, boissons, tabac)',
                                'Cibles vérifiées : taux servis ligne par ligne × marché réel × formalités',
                                'Coûts énergétiques et emballages, champions africains, focus pays, feuille de route'],
                        running='ZLECAf · Agroalimentaire — Plan d\'action Industriels'),
    'negoce': dict(num='01-C', titre=['Négoce, import-export', '& distribution'], sous_titre=['Marges préférentielles, conformité et coût rendu', 'dans la Zone de libre-échange continentale africaine'],
                   public='traders, négociants, grossistes, distributeurs et opérateurs logistiques',
                   lignes=['Régimes douaniers, marges servies et règles d\'origine des 5 destinations appliquées',
                           'Formalités, certificats, SPS et paiements ; routes, assurance et coût rendu intégral',
                           'Top 25 vérifié, créneaux et audit des cibles de l\'édition précédente'],
                   running='ZLECAf · Agroalimentaire — Plan d\'action Négoce'),
    'intrants': dict(num='01-D', titre=['Intrants, équipements', '& agrotech'], sous_titre=['Engrais, aliments du bétail, semences, phytosanitaires et machines', 'dans la Zone de libre-échange continentale africaine'],
                     public='fournisseurs d\'engrais, d\'aliments pour animaux, de semences, de machines agricoles et de technologies',
                     lignes=['Marchés africains des facteurs de production (OEC 2023-2024) et régimes tarifaires appliqués',
                             'Normes et homologations, besoins par filière, cibles vérifiées',
                             'Partenariats public-privé, hubs de distribution, focus pays et feuille de route'],
                     running='ZLECAf · Agriculture — Plan d\'action Intrants & équipements'),
}

# Chapitres du rapport unique repris dans une autre édition (renvois)
AILLEURS = {4: 'chapitre des offres du plan Négoce (01-C)', 8: 'chapitre logistique du plan Négoce (01-C)'}


class CoverEdition(Flowable):
    def __init__(self, ed):
        super().__init__(); self.ed = EDITIONS[ed]

    def wrap(self, aw, ah): return W, H

    def draw(self):
        e, c = self.ed, self.canv
        c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.saveState(); c.setStrokeColor(colors.Color(0.78, 0.58, 0.17, alpha=0.16)); c.setLineWidth(0.6)
        for k in range(26):
            p = c.beginPath(); y0 = 70 * mm + k * 5.2 * mm
            p.moveTo(W * 0.38, y0)
            for i in range(1, 41):
                p.lineTo(W * 0.38 + i * (W * 0.62) / 40, y0 + 9 * mm * math.sin(i / 40 * math.pi * 1.2 + k * 0.18) - i * 0.9)
            c.drawPath(p, stroke=1, fill=0)
        c.restoreState()
        c.setFillColor(GOLD); c.roundRect(ML, H - 30 * mm, 10 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 12); c.drawCentredString(ML + 5 * mm, H - 26.6 * mm, 'Zf')
        c.setFont('Fraunces-Bold', 14); c.drawString(ML + 13 * mm, H - 26.8 * mm, 'ZLECAf')
        c.setFont('DMSans-Regular', 7.5); c.setFillColor(colors.HexColor('#9EA3B8'))
        c.drawString(ML + 13 * mm, H - 30.6 * mm, 'TRADE INTELLIGENCE · RAPPORTS SECTORIELS')
        c.setFillColor(GOLD); c.setFont('DMSans-Bold', 8)
        c.drawRightString(W - MR, H - 26.8 * mm, f'PLAN D\'ACTION SECTORIEL N° {e["num"]}')
        c.setFillColor(colors.HexColor('#9EA3B8')); c.setFont('DMSans-Regular', 7.5)
        c.drawRightString(W - MR, H - 30.6 * mm, 'Agriculture & agroalimentaire · Édition T3 2026')
        c.setFillColor(GOLD); c.rect(ML, H - 92 * mm, 16 * mm, 2, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 36)
        c.drawString(ML, H - 110 * mm, e['titre'][0]); c.drawString(ML, H - 125 * mm, e['titre'][1])
        c.setFont('Fraunces-Italic', 15); c.setFillColor(colors.HexColor('#E7C877'))
        c.drawString(ML, H - 139 * mm, e['sous_titre'][0]); c.drawString(ML, H - 146.5 * mm, e['sous_titre'][1])
        c.setFont('DMSans-Regular', 9.2); c.setFillColor(colors.HexColor('#C9CDDC'))
        for i, l in enumerate(e['lignes']):
            c.drawString(ML, H - 161 * mm - i * 5.4 * mm, l)
        c.setFont('DMSans-Bold', 8.5); c.setFillColor(GOLD)
        c.drawString(ML, 62 * mm, 'POUR : ' + e['public'].upper()[:110])
        c.setFont('DMSans-Regular', 6.8); c.setFillColor(colors.HexColor('#7E8398'))
        c.drawString(ML, 16 * mm, 'afcfta-zlecaf.online · Document d\'analyse économique et réglementaire. Ne constitue ni un avis juridique ni une décision douanière.')
        c.drawString(ML, 12.5 * mm, 'Données arrêtées au 29 septembre 2026. © ZLECAf Trade Intelligence — reproduction interdite sans autorisation.')


def _iter(fl):
    for f in fl:
        if isinstance(f, KeepTogether):
            yield from _iter(f._content)
        else:
            yield f


def _re_para(p, txt):
    q = Paragraph(txt, p.style)
    for a in ('_toclevel', '_toctext', '_bookmark', '_notoc'):
        if hasattr(p, a):
            setattr(q, a, getattr(p, a))
    return q


def renumeroter(story):
    """Numérote les chapitres dans l'ordre de l'édition et répercute sur sections, légendes et renvois."""
    n, carte, courant = 0, {}, None
    for f in story:
        if isinstance(f, ChapterHead) and isinstance(f.num, int):
            n += 1
            carte.setdefault(f.num, n)
    motif = re.compile(r'\b(Figure|Tableau|chapitre|Chapitre|section)\s+(\d{1,3})(\.\d+)?\b')

    def sub(m, cur):
        mot, num, suite = m.group(1), int(m.group(2)), m.group(3) or ''
        if mot in ('chapitre', 'Chapitre') and suite == '' and len(m.group(2)) == 2 and m.group(2).startswith('0'):
            return m.group(0)  # chapitre SH (« chapitre 03 »)
        if mot in ('chapitre', 'Chapitre') and (m.string[max(0, m.start() - 3):m.start()] == 'Ex-' or m.string[m.end():m.end() + 1] == ':'):
            return m.group(0)  # chapitre SH (« Ex-chapitre 9: Café… », Appendice IV)
        if mot in ('Figure', 'Tableau', 'section') or num in carte:
            nouveau = carte.get(num, cur if mot in ('Figure', 'Tableau') else None)
            return f'{mot} {nouveau}{suite}' if nouveau else m.group(0)
        if num <= 10 and suite == '':  # chapitre du rapport unique absent de cette édition
            return AILLEURS.get(num, f'{mot} {num} du rapport complet')
        return m.group(0)

    def fix_list(fl, cur):
        out = []
        for f in fl:
            if isinstance(f, KeepTogether):
                f._content = fix_list(f._content, cur); out.append(f); continue
            if isinstance(f, Table):  # encadrés, fiches à deux colonnes, tableaux
                f._cellvalues = [[fix_list(c, cur) if isinstance(c, list) else (fix_list([c], cur)[0] if isinstance(c, (Paragraph, Table)) else c)
                                  for c in row] for row in f._cellvalues]
                out.append(f); continue
            if isinstance(f, Paragraph):
                t = f.text
                t2 = re.sub(r'^(\d{1,3})\.(\d+)\s', lambda m: f'{carte.get(int(m.group(1)), cur)}.{m.group(2)} ', t) if getattr(f, '_toclevel', None) == 1 else t
                t2 = motif.sub(lambda m: sub(m, cur), t2)
                if t2 != t:
                    q = _re_para(f, t2)
                    if getattr(f, '_toclevel', None) == 1:
                        q._toctext = re.sub(r'^(\d{1,3})\.', f'{cur}.', getattr(f, '_toctext', t2)) if cur else q._toctext
                    f = q
            elif getattr(f, '_toclevel', None) == 1 and cur and re.match(r'^\d{1,2}\.', getattr(f, '_toctext', '')):
                f._toctext = re.sub(r'^\d{1,2}\.', f'{cur}.', f._toctext)  # bandeaux de fiches (SectorBand)
            out.append(f)
        return out

    res = []
    for f in story:
        if isinstance(f, ChapterHead) and isinstance(f.num, int):
            courant = carte[f.num]
            if f.num != courant:
                g = copy.copy(f); g.num = courant; g._toctext = f'{courant}. {f.title}'; f = g
            res.append(f); continue
        res += fix_list([f], courant)
    return res
