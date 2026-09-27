import sys, os; sys.path.insert(0,os.environ['RG_DIR'])
from layout import *
from cover import Cover
from ch_front import about_page, toc_page, exec_summary, ch_recos, ch_method
from ch_context import ch_context, ch_legal
from ch_tariffs import ch_tariffs, ch_offers, ch_roo
from fiches_content import ch_fiches
from ch_targets import ch_targets
from ch_logistics import ch_logistics
from ch_annex import ch_annex_countries
from pays_focus import chapitre as ch_focus
from ch_front import ch_lexique
out = sys.argv[1] if len(sys.argv) > 1 else S + 'rapport.pdf'
story = [Cover(), NextPageTemplate('normal'), PageBreak()]
story += about_page() + toc_page() + exec_summary()
for part in [ch_context(), ch_legal(), ch_tariffs(), ch_offers(), ch_roo()]:
    story += part + [PageBreak()]
story += ch_fiches()
story += ch_targets() + [PageBreak()]
story += ch_logistics() + [PageBreak()]
story += ch_focus(9, 'saas_stats.json') + [PageBreak()]
story += ch_recos()
story += ch_annex_countries() + [PageBreak()]
story += ch_method() + [PageBreak()] + ch_lexique()
doc = ReportDoc(out)
doc.multiBuild(story)
print('pages', doc.page)
