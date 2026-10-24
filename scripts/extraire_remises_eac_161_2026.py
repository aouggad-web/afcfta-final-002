"""Remises de droits de la Legal Notice EAC/161/2026 (Table A, EAC Gazette
Vol. AT 1 No. 16 du 30/06/2026, p. 67-82), une mesure par code et par État,
pour data/eac/legal_overrides.json.

La grille SPEC est relue ligne par ligne sur le texte du PDF déposé
(data/sources/eac/official/EAC_Vol_AT_1_No_16_2026-06-30.pdf) :
(ligne, États, codes, taux, désignation, texte de la remise). Le taux est un
nombre, ou {taux du TEC: taux de remise} quand la ligne en donne plusieurs
(« from 25% to 10% and 10% to 0% ») : il est rattaché à chaque code par le
taux du TEC servi au socle, ou, sur une ligne modifiée par un sursis de
l'EAC/160/2026, par le taux du TEC que cite le sursis ou que sert un autre État.
Un code à 4 ou 6 chiffres vaut pour toute la position ou sous-position.

    python3 scripts/extraire_remises_eac_161_2026.py <sortie.json>
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = ("https://www.eac.int/documents?controller=download&file=a3c7fa5a-b765-48ed-befa-b6b65bf5b3cc"
       "&name=EAC+Vol.+AT+1+NO.+16+JUNE+2026.pdf.pdf&task=download.file")
SHA = "555b8fdd7cc817ae5f729762913c5f8205e503a28170bad86a8a0f66e4c93907"

U, R, T, B, K = "UGA", "RWA", "TZA", "BDI", "KEN"
M2 = {25: 10, 10: 0}
SPEC = [
 (2, [U], "85393100 85395100 85395200", 0, "Unassembled LED, CFL bulbs",
  "Uganda granted a remission of duty to apply a duty rate of 0% for assembly of LED, CFL bulbs for one year"),
 (5, [U], "85182100 85182200 85182900", 0, "Unassembled speakers (CKD)",
  "Uganda granted a remission of duty to apply a duty rate of 0% for the manufacture of speakers for one year"),
 (7, [U], "85287210 85287310", 0, "Unassembled Television (CKD)",
  "Uganda granted a remission of duty to apply a duty rate of 0% for the manufacture of Television for one year"),
 (9, [U], "48062000 48043900", 0, "Greaseproof papers; and Other, Other kraft paper and paperboard",
  "Uganda granted a remission of duty to apply a duty rate of 0% on materials for the manufacture of packaging materials for one year"),
 (10, [U], "38159000", 0, "Inputs for the manufacture of foam and spring mattresses",
  "Uganda granted a remission of duty from 10% to apply a duty rate of 0% for the manufacture of foam and spring mattresses for one year"),
 (11, [U], "73209000 54083300 55134900 54083400", 10, "Inputs for the manufacture of foam and spring mattresses; Jacquard Material for Making Spring mattresses",
  "Uganda granted a remission of duty from 35% and 25% to apply a duty rate of 10% for the manufacture of foam and spring mattresses for one year"),
 (12, [U], "84819000", 0, "Valves and their corresponding component parts used for the manufacture of motorcycle tubes",
  "Uganda granted a remission of duty to apply a duty rate of 0% on inputs for the manufacture of motorcycle inner tubes for one year"),
 (13, [U], "48041100", 0, "Unbleached Kraft Liner in rolls or sheets",
  "Uganda corrugated box manufacturers granted a remission of duty to apply a duty rate of 0% for one year"),
 (14, [U], "76052100", 0, "Aluminium wire, not alloyed, maximum cross-sectional dimension exceeding 7 mm",
  "Uganda cable manufacturers granted a remission of duty to apply a duty rate of 0% for one year"),
 (15, [U], "39202010", 0, "Other unprinted plates, sheets, film, foil and strip, of polymers of propylene",
  "Uganda granted a remission of duty to apply a duty rate of 0% for the label printing sector for one year"),
 ("16-19", [U], "85164000 85211000 85219000 85094000 85161000", 0, "Unassembled flat irons, DVD players, blenders and hot water kettles",
  "Uganda granted a remission of duty to apply a duty rate of 0% for assembly of flat irons, DVD players, blenders and hot water kettles for one year"),
 (20, [U], "84145100", 10, "Unassembled floor, table and wall fans",
  "Uganda granted a remission of duty to apply a duty rate of 10% for assembly of unassembled floor table and wall fans for one year"),
 (21, [U], "85166000 76152000 73239300", 0, "Unassembled Cookers",
  "Uganda granted a remission of duty to apply a duty rate of 0% for assembly of cookers for one year"),
 (22, [U], "70052900 39209110 73121000", 0, "Other non-wired glass; plates, sheets, film of poly vinyl butyral; stranded wire, ropes and cable",
  "Uganda granted a remission of duty to apply a duty rate of 0% for manufacture of toughened and laminated glass for one year"),
 ("23(a)", [U], "25010010", 0, "Inputs for the manufacture of edible salt of sub heading 2501.00.90",
  "(a) Uganda granted a remission of duty to apply a duty rate of 0% for one year"),
 ("23(b)", [B], "25010010", 10, "Inputs for the manufacture of edible salt of sub heading 2501.00.90",
  "(b) Burundi granted a remission of duty to apply a duty rate of 10% for one year"),
 (25, [U], "73269090", 0, "Umbrella heads for roofing nails",
  "Uganda granted a remission of duty to apply a duty rate of 0% for the manufacture of roofing nails for one year"),
 (29, [U], "34024900", 0, "Organic surface active agents (Betaine 45, Softening Agent)",
  "Uganda granted a remission of duty to apply a duty rate of 0% to manufacturers in the chemical and allied industries, leather and skin processing, textile processing and mattress manufacturers for one year"),
 (30, [U], "32089090 76061200", 10, "Other paints and varnishes; aluminium plates, sheets and strips of aluminium alloy",
  "Uganda granted a remission of duty on aluminium decorative panels to apply a duty rate of 10% for one year"),
 (31, [U], "39232900", 10, "Of other plastics",
  "Uganda granted a remission of duty to apply a duty rate of 10% for one year"),
 (32, [U], "68138100 87083000 35069900", 0, "Brake linings and pads; brakes and servo-brakes, parts; other adhesive glues",
  "Uganda granted a remission of duty to apply a duty rate of 0% for manufacture of motorcycle brake shoes for one year"),
 (33, [U], "72104900", 0, "Other zinc coated coils",
  "Uganda granted a remission of duty to apply a duty rate of 0% on galvanized coils of a thickness of 2.5 mm and above for one year"),
 (34, [U], "33021000", 0, "Odoriferous mixtures of a kind used as raw materials in the food industries",
  "Uganda granted a remission of duty to apply a duty rate of 0% for one year"),
 (35, [T], "480419 48043900 48045200", 0, "Paper products used to manufacture corrugated boxes (4804.19.00 publié, subdivisé au TEC 2022 en 4804.19.10 et 4804.19.90 : sous-position entière)",
  "Tanzania granted a remission of duty to apply a duty rate of 0% on specified paper products used by domestic manufacturers of corrugated boxes for one year"),
 (36, [T], "48052400 48052500", 10, "Paper products used to manufacture corrugated boxes",
  "Tanzania granted a remission of duty to apply a duty rate of 10% on specified paper products used by domestic manufacturers of corrugated boxes for one year"),
 ("37(a)", [T], "10019910 10019990", 10, "Hard wheat; other",
  "(a) Tanzania and Kenya granted a remission of duty to apply a duty rate of 10% instead of 35% for one year"),
 ("37(b)", [B, R], "10019910 10019990", 0, "Hard wheat; other",
  "(b) Burundi and Rwanda granted a remission of duty to apply a duty rate of 0% instead of 35% for one year"),
 (38, [T], "15119040", 0, "Palm Stearin, RBD",
  "Tanzania domestic manufacturers of soaps granted a remission of duty to apply a duty rate of 0% instead of 10% for one year"),
 (39, [T], "39235090 48192090 48193000 48195000 48219000 76071990", 0, "Packaging materials for yoghurt, powdered or UHT Milk",
  "Tanzania domestic manufacturers of dairy products granted a remission of duty to apply a duty rate of 0% on packaging materials for yoghurt, powdered or UHT Milk for one year"),
 (40, [R], "48195000", 0, "Other packing containers, including record sleeves",
  "Rwanda domestic manufacturers of UHT milk granted a remission of duty to apply a duty rate of 0% instead of 25% for one year"),
 (41, [T], "63051000 48194000 73102990 63053300 63052000 63049190 76071990", 0, "Packaging materials used by domestic producers of agricultural seeds",
  "Tanzania domestic producers of agricultural seeds granted a remission of duty to apply a duty rate of 0% for one year"),
 (42, [T], "73102100 63051000", 0, "Packaging materials for processed coffee",
  "Tanzania domestic processors of coffee granted remission of duty to apply a duty rate of 0% for one year"),
 (43, [B, U, R], "73102100 63051000 39235010 39235090 39203090", 0, "Packaging materials for processed coffee",
  "Burundi, Uganda and Rwanda domestic processors of coffee granted a remission of duty to apply a duty rate of 0% for one year"),
 ("44-45", [U], "48219000 39173900 68061000 72106100 72201200 73063000 73182300 39079900 73182200 40169900 48191000 72092700 72171000 73064000 73219000 85395200 85365000 73269090 84145900 73209000", 0,
  "Inputs and Raw Materials for use in the manufacture of Energy Saving Stoves",
  "Uganda granted a remission of duty to apply a duty rate of 0% on inputs for the manufacture of Energy Saving Stoves for one year"),
 (46, [T], "74091100 74091900 74101100 74101200 74092100 80011000 38109000", 0, "Copper and brass foils and strips in coils, tin ingots, radiator flux",
  "Tanzania granted a remission of duty to apply a duty rate of 0% for the manufacture of radiators for one year"),
 (47, [T, R, B, U], "34023100 34023900", 0, "Organic surface-active agents",
  "Tanzania, Rwanda, Burundi and Uganda granted a remission of duty to apply a duty rate of 0% for manufacturers of detergents and liquid soaps for one year"),
 (48, [T], "34024900", 0, "Organic surface-active agents",
  "Tanzania granted a remission of duty to apply a duty rate of 0% for manufacturers of detergents and liquid soaps for one year"),
 (49, [T], "73121000 72172000 74081900 74091100 76052100 27101956 38159000 54021900 59039000 79070000 27121000", 0, "Inputs used to manufacture electrical cables",
  "Tanzania granted a remission of duty to apply a duty rate of 0% on inputs used to manufacture electrical cables for one year"),
 (50, [R], "73121000 74081900 74091100 76052100 54021900 79070000", 0, "Inputs used to manufacture electrical cables",
  "Rwanda granted a remission of duty to apply a duty rate of 0% on inputs used to manufacture electrical cables for one year"),
 (51, [T, U], "34012010", 10, "Noodles for the manufacture of toilet soap",
  "Tanzania and Uganda granted a remission of duty to apply a duty rate of 10% for the manufacture of toilet soap for one year"),
 (52, [T], "87042190", 10, "CKD for Three-Wheel Motorcycle excluding Chassis and its components",
  "Tanzania granted a remission of duty on CKD for Three Wheel Motorcycle excluding Chassis and its components to apply a duty rate of 10% for assembly of Three Wheel Motorcycles for one year"),
 (53, [R], "54074400 39095000", 0, "Packaging materials for processed tea",
  "Rwanda granted a remission of duty to apply a duty rate of 0% for packaging tea for one year"),
 (54, [T], "48192090 54074400", 0, "Packaging materials for processed tea",
  "Tanzania granted a remission of duty to apply a duty rate of 0% for local manufacturers of tea (blenders) for one year"),
 (55, [T], "32082010 32082020 32089020 32100010", 0, "Raw material used in leather processing",
  "Tanzania granted a remission of duty to apply a duty rate of 0% on raw material used in leather processing for one year"),
 (56, [K, R, U], "39095000", 0, "Polyurethanes",
  "Kenya, Rwanda and Uganda granted a remission of duty to apply a duty rate of 0% on inputs and raw materials for manufacture leather and other footwear for one year"),
 (61, [U], "35052000 48042900", {35: 10, 10: 0}, "Glues based on starch; uncoated kraft paper and paperboard",
  "Uganda granted a remission of duty to apply a duty from 35% and 10% to apply a duty rate of 10% and 0% respectively for one year"),
 (62, [T], "48119000", 10, "Other paper, paper board, cellulose wadding and webs of cellulose fibres",
  "Tanzania granted a remission of duty to apply a duty rate of 10% on metalized paper used to manufacture labels, inputs used in manufacture of thermal paper rolls for cash registers, POS and EFD Machines for one year"),
 (63, [U], "34029000", 10, "Organic surface active agents (Super concentrate 8)",
  "Uganda granted a remission of duty from 25% to 10% for the manufacturers of industrial tube mill coolant for one year"),
 (64, [U], "32081020 32081090", 0, "Top coat colour primer",
  "Uganda granted a remission of duty from 35% to 0% for the manufacturers of pre painted coils and sheets for one year"),
 (65, [U], "40169200 76169900", 0, "Erasers of rubber / pencil rubber tip; other articles of aluminium / pencil ferrule",
  "Uganda granted a remission of duty from 25% and 10% to 0% for the manufacturers of school pencils for one year"),
 (66, [U], "76061100", 0, "Of aluminium, not alloyed (aluminium coils)",
  "Uganda granted a remission of duty from 10% to 0% to manufacturers of kitchenware for one year"),
 (67, [U], "32151900", 0, "Other printing ink",
  "Uganda granted a remission of duty from 10% to 0% on raw materials used in the manufacture of metal crown caps for one year"),
 (68, [U], "84818000 84819000 39201090 27075000 28170010 25191000 34039900", M2, "Inputs for the manufacture of tyres and tubes",
  "Uganda granted a remission of duty from 25% to 10% and 10% to 0% on inputs for the manufacture of tyres and tubes for one year"),
 (69, [U], "68052000 54041900 39211210 35069100 56029000 60011000", M2, "Inputs for the manufacture of construction sand paper and paint brushes",
  "Uganda granted a remission of duty from 25% to 10% and 10% to 0% on inputs for the manufacture of construction sand paper and paint brushes for one year"),
 (70, [U], "73269090", 0, "Other / Bristle metal strips",
  "Uganda granted a remission of duty on inputs for the manufacture of construction sand paper and paint brushes to apply a duty rate of 0% for one year"),
 ("71(a)", [U], "17019910", 25, "White refined sugar (for industrial use)",
  "(a) Uganda granted a remission of duty to apply a duty rate of 25% to Ugandan manufacturers for one year"),
 (72, [U], "38109000", 0, "Pickling preparations for metal surfaces",
  "Uganda granted a remission of duty from 10% to 0% on inputs for the manufacture of welding electrodes for one year"),
 (73, [U], "15162000 15131900 19019010 20071000 20079900", {35: 10, 25: 10, 10: 0}, "Raw materials and inputs for the manufacturers of chocolate",
  "Uganda granted a remission of duty from 35% and 25% to 10% and 10% to 0% on raw materials and inputs for the manufacturers of chocolate for one year"),
 (74, [U], "85079000", 0, "Parts / Battery separators",
  "Uganda granted a remission of duty from 10% to 0% on inputs for the manufacture of batteries for one year"),
 (75, [U], "21069020", 0, "Preparations of a kind used in manufacturing of beverages and food",
  "Uganda granted a remission of duty from 25% to 0% on preparations of a kind used in manufacturing of food and beverages for one year"),
 (76, [U], "56031100 96039000", 0, "Duster pad material, non woven fabric; other incomplete dusters",
  "Uganda granted a remission of duty from 25% and 10% to 0% on inputs for the manufacture of school exercise books and school dusters for one year"),
 (77, [U], "56029000 60011000 82023900 48191000", {35: 10, 25: 10, 10: 0}, "Paint roller fabric, accessories and paint brush materials",
  "Uganda granted a remission of duty from 35% and 25% to 10% and 10% to 0% on raw materials and inputs for the manufacturers of paint and roller brushes for one year"),
 (78, [U], "73079200 73079300 73079900 73079100 84818000", M2, "Pipe fittings and valves for specialized PPR pipes",
  "Uganda granted a remission of duty from 25% to 10% and 10% to 0% on raw materials and inputs for the manufacturers of specialized PPR pipes for one year"),
 (81, [U], "76071100", 0, "Aluminium foil, jumbo roll, rolled but not further worked",
  "Uganda granted a remission of duty at 0% on raw materials used in the manufacture of aluminium foil packs for one year"),
 (82, [T, B], "85076000", 0, "Lithium ion electric accumulators",
  "Tanzania and Burundi granted a remission of duty at 0% on Lithium ion Electric accumulators used in the assembly and manufacture of electric motor vehicles and motorcycles for one year"),
 (83, [T], "32151900 34039900 35069100 38180000 39079900 39169000 39173900 39199090 39206990 39209990 39211490 39219090 54021100 54049000 70199090 85369000 85444900", 0,
  "Inputs and raw materials used to manufacture optical fiber cables",
  "Tanzania granted a remission of duty at 0% on inputs and raw materials used in the manufacture optical fiber cables for one year"),
 (84, [K], "25174900 72106100", 0, "Geobitec stone chips; alu-zinc coated steel coils",
  "Kenya granted a remission of duty to apply a duty rate of 0% on inputs for the manufacture of roofing tiles coated with acrylic paint and the weather side coated with natural sand granules for one year"),
 (85, [R], "35052000", 0, "Glues based on starch",
  "Rwanda granted a remission of duty at 0% on glues based on starch used in the manufacture of goods for one year"),
 (86, [R], "35069900", 0, "Other glues",
  "Rwanda granted a remission of duty at 0% on other glues used in the manufacture of goods for one year"),
 (87, [R], "4107", 0, "Leather further prepared after tanning or crusting, of bovine (including buffalo) or equine",
  "Rwanda granted a remission of duty at 0% on leather further prepared after tanning or crusting, including parchment dressed leather of bovine (including buffalo) or equine for one year"),
 (88, [R], "41120000", 0, "Leather further prepared after tanning",
  "Rwanda granted a remission of duty at 0% on leather further prepared after tanning for one year"),
 (89, [R], "4113", 0, "Leather further prepared after tanning or crusting, of other animals",
  "Rwanda granted a remission of duty at 0% on leather further prepared after tanning or crusting, including parchment dressed leather of other animals, without wool or hair on, whether or not split, other than leather of heading 41.14 for one year"),
 (90, [T], "27132000 56031400 27101959 39201010", 0, "Petroleum bitumen, polyester nonwoven, rubber oil, PE with silicone oil film",
  "Tanzania granted a remission of duty to apply 0% instead of 10% on raw materials used in production of the waterproofing membranes for one year"),
 (91, [T], "68029900", 10, "Colored sand",
  "Tanzania granted a remission of duty to apply 10% instead of 35% on raw materials used in production of the waterproofing membranes for one year"),
 (92, [U], "73069000 73084000", 0, "Scaffolding pipes, cup lock systems, prop jacks, U jacks, base jacks",
  "Uganda granted a remission of duty from 25% to 0% for raw materials for the manufacture of modular scaffolding for one year"),
 (93, [U], "39092000", 0, "Melamine resins / powder",
  "Uganda granted a remission of duty from 10% to 0% for raw materials for the manufacture of table and kitchenware for one year"),
 (94, [U], "72104900", 0, "Other zinc coated coils",
  "Uganda granted a remission of duty from 25% to apply a duty rate of 0% on decking sheets used in the construction of suspended floor for one year"),
 (95, [U], "39204900", 10, "Poly Chloride (PVC) Sheets (25%)", "Uganda granted a remission of duty from 35% to 25%, 25% to 10%, 10% to 0% on raw materials for the manufacture of pharma grade packaging for medicine tablets and capsules, medicine inserts for the pharmaceutical industry for one year"),
 (96, [U], "76071910", 0, "Unprinted aluminium foil (10%)", "Uganda granted a remission of duty from 35% to 25%, 25% to 10%, 10% to 0% on raw materials for the manufacture of pharma grade packaging for medicine tablets and capsules, medicine inserts for the pharmaceutical industry for one year"),
 (97, [U], "48191000", 25, "Folding cartons, boxes and cases, of non-corrugated paper or paperboard (35%)", "Uganda granted a remission of duty from 35% to 25%, 25% to 10%, 10% to 0% on raw materials for the manufacture of pharma grade packaging for medicine tablets and capsules, medicine inserts for the pharmaceutical industry for one year"),
 (98, [U], "72201100 72201200 72202000 72209000", 0, "Flat-rolled products of stainless steel, of a width of less than 600 mm",
  "Uganda granted a remission of duty from 10% to 0% on raw materials and inputs for the manufacture of stainless steel pipes for one year"),
 (99, [U], "48101300 48101900", 0, "Paper and paperboard, in rolls and sheets",
  "Uganda granted a remission of duty from 10% to 0% on raw materials for the manufacture of beer labels and cigarette packaging for one year"),
 (100, [U], "32100091 32082090", 0, "Lacquers; other (varnish)",
  "Uganda granted a remission of duty from 35% to 0% on raw materials and inputs for manufacturing of metallic labels for one year"),
 (107, [R], "24011000 24012000 48139000 48193000 48219000", 0, "Inputs used to manufacture cigarettes",
  "Rwanda granted a remission of duty to apply a duty rate of 0% for inputs for the manufacture cigarettes for one year"),
 (108, [U], "32151100 32151900", 10, "Printing ink",
  "Uganda granted a remission of duty from 25% to 10% for manufacturers of labels using Ultra Violet (UV) inks and metallic inks for one year"),
 (111, [U], "3907", 0, "Polyacetals, other polyether and epoxide resins, polycarbonates, alkyd resins, polyallyl esters and other polyesters, in primary forms",
  "Uganda granted a remission of duty to apply a duty rate of 0% in the food and beverage sector, chemical and allied industries and plastic and foam sectors for one year"),
 (112, [R], "34029000 35069100 39172900 39269090 40169900 68042100 72210000 72288000 73181100 73181300 73181500 73181600 73182100 73182200 73182900 73209000 73269090 76169900 82029900 83099090 84313900 84314900 84818000 84828000 84829900 84833000 85439000", 0,
  "Inputs for the manufacture of granite tiles and slabs",
  "Rwanda granted a remission of duty on inputs for the manufacture of granite tiles and slabs to apply a duty rate of 0% for one year"),
 (115, [U], "72171000 56074100 39269090 54041900 55091100 40161000", 0, "Inputs for the manufacture of synthetic brooms",
  "Uganda granted a remission of duty on inputs for the manufacture of synthetic brooms to apply a duty rate of 0% for one year"),
 (116, [U], "55122900", 10, "Printed mattress covers",
  "Uganda granted a remission of duty on raw materials and inputs for the manufacture of foam and spring mattresses from 25% to apply a duty rate of 10% for one year"),
 (117, [U], "8301 8423", 0, "Unassembled lock sets and weighing scales",
  "Uganda granted a remission of duty on specified raw materials and inputs for assembly of lock sets and weighing scales to apply a duty rate of 0% for one year"),
 (118, [U], "72123000", 0, "Galvanized slit coils",
  "Uganda granted a remission of duty on galvanized slit coils of a thickness of 1.8 mm to 4 mm for the manufacture of galvanized iron and steel pipes to apply a duty rate of 0% for one year"),
 (119, [T], "35069100 39201010", 0, "Raw materials for the manufacture of packaging",
  "Tanzania granted a remission of duty on specified raw materials and inputs for manufacture of packaging to apply a duty rate of 0% for one year"),
 (120, [T], "32100099", 10, "Outdoor pure polyester powder coating",
  "Tanzania granted a remission of duty on outdoor pure polyester powder coating used by manufacturers of aluminium products to apply a duty rate of 10% for one year"),
 (126, [R], "22071000", 10, "Undenatured ethyl alcohol of an alcoholic strength by volume of 80% vol or higher",
  "Rwanda granted a remission of duty to apply a duty rate of 10% for manufacture of spirits, liqueurs and other spirituous beverages for one year"),
 (127, [B], "87116000 870380 87046090", 0, "Vehicles, motorcycles and tricycles with electric motor for propulsion or hybrid (8703.80.90 publié, absent du tarif servi au Burundi, qui porte 8703.80.00 : sous-position entière)",
  "Burundi granted a remission of duty to apply a duty rate of 0% for the assembly of electric mobility motorcyles for one year"),
 (129, [U], "480419", 0, "Uncoated kraft paper and paperboard (4804.19.00 publié, subdivisé au TEC 2022 en 4804.19.10 à 0 % et 4804.19.90 à 10 % : 0 % pour les deux)",
  "Uganda granted a duty remission to apply a duty rate of 10% for 25% and 35% and 0% for 10% for manufacturers of surgical and examination medical gloves for one year"),
 (129, [U], "48236900 39206990 39219010 39219090 48211090", {25: 10, 35: 10, 10: 0},
  "Other paper, paperboard, plastic plates and film, paper labels",
  "Uganda granted a duty remission to apply a duty rate of 10% for 25% and 35% and 0% for 10% for manufacturers of surgical and examination medical gloves for one year"),
]

#: Lignes non intégrées, et pourquoi.
ECARTEES = {
    "1, 3, 4, 6, 57, 58, 59, 60, 79, 80, 110, 113, 114, 125, 128": "« Various » : aucun code SH publié dans la table",
    "24, 26, 27, 28": "listes d'intrants publiées par les Legal Notices EAC/163 à EAC/171/2026, relevées par scripts/extraire_remises_eac_162_173_2026.py",
    "8": "Mechanically Deboned Chicken Paste : aucun code SH publié",
    "71(b)": "traitement préférentiel des produits kényans et tanzaniens fabriqués avec du sucre à 10 %, pas une remise à l'importation",
    "130": "aucun État partenaire désigné (« Granted remission of duty to apply a duty rate of 10% »)",
    "37(a) Kenya, 101-106, 109, 121-124": "Kenya, déjà au fichier",
}


_socles = {}


def taux_tec(etat, code, repli=True):
    """Droit du TEC pour ce code (position à 8 chiffres), ou (None, raison)."""
    if etat not in _socles:
        with open(os.path.join(REPO, "backend", "socle", f"{etat}.json"), encoding="utf-8") as f:
            _socles[etat] = json.load(f)["positions"]
    pos = _socles[etat].get(code)
    if pos is None:
        return None, "absent du socle"
    dd = next((d for d in pos.get("droits") or [] if d.get("code") == "DD"), None)
    if dd is None or dd.get("taux") is None:
        return None, "droit du socle sans taux"
    if "EAC/160" in (dd.get("source") or "") + (dd.get("note") or ""):
        cite = re.search(r"EAC CET rate of (\d+(?:\.\d+)?)%", dd.get("note") or "")
        if cite:
            return float(cite.group(1)), None
        for autre in ("TZA", "RWA", "BDI", "KEN", "UGA") if repli else ():
            if autre != etat:
                tec, _ = taux_tec(autre, code, repli=False)
                if tec is not None:
                    return tec, None
        return None, "droit du socle modifié par l'EAC/160/2026"
    return dd["taux"], None


def mesures_161():
    mesures = []
    for row, etats, codes, taux, desc, rem in SPEC:
        for etat in etats:
            for code in codes.split():
                note = None
                taux_m = taux
                if isinstance(taux, dict):
                    tec, raison = (None, "position à 4 ou 6 chiffres") if len(code) < 8 else taux_tec(etat, code)
                    if tec is None:
                        taux_m, note = None, f"taux du TEC non lu ({raison})"
                    elif tec in taux:
                        taux_m = taux[tec]
                    else:
                        taux_m, note = None, f"TEC à {tec:g} %, absent de la ligne"
                ref = str(row)
                mesures.append({
                    "measure_id": f"EAC-161-2026-REMISSION-{code}-{etat}-R{re.sub(r'[^0-9a-z]', '', ref)}",
                    "jurisdiction": etat,
                    "measure_type": "DUTY_REMISSION",
                    "legal_title": "Approved Duty Remission on Raw Materials and Industrial Inputs for the Manufacture of Goods",
                    "gazette_number": "EAC Gazette Vol. AT 1 No. 16; Legal Notice EAC/161/2026",
                    "gazette_date": "2026-06-30",
                    "legal_reference": f"Legal Notice EAC/161/2026, Table A, row {ref}",
                    "publication_url": URL,
                    "source_hash": SHA,
                    "effective_from": "2026-07-01",
                    "effective_to": "2027-06-30",
                    "hs_code_from": code,
                    "hs_code_to": code,
                    "hs_version": "HS2022",
                    "product_description": desc,
                    "base_rate": None,
                    "override_rate": taux_m,
                    "rate_unit": "%",
                    "beneficiary": "MANUFACTURER",
                    "origin_scope": "ALL",
                    "import_purpose": None,
                    "quantity_limit": None,
                    "condition_text": rem + (f" — {note} : taux de remise non servi." if note else ""),
                    "verification_status": "VERIFIED_OFFICIAL_EXTRACT",
                    "requires_human_review": False,
                })
    return mesures


if __name__ == "__main__":
    resultat = mesures_161()
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)
    print(len(resultat), "mesures, dont", sum(m["override_rate"] is None for m in resultat), "sans taux")
