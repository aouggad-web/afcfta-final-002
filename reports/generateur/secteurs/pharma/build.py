import sys, os; sys.path.insert(0, os.environ['RG_DIR'])
from layout import *
from cover import Cover
from ch_front import about_page, toc_page, exec_summary
from ch_context import ch_market, ch_legal
from ch_tariffs import ch_tariffs, ch_offers, ch_roo
from ch_segments import ch_segments
from ch_mauritius import ch_mauritius
from pays_focus import chapitre as ch_focus
from ch_politique import ch_politique
from ch_annex import ch_annex_countries
from ch_back import ch_method, ch_lexique, ch_recos
out = sys.argv[1] if len(sys.argv) > 1 else S + 'rapport.pdf'
story = [Cover(), NextPageTemplate('normal'), PageBreak()]
story += about_page() + toc_page() + exec_summary()
story += ch_market() + ch_legal() + [PageBreak()]
story += ch_tariffs() + ch_offers() + ch_roo() + ch_segments() + [PageBreak()]
story += ch_mauritius() + [PageBreak()] + ch_focus(8, 'saas_pharma.json', 'served.json') + [PageBreak()] + ch_politique() + [PageBreak()] + ch_recos() + [PageBreak()]
story += ch_annex_countries() + [PageBreak()] + ch_method() + [PageBreak()] + ch_lexique()
doc = ReportDoc(out); doc.multiBuild(story); print('pages', doc.page)
