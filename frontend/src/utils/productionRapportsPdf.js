/**
 * Rapports PDF du module Production : valeur ajoutée macro, agriculture,
 * mines et débouchés.
 *
 * Même bâtisseur que les autres modules (utils/opportunityPdf.js) : bandeau
 * avec le logo du site, cartes, tableaux, pied paginé. Chaque rapport reprend
 * la réponse de l'API telle que l'écran l'affiche — tous les sous-onglets, pas
 * seulement celui qui est ouvert —, chaque chiffre avec son année et sa source,
 * et un court paragraphe qui explique ce qu'on lit. Une valeur que la source
 * ne publie pas s'écrit « non publié », jamais 0.
 *
 * Les libellés de données (cultures, minéraux, unités) restent dans la langue
 * de la source ; en arabe ils passent par le dictionnaire des données.
 */
import { montantCompact, nombre, estAnglais } from './nombres';
import { AFRICAN_COUNTRIES } from './countryCodes';
import { getRegionName } from './translations';
import { trDonnee } from '../i18n/donnees';

const T = {
  fr: {
    module: 'MODULE PRODUCTION',
    na: 'non publié',
    iso: (c) => `code ISO ${c}`,
    warning: 'Avertissement',
    warningText: (sources) => [
      `Chiffres repris des sources publiques citées (${sources}), à l'année indiquée pour chacun. Les sources révisent leurs séries : vérifier la dernière publication avant une décision.`,
      "Ce rapport est une synthèse d'information économique : il ne constitue pas un conseil en investissement.",
    ],
    cols: { year: 'Année', source: 'Source', unit: 'Unité', rank: 'Rang en Afrique' },
    rankAfrica: (r) => `rang ${r} en Afrique`,

    macro: {
      badge: 'VALEUR AJOUTÉE MACRO',
      title: (n) => `Valeur ajoutée par secteur — ${n}`,
      subtitle: (y, c) => `Banque mondiale, World Development Indicators · ${y} · code ISO ${c}`,
      sectors: {
        A: 'Agriculture, sylviculture et pêche (A)',
        'B-F': 'Industrie, construction comprise (B-F)',
        C: 'dont industrie manufacturière (C)',
        'G-T': 'Services (G-T)',
        TOTAL: 'PIB',
      },
      short: { A: 'Agriculture (A)', 'B-F': 'Industrie (B-F)', C: 'Manufacturier (C)', 'G-T': 'Services (G-T)', TOTAL: 'PIB' },
      shareSub: (y) => `% du PIB, ${y}`,
      growth: 'Croissance du PIB',
      gdpUsd: 'PIB (dollars courants)',
      shareTitle: 'Valeur ajoutée par secteur (% du PIB), année par année',
      shareText: [
        "Valeur ajoutée : ce qu'un secteur produit, moins ce qu'il consomme pour produire (matières, énergie, services achetés). La somme des valeurs ajoutées de tous les secteurs, plus les impôts sur les produits moins les subventions, donne le PIB.",
        "% du PIB : poids du secteur dans l'économie la même année. Les parts ne totalisent pas 100 % : les impôts nets sur les produits n'appartiennent à aucun secteur, et le manufacturier (C) est déjà compris dans l'industrie (B-F).",
        'Secteurs selon la nomenclature CITI/ISIC rév. 4 : A = agriculture, sylviculture et pêche ; B-F = industrie (mines et carrières, manufacturier, électricité, gaz et eau, construction) ; C = industrie manufacturière seule ; G-T = services (commerce, transport, hébergement, finance, administration, éducation, santé…).',
      ],
      usdTitle: 'Valeur ajoutée par secteur en dollars courants',
      usdText: "Une part de PIB situe un secteur dans son économie ; elle ne dit pas sa taille. Ces montants sont publiés séparément, en dollars courants (convertis au taux de change de chaque année, sans correction de l'inflation) : ils ne se comparent pas aux pourcentages ci-dessus.",
      usdNone: 'La Banque mondiale ne publie pas ces montants pour ce pays.',
      growthTitle: 'Croissance du PIB (% annuel)',
      growthCol: 'Croissance réelle du PIB',
      growthText: "Variation du PIB en volume (prix constants) d'une année sur l'autre : c'est une évolution, pas une part du PIB, d'où un tableau séparé. Une valeur négative signale une contraction de l'économie.",
      growthNone: 'La Banque mondiale ne publie pas la croissance du PIB pour ce pays.',
      seriesTitle: 'Séries utilisées',
      seriesText: (ans) => `Source : Banque mondiale, World Development Indicators (WDI), séries de valeur ajoutée ; années couvertes : ${ans}. Les codes ci-dessous se consultent sur data.worldbank.org.`,
      seriesCols: { series: 'Série', pct: 'Code (% du PIB ou %)', usd: 'Code (dollars courants)' },
      proj: 'projection',
      projNote: '« projection » : valeur prévue par le FMI (Perspectives de l’économie mondiale), pas encore observée.',
      sources: 'Banque mondiale, FMI',
      source: 'Banque mondiale — World Development Indicators',
      filename: 'Production_valeur_ajoutee',
    },

    agri: {
      badge: 'AGRICULTURE · FAOSTAT',
      title: (n) => `Production agricole — ${n}`,
      subtitle: (r, y, c) => `${r} · données ${y} · code ISO ${c}`,
      kCrops: 'Cultures suivies',
      kGdp: 'Agriculture, part du PIB',
      kEmploy: 'Emploi agricole',
      kArable: 'Terres arables',
      kIrrigated: 'Terres irriguées',
      kCapture: 'Pêche de capture',
      kAquaculture: 'Aquaculture',
      cropsTitle: 'Cultures : production, surface et rang',
      cropsCols: { product: 'Produit', production: 'Production', area: 'Surface récoltée' },
      cropsText: [
        "Production : quantité récoltée dans l'année, en tonnes (t). Surface : superficie récoltée, en hectares (ha). Rang en Afrique : place du pays parmi les producteurs africains du produit (1 = premier) ; « — » quand la source ne fournit pas de rang.",
        "Les premières lignes viennent de la fiche pays (FAOSTAT et sources nationales) ; les suivantes du fichier FAOSTAT Production (QCL), à l'année de la dernière récolte publiée. Le renvoi [1], [2]… de la colonne Source désigne la liste des sources ci-dessous.",
      ],
      noCrops: 'La source ne publie pas de données de cultures pour ce pays.',
      sourcesTitle: 'Sources',
      evoTitle: 'Évolution de la production des principales cultures (t)',
      evoCol: 'Culture',
      evoText: 'Production annuelle en tonnes, telle que la publie la fiche pays ; « non publié » signale une année sans chiffre.',
      indTitle: 'Indicateurs clés du secteur agricole',
      indText: "Part du PIB : valeur ajoutée agricole rapportée au PIB. Emploi agricole : part des actifs occupés qui travaillent dans l'agriculture. Terres arables : surfaces labourées ou cultivables ; terres irriguées : surfaces équipées pour l'irrigation, en hectares.",
      indSource: (y) => `fiche pays FAOSTAT ${y}`,
      livestockTitle: 'Élevage : cheptel',
      livestockCols: { species: 'Espèce', count: 'Effectif' },
      livestockText: "Effectif : nombre d'animaux vivants recensés dans l'année. Rang en Afrique : place du pays parmi les pays africains pour l'espèce.",
      noLivestock: "La source ne publie pas de données d'élevage pour ce pays.",
      animalTitle: 'Production animale',
      animalCols: { product: 'Produit', volume: 'Volume' },
      animalText: "Quantités produites dans l'année (viande en équivalent carcasse, lait, laine, œufs).",
      fishTitle: 'Pêche et aquaculture',
      fishText: "Pêche de capture : poissons et fruits de mer prélevés dans le milieu naturel (mer, lacs, fleuves). Aquaculture : élevage d'organismes aquatiques. Volumes en tonnes ; rang parmi les pays africains.",
      fishSource: 'FAO FishStat 2023 / Direction des Pêches',
      noFish: 'La source ne publie pas de données de pêche pour ce pays.',
      species: 'Espèces principales',
      ports: 'Principaux ports',
      projTitle: 'Perspectives de production (OCDE-FAO)',
      projCols: { aggregate: 'Agrégat', sector: 'Secteur', change: 'Évolution' },
      projText: "Prévisions de production par grand agrégat, tirées des Perspectives agricoles de l'OCDE et de la FAO 2024-2033 : ce sont des projections, pas des observations. Évolution : variation entre la première et la dernière année affichées.",
      sectorCrops: 'Cultures',
      sectorLivestock: 'Élevage',
      aggregates: { cereals: 'Céréales', oilseeds: 'Oléagineux', sugar: 'Sucre', meat: 'Viande', 'roots & tubers': 'Racines et tubercules' },
      units: { tonnes: 't', 'têtes': 'têtes' },
      sources: 'FAOSTAT, FAO FishStat, OCDE-FAO, sources nationales',
      filename: 'Production_agriculture',
    },

    mining: {
      badge: 'MINES · USGS',
      title: (n) => `Production minière — ${n}`,
      subtitle: (y, c) => `USGS et sources complémentaires · ${y} · code ISO ${c}`,
      kMinerals: 'Minéraux suivis',
      kRecords: 'Valeurs publiées',
      kLatest: 'Dernière année',
      kDatasets: 'Jeux de données',
      profileTitle: 'Profil minier',
      profile: { country: 'Pays', region: 'Région', years: 'Années couvertes', minerals: 'Minéraux suivis', records: 'Valeurs publiées', datasets: 'Jeux de données' },
      synthTitle: (y) => `Synthèse : dernière valeur publiée et évolution (dernière année : ${y})`,
      synthCols: { latest: 'Dernière valeur', year: 'Année', previous: 'Année précédente', change: 'Variation' },
      synthText: "Pour chaque minéral, la dernière valeur publiée et sa variation par rapport à l'année d'avant, dans la même unité. Les minéraux ne se comparent pas entre eux : leurs unités diffèrent (tonnes, milliers de tonnes, carats).",
      tableTitle: 'Production par minéral et par année',
      cols: { mineral: 'Minéral', code: 'Code', source: 'Mesure et source' },
      tableText: [
        "Volumes produits dans l'année, dans l'unité publiée par la source : tonnes, milliers de tonnes métriques, carats pour les diamants et les pierres. Noms et unités sont traduits de l'anglais de la source.",
        "« estimée » : estimation de la source. « Production minière » : extraction à la mine ; « Production de raffinerie » : métal raffiné ; « Production d'usine » : production d'usine. « non publié » : pas de chiffre pour cette année.",
        "Source principale : USGS (Service géologique des États-Unis), Mineral Commodity Summaries, publication annuelle qui révise les années précédentes ; le pétrole, le gaz et le charbon viennent de l'EIA (International Energy Statistics), l'uranium de la World Nuclear Association. Chaque chiffre est extrait par script des publications de ces sources. Cette vue ne publie ni rang ni part africaine ou mondiale.",
      ],
      coverageTitle: 'Couverture des sources',
      coverage: { status: 'Statut', note: 'Note de la source', edition: 'Édition USGS', consulted: 'Sources consultées' },
      status: {
        COVERED: 'Production publiée',
        LISTED_BY_USGS_NOT_INGESTED: 'Pays recensé par USGS, chiffres pas encore intégrés',
        NOT_LISTED_BY_SOURCES: 'Aucune production rapportée par les sources consultées',
      },
      none: 'Aucune valeur de production publiée pour ce pays.',
      sources: 'USGS, EIA, World Nuclear Association',
      filename: 'Production_mines',
    },

    outlets: {
      badge: 'DÉBOUCHÉS',
      title: (n) => `Débouchés — ${n}`,
      subtitle: (c) => `De la production au marché · code ISO ${c}`,
      kLinked: 'Produits reliés à un code SH',
      kTracked: 'Produits suivis',
      kFirst: 'Rangs n° 1 africains',
      kDatasets: 'Agriculture / mines / manuf.',
      shown: (n, total) => `${n} affichés sur ${total}`,
      tableTitle: 'Produits, rang africain et source',
      cols: { product: 'Produit', hs: 'Code SH', output: 'Production', rank: 'Rang africain', share: 'Part', source: 'Source' },
      rankOf: (r, n) => `${r === 1 ? '1er' : `${r}e`} sur ${n} pays couverts`,
      datasets: { agri: 'agriculture', mining: 'mines', manufacturing: 'manufacturier' },
      tableText: (n, total) => [
        "Ce que ce pays produit réellement, et où le vendre sous la ZLECAf. Chaque ligne porte son code SH, qui ouvre à l'écran la recherche de marchés pour ce produit.",
        `${n} produits affichés sur ${total} suivis, classés par part africaine décroissante.`,
        "Code SH : position du produit dans le Système harmonisé des douanes, la clé qui relie la production aux flux commerciaux et aux droits de douane. Production : volume récolté (FAO) ou extrait (USGS), ou valeur ajoutée manufacturière en dollars (UNIDO), pour l'année indiquée.",
        "Rang africain : place du pays parmi les pays africains couverts pour ce produit, toujours suivie du nombre de pays couverts. Part : poids du pays dans le total de ces pays. Rangs et parts portent sur les seuls pays présents dans le référentiel, jamais sur l'Afrique entière. « non publié » : rang ou part retenus par le serveur faute de couverture suffisante.",
      ],
      caveatsTitle: 'Réserves sur certaines lignes',
      caveatsText: 'Réserves attachées par le serveur à un produit ou à une couverture, reprises telles quelles.',
      none: "Aucun produit de ce pays n'est relié à un code SH dans le référentiel.",
      sources: 'FAO, USGS, UNIDO',
      source: 'FAO (FAOSTAT), USGS, UNIDO',
      filename: 'Production_debouches',
    },
  },

  en: {
    module: 'PRODUCTION MODULE',
    na: 'not published',
    iso: (c) => `ISO code ${c}`,
    warning: 'Disclaimer',
    warningText: (sources) => [
      `Figures taken from the public sources cited (${sources}), for the year shown for each. Sources revise their series: check the latest release before making a decision.`,
      'This report summarises economic information: it is not investment advice.',
    ],
    cols: { year: 'Year', source: 'Source', unit: 'Unit', rank: 'Rank in Africa' },
    rankAfrica: (r) => `rank ${r} in Africa`,

    macro: {
      badge: 'MACRO VALUE ADDED',
      title: (n) => `Value added by sector — ${n}`,
      subtitle: (y, c) => `World Bank, World Development Indicators · ${y} · ISO code ${c}`,
      sectors: {
        A: 'Agriculture, forestry and fishing (A)',
        'B-F': 'Industry, including construction (B-F)',
        C: 'of which manufacturing (C)',
        'G-T': 'Services (G-T)',
        TOTAL: 'GDP',
      },
      short: { A: 'Agriculture (A)', 'B-F': 'Industry (B-F)', C: 'Manufacturing (C)', 'G-T': 'Services (G-T)', TOTAL: 'GDP' },
      shareSub: (y) => `% of GDP, ${y}`,
      growth: 'GDP growth',
      gdpUsd: 'GDP (current dollars)',
      shareTitle: 'Value added by sector (% of GDP), year by year',
      shareText: [
        'Value added: what a sector produces, minus what it uses up to produce it (materials, energy, purchased services). The value added of all sectors, plus taxes on products minus subsidies, makes up GDP.',
        '% of GDP: weight of the sector in the economy in the same year. Shares do not add up to 100%: net taxes on products belong to no sector, and manufacturing (C) is already included in industry (B-F).',
        'Sectors follow the ISIC Rev. 4 classification: A = agriculture, forestry and fishing; B-F = industry (mining and quarrying, manufacturing, electricity, gas and water, construction); C = manufacturing alone; G-T = services (trade, transport, accommodation, finance, public administration, education, health…).',
      ],
      usdTitle: 'Value added by sector in current dollars',
      usdText: 'A share of GDP places a sector within its economy; it does not state its size. These amounts are published separately, in current dollars (converted at each year\'s exchange rate, not adjusted for inflation): they are not comparable to the percentages above.',
      usdNone: 'The World Bank does not publish these amounts for this country.',
      growthTitle: 'GDP growth (annual %)',
      growthCol: 'Real GDP growth',
      growthText: 'Change in GDP volume (constant prices) from one year to the next: it is a change, not a share of GDP, hence a separate table. A negative value means the economy contracted.',
      growthNone: 'The World Bank does not publish GDP growth for this country.',
      seriesTitle: 'Series used',
      seriesText: (ans) => `Source: World Bank, World Development Indicators (WDI), value added series; years covered: ${ans}. The codes below can be looked up on data.worldbank.org.`,
      seriesCols: { series: 'Series', pct: 'Code (% of GDP or %)', usd: 'Code (current dollars)' },
      proj: 'projection',
      projNote: '"projection": value forecast by the IMF (World Economic Outlook), not yet observed.',
      sources: 'World Bank, IMF',
      source: 'World Bank — World Development Indicators',
      filename: 'Production_value_added',
    },

    agri: {
      badge: 'AGRICULTURE · FAOSTAT',
      title: (n) => `Agricultural production — ${n}`,
      subtitle: (r, y, c) => `${r} · ${y} data · ISO code ${c}`,
      kCrops: 'Crops tracked',
      kGdp: 'Agriculture, share of GDP',
      kEmploy: 'Agricultural employment',
      kArable: 'Arable land',
      kIrrigated: 'Irrigated land',
      kCapture: 'Capture fisheries',
      kAquaculture: 'Aquaculture',
      cropsTitle: 'Crops: output, area and rank',
      cropsCols: { product: 'Product', production: 'Output', area: 'Harvested area' },
      cropsText: [
        'Output: quantity harvested in the year, in tonnes (t). Area: harvested area, in hectares (ha). Rank in Africa: the country\'s place among African producers of the product (1 = top producer); "—" when the source gives no rank.',
        'The first rows come from the country sheet (FAOSTAT and national sources); the following ones from the FAOSTAT Production (QCL) file, for the latest harvest year published. The [1], [2]… marks in the Source column refer to the list of sources below.',
      ],
      noCrops: 'The source publishes no crop data for this country.',
      sourcesTitle: 'Sources',
      evoTitle: 'Output trend of the main crops (t)',
      evoCol: 'Crop',
      evoText: 'Annual output in tonnes, as published in the country sheet; "not published" marks a year without a figure.',
      indTitle: 'Key indicators of the agricultural sector',
      indText: 'Share of GDP: agricultural value added relative to GDP. Agricultural employment: share of employed people working in agriculture. Arable land: ploughed or cultivable land; irrigated land: land equipped for irrigation, in hectares.',
      indSource: (y) => `FAOSTAT country sheet ${y}`,
      livestockTitle: 'Livestock: herd size',
      livestockCols: { species: 'Species', count: 'Head count' },
      livestockText: 'Head count: number of live animals recorded in the year. Rank in Africa: the country\'s place among African countries for the species.',
      noLivestock: 'The source publishes no livestock data for this country.',
      animalTitle: 'Livestock products',
      animalCols: { product: 'Product', volume: 'Volume' },
      animalText: 'Quantities produced in the year (meat in carcass weight, milk, wool, eggs).',
      fishTitle: 'Fisheries and aquaculture',
      fishText: 'Capture fisheries: fish and seafood taken from the wild (sea, lakes, rivers). Aquaculture: farming of aquatic organisms. Volumes in tonnes; rank among African countries.',
      fishSource: 'FAO FishStat 2023 / Fisheries Directorate',
      noFish: 'The source publishes no fisheries data for this country.',
      species: 'Main species',
      ports: 'Main ports',
      projTitle: 'Production outlook (OECD-FAO)',
      projCols: { aggregate: 'Aggregate', sector: 'Sector', change: 'Change' },
      projText: 'Production forecasts by major aggregate, from the OECD-FAO Agricultural Outlook 2024-2033: these are projections, not observations. Change: variation between the first and last years shown.',
      sectorCrops: 'Crops',
      sectorLivestock: 'Livestock',
      aggregates: { cereals: 'Cereals', oilseeds: 'Oilseeds', sugar: 'Sugar', meat: 'Meat', 'roots & tubers': 'Roots & tubers' },
      units: { tonnes: 't', 'têtes': 'head' },
      sources: 'FAOSTAT, FAO FishStat, OECD-FAO, national sources',
      filename: 'Production_agriculture',
    },

    mining: {
      badge: 'MINING · USGS',
      title: (n) => `Mining production — ${n}`,
      subtitle: (y, c) => `USGS and complementary sources · ${y} · ISO code ${c}`,
      kMinerals: 'Minerals tracked',
      kRecords: 'Published values',
      kLatest: 'Latest year',
      kDatasets: 'Datasets',
      profileTitle: 'Mining profile',
      profile: { country: 'Country', region: 'Region', years: 'Years covered', minerals: 'Minerals tracked', records: 'Published values', datasets: 'Datasets' },
      synthTitle: (y) => `Summary: latest published value and change (latest year: ${y})`,
      synthCols: { latest: 'Latest value', year: 'Year', previous: 'Previous year', change: 'Change' },
      synthText: 'For each mineral, the latest published value and its change from the year before, in the same unit. Minerals cannot be compared with each other: their units differ (tonnes, thousand tonnes, carats).',
      tableTitle: 'Output by mineral and year',
      cols: { mineral: 'Mineral', code: 'Code', source: 'Measure and source' },
      tableText: [
        'Volumes produced in the year, in the unit published by the source: tonnes (tonnes, metric tons), thousand metric tons, carats for diamonds and gemstones. Names and units are those of the source.',
        '"estimated": estimate by the source. "Mine production": extraction at the mine; "Refinery production": refined metal; "Plant production": plant output. "not published": no figure for that year.',
        'Main source: USGS (United States Geological Survey), Mineral Commodity Summaries, an annual release that revises previous years; oil, gas and coal come from the EIA (International Energy Statistics), uranium from the World Nuclear Association. Every figure is extracted by script from the publications of these sources. This view publishes no African or world rank or share.',
      ],
      coverageTitle: 'Source coverage',
      coverage: { status: 'Status', note: 'Source note', edition: 'USGS edition', consulted: 'Sources consulted' },
      status: {
        COVERED: 'Production published',
        LISTED_BY_USGS_NOT_INGESTED: 'Country listed by USGS, figures not yet ingested',
        NOT_LISTED_BY_SOURCES: 'No production reported by the sources consulted',
      },
      none: 'No production value published for this country.',
      sources: 'USGS, EIA, World Nuclear Association',
      filename: 'Production_mining',
    },

    outlets: {
      badge: 'OUTLETS',
      title: (n) => `Outlets — ${n}`,
      subtitle: (c) => `From production to market · ISO code ${c}`,
      kLinked: 'Products linked to an HS code',
      kTracked: 'Products tracked',
      kFirst: 'African #1 ranks',
      kDatasets: 'Agriculture / mining / manuf.',
      shown: (n, total) => `${n} shown out of ${total}`,
      tableTitle: 'Products, African rank and source',
      cols: { product: 'Product', hs: 'HS code', output: 'Output', rank: 'African rank', share: 'Share', source: 'Source' },
      rankOf: (r, n) => `#${r} of ${n} covered countries`,
      datasets: { agri: 'agriculture', mining: 'mining', manufacturing: 'manufacturing' },
      tableText: (n, total) => [
        'What this country actually produces, and where to sell it under the AfCFTA. Every row carries its HS code, which opens the market search for that product on screen.',
        `${n} products shown out of ${total} tracked, sorted by decreasing African share.`,
        'HS code: the product\'s position in the customs Harmonized System, the key linking production to trade flows and customs duties. Output: volume harvested (FAO) or extracted (USGS), or manufacturing value added in dollars (UNIDO), for the year shown.',
        'African rank: the country\'s place among the African countries covered for the product, always followed by the number of covered countries. Share: the country\'s weight in the total of those countries. Ranks and shares cover only the countries present in the dataset, never the whole continent. "not published": rank or share withheld by the server for lack of coverage.',
      ],
      caveatsTitle: 'Caveats on some rows',
      caveatsText: 'Caveats attached by the server to a product or to a coverage, reproduced as is.',
      none: 'None of this country\'s products is linked to an HS code in the dataset.',
      sources: 'FAO, USGS, UNIDO',
      source: 'FAO (FAOSTAT), USGS, UNIDO',
      filename: 'Production_outlets',
    },
  },

  ar: {
    module: 'وحدة الإنتاج',
    na: 'غير منشور',
    iso: (c) => `الرمز ISO ${c}`,
    warning: 'تنبيه',
    warningText: (sources) => [
      `أرقام مأخوذة من المصادر العامة المذكورة (${sources})، للسنة المبيّنة لكل منها. تراجع المصادر سلاسلها: يُرجى التحقق من آخر إصدار قبل أي قرار.`,
      'هذا التقرير خلاصة لمعلومات اقتصادية: لا يُعدّ نصيحة استثمارية.',
    ],
    cols: { year: 'السنة', source: 'المصدر', unit: 'الوحدة', rank: 'الترتيب أفريقيًا' },
    rankAfrica: (r) => `الترتيب ${r} في أفريقيا`,

    macro: {
      badge: 'القيمة المضافة الكلية',
      title: (n) => `القيمة المضافة حسب القطاع — ${n}`,
      subtitle: (y, c) => `البنك الدولي، مؤشرات التنمية العالمية · ${y} · الرمز ISO ${c}`,
      sectors: {
        A: 'الزراعة والحراجة وصيد الأسماك (A)',
        'B-F': 'الصناعة بما فيها البناء (B-F)',
        C: 'منها الصناعة التحويلية (C)',
        'G-T': 'الخدمات (G-T)',
        TOTAL: 'الناتج المحلي الإجمالي',
      },
      short: { A: 'الزراعة (A)', 'B-F': 'الصناعة (B-F)', C: 'التحويلية (C)', 'G-T': 'الخدمات (G-T)', TOTAL: 'الناتج المحلي' },
      shareSub: (y) => `% من الناتج المحلي، ${y}`,
      growth: 'نمو الناتج المحلي',
      gdpUsd: 'الناتج المحلي (بالدولار الجاري)',
      shareTitle: 'القيمة المضافة حسب القطاع (% من الناتج المحلي الإجمالي)، سنة بسنة',
      shareText: [
        'القيمة المضافة: ما ينتجه القطاع مطروحًا منه ما يستهلكه من أجل الإنتاج (مواد، طاقة، خدمات مشتراة). مجموع القيم المضافة لكل القطاعات، مضافًا إليه الضرائب على المنتجات مطروحًا منه الإعانات، يساوي الناتج المحلي الإجمالي.',
        'نسبة من الناتج المحلي: وزن القطاع في الاقتصاد في السنة نفسها. لا يبلغ مجموع النسب 100%: فالضرائب الصافية على المنتجات لا تنتمي إلى أي قطاع، والصناعة التحويلية (C) مشمولة أصلًا في الصناعة (B-F).',
        'القطاعات وفق التصنيف الصناعي الدولي الموحد (ISIC، التنقيح 4): A = الزراعة والحراجة وصيد الأسماك؛ B-F = الصناعة (التعدين واستغلال المحاجر، الصناعة التحويلية، الكهرباء والغاز والمياه، البناء)؛ C = الصناعة التحويلية وحدها؛ G-T = الخدمات (التجارة، النقل، الإيواء، المالية، الإدارة، التعليم، الصحة…).',
      ],
      usdTitle: 'القيمة المضافة حسب القطاع بالدولار الجاري',
      usdText: 'تحدد حصة الناتج المحلي الإجمالي موقع القطاع داخل اقتصاده، لكنها لا تدل على حجمه. تُنشر هذه المبالغ بشكل منفصل بالدولار الجاري (محوّلة بسعر صرف كل سنة، دون تصحيح للتضخم)، ولا تُقارن بالنسب المئوية أعلاه.',
      usdNone: 'لا ينشر البنك الدولي هذه المبالغ لهذا البلد.',
      growthTitle: 'نمو الناتج المحلي الإجمالي (% سنويًا)',
      growthCol: 'النمو الحقيقي للناتج المحلي',
      growthText: 'تغيّر حجم الناتج المحلي (بالأسعار الثابتة) من سنة إلى أخرى: إنه تطوّر لا حصة من الناتج، ولذلك يُعرض في جدول مستقل. تدل القيمة السالبة على انكماش الاقتصاد.',
      growthNone: 'لا ينشر البنك الدولي نمو الناتج المحلي لهذا البلد.',
      seriesTitle: 'السلاسل المستخدمة',
      seriesText: (ans) => `المصدر: البنك الدولي، مؤشرات التنمية العالمية (WDI)، سلاسل القيمة المضافة؛ السنوات المشمولة: ${ans}. يمكن الاطلاع على الرموز أدناه في data.worldbank.org.`,
      seriesCols: { series: 'السلسلة', pct: 'الرمز (% من الناتج أو %)', usd: 'الرمز (بالدولار الجاري)' },
      proj: 'إسقاط',
      projNote: '«إسقاط»: قيمة يتوقعها صندوق النقد الدولي (آفاق الاقتصاد العالمي)، لم تُرصد بعد.',
      sources: 'البنك الدولي، صندوق النقد الدولي',
      source: 'World Bank — World Development Indicators',
      filename: 'Production_valeur_ajoutee_ar',
    },

    agri: {
      badge: 'الزراعة · FAOSTAT',
      title: (n) => `الإنتاج الزراعي — ${n}`,
      subtitle: (r, y, c) => `${r} · بيانات ${y} · الرمز ISO ${c}`,
      kCrops: 'المحاصيل المتابَعة',
      kGdp: 'الزراعة، الحصة من الناتج',
      kEmploy: 'العمالة الزراعية',
      kArable: 'الأراضي الصالحة للزراعة',
      kIrrigated: 'الأراضي المروية',
      kCapture: 'الصيد الطبيعي',
      kAquaculture: 'تربية الأحياء المائية',
      cropsTitle: 'المحاصيل: الإنتاج والمساحة والترتيب',
      cropsCols: { product: 'المنتَج', production: 'الإنتاج', area: 'المساحة المحصودة' },
      cropsText: [
        'الإنتاج: الكمية المحصودة في السنة، بالطن. المساحة: المساحة المحصودة بالهكتار. الترتيب في أفريقيا: مكانة البلد بين المنتجين الأفارقة للمنتَج (1 = الأول)؛ «—» حين لا يقدّم المصدر ترتيبًا.',
        'تأتي الأسطر الأولى من بطاقة البلد (FAOSTAT ومصادر وطنية)، والتالية من ملف FAOSTAT للإنتاج (QCL) لآخر سنة حصاد منشورة. تحيل العلامات [1]، [2]… في عمود المصدر إلى قائمة المصادر أدناه.',
      ],
      noCrops: 'لا ينشر المصدر بيانات عن المحاصيل لهذا البلد.',
      sourcesTitle: 'المصادر',
      evoTitle: 'تطوّر إنتاج المحاصيل الرئيسية (طن)',
      evoCol: 'المحصول',
      evoText: 'الإنتاج السنوي بالطن كما تنشره بطاقة البلد؛ «غير منشور» يدل على سنة بلا رقم.',
      indTitle: 'المؤشرات الرئيسية للقطاع الزراعي',
      indText: 'الحصة من الناتج المحلي: القيمة المضافة الزراعية منسوبة إلى الناتج المحلي الإجمالي. العمالة الزراعية: نسبة المشتغلين في الزراعة. الأراضي الصالحة للزراعة: المساحات المحروثة أو القابلة للزراعة؛ الأراضي المروية: المساحات المجهزة للري، بالهكتار.',
      indSource: (y) => `بطاقة البلد FAOSTAT ${y}`,
      livestockTitle: 'تربية المواشي: أعداد القطيع',
      livestockCols: { species: 'النوع', count: 'العدد' },
      livestockText: 'العدد: عدد الحيوانات الحية المسجلة في السنة. الترتيب في أفريقيا: مكانة البلد بين البلدان الأفريقية لهذا النوع.',
      noLivestock: 'لا ينشر المصدر بيانات عن تربية المواشي لهذا البلد.',
      animalTitle: 'الإنتاج الحيواني',
      animalCols: { product: 'المنتَج', volume: 'الحجم' },
      animalText: 'الكميات المنتَجة في السنة (اللحوم بوزن الذبيحة، الحليب، الصوف، البيض).',
      fishTitle: 'الصيد البحري وتربية الأحياء المائية',
      fishText: 'الصيد الطبيعي: الأسماك والمأكولات البحرية المأخوذة من الوسط الطبيعي (البحر، البحيرات، الأنهار). تربية الأحياء المائية: تربية الكائنات المائية. الأحجام بالطن؛ الترتيب بين البلدان الأفريقية.',
      fishSource: 'FAO FishStat 2023 / مديرية الصيد البحري',
      noFish: 'لا ينشر المصدر بيانات عن الصيد البحري لهذا البلد.',
      species: 'الأنواع الرئيسية',
      ports: 'الموانئ الرئيسية',
      projTitle: 'آفاق الإنتاج (منظمة التعاون الاقتصادي والتنمية ومنظمة الأغذية والزراعة)',
      projCols: { aggregate: 'المجموعة', sector: 'القطاع', change: 'التطوّر' },
      projText: 'توقعات الإنتاج حسب المجموعات الكبرى، مأخوذة من آفاق الزراعة لمنظمة التعاون الاقتصادي والتنمية ومنظمة الأغذية والزراعة 2024-2033: إنها إسقاطات لا مشاهدات. التطوّر: التغيّر بين أول سنة وآخر سنة معروضتين.',
      sectorCrops: 'المحاصيل',
      sectorLivestock: 'تربية المواشي',
      aggregates: { cereals: 'الحبوب', oilseeds: 'البذور الزيتية', sugar: 'السكر', meat: 'اللحوم', 'roots & tubers': 'الجذور والدرنات' },
      units: {},
      sources: 'FAOSTAT، FAO FishStat، منظمة التعاون الاقتصادي والتنمية ومنظمة الأغذية والزراعة، مصادر وطنية',
      filename: 'Production_agriculture_ar',
    },

    mining: {
      badge: 'التعدين · USGS',
      title: (n) => `الإنتاج المعدني — ${n}`,
      subtitle: (y, c) => `USGS ومصادر مكمّلة · ${y} · الرمز ISO ${c}`,
      kMinerals: 'المعادن المتابَعة',
      kRecords: 'القيم المنشورة',
      kLatest: 'آخر سنة',
      kDatasets: 'مجموعات البيانات',
      profileTitle: 'الملف المعدني',
      profile: { country: 'البلد', region: 'المنطقة', years: 'السنوات المشمولة', minerals: 'المعادن المتابَعة', records: 'القيم المنشورة', datasets: 'مجموعات البيانات' },
      synthTitle: (y) => `خلاصة: آخر قيمة منشورة وتطورها (آخر سنة: ${y})`,
      synthCols: { latest: 'آخر قيمة', year: 'السنة', previous: 'السنة السابقة', change: 'التغيّر' },
      synthText: 'لكل معدن، آخر قيمة منشورة وتغيّرها مقارنة بالسنة السابقة، بالوحدة نفسها. لا تُقارَن المعادن ببعضها: وحداتها مختلفة (طن، آلاف الأطنان، قيراط).',
      tableTitle: 'الإنتاج حسب المعدن والسنة',
      cols: { mineral: 'المعدن', code: 'الرمز', source: 'المقياس والمصدر' },
      tableText: [
        'الأحجام المنتَجة في السنة بالوحدة التي ينشرها المصدر: الطن، ألف طن متري، القيراط للماس والأحجار الكريمة.',
        '«تقديري»: تقدير المصدر. إنتاج المناجم: الاستخراج من المنجم؛ إنتاج المصافي: المعدن المكرَّر؛ إنتاج المصانع: إنتاج المعامل. «غير منشور»: لا رقم لتلك السنة.',
        'المصدر الرئيسي: هيئة المسح الجيولوجي الأمريكية (USGS)، الملخصات السنوية للسلع المعدنية (Mineral Commodity Summaries) التي تراجع السنوات السابقة؛ النفط والغاز والفحم من إدارة معلومات الطاقة الأمريكية (EIA)، واليورانيوم من الرابطة النووية العالمية. يُستخرج كل رقم آليًا من منشورات هذه المصادر. لا تنشر هذه الواجهة ترتيبًا ولا حصة أفريقية أو عالمية.',
      ],
      coverageTitle: 'تغطية المصادر',
      coverage: { status: 'الحالة', note: 'ملاحظة المصدر', edition: 'إصدار USGS', consulted: 'المصادر المعتمدة' },
      status: {
        COVERED: 'إنتاج منشور',
        LISTED_BY_USGS_NOT_INGESTED: 'بلد مدرج لدى USGS، لم تُدمج أرقامه بعد',
        NOT_LISTED_BY_SOURCES: 'لا إنتاج مُبلَّغ عنه لدى المصادر المعتمدة',
      },
      none: 'لا توجد قيمة إنتاج منشورة لهذا البلد.',
      sources: 'USGS، EIA، الرابطة النووية العالمية',
      filename: 'Production_mines_ar',
    },

    outlets: {
      badge: 'المنافذ',
      title: (n) => `المنافذ — ${n}`,
      subtitle: (c) => `من الإنتاج إلى السوق · الرمز ISO ${c}`,
      kLinked: 'منتجات مرتبطة برمز SH',
      kTracked: 'المنتجات المتابَعة',
      kFirst: 'المرتبة الأولى أفريقيًا',
      kDatasets: 'الزراعة / التعدين / التحويلية',
      shown: (n, total) => `${n} معروضة من ${total}`,
      tableTitle: 'المنتجات والترتيب الأفريقي والمصدر',
      cols: { product: 'المنتج', hs: 'رمز SH', output: 'الإنتاج', rank: 'الترتيب الأفريقي', share: 'الحصة', source: 'المصدر' },
      rankOf: (r, n) => `المرتبة ${r} من ${n} بلدًا مشمولًا`,
      datasets: { agri: 'الزراعة', mining: 'التعدين', manufacturing: 'الصناعة التحويلية' },
      tableText: (n, total) => [
        'ما ينتجه هذا البلد فعلًا، وأين يبيعه في إطار منطقة التجارة الحرة القارية الأفريقية. يحمل كل سطر رمز النظام المنسق (SH) الذي يفتح على الشاشة البحث عن أسواق لهذا المنتج.',
        `${n} منتجًا معروضًا من أصل ${total} متابَعًا، مرتبة حسب الحصة الأفريقية تنازليًا.`,
        'رمز SH: موقع المنتج في النظام المنسق للجمارك، وهو المفتاح الذي يربط الإنتاج بالتدفقات التجارية والرسوم الجمركية. الإنتاج: الحجم المحصود (FAO) أو المستخرج (USGS)، أو القيمة المضافة الصناعية بالدولار (UNIDO)، للسنة المبيّنة.',
        'الترتيب الأفريقي: مكانة البلد بين البلدان الأفريقية المشمولة لهذا المنتج، مع عدد البلدان المشمولة دائمًا. الحصة: وزن البلد في مجموع هذه البلدان. تقتصر المراتب والحصص على البلدان الموجودة في المرجع فقط، ولا تشمل أفريقيا بأكملها أبدًا. «غير منشور»: ترتيب أو حصة حجبها الخادم لعدم كفاية التغطية.',
      ],
      caveatsTitle: 'تحفظات على بعض الأسطر',
      caveatsText: 'تحفظات يرفقها الخادم بمنتج أو بتغطية، منقولة كما هي.',
      none: 'لا يرتبط أي منتج لهذا البلد برمز SH في المرجع.',
      sources: 'FAO، USGS، UNIDO',
      source: 'FAO (FAOSTAT), USGS, UNIDO',
      filename: 'Production_debouches_ar',
    },
  },
};

const estNombre = (v) => typeof v === 'number' && Number.isFinite(v);
const dateDuJour = () => new Date().toISOString().slice(0, 10);
const nomFichier = (base, code) => [base, code, dateDuJour()].filter(Boolean).join('_');

/** Outils communs à un rapport : dictionnaire, nom du pays, formats. */
function outils(langue, code, nomSource) {
  const lang = T[langue] ? langue : 'fr';
  const t = T[lang];
  const nom = AFRICAN_COUNTRIES[code]?.[`name_${lang}`] || trDonnee(nomSource, lang) || code || '—';
  // Valeur absente : « non publié », jamais 0.
  const num = (v, d = 0) => (estNombre(v) ? nombre(v, lang, d) : t.na);
  // Petites valeurs (moins de 100) avec deux décimales, sinon entières.
  const vol = (v) => (estNombre(v) ? nombre(v, lang, Math.abs(v) < 100 ? 2 : 0) : t.na);
  const pct = (v, d = 2) => (estNombre(v) ? `${nombre(v, lang, d)}${estAnglais(lang) ? '' : ' '}%` : t.na);
  const usd = (v) => (estNombre(v) ? montantCompact(v, lang, { B: 2, M: 1, u: 0 }, { max: true }) : t.na);
  const donnee = (texte) => trDonnee(texte, lang);
  const annees = (liste) => (liste.length > 1 ? `${liste[0]}–${liste[liste.length - 1]}` : String(liste[0] ?? '—'));
  return { lang, t, nom, num, vol, pct, usd, donnee, annees };
}

const avertissement = (t, sources) => ({ title: t.warning, notice: t.warningText(sources) });

/* ═════════════════════════════ Valeur ajoutée macro ═════════════════════════════ */

const ORDRE_SECTEURS = ['A', 'B-F', 'C', 'G-T', 'TOTAL'];

// Même règle que l'écran : la croissance du PIB est une variation annuelle,
// pas une part sectorielle — elle sort du tableau des parts.
const estCroissance = (recs) => Array.isArray(recs) && recs.some(
  (r) => r.indicator_code === 'NGDP_RPCH' || r.indicator_code === 'NY.GDP.MKTP.KD.ZG' || r.sector_isic_section === 'TOTAL'
);

/** { nomSecteur: [enregistrements] } → [{ cle, nom, parAn: {année: enregistrement} }], dans l'ordre CITI. */
function seriesParSecteur(parSecteur) {
  const series = Object.entries(parSecteur || {}).map(([nom, recs]) => ({
    cle: recs?.[0]?.sector_isic_section || nom,
    nom,
    recs: recs || [],
    parAn: Object.fromEntries((recs || []).map((r) => [r.year, r])),
  }));
  const rang = (cle) => (ORDRE_SECTEURS.includes(cle) ? ORDRE_SECTEURS.indexOf(cle) : ORDRE_SECTEURS.length);
  return series.sort((a, b) => rang(a.cle) - rang(b.cle));
}

const anneesDe = (series) => [...new Set(series.flatMap((s) => s.recs.map((r) => r.year)))]
  .filter(Number.isFinite)
  .sort((a, b) => a - b);

export function specMacroPdf(macro, langue = 'fr') {
  const code = macro?.country_iso3 || '';
  const { lang, t: tc, nom, pct, usd, donnee, annees } = outils(langue, code, macro?.country_name);
  const t = tc.macro;
  const libelle = (s, court = false) => (court ? t.short : t.sectors)[s.cle] || donnee(s.nom);

  const toutes = seriesParSecteur(macro?.data_by_sector);
  const parts = toutes.filter((s) => !estCroissance(s.recs));
  const croissance = toutes.find((s) => estCroissance(s.recs));
  const montants = seriesParSecteur(macro?.data_by_sector_usd);

  const couverture = Array.isArray(macro?.years_covered) && macro.years_covered.length
    ? [...macro.years_covered].sort((a, b) => a - b)
    : anneesDe(toutes);
  let projection = false;
  const cellule = (rec, format) => {
    if (!rec || !estNombre(rec.value)) return tc.na;
    if (rec.is_projection) projection = true;
    return rec.is_projection ? `${format(rec.value)} (${t.proj})` : format(rec.value);
  };

  // Dernière année publiée de chaque série, pour les cartes.
  const dernier = (s) => (s ? [...s.recs].filter((r) => estNombre(r.value)).sort((a, b) => a.year - b.year).pop() : null);
  const carte = (s, accent) => {
    const r = dernier(s);
    return { label: libelle(s, true), value: r ? pct(r.value) : tc.na, sub: r ? t.shareSub(r.year) : '', accent };
  };
  const accents = { A: 'green', 'B-F': 'terra', C: 'gold', 'G-T': 'gold' };
  const kpis = parts.map((s) => carte(s, accents[s.cle] || 'gold'));
  const rc = dernier(croissance);
  kpis.push({ label: t.growth, value: rc ? pct(rc.value, 1) : tc.na, sub: rc ? String(rc.year) : '', accent: rc && rc.value < 0 ? 'red' : 'green' });
  const pib = montants.find((s) => s.cle === 'TOTAL');
  const rp = dernier(pib);
  kpis.push({ label: t.gdpUsd, value: rp ? usd(rp.value) : tc.na, sub: rp ? String(rp.year) : '', accent: 'terra' });

  const colonneAn = { key: 'year', label: tc.cols.year, width: 0.8 };
  const sections = [];

  const anParts = anneesDe(parts);
  sections.push({
    title: t.shareTitle,
    table: {
      columns: [colonneAn, ...parts.map((s) => ({ key: s.cle, label: libelle(s, true), width: 1.3, align: 'right' }))],
      rows: anParts.map((an) => Object.fromEntries([
        ['year', String(an)],
        ...parts.map((s) => [s.cle, cellule(s.parAn[an], (v) => pct(v))]),
      ])),
    },
  });
  sections.push({ paragraphs: t.shareText });

  const anUsd = anneesDe(montants);
  if (montants.length && anUsd.length) {
    sections.push({
      title: t.usdTitle,
      table: {
        columns: [colonneAn, ...montants.map((s) => ({ key: s.cle, label: libelle(s, true), width: 1.3, align: 'right' }))],
        rows: anUsd.map((an) => Object.fromEntries([
          ['year', String(an)],
          ...montants.map((s) => [s.cle, cellule(s.parAn[an], usd)]),
        ])),
      },
    });
    sections.push({ paragraphs: [t.usdText] });
  } else {
    sections.push({ title: t.usdTitle, paragraphs: [t.usdNone] });
  }

  if (croissance?.recs.length) {
    sections.push({
      title: t.growthTitle,
      table: {
        columns: [colonneAn, { key: 'value', label: t.growthCol, width: 2, align: 'right' }],
        rows: anneesDe([croissance]).map((an) => ({
          year: String(an),
          value: cellule(croissance.parAn[an], (v) => pct(v, 1)),
        })),
      },
    });
    sections.push({ paragraphs: [t.growthText] });
  } else {
    sections.push({ title: t.growthTitle, paragraphs: [t.growthNone] });
  }

  // Traçabilité : le code WDI de chaque série affichée.
  const codes = {};
  [...toutes.map((s) => [s, 'pct']), ...montants.map((s) => [s, 'usd'])].forEach(([s, k]) => {
    const cle = estCroissance(s.recs) && k === 'pct' ? 'GROWTH' : s.cle;
    codes[cle] = codes[cle] || { series: cle === 'GROWTH' ? t.growth : libelle(s) };
    codes[cle][k] = s.recs[0]?.indicator_code || '—';
  });
  sections.push({ title: t.seriesTitle, paragraphs: [t.seriesText(couverture.length ? annees(couverture) : tc.na)] });
  sections.push({
    table: {
      columns: [
        { key: 'series', label: t.seriesCols.series, width: 2.4 },
        { key: 'pct', label: t.seriesCols.pct, width: 1.5 },
        { key: 'usd', label: t.seriesCols.usd, width: 1.5 },
      ],
      rows: Object.values(codes).map((c) => ({ series: c.series, pct: c.pct || '—', usd: c.usd || '—' })),
    },
  });
  if (projection) sections.push({ paragraphs: [t.projNote] });

  sections.push(avertissement(tc, t.sources));

  return {
    moduleLabel: tc.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(couverture.length ? annees(couverture) : tc.na, code),
    kpis,
    sections,
    source: t.source,
    filename: nomFichier(t.filename, code),
    language: lang,
  };
}

/* ═════════════════════════════════ Agriculture ═════════════════════════════════ */

export function specAgriculturePdf(detail, langue = 'fr') {
  const code = detail?.country_iso3 || '';
  const { lang, t: tc, nom, num, vol, pct, donnee, annees } = outils(langue, code, detail?.country_name);
  const t = tc.agri;
  const unite = (u) => (u ? t.units[u] || donnee(u) : '');
  const anDonnees = detail?.data_year || 2023;
  const region = getRegionName(detail?.region, lang) || donnee(detail?.region) || '—';
  const ki = detail?.key_indicators || {};
  const peche = detail?.peche_aquaculture || {};
  const cultures = detail?.cultures || [];

  // Sources numérotées : la colonne Source du tableau des cultures y renvoie.
  const sources = [...new Set([...(detail?.sources || []), detail?.source, ...cultures.map((c) => c.source)].filter(Boolean))];
  const renvoi = (src) => (sources.includes(src) ? `[${sources.indexOf(src) + 1}]` : '—');

  const kpis = [
    { label: t.kCrops, value: String(cultures.length), sub: t.indSource(anDonnees), accent: 'green' },
    { label: t.kGdp, value: pct(ki.agri_gdp_percent, 1), sub: t.indSource(anDonnees), accent: 'gold' },
    { label: t.kEmploy, value: pct(ki.agri_employment_percent, 1), sub: t.indSource(anDonnees), accent: 'gold' },
    { label: t.kArable, value: estNombre(ki.arable_land_ha) ? `${num(ki.arable_land_ha)} ha` : tc.na, sub: t.indSource(anDonnees), accent: 'terra' },
    { label: t.kIrrigated, value: estNombre(ki.irrigated_land_ha) ? `${num(ki.irrigated_land_ha)} ha` : tc.na, sub: t.indSource(anDonnees), accent: 'terra' },
    { label: t.kCapture, value: detail?.has_fisheries && estNombre(peche.capture_tonnes) ? `${num(peche.capture_tonnes)} ${unite('tonnes')}` : tc.na, sub: peche.capture_rank_africa ? tc.rankAfrica(peche.capture_rank_africa) : '', accent: 'green' },
    { label: t.kAquaculture, value: detail?.has_fisheries && estNombre(peche.aquaculture_tonnes) ? `${num(peche.aquaculture_tonnes)} ${unite('tonnes')}` : tc.na, sub: peche.aquaculture_rank_africa ? tc.rankAfrica(peche.aquaculture_rank_africa) : '', accent: 'green' },
  ];

  const sections = [];

  // ── Cultures
  if (cultures.length) {
    sections.push({
      title: t.cropsTitle,
      table: {
        columns: [
          { key: 'product', label: t.cropsCols.product, width: 2.4 },
          { key: 'production', label: t.cropsCols.production, width: 1.5, align: 'right' },
          { key: 'year', label: tc.cols.year, width: 0.7, align: 'right' },
          { key: 'area', label: t.cropsCols.area, width: 1.4, align: 'right' },
          { key: 'rank', label: tc.cols.rank, width: 1.3, align: 'right' },
          { key: 'source', label: tc.cols.source, width: 0.7, align: 'right' },
        ],
        rows: cultures.map((c) => ({
          product: donnee(c.name),
          production: estNombre(c.value_2023) ? `${vol(c.value_2023)} ${unite(c.unit || 'tonnes')}` : tc.na,
          year: String(c.is_bulk_faostat ? c.year ?? anDonnees : anDonnees),
          area: estNombre(c.area_ha) ? `${num(c.area_ha)} ha` : tc.na,
          rank: c.rank_africa ? String(c.rank_africa) : '—',
          source: renvoi(c.source || detail?.source),
        })),
      },
    });
    sections.push({ paragraphs: t.cropsText });
  } else {
    sections.push({ title: t.cropsTitle, paragraphs: [t.noCrops] });
  }
  if (sources.length) {
    sections.push({ title: t.sourcesTitle, keyValues: sources.map((s, i) => ({ label: `[${i + 1}]`, value: s })) });
  }

  // ── Évolution (toutes les cultures servies, pas seulement les cinq tracées à l'écran)
  const evo = detail?.evolution || {};
  const evoCultures = Object.keys(evo);
  if (evoCultures.length) {
    const ans = [...new Set(evoCultures.flatMap((c) => Object.keys(evo[c] || {})))].map(Number).filter(Number.isFinite).sort((a, b) => a - b);
    sections.push({
      title: t.evoTitle,
      table: {
        columns: [
          { key: 'crop', label: t.evoCol, width: 2.2 },
          ...ans.map((a) => ({ key: String(a), label: String(a), width: 1, align: 'right' })),
        ],
        rows: evoCultures.map((c) => Object.fromEntries([
          ['crop', donnee(c)],
          ...ans.map((a) => [String(a), vol(evo[c]?.[a] ?? evo[c]?.[String(a)])]),
        ])),
      },
    });
    sections.push({ paragraphs: [t.evoText] });
  }

  // ── Indicateurs clés
  const indicateurs = [
    estNombre(ki.agri_gdp_percent) && { label: t.kGdp, value: pct(ki.agri_gdp_percent, 1) },
    estNombre(ki.agri_employment_percent) && { label: t.kEmploy, value: pct(ki.agri_employment_percent, 1) },
    estNombre(ki.arable_land_ha) && { label: t.kArable, value: `${num(ki.arable_land_ha)} ha` },
    estNombre(ki.irrigated_land_ha) && { label: t.kIrrigated, value: `${num(ki.irrigated_land_ha)} ha` },
  ].filter(Boolean);
  if (indicateurs.length) {
    sections.push({ title: `${t.indTitle} (${t.indSource(anDonnees)})`, keyValues: indicateurs });
    sections.push({ paragraphs: [t.indText] });
  }

  // ── Élevage
  const elevage = detail?.has_livestock ? detail?.elevage || [] : [];
  if (elevage.length) {
    sections.push({
      title: t.livestockTitle,
      table: {
        columns: [
          { key: 'species', label: t.livestockCols.species, width: 2.2 },
          { key: 'count', label: t.livestockCols.count, width: 1.6, align: 'right' },
          { key: 'unit', label: tc.cols.unit, width: 1 },
          { key: 'year', label: tc.cols.year, width: 0.8, align: 'right' },
          { key: 'rank', label: tc.cols.rank, width: 1.2, align: 'right' },
        ],
        rows: elevage.map((e) => ({
          species: donnee(e.name),
          count: num(e.value),
          unit: unite(e.unit) || '—',
          year: String(anDonnees),
          rank: e.rank_africa ? String(e.rank_africa) : '—',
        })),
      },
    });
    sections.push({ paragraphs: [t.livestockText] });
  } else {
    sections.push({ title: t.livestockTitle, paragraphs: [t.noLivestock] });
  }
  const animale = detail?.has_livestock ? Object.entries(detail?.livestock_production_2023 || {}) : [];
  if (animale.length) {
    sections.push({
      title: t.animalTitle,
      table: {
        columns: [
          { key: 'product', label: t.animalCols.product, width: 2.2 },
          { key: 'volume', label: t.animalCols.volume, width: 1.6, align: 'right' },
          { key: 'unit', label: tc.cols.unit, width: 1 },
          { key: 'year', label: tc.cols.year, width: 0.8, align: 'right' },
        ],
        rows: animale.map(([produit, d]) => ({
          product: donnee(produit),
          volume: vol(d?.value),
          unit: unite(d?.unit) || '—',
          year: '2023',
        })),
      },
    });
    sections.push({ paragraphs: [t.animalText] });
  }

  // ── Pêche et aquaculture
  if (detail?.has_fisheries) {
    const tonnes = (v, r) => (estNombre(v) ? `${num(v)} ${unite('tonnes')}${r ? ` · ${tc.rankAfrica(r)}` : ''}` : tc.na);
    sections.push({
      title: t.fishTitle,
      keyValues: [
        { label: `${t.kCapture} (2023)`, value: tonnes(peche.capture_tonnes, peche.capture_rank_africa) },
        { label: `${t.kAquaculture} (2023)`, value: tonnes(peche.aquaculture_tonnes, peche.aquaculture_rank_africa) },
        peche.species?.length && { label: t.species, value: peche.species.map(donnee).join(', ') },
        peche.main_ports?.length && { label: t.ports, value: peche.main_ports.map(donnee).join(', ') },
        { label: tc.cols.source, value: t.fishSource },
      ].filter(Boolean),
    });
    sections.push({ paragraphs: [t.fishText] });
  } else {
    sections.push({ title: t.fishTitle, paragraphs: [t.noFish] });
  }

  // ── Perspectives OCDE-FAO
  const projections = detail?.has_projections ? detail?.projections || [] : [];
  if (projections.length) {
    const ans = [...new Set(projections.flatMap((p) => (p.points || []).map((x) => x.year)))].sort((a, b) => a - b);
    const agregat = (c) => {
      const court = String(c || '').replace(/\s*\(projection\)\s*$/i, '').trim();
      return t.aggregates[court.toLowerCase()] || donnee(court);
    };
    sections.push({
      title: t.projTitle,
      table: {
        columns: [
          { key: 'aggregate', label: t.projCols.aggregate, width: 1.6 },
          { key: 'sector', label: t.projCols.sector, width: 1.1 },
          { key: 'unit', label: tc.cols.unit, width: 0.7 },
          ...ans.map((a) => ({ key: String(a), label: String(a), width: 1.2, align: 'right' })),
          { key: 'change', label: t.projCols.change, width: 1.3, align: 'right' },
        ],
        rows: projections.map((p) => {
          const points = p.points || [];
          const premier = points[0];
          const dernier = points[points.length - 1];
          const evolution = premier && dernier && premier !== dernier && premier.value
            ? `${dernier.value >= premier.value ? '+' : ''}${pct(((dernier.value - premier.value) / premier.value) * 100, 1)} (${premier.year}-${dernier.year})`
            : '—';
          return Object.fromEntries([
            ['aggregate', agregat(p.commodity)],
            ['sector', p.is_livestock ? t.sectorLivestock : t.sectorCrops],
            ['unit', unite(p.unit) || '—'],
            ...ans.map((a) => [String(a), vol(points.find((x) => x.year === a)?.value)]),
            ['change', evolution],
          ]);
        }),
      },
    });
    const src = [...new Set(projections.map((p) => p.source_dataset).filter(Boolean))].join(', ');
    sections.push({ paragraphs: [`${t.projText}${src ? ` (${src})` : ''}`] });
  }

  sections.push(avertissement(tc, t.sources));

  return {
    moduleLabel: tc.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(region, annees([anDonnees]), code),
    kpis,
    sections,
    source: sources.join(' ; ') || 'FAOSTAT',
    filename: nomFichier(t.filename, code),
    language: lang,
  };
}

/* ════════════════════════════════════ Mines ════════════════════════════════════ */

export function specMiningPdf(mining, langue = 'fr') {
  const code = mining?.country_iso3 || '';
  const { lang, t: tc, nom, vol, donnee, annees } = outils(langue, code, mining?.country_name);
  const t = tc.mining;
  const parMineral = mining?.data_by_commodity || {};
  const mineraux = Object.entries(parMineral).filter(([, recs]) => recs?.length);
  const ans = Array.isArray(mining?.years_covered) && mining.years_covered.length
    ? [...mining.years_covered].sort((a, b) => a - b)
    : [...new Set(mineraux.flatMap(([, recs]) => recs.map((r) => r.year)))].filter(Number.isInteger).sort((a, b) => a - b);
  const dernierAn = mining?.latest_year || ans[ans.length - 1];
  const jeux = [...new Set(mineraux.flatMap(([, recs]) => recs.map((r) => r.source_dataset)).filter(Boolean))];

  const kpis = [
    { label: t.kMinerals, value: String(mineraux.length), accent: 'gold' },
    { label: t.kRecords, value: String(mining?.total_records ?? 0), accent: 'terra' },
    { label: t.kLatest, value: dernierAn ? String(dernierAn) : tc.na, accent: 'green' },
    { label: t.kDatasets, value: String(jeux.length), accent: 'gold' },
  ];

  // « Mineral Commodity Summaries 2024 », « … 2025 » → « Mineral Commodity Summaries 2024, 2025 ».
  const editions = (noms) => {
    const groupes = new Map();
    noms.forEach((n) => {
      const [, base = n, an = ''] = /^(.*\S)\s+(\d{4})$/.exec(n) || [];
      groupes.set(base, [...(groupes.get(base) || []), an].filter(Boolean));
    });
    return [...groupes].map(([base, ans]) => [base, [...new Set(ans)].sort().join(', ')].filter(Boolean).join(' '));
  };

  // « Perlite — Mine production, estimated 2024 » → « Mine production, estimated ».
  const mesure = (r) => /^.+ — (.+) \d{4}$/.exec(r?.usgs_table_name || '')?.[1];

  const sections = [];
  const region = getRegionName(mining?.region, lang) || donnee(mining?.region) || tc.na;
  sections.push({
    title: t.profileTitle,
    keyValues: [
      { label: t.profile.country, value: nom },
      { label: t.profile.region, value: region },
      { label: t.profile.years, value: ans.length ? annees(ans) : tc.na },
      { label: t.profile.minerals, value: String(mineraux.length) },
      { label: t.profile.records, value: String(mining?.total_records ?? 0) },
      { label: t.profile.datasets, value: jeux.length ? editions(jeux).join(' ; ') : tc.na },
    ],
  });
  if (mineraux.length) {
    // Dernière valeur publiée et variation sur l'année d'avant, même unité.
    const pctVar = (v) => `${v > 0 ? '+' : ''}${nombre(v, lang, 1)}${estAnglais(lang) ? '' : ' '}%`;
    sections.push({
      title: t.synthTitle(dernierAn || tc.na),
      table: {
        columns: [
          { key: 'mineral', label: t.cols.mineral, width: 2 },
          { key: 'latest', label: t.synthCols.latest, width: 1.6, align: 'right' },
          { key: 'year', label: t.synthCols.year, width: 0.7, align: 'right' },
          { key: 'previous', label: t.synthCols.previous, width: 1.6, align: 'right' },
          { key: 'change', label: t.synthCols.change, width: 0.9, align: 'right' },
        ],
        rows: mineraux.map(([mineral, recs]) => {
          const tries = [...recs].filter((r) => estNombre(r.value)).sort((a, b) => a.year - b.year);
          const der = tries[tries.length - 1];
          const avant = der ? tries.filter((r) => r.year < der.year && r.unit === der.unit).pop() : null;
          const avecUnite = (r) => (r ? `${vol(r.value)} ${donnee(r.unit) || ''}`.trim() : tc.na);
          return {
            mineral: donnee(mineral),
            latest: avecUnite(der),
            year: der ? String(der.year) : '—',
            previous: avant ? `${avecUnite(avant)} (${avant.year})` : tc.na,
            change: der && avant && avant.value ? pctVar(((der.value - avant.value) / avant.value) * 100) : '—',
          };
        }),
      },
    });
    sections.push({ paragraphs: [t.synthText] });
    sections.push({
      title: t.tableTitle,
      table: {
        columns: [
          { key: 'mineral', label: t.cols.mineral, width: 1.9 },
          { key: 'code', label: t.cols.code, width: 0.6 },
          { key: 'unit', label: tc.cols.unit, width: 1.3 },
          ...ans.map((a) => ({ key: String(a), label: String(a), width: 1.15, align: 'right' })),
          { key: 'source', label: t.cols.source, width: 2.4 },
        ],
        rows: mineraux.map(([mineral, recs]) => {
          const tries = [...recs].sort((a, b) => a.year - b.year);
          const unite = tries[tries.length - 1]?.unit;
          const parAn = Object.fromEntries(tries.map((r) => [r.year, r]));
          const m = [...new Set(tries.map(mesure).filter(Boolean))].map(donnee);
          const src = editions([...new Set(tries.map((r) => r.source_dataset).filter(Boolean))]);
          return Object.fromEntries([
            ['mineral', donnee(mineral)],
            ['code', [...new Set(tries.map((r) => r.commodity_code).filter(Boolean))].join(', ') || '—'],
            ['unit', donnee(unite) || '—'],
            // Une année publiée dans une autre unité que la dernière garde son unité.
            ...ans.map((a) => {
              const r = parAn[a];
              const v = r && estNombre(r.value) ? vol(r.value) : tc.na;
              return [String(a), r && r.unit && r.unit !== unite ? `${v} ${donnee(r.unit)}` : v];
            }),
            ['source', [...m, ...src].join(' · ') || '—'],
          ]);
        }),
      },
    });
    sections.push({ paragraphs: t.tableText });
  } else {
    sections.push({ title: t.tableTitle, paragraphs: [t.none] });
  }

  const cov = mining?.coverage;
  if (cov) {
    sections.push({
      title: t.coverageTitle,
      keyValues: [
        { label: t.coverage.status, value: t.status[cov.status] || cov.status || tc.na },
        cov.note && { label: t.coverage.note, value: donnee(cov.note) },
        cov.sources_consulted?.length && { label: t.coverage.consulted, value: cov.sources_consulted.map(donnee).join(' ; ') },
        cov.usgs_edition && { label: t.coverage.edition, value: `${donnee(cov.usgs_edition)}${cov.usgs_source_url ? ` — ${cov.usgs_source_url}` : ''}` },
      ].filter(Boolean),
    });
  }

  sections.push(avertissement(tc, t.sources));

  return {
    moduleLabel: tc.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(ans.length ? annees(ans) : tc.na, code),
    kpis,
    sections,
    source: jeux.length ? editions(jeux).join(' ; ') : donnee(cov?.usgs_edition) || 'USGS',
    filename: nomFichier(t.filename, code),
    language: lang,
  };
}

/* ═══════════════════════════════════ Débouchés ═══════════════════════════════════ */

// Réserve de couverture : phrase gabarit du serveur, recomposée en arabe comme
// à l'écran (ProductionOutlets.jsx) ; toute autre réserve passe par le
// dictionnaire des données.
const COUVERTURE_LIMITEE = /^Couverture (\S+) limitée à (\d+) pays africain\(s\) pour « (.+?) » dans notre base actuelle/;

function texteReserve(reserve, lang) {
  const m = lang === 'ar' && COUVERTURE_LIMITEE.exec(reserve);
  if (!m) return trDonnee(reserve, lang);
  const [, institution, n, libelle] = m;
  return `تغطية ${institution} في قاعدتنا الحالية مقتصرة على ${n} بلد(ان) أفريقي(ة) بالنسبة إلى «${trDonnee(libelle, lang)}» — فالترتيب أو الحصة القارية المحسوبة على عدد قليل كهذا من البلدان لا تعكس ريادة فعلية: يُرجَّح جدًا وجود منتجين أفارقة آخرين لم تُدرَج بياناتهم بعد. تُعامَل هذه البيانات على أنها جزئية، لا على أنها ترتيب موثوق.`;
}

export function specDebouchesPdf(profil, langue = 'fr') {
  const code = profil?.country_iso3 || '';
  const { lang, t: tc, nom, vol, usd, pct, donnee } = outils(langue, code);
  const t = tc.outlets;
  const produits = profil?.products || [];
  const suivis = profil?.total_tracked ?? produits.length;
  const compte = (ds) => produits.filter((p) => p.dataset === ds).length;

  const kpis = [
    { label: t.kLinked, value: String(produits.length), sub: t.shown(produits.length, suivis), accent: 'gold' },
    { label: t.kTracked, value: String(suivis), accent: 'terra' },
    { label: t.kFirst, value: String(produits.filter((p) => p.rank === 1).length), accent: 'green' },
    { label: t.kDatasets, value: `${compte('agri')} / ${compte('mining')} / ${compte('manufacturing')}`, accent: 'gold' },
  ];

  const production = (p) => {
    if (!estNombre(p.value)) return tc.na;
    return p.unit === 'USD' ? usd(p.value) : `${vol(p.value)} ${donnee(p.unit) || ''}`.trim();
  };

  const sections = [];
  if (produits.length) {
    sections.push({
      title: t.tableTitle,
      table: {
        columns: [
          { key: 'product', label: t.cols.product, width: 2.3 },
          { key: 'hs', label: t.cols.hs, width: 0.8 },
          { key: 'output', label: t.cols.output, width: 1.6, align: 'right' },
          { key: 'rank', label: t.cols.rank, width: 2 },
          { key: 'share', label: t.cols.share, width: 0.7, align: 'right' },
          { key: 'source', label: t.cols.source, width: 1.4 },
        ],
        rows: produits.map((p) => ({
          // Astérisque : une réserve accompagne la ligne (liste plus bas).
          product: `${donnee(p.commodity)}${p.coverage_caveat || p.commodity_caveat ? ' *' : ''}`,
          hs: p.hs_code || '—',
          output: production(p),
          rank: p.rank ? t.rankOf(p.rank, p.total_countries) : tc.na,
          share: pct(p.share_pct, 1),
          source: [p.institution, p.year, t.datasets[p.dataset] ? `(${t.datasets[p.dataset]})` : ''].filter(Boolean).join(' '),
        })),
      },
    });
    sections.push({ paragraphs: t.tableText(produits.length, suivis) });

    const reserves = produits.filter((p) => p.coverage_caveat || p.commodity_caveat);
    if (reserves.length) {
      sections.push({
        title: t.caveatsTitle,
        keyValues: reserves.map((p) => ({
          label: `${donnee(p.commodity)} * (${p.hs_code})`,
          value: texteReserve(p.coverage_caveat || p.commodity_caveat, lang),
        })),
      });
      sections.push({ paragraphs: [t.caveatsText] });
    }
  } else {
    sections.push({ title: t.tableTitle, paragraphs: [t.none] });
  }

  sections.push(avertissement(tc, t.sources));

  return {
    moduleLabel: tc.module,
    badge: t.badge,
    title: t.title(nom),
    subtitle: t.subtitle(code),
    kpis,
    sections,
    source: t.source,
    filename: nomFichier(t.filename, code),
    language: lang,
  };
}
