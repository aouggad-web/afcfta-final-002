import os
"""Mise en page commune du rapport (styles, gabarits de page, composants)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether, NextPageTemplate, Flowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

S = (os.environ['RG_DIR'] + '/')
F = os.environ['RG_POLICES'] + '/'
for n in ['DMSans-Regular', 'DMSans-Medium', 'DMSans-Bold', 'DMSans-Light', 'DMSans-Italic',
          'Fraunces-SemiBold', 'Fraunces-Bold', 'Fraunces-Regular', 'Fraunces-Italic']:
    pdfmetrics.registerFont(TTFont(n, F + n + '.ttf'))
pdfmetrics.registerFontFamily('DMSans', normal='DMSans-Regular', bold='DMSans-Bold', italic='DMSans-Italic', boldItalic='DMSans-Bold')

INK = colors.HexColor('#161820'); INK2 = colors.HexColor('#2A2D3A'); MUTED = colors.HexColor('#5E6273')
GOLD = colors.HexColor('#C8952B'); GOLD_L = colors.HexColor('#F6EEDB'); GOLD_D = colors.HexColor('#8A6414')
GREEN = colors.HexColor('#1E8C5A'); GREEN_L = colors.HexColor('#E3F4EB'); RED = colors.HexColor('#C0493D'); RED_L = colors.HexColor('#F8E6E3')
LINE = colors.HexColor('#DADDE4'); ZEBRA = colors.HexColor('#F6F7F9'); BLUE_L = colors.HexColor('#E8EEF8'); BLUE = colors.HexColor('#2F5E9E'); TEAL = colors.HexColor('#1F7A8C'); TEAL_L = colors.HexColor('#E4F1F4')

W, H = A4
ML, MR, MT, MB = 18 * mm, 18 * mm, 22 * mm, 20 * mm
CW = W - ML - MR

def st(name, **kw):
    base = dict(fontName='DMSans-Regular', fontSize=9.2, leading=13.4, textColor=INK2)
    base.update(kw)
    return ParagraphStyle(name, **base)

BODY = st('body', alignment=TA_JUSTIFY, spaceAfter=5)
BODY_L = st('bodyl', spaceAfter=4)
SMALL = st('small', fontSize=7.6, leading=10, textColor=MUTED)
SMALL_J = st('smallj', fontSize=7.6, leading=10, textColor=MUTED, alignment=TA_JUSTIFY)
NOTE = st('note', fontSize=7.2, leading=9.4, textColor=MUTED, fontName='DMSans-Italic')
H1 = st('h1', fontName='Fraunces-Bold', fontSize=22, leading=26, textColor=INK, spaceAfter=4)
H2 = st('h2', fontName='Fraunces-SemiBold', fontSize=13.5, leading=17, textColor=INK, spaceBefore=8, spaceAfter=4)
H3 = st('h3', fontName='DMSans-Bold', fontSize=9.6, leading=12.5, textColor=INK, spaceBefore=6, spaceAfter=2)
KICK = st('kick', fontName='DMSans-Bold', fontSize=7.8, leading=10, textColor=GOLD_D)
LEAD = st('lead', fontName='Fraunces-Regular', fontSize=11.2, leading=15.6, textColor=INK2, spaceAfter=8)
BUL = st('bul', leftIndent=10, bulletIndent=0, spaceAfter=2.5, alignment=TA_LEFT)
TH = st('th', fontName='DMSans-Bold', fontSize=7.3, leading=9, textColor=colors.white)
TD = st('td', fontSize=7.4, leading=9.3)
TDB = st('tdb', fontName='DMSans-Bold', fontSize=7.4, leading=9.3, textColor=INK)
TDR = st('tdr', fontSize=7.4, leading=9.3, alignment=TA_RIGHT)
CAP = st('cap', fontName='DMSans-Bold', fontSize=8, leading=10.5, textColor=INK, spaceBefore=4, spaceAfter=2)
SRC = st('src', fontSize=6.8, leading=8.8, textColor=MUTED, spaceAfter=6)

def P(t, s=BODY): return Paragraph(t, s)

def bullets(items, style=BUL, sym='▪'):
    return [Paragraph(t, style, bulletText=sym) for t in items]

class Rule(Flowable):
    def __init__(self, w=CW, c=LINE, t=0.6, sb=2, sa=4):
        super().__init__(); self.w, self.c, self.t, self.sb, self.sa = w, c, t, sb, sa
    def wrap(self, *a): return self.w, self.t + self.sb + self.sa
    def draw(self):
        self.canv.setStrokeColor(self.c); self.canv.setLineWidth(self.t); self.canv.line(0, self.sa, self.w, self.sa)

class ChapterHead(Flowable):
    """Bandeau d'ouverture de chapitre : numéro doré + titre + chapeau."""
    def __init__(self, num, title, toc_title=None):
        super().__init__(); self.num, self.title = num, title; self.toc_title = toc_title or title
    def wrap(self, aw, ah):
        self.aw = aw; return aw, 23 * mm
    def draw(self):
        c = self.canv
        c.setFillColor(GOLD); c.rect(0, 20 * mm, 14 * mm, 1.6, fill=1, stroke=0)
        c.setFont('DMSans-Bold', 8); c.setFillColor(GOLD_D); c.drawString(0, 15.5 * mm, 'SYNTHÈSE' if self.num is None else ('ANNEXE' if str(self.num).startswith('A') else f'CHAPITRE {self.num}'))
        c.setFont('Fraunces-Bold', 21); c.setFillColor(INK); c.drawString(0, 6 * mm, self.title)

def chapter(num, title, key=None):
    ch = ChapterHead(num, title)
    ch._bookmark = key or title
    ch._toclevel = 0
    ch._toctext = (f'{num}. ' if num and not str(num).startswith('A') else '') + title
    return ch

def h2(t, key=None):
    p = Paragraph(t, H2); p._toclevel = 1; p._toctext = t; p._bookmark = key or t
    return p

def table(data, colw, header=True, zebra=True, align_right_from=None, font=7.4, hdr_bg=INK, extra=None, rowh=None):
    rows = []
    for i, r in enumerate(data):
        row = []
        for j, cell in enumerate(r):
            if isinstance(cell, (Paragraph, Image, Table)) or hasattr(cell, 'wrap'):
                row.append(cell); continue
            txt = '' if cell is None else str(cell)
            if i == 0 and header: row.append(Paragraph(txt, TH))
            elif align_right_from is not None and j >= align_right_from: row.append(Paragraph(txt, TDR))
            else: row.append(Paragraph(txt, TD))
        rows.append(row)
    t = Table(rows, colWidths=colw, repeatRows=1 if header else 0, rowHeights=rowh)
    ts = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
          ('LINEBELOW', (0, 0), (-1, -1), 0.35, LINE)]
    if header: ts += [('BACKGROUND', (0, 0), (-1, 0), hdr_bg), ('LINEBELOW', (0, 0), (-1, 0), 0, hdr_bg)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0: ts.append(('BACKGROUND', (0, i), (-1, i), ZEBRA))
    if extra: ts += extra
    t.setStyle(TableStyle(ts))
    return t

def callout(title, body_items, bg=GOLD_L, bar=GOLD, width=CW, title_color=GOLD_D):
    inner = [Paragraph(title, st('ct', fontName='DMSans-Bold', fontSize=8.4, leading=11, textColor=title_color, spaceAfter=3))]
    for b in body_items:
        inner.append(b if not isinstance(b, str) else Paragraph(b, st('cb', fontSize=8.3, leading=11.6, spaceAfter=2.5)))
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg), ('LINEBEFORE', (0, 0), (0, -1), 2.2, bar),
                           ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                           ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    return t

def kpis(items, cols=4, width=CW, bg=colors.white):
    """items: list of (valeur, libellé, source)."""
    cw = width / cols
    cells = []
    for v, l, s in items:
        cells.append([Paragraph(v, st('kv', fontName='Fraunces-Bold', fontSize=17, leading=20, textColor=INK)),
                      Paragraph(l, st('kl', fontSize=7.6, leading=9.8, textColor=INK2)),
                      Paragraph(s, st('ks', fontSize=6.3, leading=8, textColor=MUTED))])
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    for r in rows:
        while len(r) < cols: r.append('')
    t = Table(rows, colWidths=[cw] * cols)
    ts = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
          ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 7), ('BACKGROUND', (0, 0), (-1, -1), bg)]
    for i in range(len(rows)):
        for j in range(cols):
            ts.append(('LINEABOVE', (j, i), (j, i), 1.6, GOLD if (i + j) % 2 == 0 else INK))
    t.setStyle(TableStyle(ts))
    return t

def img(path, width=CW, maxh=None):
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(path); iw, ih = ir.getSize()
    h = width * ih / iw
    if maxh and h > maxh:
        h = maxh; width = h * iw / ih
    return Image(path, width=width, height=h)

def figure(path, caption, source, width=CW, maxh=None):
    return KeepTogether([Paragraph(caption, CAP), img(path, width, maxh), Paragraph(source, SRC)])

EDITION = 'Édition T3 2026 · septembre 2026'
RUNNING = 'ZLECAf · Rapport Chimie, Cosmétiques & Hygiène'

def draw_page(c, doc):
    c.saveState()
    c.setFillColor(GOLD); c.rect(ML, H - 13 * mm, 6 * mm, 1.2, fill=1, stroke=0)
    c.setFont('DMSans-Bold', 7); c.setFillColor(INK); c.drawString(ML + 8 * mm, H - 13.6 * mm, RUNNING.upper())
    c.setFont('DMSans-Regular', 7); c.setFillColor(MUTED); c.drawRightString(W - MR, H - 13.6 * mm, EDITION)
    c.setStrokeColor(LINE); c.setLineWidth(0.4); c.line(ML, 13 * mm, W - MR, 13 * mm)
    c.setFont('DMSans-Regular', 6.6); c.setFillColor(MUTED)
    c.drawString(ML, 9 * mm, 'Sources : SaaS ZLECAf + sources publiques citées · Document d\'analyse, sans valeur d\'avis juridique ou douanier')
    c.setFont('DMSans-Bold', 8); c.setFillColor(INK); c.drawRightString(W - MR, 9 * mm, str(doc.page))
    c.restoreState()

class ReportDoc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                         title='Rapport Industrie chimique, Cosmétiques & Hygiène — ZLECAf', author='ZLECAf Trade Intelligence',
                         subject='Chimie de base, engrais, plastiques, cosmétiques, hygiène corporelle et des surfaces : tarifs, origine, opportunités', **kw)
        fr = Frame(ML, MB, CW, H - MT - MB, id='f', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        full = Frame(0, 0, W, H, id='full', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate('cover', [full], onPage=lambda c, d: None),
                               PageTemplate('normal', [fr], onPage=draw_page)])
    def afterFlowable(self, fl):
        lvl = getattr(fl, '_toclevel', None)
        if lvl is not None:
            key = f'bm{id(fl)}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(fl._toctext, key, level=lvl, closed=True)
            if not getattr(fl, '_notoc', False):
                self.notify('TOCEntry', (lvl, fl._toctext, self.page, key))
