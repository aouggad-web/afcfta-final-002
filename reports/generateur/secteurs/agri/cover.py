from layout import *
import math

class Cover(Flowable):
    def wrap(self, aw, ah): return W, H
    def draw(self):
        c = self.canv
        c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
        # motif : champ de sillons (courbes) en filigrane doré
        c.saveState(); c.setStrokeColor(colors.Color(0.78, 0.58, 0.17, alpha=0.16)); c.setLineWidth(0.6)
        for k in range(26):
            p = c.beginPath(); y0 = 70 * mm + k * 5.2 * mm
            p.moveTo(W * 0.38, y0)
            for i in range(1, 41):
                x = W * 0.38 + i * (W * 0.62) / 40
                y = y0 + 9 * mm * math.sin(i / 40 * math.pi * 1.2 + k * 0.18) - i * 0.9
                p.lineTo(x, y)
            c.drawPath(p, stroke=1, fill=0)
        c.restoreState()
        # logo
        c.setFillColor(GOLD); c.roundRect(ML, H - 30 * mm, 10 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 12); c.drawCentredString(ML + 5 * mm, H - 26.6 * mm, 'Zf')
        c.setFont('Fraunces-Bold', 14); c.drawString(ML + 13 * mm, H - 26.8 * mm, 'ZLECAf')
        c.setFont('DMSans-Regular', 7.5); c.setFillColor(colors.HexColor('#9EA3B8'))
        c.drawString(ML + 13 * mm, H - 30.6 * mm, 'TRADE INTELLIGENCE · RAPPORTS SECTORIELS')
        c.setFillColor(GOLD); c.setFont('DMSans-Bold', 8)
        c.drawRightString(W - MR, H - 26.8 * mm, 'RAPPORT SECTORIEL N° 01')
        c.setFillColor(colors.HexColor('#9EA3B8')); c.setFont('DMSans-Regular', 7.5)
        c.drawRightString(W - MR, H - 30.6 * mm, 'Édition T3 2026 · mise à jour trimestrielle')
        # titre
        c.setFillColor(GOLD); c.rect(ML, H - 92 * mm, 16 * mm, 2, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Fraunces-Bold', 40)
        c.drawString(ML, H - 110 * mm, 'Agriculture &')
        c.drawString(ML, H - 126 * mm, 'Agroalimentaire')
        c.setFont('Fraunces-Italic', 16); c.setFillColor(colors.HexColor('#E7C877'))
        c.drawString(ML, H - 140 * mm, 'Tarifs, règles d\'origine et opportunités')
        c.drawString(ML, H - 147.5 * mm, 'dans la Zone de libre-échange continentale africaine')
        c.setFont('DMSans-Regular', 9.5); c.setFillColor(colors.HexColor('#C9CDDC'))
        lines = ['15 filières agricoles et agro-industrielles (SH 01 à 24) · 54 pays',
                 '40 barèmes nationaux · 10 offres tarifaires officielles · Appendice IV des règles d\'origine',
                 'Données SaaS ZLECAf croisées avec FAO, Banque mondiale, Afreximbank, CNUCED, OMC, ITC']
        for i, l in enumerate(lines): c.drawString(ML, H - 162 * mm - i * 5.4 * mm, l)
        # bandeau chiffres
        y = 44 * mm
        c.setStrokeColor(colors.HexColor('#3A3E52')); c.setLineWidth(0.5); c.line(ML, y + 24 * mm, W - MR, y + 24 * mm)
        figs = [('15', 'filières analysées'), ('54', 'pays couverts'), ('35 240', 'lignes tarifaires\nagricoles exploitées'), ('10', 'offres ZLECAf\ncomparées')]
        cw = (W - ML - MR) / 4
        for i, (v, l) in enumerate(figs):
            x = ML + i * cw
            c.setFillColor(GOLD); c.setFont('Fraunces-Bold', 22); c.drawString(x, y + 12 * mm, v)
            c.setFillColor(colors.HexColor('#C9CDDC')); c.setFont('DMSans-Regular', 7.8)
            for j, ll in enumerate(l.split('\n')): c.drawString(x, y + 6.5 * mm - j * 3.6 * mm, ll)
        c.setFont('DMSans-Regular', 6.8); c.setFillColor(colors.HexColor('#7E8398'))
        c.drawString(ML, 16 * mm, 'afcfta-zlecaf.online · Document d\'analyse économique et réglementaire. Ne constitue ni un avis juridique ni une décision douanière.')
        c.drawString(ML, 12.5 * mm, 'Données arrêtées au 27 septembre 2026. © ZLECAf Trade Intelligence — reproduction interdite sans autorisation.')
