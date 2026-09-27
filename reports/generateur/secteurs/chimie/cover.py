from layout import *
import math

class Cover(Flowable):
    def wrap(self, aw, ah): return W, H
    def draw(self):
        c = self.canv
        c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
        # motif : réseau hexagonal (cycles benzéniques) en filigrane
        c.saveState(); c.setStrokeColor(colors.Color(0.12, 0.48, 0.55, alpha=0.30)); c.setLineWidth(0.7)
        r = 7.2 * mm; dx = r * math.sqrt(3); dy = 1.5 * r
        for row in range(-1, 22):
            for col in range(-1, 9):
                cx = W * 0.40 + col * dx + (dx / 2 if row % 2 else 0); cy = 60 * mm + row * dy
                if (row * 7 + col * 3) % 5 == 0 or cx < W * 0.50 or (cx < W * 0.62 and row > 8): continue
                p = c.beginPath()
                for k in range(7):
                    a = math.pi / 6 + k * math.pi / 3
                    x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                    (p.moveTo if k == 0 else p.lineTo)(x, y)
                c.drawPath(p, stroke=1, fill=0)
                if (row + col) % 4 == 0:
                    c.setFillColor(colors.Color(0.78, 0.58, 0.17, alpha=0.55)); c.circle(cx + r * math.cos(math.pi / 6), cy + r * math.sin(math.pi / 6), 0.9, fill=1, stroke=0)
        c.restoreState()
        # logo
        c.setFillColor(GOLD); c.roundRect(ML, H - 30 * mm, 10 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 12); c.drawCentredString(ML + 5 * mm, H - 26.6 * mm, 'Zf')
        c.setFont('Fraunces-Bold', 14); c.drawString(ML + 13 * mm, H - 26.8 * mm, 'ZLECAf')
        c.setFont('DMSans-Regular', 7.5); c.setFillColor(colors.HexColor('#9EA3B8'))
        c.drawString(ML + 13 * mm, H - 30.6 * mm, 'TRADE INTELLIGENCE · RAPPORTS SECTORIELS')
        c.setFillColor(GOLD); c.setFont('DMSans-Bold', 8)
        c.drawRightString(W - MR, H - 26.8 * mm, 'RAPPORT SECTORIEL N° 04')
        c.setFillColor(colors.HexColor('#9EA3B8')); c.setFont('DMSans-Regular', 7.5)
        c.drawRightString(W - MR, H - 30.6 * mm, 'Édition T3 2026 · mise à jour trimestrielle')
        # titre
        c.setFillColor(GOLD); c.rect(ML, H - 92 * mm, 16 * mm, 2, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 40)
        c.drawString(ML, H - 110 * mm, 'Chimie, Cosmétiques')
        c.drawString(ML, H - 126 * mm, '& Hygiène')
        c.setFont('Fraunces-Italic', 16); c.setFillColor(colors.HexColor('#8FD0DC'))
        c.drawString(ML, H - 140 * mm, 'Tarifs, règles d\'origine et opportunités')
        c.drawString(ML, H - 147.5 * mm, 'de la chimie de base au savon, dans la ZLECAf')
        c.setFont('DMSans-Regular', 9.5); c.setFillColor(colors.HexColor('#C9CDDC'))
        lines = ['16 segments : chimie de base, engrais, plastiques, peintures, parfums, cosmétiques,',
                 'savons, détergents, javel, désinfectants et articles d\'hygiène',
                 'Focus Algérie : urée, ammoniac, méthanol, DAPS sur les cosmétiques, marchés d\'export',
                 'Données SaaS ZLECAf croisées avec BACI, UN Comtrade, USGS, Fertiglobe et la presse']
        for i, l in enumerate(lines): c.drawString(ML, H - 162 * mm - i * 5.4 * mm, l)
        y = 44 * mm
        c.setStrokeColor(colors.HexColor('#3A3E52')); c.setLineWidth(0.5); c.line(ML, y + 24 * mm, W - MR, y + 24 * mm)
        figs = [('16', 'segments chimie,\ncosmétiques et hygiène'), ('30 958', 'lignes tarifaires\n(40 barèmes nationaux)'), ('112 %', 'charge à l\'import des\ncosmétiques en Algérie (NPF)'), ('54', 'pays couverts')]
        cw = (W - ML - MR) / 4
        for i, (v, l) in enumerate(figs):
            x = ML + i * cw
            c.setFillColor(GOLD); c.setFont('Fraunces-Bold', 22); c.drawString(x, y + 12 * mm, v)
            c.setFillColor(colors.HexColor('#C9CDDC')); c.setFont('DMSans-Regular', 7.8)
            for j, ll in enumerate(l.split('\n')): c.drawString(x, y + 6.5 * mm - j * 3.6 * mm, ll)
        c.setFont('DMSans-Regular', 6.8); c.setFillColor(colors.HexColor('#7E8398'))
        c.drawString(ML, 16 * mm, 'afcfta-zlecaf.online · Document d\'analyse économique et réglementaire. Ne constitue ni un avis juridique, ni une décision douanière, ni un avis médical.')
        c.drawString(ML, 12.5 * mm, 'Données arrêtées au 27 septembre 2026. © ZLECAf Trade Intelligence — reproduction interdite sans autorisation.')
