import sys, os; sys.path.insert(0,os.environ['RG_DIR'])
from layout import *
import layout
from cover import Cover
from ch_front import about_page, toc_page, exec_summary, ch_recos, ch_method
from ch_context import ch_context, ch_legal
from ch_tariffs import ch_tariffs, ch_offers, ch_roo
from fiches_content import ch_fiches
from ch_logistics import ch_logistics
from ch_annex import ch_annex_countries
from pays_focus import chapitre as ch_focus
from ch_front import ch_lexique
out = sys.argv[1] if len(sys.argv) > 1 else S + 'rapport.pdf'
ED = os.environ.get('RG_EDITION')
pb = [PageBreak()]
if not ED:
    from ch_targets import ch_targets
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
else:
    # Plans d'action par profil : les numéros passés ici sont des identifiants, renumeroter() numérote dans l'ordre.
    from editions import EDITIONS, CoverEdition, renumeroter
    from ch_plans import (FILIERES, about_edition, synthese, ch_cibles, ch_froid, ch_couts, ch_formalites,
                          ch_intrants_marche, ch_intrants_regimes, ch_intrants_besoins, ch_feuille)
    from ch_verif import methode_verif
    layout.RUNNING = EDITIONS[ED]['running']
    story = [CoverEdition(ED), NextPageTemplate('normal'), PageBreak()] + about_edition(ED) + toc_page() + synthese(ED)
    commun = ch_context() + pb + ch_legal() + pb
    focus = ch_focus(9, 'saas_stats.json') + pb
    if ED == 'producteurs':
        story += commun + ch_tariffs() + pb + ch_roo() + pb + ch_fiches(FILIERES[ED], verif=True) + ch_cibles(ED, 7) + pb + ch_froid(112) + pb + focus
    elif ED == 'industriels':
        story += commun + ch_tariffs() + pb + ch_roo() + pb + ch_fiches(FILIERES[ED], verif=True) + ch_cibles(ED, 7) + pb + ch_couts(113) + pb + focus
    elif ED == 'negoce':
        story += commun + ch_tariffs() + pb + ch_offers() + pb + ch_roo() + pb + ch_cibles(ED, 7) + pb + ch_formalites(114) + pb + ch_logistics() + pb + focus
    elif ED == 'intrants':
        story += commun + ch_intrants_marche(115) + pb + ch_intrants_regimes(116) + pb + ch_intrants_besoins(117) + pb + ch_cibles(ED, 7) + pb + focus
    else:
        raise SystemExit(f'édition inconnue : {ED} (producteurs, industriels, negoce, intrants)')
    story += ch_feuille(ED, 10) + pb
    if ED == 'negoce':
        story += ch_annex_countries() + pb
    m = ch_method(edition=True)
    story += m[:1] + [methode_verif()] + m[1:] + pb + ch_lexique()
    story = renumeroter(story)
doc = ReportDoc(out)
if ED:
    doc.title = f"Plan d'action {EDITIONS[ED]['num']} — {' '.join(EDITIONS[ED]['titre'])} — ZLECAf"
doc.multiBuild(story)
print('pages', doc.page)
