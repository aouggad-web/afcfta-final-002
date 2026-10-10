from layout import *
import json
D = json.load(open(S + 'saas_stats.json')); D2 = json.load(open(S + 'saas_stats2.json'))
ROO = D['roo']; MG = D2['margins']

class SectorBand(Flowable):
    def __init__(self, num, name, hs):
        super().__init__(); self.num, self.name, self.hs = num, name, hs
    def wrap(self, aw, ah): self.aw = aw; return aw, 15 * mm
    def draw(self):
        c = self.canv
        c.setFillColor(INK); c.rect(0, 0, self.aw, 13 * mm, fill=1, stroke=0)
        c.setFillColor(GOLD); c.rect(0, 0, 2.2 * mm, 13 * mm, fill=1, stroke=0)
        c.setFont('Fraunces-Bold', 17); c.setFillColor(GOLD); c.drawString(6 * mm, 4.3 * mm, f'{self.num:02d}')
        c.setFont('Fraunces-SemiBold', 14); c.setFillColor(colors.white); c.drawString(17 * mm, 4.6 * mm, self.name)
        c.setFont('DMSans-Regular', 7.5); c.setFillColor(colors.HexColor('#C9CDDC')); c.drawRightString(self.aw - 4 * mm, 5 * mm, 'SH ' + self.hs)

def fiche(num, sid, name, hs, lead, kp, marche, tarif, origine, cibles, risques, sources):
    """kp: list of 4 (valeur, libellé, source). cibles: list of strings. risques: list of strings."""
    band = SectorBand(num, name, hs)
    band._toclevel = 1; band._toctext = f'6.{num} {name}'; band._bookmark = name; band._notoc = True
    fl = [band, Spacer(1, 4), P(lead, st('fl', fontName='Fraunces-Regular', fontSize=10, leading=13.6, textColor=INK2, spaceAfter=5))]
    fl.append(kpis(kp, cols=4))
    fl.append(Spacer(1, 4))
    fl.append(img(S + f'charts/sec_{sid}.png', CW, 56 * mm))
    fl.append(Paragraph('Graphiques : SaaS ZLECAf — FAOSTAT (production 2024, ou 2023 pour le sucre, l\'huile de palme et la bière) et barèmes e-Tariff Book / SARS (droit moyen NPF vs offre ZLECAf 2026, lignes du périmètre de la filière).', SRC))
    left = [Paragraph('Marché & dynamique', H3)] + [Paragraph(x, st('fb', fontSize=8.6, leading=12.1, alignment=TA_JUSTIFY, spaceAfter=3)) for x in marche]
    left += [Paragraph('Tarifs & règle d\'origine', H3), Paragraph(tarif, st('fb2', fontSize=8.6, leading=12.1, alignment=TA_JUSTIFY, spaceAfter=3)),
             Paragraph(origine, st('fb3', fontSize=8.6, leading=12.1, alignment=TA_JUSTIFY, spaceAfter=3, textColor=BLUE))]
    right = [Paragraph('Cibles & opportunités', st('h3g', fontName='DMSans-Bold', fontSize=9, leading=12, textColor=GREEN, spaceAfter=2))]
    right += [Paragraph(x, st('rb', fontSize=8.4, leading=11.6, leftIndent=8, spaceAfter=2.6), bulletText='▸') for x in cibles]
    right += [Paragraph('Risques & points de vigilance', st('h3r', fontName='DMSans-Bold', fontSize=9, leading=12, textColor=RED, spaceBefore=4, spaceAfter=2))]
    right += [Paragraph(x, st('rr', fontSize=8.4, leading=11.6, leftIndent=8, spaceAfter=2.6), bulletText='▸') for x in risques]
    t = Table([[left, right]], colWidths=[CW * 0.53, CW * 0.47])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 8),
                           ('LEFTPADDING', (1, 0), (1, 0), 8), ('RIGHTPADDING', (1, 0), (1, 0), 6), ('BACKGROUND', (1, 0), (1, 0), ZEBRA),
                           ('TOPPADDING', (1, 0), (1, 0), 5), ('BOTTOMPADDING', (1, 0), (1, 0), 5)]))
    fl.append(t)
    fl.append(Paragraph('Sources : ' + sources, SRC))
    fl.append(PageBreak())
    return fl
