/**
 * Fiches PDF du module Logistique : un port, un aéroport, un corridor.
 *
 * Même bâtisseur que les autres modules (utils/opportunityPdf.js) : bandeau
 * avec le logo du site, cartes, tableaux, pied paginé. Source : la réponse
 * du backend telle que la fenêtre de détail l'affiche
 * (`GET /logistics/ports/{id}`, `GET /logistics/air/airports/{id}`, un
 * élément de `GET /logistics/land/corridors`).
 *
 * Une valeur que la source ne publie pas s'écrit « non publié », jamais 0.
 * Une valeur estimée (champ `nature` du bloc = « estimation ») porte la
 * mention « estimé » ; le backend ne sert plus les valeurs générées. Les
 * libellés de données n'existant qu'en une langue restent tels quels, sauf
 * en arabe où trDonnee() les traduit quand le dictionnaire les connaît.
 * Les téléphones sont écrits tels que publiés, seuls dans leur texte : la
 * couche arabe du PDF garde l'ordre des groupes de chiffres.
 */
import { nombre } from './nombres';
import { AFRICAN_COUNTRIES } from './countryCodes';
import { trDonnee } from '../i18n/donnees';

const COMMUN = {
  fr: {
    module: 'MODULE LOGISTIQUE',
    na: 'non publié',
    yes: 'oui',
    no: 'non',
    rank: 'rang',
    warning: 'Avertissement',
    estimated: 'estimé',
    contactsNotice: "Les coordonnées (téléphones, courriels, sites web) sont reproduites telles que publiées par les organismes : les vérifier auprès d'eux avant tout usage. Cette fiche est informative ; elle n'engage ni les organismes cités ni l'éditeur.",
    u: { t: 't', h: 'h', days: 'jours', km: 'km', teuYear: 'TEU/an', tYear: 't/an', paxYear: 'passagers/an', sqm: 'm²', trucksDay: 'camions/jour', m: 'm', ha: 'ha' },
  },
  en: {
    module: 'LOGISTICS MODULE',
    na: 'not published',
    yes: 'yes',
    no: 'no',
    rank: 'rank',
    warning: 'Disclaimer',
    estimated: 'estimated',
    contactsNotice: 'Contact details (phone numbers, emails, websites) are reproduced as published by the organisations: check them with the organisation before any use. This profile is for information only; it commits neither the organisations cited nor the publisher.',
    u: { t: 't', h: 'h', days: 'days', km: 'km', teuYear: 'TEU/yr', tYear: 't/yr', paxYear: 'passengers/yr', sqm: 'm²', trucksDay: 'trucks/day', m: 'm', ha: 'ha' },
  },
  ar: {
    module: 'وحدة اللوجستيك',
    na: 'غير منشور',
    yes: 'نعم',
    no: 'لا',
    rank: 'الترتيب',
    warning: 'تنبيه',
    estimated: 'تقديري',
    contactsNotice: 'بيانات الاتصال (الهواتف، البريد الإلكتروني، المواقع) منقولة كما نشرتها الجهات المعنية: يُرجى التحقق منها لدى الجهة قبل أي استعمال. هذه البطاقة إعلامية ولا تُلزم الجهات المذكورة ولا الناشر.',
    u: { t: 'طن', h: 'ساعة', days: 'يوم', km: 'كم', teuYear: 'TEU/سنة', tYear: 'طن/سنة', paxYear: 'مسافر/سنة', sqm: 'متر مربع', trucksDay: 'شاحنة/يوم', m: 'م', ha: 'هكتار' },
  },
};

// Valeurs que la source met à la place d'une donnée absente.
const VIDES = new Set(['na', 'n/a', 'non disponible', 'not available', 'voir site officiel',
  'voir direction aéroportuaire', 'contact@authority.com', '-', '—']);
// Pictogrammes des données (ℹ️, ⚠️, ⏱…) : absents des polices du PDF.
const PICTOS = /[\u{1F000}-\u{1FAFF}\u{2300}-\u{23FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}\u{2139}]/gu;

const estNombre = (v) => typeof v === 'number' && Number.isFinite(v);
const propre = (v) => String(v).replace(PICTOS, '').replace(/\s+/g, ' ').trim();

/** Valeur absente, vide ou « NA / Non disponible… » : la source ne la publie pas. */
export function publiee(v) {
  if (v == null || v === false) return false;
  if (typeof v === 'number') return Number.isFinite(v);
  if (Array.isArray(v)) return v.some(publiee);
  if (typeof v === 'object') return false;
  const s = propre(v);
  return s !== '' && !VIDES.has(s.toLowerCase()) && !/^N\/A\b/i.test(s);
}

/**
 * Un titre trop long pour le bandeau (une ligne, à côté du logo) : la
 * précision entre parenthèses ou après « : » passe dans le sous-titre.
 */
function decouperTitre(nom) {
  if (nom.length <= 46) return [nom, ''];
  const m = nom.match(/^(.+?)\s*\((.+)\)\s*$/) || nom.match(/^(.+?)\s*:\s*(.+)$/);
  return m ? [m[1], m[2]] : [nom, ''];
}

const nomFichier = (...parties) => ['ZLECAf_Logistique', ...parties, new Date().toISOString().slice(0, 10)]
  .filter(Boolean)
  .map((s) => String(s).trim().replace(/[\\/:*?"<>|\s]+/g, '_'))
  .join('_');

/** Formateurs communs aux trois fiches, dans la langue du PDF. */
function outils(langue) {
  const c = COMMUN[langue] || COMMUN.fr;
  const na = c.na;
  const num = (v, d = 0) => (estNombre(v) ? nombre(v, langue, d) : na);
  // Libellé de donnée (traduit en arabe s'il est au dictionnaire), sinon « non publié ».
  const txt = (v) => (publiee(v) ? trDonnee(propre(v), langue) : na);
  // Nombre ou intervalle publié (« 120-168 ») suivi de son unité.
  const unite = (v, u, d = 1) => (estNombre(v) ? `${nombre(v, langue, d)} ${u}`
    : publiee(v) ? `${propre(v)} ${u}` : na);
  const liste = (arr, sep = ', ') => {
    const l = (arr || []).filter(publiee).map((x) => trDonnee(propre(x), langue));
    return l.length ? l.join(sep) : na;
  };
  const pays = (iso, repli) => AFRICAN_COUNTRIES[iso]?.[`name_${langue}`] || repli || iso || na;
  const site = (u) => propre(u).replace(/^https?:\/\//, '').replace(/\/$/, '');
  const an = (v) => (publiee(v) ? String(v) : '');
  return { c, na, num, txt, unite, liste, pays, site, an };
}

// ───────────────────────────── PORT ─────────────────────────────

const T_PORT = {
  fr: {
    badge: 'FICHE PORT',
    subtitle: (pays, locode, type) => [pays, locode && `UN/LOCODE ${locode}`, type].filter(Boolean).join(' · '),
    teu: 'Trafic conteneurs', tonnage: 'Tonnage global', calls: 'Escales navires', dwell: 'Dwell time',
    waiting: 'Attente au mouillage', lsci: 'Connectivité LSCI',
    worldRank: (r) => `rang mondial ${r}`,
    identity: 'Identité du port',
    name: 'Nom', country: 'Pays', locode: 'UN/LOCODE', type: 'Type de port', gps: 'Coordonnées GPS',
    authority: 'Autorité portuaire',
    address: 'Adresse', phone: 'Téléphone', email: 'Courriel', website: 'Site web',
    departments: { direction_generale: 'Direction générale', capitainerie: 'Capitainerie', exploitation_conteneurs: 'Exploitation conteneurs', douane_port: 'Douane du port' },
    terminals: 'Infrastructures — terminaux',
    tCols: { name: 'Terminal', operator: 'Opérateur', type: 'Type', capacity: 'Capacité', quay: 'Quai (m)', draft: "Tirant d'eau (m)" },
    terminalsText: "Capacité : volume que le terminal peut traiter en un an. Longueur de quai : linéaire où les navires accostent. Tirant d'eau maximal : profondeur d'eau à quai, qui limite la taille des navires accueillis.",
    traffic: 'Statistiques de trafic',
    refYear: 'Année de référence', containerCalls: 'Escales porte-conteneurs', source: 'Source', note: 'Note',
    projection: (a) => `Projection ${a}`,
    evolution: 'Évolution du trafic',
    trCols: { year: 'Année', teu: 'TEU', vessels: 'Navires', containerCalls: 'Porte-conteneurs', tons: 'Tonnage (t)', wait: 'Attente (h)', source: 'Source' },
    trafficText: "TEU (équivalent vingt pieds, EVP) : unité de comptage des conteneurs — un conteneur de 20 pieds vaut 1 TEU, un 40 pieds 2 TEU. Le tonnage global additionne toutes les marchandises (conteneurs, vrac, roulier). Une année marquée « estimé » n'est pas publiée par une source : la colonne Source donne la base de l'estimation.",
    perf: 'Performance portuaire',
    waitingFull: 'Attente au mouillage', occupancy: (a) => `Taux d'occupation des quais ${a}`, updated: 'Mise à jour',
    perfText: "Attente au mouillage : temps moyen entre l'arrivée du navire en rade et son accostage, signe de congestion. Taux d'occupation des quais : part du temps où les postes à quai sont occupés. Une valeur marquée « estimé » n'est pas publiée par une source ; une valeur sans source n'est pas reprise.",
    trs: 'Temps de séjour des conteneurs (dwell time) et TRS',
    dwellFull: 'Dwell time (séjour moyen des conteneurs)', turnaround: 'Rotation navire', clearance: 'Dédouanement',
    vesselWaiting: 'Attente des navires', cppi: 'Rang CPPI (Banque mondiale)', dataYear: 'Année des données',
    reliability: 'Fiabilité de la source', methodology: 'Méthodologie', publication: 'Publication', notes: 'Notes',
    sourceWarning: 'Mise en garde de la source', noOfficial: 'Pourquoi pas de données officielles', estimation: "Méthode d'estimation",
    best: 'Meilleure performance', target: 'Objectif de séjour', inProgress: 'Étude TRS OMD en cours', link: 'Lien source',
    facts: 'Données factuelles utilisées',
    trsText: "Dwell time : nombre moyen de jours entre le déchargement d'un conteneur et sa sortie du port, dédouanement compris. TRS (Time Release Study, Organisation mondiale des douanes) : étude qui mesure le délai de mainlevée des marchandises. CPPI (Container Port Performance Index, Banque mondiale) : classement mondial des ports à conteneurs, 1 = le plus performant.",
    benchmarks: 'Repères de comparaison (dwell time)',
    bAfrica: 'Moyenne Afrique', bNorth: 'Moyenne Afrique du Nord', bCasa: 'Casablanca', bTunis: 'Tunis', bWorld: 'Médiane mondiale (CNUCED, S2 2023)',
    connect: 'Connectivité maritime et performance logistique du pays',
    lsciValue: (a) => `LSCI (CNUCED)${a ? ` ${a}` : ''}`, lsciRank: 'Rang mondial LSCI',
    lpi: (a) => `LPI${a ? ` ${a}` : ''} — note globale (1-5)`, lpiCustoms: 'LPI — douane', lpiInfra: 'LPI — infrastructures',
    lpiTracking: 'LPI — suivi des envois', lpiTime: 'LPI — ponctualité', lpiWorld: 'LPI — rang mondial', lpiAfrica: 'LPI — rang en Afrique',
    connectText: "LSCI (indice de connectivité des transports maritimes réguliers, CNUCED) : intégration du port dans les réseaux de lignes régulières ; plus il est élevé, mieux le port est desservi. LPI (indice de performance logistique, Banque mondiale) : note du pays de 1 à 5 sur la douane, les infrastructures, le suivi des envois et la ponctualité.",
    lines: 'Lignes maritimes régulières',
    lCols: { service: 'Service', carrier: 'Armateur', frequency: 'Fréquence', rotation: 'Rotation' },
    transit: (j) => `transit Marseille–Alger : ${j} j`,
    noLines: 'Aucune ligne régulière référencée par la source.',
    agents: 'Agents maritimes et opérateurs',
    aCols: { agent: 'Agent', activity: 'Activité', address: 'Adresse', contact: 'Contact' },
    noAgents: 'Aucun agent maritime référencé par la source.',
    network: 'Réseau logistique du port',
    nCarriers: 'Armateurs mondiaux présents', nTerminalOps: 'Opérateurs de terminaux', nRegional: 'Spécialistes régionaux',
    nBrokers: 'Commissionnaires en douane', nProviders: 'Prestataires disponibles', nRoad: 'Desserte routière', nRail: 'Desserte ferroviaire', nAirport: 'Aéroport',
    noticeData: "Données reprises des sources publiques citées (CNUCED, Banque mondiale, Organisation mondiale des douanes, autorités portuaires, armateurs), à la date indiquée pour chacune. Certaines valeurs sont des estimations, signalées comme telles par la source ; une valeur absente est notée « non publié ».",
    sourceFooter: 'CNUCED (LSCI), OMD (TRS), Banque mondiale (LPI, CPPI), autorités portuaires',
    file: 'Port',
  },
  en: {
    badge: 'PORT PROFILE',
    subtitle: (pays, locode, type) => [pays, locode && `UN/LOCODE ${locode}`, type].filter(Boolean).join(' · '),
    teu: 'Container traffic', tonnage: 'Total tonnage', calls: 'Vessel calls', dwell: 'Dwell time',
    waiting: 'Anchorage waiting', lsci: 'LSCI connectivity',
    worldRank: (r) => `world rank ${r}`,
    identity: 'Port identity',
    name: 'Name', country: 'Country', locode: 'UN/LOCODE', type: 'Port type', gps: 'GPS coordinates',
    authority: 'Port authority',
    address: 'Address', phone: 'Phone', email: 'Email', website: 'Website',
    departments: { direction_generale: 'General management', capitainerie: "Harbour master's office", exploitation_conteneurs: 'Container operations', douane_port: 'Port customs' },
    terminals: 'Infrastructure — terminals',
    tCols: { name: 'Terminal', operator: 'Operator', type: 'Type', capacity: 'Capacity', quay: 'Quay (m)', draft: 'Draft (m)' },
    terminalsText: 'Capacity: volume the terminal can handle in a year. Quay length: berth line where ships moor. Maximum draft: water depth at the quay, which limits the size of ships the terminal can receive.',
    traffic: 'Traffic statistics',
    refYear: 'Reference year', containerCalls: 'Container ship calls', source: 'Source', note: 'Note',
    projection: (a) => `${a} projection`,
    evolution: 'Traffic trend',
    trCols: { year: 'Year', teu: 'TEU', vessels: 'Vessels', containerCalls: 'Container ships', tons: 'Tonnage (t)', wait: 'Waiting (h)', source: 'Source' },
    trafficText: 'TEU (twenty-foot equivalent unit): the unit used to count containers — a 20-foot container is 1 TEU, a 40-foot one 2 TEU. Total tonnage adds up all cargo (containers, bulk, ro-ro). A year marked "estimated" is not published by a source: the Source column gives the basis of the estimate.',
    perf: 'Port performance',
    waitingFull: 'Anchorage waiting time', occupancy: (a) => `Berth occupancy rate ${a}`, updated: 'Last updated',
    perfText: 'Anchorage waiting: average time between a ship arriving at the roads and berthing, a sign of congestion. Berth occupancy rate: share of time the berths are occupied. A value marked "estimated" is not published by a source; a value without a source is left out.',
    trs: 'Container dwell time and TRS',
    dwellFull: 'Dwell time (average container stay)', turnaround: 'Vessel turnaround', clearance: 'Customs clearance',
    vesselWaiting: 'Vessel waiting', cppi: 'CPPI rank (World Bank)', dataYear: 'Data year',
    reliability: 'Source reliability', methodology: 'Methodology', publication: 'Publication', notes: 'Notes',
    sourceWarning: 'Source caveat', noOfficial: 'Why no official data', estimation: 'Estimation method',
    best: 'Best performance', target: 'Dwell time target', inProgress: 'WCO TRS study in progress', link: 'Source link',
    facts: 'Factual data used',
    trsText: 'Dwell time: average number of days between a container being unloaded and leaving the port, customs clearance included. TRS (Time Release Study, World Customs Organization): a study measuring the time taken to release goods. CPPI (Container Port Performance Index, World Bank): world ranking of container ports, 1 = best performing.',
    benchmarks: 'Comparison benchmarks (dwell time)',
    bAfrica: 'Africa average', bNorth: 'North Africa average', bCasa: 'Casablanca', bTunis: 'Tunis', bWorld: 'World median (UNCTAD, H2 2023)',
    connect: "Maritime connectivity and the country's logistics performance",
    lsciValue: (a) => `LSCI (UNCTAD)${a ? ` ${a}` : ''}`, lsciRank: 'LSCI world rank',
    lpi: (a) => `LPI${a ? ` ${a}` : ''} — overall score (1-5)`, lpiCustoms: 'LPI — customs', lpiInfra: 'LPI — infrastructure',
    lpiTracking: 'LPI — tracking and tracing', lpiTime: 'LPI — timeliness', lpiWorld: 'LPI — world rank', lpiAfrica: 'LPI — rank in Africa',
    connectText: "LSCI (Liner Shipping Connectivity Index, UNCTAD): how well the port is integrated into liner shipping networks; the higher, the better served. LPI (Logistics Performance Index, World Bank): the country's score from 1 to 5 on customs, infrastructure, tracking and timeliness.",
    lines: 'Regular shipping lines',
    lCols: { service: 'Service', carrier: 'Carrier', frequency: 'Frequency', rotation: 'Rotation' },
    transit: (j) => `Marseille–Algiers transit: ${j} d`,
    noLines: 'No regular line listed by the source.',
    agents: 'Shipping agents and operators',
    aCols: { agent: 'Agent', activity: 'Activity', address: 'Address', contact: 'Contact' },
    noAgents: 'No shipping agent listed by the source.',
    network: 'Port logistics network',
    nCarriers: 'Global carriers present', nTerminalOps: 'Terminal operators', nRegional: 'Regional specialists',
    nBrokers: 'Customs brokers', nProviders: 'Service providers available', nRoad: 'Road links', nRail: 'Rail links', nAirport: 'Airport',
    noticeData: 'Data taken from the public sources cited (UNCTAD, World Bank, World Customs Organization, port authorities, carriers), as of the date shown for each. Some values are estimates, flagged as such by the source; a missing value is shown as "not published".',
    sourceFooter: 'UNCTAD (LSCI), WCO (TRS), World Bank (LPI, CPPI), port authorities',
    file: 'Port',
  },
  ar: {
    badge: 'بطاقة ميناء',
    subtitle: (pays, locode, type) => [pays, locode && `UN/LOCODE ${locode}`, type].filter(Boolean).join(' · '),
    teu: 'حركة الحاويات', tonnage: 'الحمولة الإجمالية', calls: 'توقفات السفن', dwell: 'مدة بقاء الحاويات',
    waiting: 'الانتظار في المرسى', lsci: 'الربط LSCI',
    worldRank: (r) => `الترتيب العالمي ${r}`,
    identity: 'هوية الميناء',
    name: 'الاسم', country: 'البلد', locode: 'UN/LOCODE', type: 'نوع الميناء', gps: 'إحداثيات GPS',
    authority: 'السلطة المينائية',
    address: 'العنوان', phone: 'الهاتف', email: 'البريد الإلكتروني', website: 'الموقع الإلكتروني',
    departments: { direction_generale: 'الإدارة العامة', capitainerie: 'قبطانية الميناء', exploitation_conteneurs: 'استغلال الحاويات', douane_port: 'جمارك الميناء' },
    terminals: 'البنية التحتية — المحطات',
    tCols: { name: 'المحطة', operator: 'المشغّل', type: 'النوع', capacity: 'الطاقة', quay: 'الرصيف (م)', draft: 'الغاطس (م)' },
    terminalsText: 'الطاقة: الحجم الذي تستطيع المحطة معالجته في سنة. طول الرصيف: الخط الذي ترسو عليه السفن. أقصى غاطس: عمق المياه عند الرصيف، وهو يحدّ من حجم السفن المستقبَلة.',
    traffic: 'إحصائيات الحركة',
    refYear: 'السنة المرجعية', containerCalls: 'توقفات سفن الحاويات', source: 'المصدر', note: 'ملاحظة',
    projection: (a) => `توقع ${a}`,
    evolution: 'تطور الحركة',
    trCols: { year: 'السنة', teu: 'TEU', vessels: 'السفن', containerCalls: 'سفن الحاويات', tons: 'الحمولة (طن)', wait: 'الانتظار (ساعة)', source: 'المصدر' },
    trafficText: 'TEU (وحدة مكافئة لعشرين قدمًا): وحدة عدّ الحاويات — الحاوية ذات 20 قدمًا تساوي 1 TEU وذات 40 قدمًا 2 TEU. تجمع الحمولة الإجمالية كل البضائع (حاويات، سائبة، دحرجة). السنة الموسومة «تقديري» لا ينشرها أي مصدر، ويبيّن عمود المصدر أساس التقدير.',
    perf: 'أداء الميناء',
    waitingFull: 'مدة الانتظار في المرسى', occupancy: (a) => `نسبة إشغال الأرصفة ${a}`, updated: 'آخر تحديث',
    perfText: 'الانتظار في المرسى: متوسط المدة بين وصول السفينة إلى المرسى ورسوّها، وهو مؤشر على الازدحام. نسبة إشغال الأرصفة: حصة الوقت الذي تكون فيه الأرصفة مشغولة. القيمة الموسومة «تقديري» لا ينشرها أي مصدر، والقيمة التي لا مصدر لها لا تُدرج.',
    trs: 'مدة بقاء الحاويات ودراسة TRS',
    dwellFull: 'مدة بقاء الحاويات (المتوسط)', turnaround: 'دوران السفينة', clearance: 'التخليص الجمركي',
    vesselWaiting: 'انتظار السفن', cppi: 'ترتيب CPPI (البنك الدولي)', dataYear: 'سنة البيانات',
    reliability: 'موثوقية المصدر', methodology: 'المنهجية', publication: 'النشر', notes: 'ملاحظات',
    sourceWarning: 'تحفّظ المصدر', noOfficial: 'سبب غياب البيانات الرسمية', estimation: 'منهجية التقدير',
    best: 'أفضل أداء', target: 'المدة المستهدفة', inProgress: 'دراسة TRS لمنظمة الجمارك العالمية قيد الإنجاز', link: 'رابط المصدر',
    facts: 'البيانات الواقعية المستخدمة',
    trsText: 'مدة بقاء الحاويات: متوسط عدد الأيام بين تفريغ الحاوية وخروجها من الميناء، بما في ذلك التخليص الجمركي. TRS (دراسة زمن الإفراج، منظمة الجمارك العالمية): دراسة تقيس مدة الإفراج عن البضائع. CPPI (مؤشر أداء موانئ الحاويات، البنك الدولي): ترتيب عالمي لموانئ الحاويات، 1 = الأفضل أداءً.',
    benchmarks: 'معايير المقارنة (مدة البقاء)',
    bAfrica: 'المتوسط الأفريقي', bNorth: 'متوسط شمال أفريقيا', bCasa: 'الدار البيضاء', bTunis: 'تونس', bWorld: 'الوسيط العالمي (الأونكتاد، النصف الثاني 2023)',
    connect: 'الربط البحري والأداء اللوجستي للبلد',
    lsciValue: (a) => `LSCI (الأونكتاد)${a ? ` ${a}` : ''}`, lsciRank: 'الترتيب العالمي LSCI',
    lpi: (a) => `LPI${a ? ` ${a}` : ''} — النتيجة الإجمالية (1-5)`, lpiCustoms: 'LPI — الجمارك', lpiInfra: 'LPI — البنية التحتية',
    lpiTracking: 'LPI — تتبع الشحنات', lpiTime: 'LPI — الالتزام بالمواعيد', lpiWorld: 'LPI — الترتيب العالمي', lpiAfrica: 'LPI — الترتيب في أفريقيا',
    connectText: 'LSCI (مؤشر الربط بالنقل البحري المنتظم، الأونكتاد): مدى اندماج الميناء في شبكات الخطوط المنتظمة؛ كلما ارتفع كان الميناء أفضل خدمة. LPI (مؤشر الأداء اللوجستي، البنك الدولي): نتيجة البلد من 1 إلى 5 في الجمارك والبنية التحتية وتتبع الشحنات والالتزام بالمواعيد.',
    lines: 'الخطوط البحرية المنتظمة',
    lCols: { service: 'الخدمة', carrier: 'شركة الملاحة', frequency: 'التواتر', rotation: 'الدورة' },
    transit: (j) => `العبور مرسيليا–الجزائر: ${j} يوم`,
    noLines: 'لا توجد خطوط منتظمة مسجلة لدى المصدر.',
    agents: 'الوكلاء البحريون والمشغّلون',
    aCols: { agent: 'الوكيل', activity: 'النشاط', address: 'العنوان', contact: 'الاتصال' },
    noAgents: 'لا يوجد وكلاء بحريون مسجلون لدى المصدر.',
    network: 'الشبكة اللوجستية للميناء',
    nCarriers: 'شركات الملاحة العالمية الحاضرة', nTerminalOps: 'مشغّلو المحطات', nRegional: 'المتخصصون الإقليميون',
    nBrokers: 'المعشّرون الجمركيون', nProviders: 'مقدمو الخدمات المتاحون', nRoad: 'الربط البري', nRail: 'الربط بالسكك الحديدية', nAirport: 'المطار',
    noticeData: 'بيانات مأخوذة من المصادر العامة المذكورة (الأونكتاد، البنك الدولي، منظمة الجمارك العالمية، السلطات المينائية، شركات الملاحة) في التاريخ المبيّن لكل منها. بعض القيم تقديرات يصفها المصدر بذلك؛ والقيمة الغائبة تُكتب «غير منشور».',
    sourceFooter: 'UNCTAD (LSCI), WCO (TRS), World Bank (LPI, CPPI)',
    file: 'Port_ar',
  },
};

export function specFichePortPdf(port, langue = 'fr') {
  const t = T_PORT[langue] || T_PORT.fr;
  const { c, na, num, txt, unite, liste, pays, site, an } = outils(langue);
  const u = c.u;
  const stats = port.latest_stats || {};
  const metrics = port.performance_metrics || {};
  const trs = port.trs_analysis || {};
  const auth = port.port_authority || {};
  const lsci = port.lsci || {};
  const lpi = port.lpi_2023 || {};
  const nom = txt(port.port_name);
  const nomPays = pays(port.country_iso, port.country_name);
  const [titre, suite] = decouperTitre(nom);
  // Bloc dont la source ne publie pas les valeurs telles quelles (champ `nature`
  // servi par le backend) : chaque valeur porte la mention « estimé ».
  const estime = (bloc) => (bloc?.nature === 'estimation' ? c.estimated : '');
  const marque = (texte, bloc) => (estime(bloc) && texte !== na ? `${texte} (${c.estimated})` : texte);

  const kpis = [
    { label: t.teu, value: num(stats.container_throughput_teu), sub: ['TEU', an(stats.year), estime(stats)].filter(Boolean).join(' · '), accent: 'gold' },
    { label: t.tonnage, value: num(stats.cargo_throughput_tons), sub: [u.t, an(stats.year), estime(stats)].filter(Boolean).join(' · '), accent: 'gold' },
    { label: t.calls, value: num(stats.vessel_calls), sub: [an(stats.year), estime(stats)].filter(Boolean).join(' · '), accent: 'terra' },
    { label: t.dwell, value: unite(trs.container_dwell_time_days, u.days), sub: [an(trs.data_year), estime(trs)].filter(Boolean).join(' · '), accent: 'red' },
    { label: t.waiting, value: unite(metrics.avg_waiting_time_hours, u.h), sub: estime(metrics), accent: 'red' },
    { label: t.lsci, value: num(lsci.value, 2), sub: an(lsci.year), accent: 'green' },
  ];

  const sections = [];

  sections.push({
    title: t.identity,
    keyValues: [
      { label: t.name, value: nom },
      { label: t.country, value: nomPays },
      { label: t.locode, value: publiee(port.un_locode) ? port.un_locode : na },
      { label: t.type, value: txt(port.port_type) },
      { label: t.gps, value: estNombre(port.geo_lat) && estNombre(port.geo_lon) ? `${port.geo_lat.toFixed(4)}, ${port.geo_lon.toFixed(4)}` : na },
    ],
  });

  // Autorité portuaire : coordonnées principales, puis services (capitainerie, douane…).
  if (publiee(auth.name)) {
    const kv = [
      { label: t.name, value: propre(auth.name) },
      { label: t.address, value: publiee(auth.address) ? propre(auth.address) : na },
      { label: t.phone, value: publiee(auth.contact_phone) ? propre(auth.contact_phone) : na },
      { label: t.email, value: publiee(auth.contact_email) ? propre(auth.contact_email) : na },
      { label: t.website, value: publiee(auth.website) ? site(auth.website) : na },
    ];
    Object.entries(auth.departments || {}).forEach(([cle, dep]) => {
      const valeur = [dep.label, dep.phone, dep.vhf_channel && `VHF ${dep.vhf_channel}`, dep.email, dep.website && site(dep.website)]
        .filter(publiee).map(propre).join(' · ');
      if (valeur) kv.push({ label: t.departments[cle] || cle.replace(/_/g, ' '), value: valeur });
    });
    sections.push({ title: t.authority, keyValues: kv });
  }

  const terminaux = port.terminals || [];
  if (terminaux.length) {
    const capacite = (x) => (estNombre(x.capacity_teu_year) ? `${num(x.capacity_teu_year)} ${u.teuYear}`
      : estNombre(x.capacity_tons_year) ? `${num(x.capacity_tons_year)} ${u.tYear}`
        : estNombre(x.capacity_passagers_year) ? `${num(x.capacity_passagers_year)} ${u.paxYear}` : na);
    sections.push({
      title: t.terminals,
      table: {
        columns: [
          { key: 'name', label: t.tCols.name, width: 2 },
          { key: 'operator', label: t.tCols.operator, width: 1.5 },
          { key: 'type', label: t.tCols.type, width: 1.6 },
          { key: 'capacity', label: t.tCols.capacity, width: 1.6, align: 'right' },
          { key: 'quay', label: t.tCols.quay, width: 1, align: 'right' },
          { key: 'draft', label: t.tCols.draft, width: 1.3, align: 'right' },
        ],
        rows: terminaux.map((x) => ({
          name: txt(x.name), operator: txt(x.operator), type: txt(x.type), capacity: capacite(x),
          quay: num(x.quay_length_m), draft: num(x.max_draft_m, 1),
        })),
      },
    });
    sections.push({ paragraphs: [t.terminalsText] });
  }

  // Trafic : chiffres de l'année de référence, puis la série annuelle.
  const proj = stats.year_2025_projection;
  const trafficKv = [
    { label: t.refYear, value: marque(an(stats.year) || na, stats) },
    estNombre(stats.container_vessel_calls) && { label: t.containerCalls, value: num(stats.container_vessel_calls) },
    publiee(stats.source) && { label: t.source, value: propre(stats.source) },
    publiee(stats.note) && { label: t.note, value: propre(stats.note) },
    proj && estNombre(proj.container_throughput_teu) && {
      label: t.projection(2025),
      value: `${num(proj.container_throughput_teu)} TEU${proj.source ? ` (${propre(proj.source)})` : ''}`,
    },
  ].filter(Boolean);
  sections.push({ title: t.traffic, keyValues: trafficKv });

  const serie = (port.traffic_evolution || []).slice().sort((a, b) => a.year - b.year);
  if (serie.length) {
    // Une colonne n'apparaît que si la source la renseigne pour au moins une année.
    const a = (cle) => serie.some((r) => publiee(r[cle]));
    const columns = [
      { key: 'year', label: t.trCols.year, width: 0.7 },
      { key: 'teu', label: t.trCols.teu, width: 1.1, align: 'right', fmt: (v) => num(v) },
      a('vessels') && { key: 'vessels', label: t.trCols.vessels, width: 0.9, align: 'right', fmt: (v) => num(v) },
      a('container_vessel_calls') && { key: 'container_vessel_calls', label: t.trCols.containerCalls, width: 1.4, align: 'right', fmt: (v) => num(v) },
      a('cargo_tons') && { key: 'cargo_tons', label: t.trCols.tons, width: 1.2, align: 'right', fmt: (v) => num(v) },
      a('avg_wait_time') && { key: 'avg_wait_time', label: t.trCols.wait, width: 0.9, align: 'right', fmt: (v) => num(v, 1) },
      a('source') && { key: 'source', label: t.trCols.source, width: 2.8, fmt: (v) => (publiee(v) ? propre(v) : na) },
    ].filter(Boolean);
    sections.push({ title: t.evolution, table: { columns, rows: serie.map((r) => ({ ...r, year: marque(String(r.year), r) })) } });
  }
  sections.push({ paragraphs: [t.trafficText] });

  // Seules les valeurs dont le backend sert la source restent (attente, taux
  // d'occupation) : séjour au port, productivité à quai et note d'efficacité,
  // générés, ne sont plus servis.
  const avecLibelle = (v, libelle) => (publiee(v) ? `${marque(unite(v, u.h), metrics)}${publiee(libelle) ? ` — ${propre(libelle)}` : ''}` : na);
  const perfKv = [
    { label: t.waitingFull, value: avecLibelle(metrics.avg_waiting_time_hours, metrics.avg_waiting_time_label) },
    estNombre(metrics.quay_occupancy_rate_2024_pct) && { label: t.occupancy(2024), value: marque(`${num(metrics.quay_occupancy_rate_2024_pct)} %`, metrics) },
    estNombre(metrics.quay_occupancy_rate_2025_pct) && { label: t.occupancy(2025), value: marque(`${num(metrics.quay_occupancy_rate_2025_pct)} %`, metrics) },
    publiee(metrics.source) && { label: t.source, value: propre(metrics.source) },
    publiee(metrics.last_updated) && { label: t.updated, value: propre(metrics.last_updated) },
  ].filter(Boolean);
  sections.push({ title: t.perf, keyValues: perfKv }, { paragraphs: [t.perfText] });

  const trsKv = [
    { label: t.dwellFull, value: marque(unite(trs.container_dwell_time_days, u.days), trs) },
    { label: t.turnaround, value: marque(unite(trs.vessel_turnaround_hours, u.h), trs) },
    { label: t.clearance, value: marque(unite(trs.customs_clearance_hours, u.h), trs) },
    publiee(trs.vessel_waiting_days) && { label: t.vesselWaiting, value: `${unite(trs.vessel_waiting_days, u.days)}${publiee(trs.vessel_waiting_source) ? ` (${propre(trs.vessel_waiting_source)})` : ''}` },
    { label: t.cppi, value: publiee(trs.cppi_rank) ? `${propre(trs.cppi_rank)}${publiee(trs.cppi_year) ? ` (${trs.cppi_year})` : ''}` : na },
    publiee(trs.best_performance_days) && { label: t.best, value: `${unite(trs.best_performance_days, u.days)}${publiee(trs.best_performance_date) ? ` (${propre(trs.best_performance_date)})` : ''}` },
    publiee(trs.target_dwell_hours) && { label: t.target, value: unite(trs.target_dwell_hours, u.h) },
    { label: t.dataYear, value: an(trs.data_year) || na },
    { label: t.reliability, value: txt(trs.source_reliability_label) },
    { label: t.source, value: publiee(trs.source) ? propre(trs.source) : na },
    publiee(trs.methodology) && { label: t.methodology, value: propre(trs.methodology) },
    publiee(trs.publication_date) && { label: t.publication, value: propre(trs.publication_date) },
    publiee(trs.notes) && { label: t.notes, value: propre(trs.notes) },
    publiee(trs.warning) && { label: t.sourceWarning, value: propre(trs.warning) },
    publiee(trs.no_official_data_reason) && { label: t.noOfficial, value: propre(trs.no_official_data_reason) },
    publiee(trs.estimation_methodology) && { label: t.estimation, value: propre(trs.estimation_methodology) },
    trs.wco_trs_in_progress && { label: t.inProgress, value: c.yes },
    publiee(trs.source_url || trs.wco_report_url) && { label: t.link, value: site(trs.source_url || trs.wco_report_url) },
  ].filter(Boolean);
  sections.push({ title: t.trs, keyValues: trsKv });
  const faits = (trs.factual_data_points || []).filter(publiee);
  if (faits.length) sections.push({ title: t.facts, paragraphs: faits.map((f) => `- ${propre(f)}`) });
  sections.push({ paragraphs: [t.trsText] });

  const bench = port.global_benchmarks;
  if (bench) {
    const jours = (v) => unite(v, u.days);
    const benchKv = [
      publiee(bench.africa_avg_dwell_days) && { label: t.bAfrica, value: `${jours(bench.africa_avg_dwell_days)}${publiee(bench.africa_avg_source) ? ` (${propre(bench.africa_avg_source)})` : ''}` },
      publiee(bench.north_africa_avg_dwell_days) && { label: t.bNorth, value: jours(bench.north_africa_avg_dwell_days) },
      publiee(bench.casablanca_dwell_days) && { label: t.bCasa, value: jours(bench.casablanca_dwell_days) },
      publiee(bench.tunis_dwell_days) && { label: t.bTunis, value: jours(bench.tunis_dwell_days) },
      publiee(bench.global_median_dwell_days_h2_2023) && { label: t.bWorld, value: jours(bench.global_median_dwell_days_h2_2023) },
      publiee(bench.africa_avg_note) && { label: t.note, value: propre(bench.africa_avg_note) },
      publiee(bench.source) && { label: t.source, value: propre(bench.source) },
    ].filter(Boolean);
    if (benchKv.length) sections.push({ title: t.benchmarks, keyValues: benchKv });
  }

  const connectKv = [
    { label: t.lsciValue(an(lsci.year)), value: num(lsci.value, 2) },
    publiee(lsci.note) && { label: t.note, value: propre(lsci.note) },
    { label: t.lpi(an(lpi.year)), value: num(lpi.overall_score, 2) },
    estNombre(lpi.customs_score) && { label: t.lpiCustoms, value: num(lpi.customs_score, 2) },
    estNombre(lpi.infrastructure_score) && { label: t.lpiInfra, value: num(lpi.infrastructure_score, 2) },
    estNombre(lpi.tracking_tracing_score) && { label: t.lpiTracking, value: num(lpi.tracking_tracing_score, 2) },
    estNombre(lpi.timeliness_score) && { label: t.lpiTime, value: num(lpi.timeliness_score, 2) },
    estNombre(lpi.world_rank) && { label: t.lpiWorld, value: num(lpi.world_rank) },
    estNombre(lpi.africa_rank) && { label: t.lpiAfrica, value: num(lpi.africa_rank) },
    publiee(lsci.source || lpi.source) && { label: t.source, value: [lsci.source, lpi.source].filter(publiee).map(propre).join(' ; ') },
  ].filter(Boolean);
  sections.push({ title: t.connect, keyValues: connectKv }, { paragraphs: [t.connectText] });

  const lignes = port.services || port.connectivity?.liner_services || [];
  if (lignes.length) {
    sections.push({
      title: t.lines,
      table: {
        columns: [
          { key: 'service', label: t.lCols.service, width: 1.8 },
          { key: 'carrier', label: t.lCols.carrier, width: 1.3 },
          { key: 'frequency', label: t.lCols.frequency, width: 1 },
          { key: 'rotation', label: t.lCols.rotation, width: 3.4 },
        ],
        rows: lignes.map((s) => (typeof s === 'object' ? {
          service: publiee(s.service_name || s.carrier) ? propre(s.service_name || s.carrier) : na,
          carrier: publiee(s.carrier) ? propre(s.carrier) : na,
          frequency: txt(s.frequency),
          rotation: [publiee(s.rotation) ? propre(s.rotation) : na,
            estNombre(s.transit_time_marseille_alger_days) && t.transit(s.transit_time_marseille_alger_days)].filter(Boolean).join('\n'),
        } : { service: propre(s), carrier: na, frequency: na, rotation: na })),
      },
    });
  } else {
    sections.push({ title: t.lines, paragraphs: [t.noLines] });
  }

  const agents = port.agents || port.connectivity?.shipping_agents || [];
  if (agents.length) {
    sections.push({
      title: t.agents,
      table: {
        columns: [
          { key: 'agent', label: t.aCols.agent, width: 1.8 },
          { key: 'activity', label: t.aCols.activity, width: 2.2 },
          { key: 'address', label: t.aCols.address, width: 1.7 },
          { key: 'contact', label: t.aCols.contact, width: 2 },
        ],
        rows: agents.map((a) => (typeof a === 'object' ? {
          agent: [propre(a.agent_name || '—'), publiee(a.group) && txt(a.group)].filter(Boolean).join('\n'),
          activity: [
            publiee(a.role) && txt(a.role),
            publiee(a.services) && liste(a.services),
            publiee(a.cargo_types) && liste(a.cargo_types),
            publiee(a.operating_hours) && txt(a.operating_hours),
            publiee(a.certifications) && liste(a.certifications),
          ].filter(Boolean).join('\n') || na,
          address: publiee(a.address) ? propre(a.address) : na,
          // Un contact par ligne, sans libellé : le téléphone reste seul dans son texte.
          contact: [a.contact, a.email, publiee(a.website) && site(a.website)].filter(publiee).map(propre).join('\n') || na,
        } : { agent: propre(a), activity: na, address: na, contact: na })),
      },
    });
  } else {
    sections.push({ title: t.agents, paragraphs: [t.noAgents] });
  }

  const net = port.logistics_network;
  if (net) {
    const hint = net.hinterland_connections || {};
    const netKv = [
      publiee(net.global_carriers_present) && { label: t.nCarriers, value: liste(net.global_carriers_present) },
      publiee(net.terminal_operators) && { label: t.nTerminalOps, value: liste(net.terminal_operators) },
      publiee(net.regional_specialists_present) && { label: t.nRegional, value: liste(net.regional_specialists_present) },
      publiee(net.customs_brokers_count) && { label: t.nBrokers, value: propre(net.customs_brokers_count) },
      publiee(net.service_providers_available) && { label: t.nProviders, value: liste(net.service_providers_available) },
      publiee(hint.road) && { label: t.nRoad, value: propre(hint.road) },
      publiee(hint.rail) && { label: t.nRail, value: propre(hint.rail) },
      publiee(hint.airport) && { label: t.nAirport, value: propre(hint.airport) },
    ].filter(Boolean);
    if (netKv.length) sections.push({ title: t.network, keyValues: netKv });
  }

  sections.push({ title: c.warning, notice: [t.noticeData, c.contactsNotice] });

  return {
    moduleLabel: c.module,
    badge: t.badge,
    title: titre,
    subtitle: [suite, t.subtitle(nomPays, port.un_locode, publiee(port.port_type) ? txt(port.port_type) : '')].filter(Boolean).join(' · '),
    kpis,
    sections,
    source: t.sourceFooter,
    filename: nomFichier(t.file, port.port_id),
  };
}

// ──────────────────────────── AÉROPORT ────────────────────────────

const T_AERO = {
  fr: {
    badge: 'FICHE AÉROPORT',
    subtitle: (pays, iata, icao) => [pays, iata && `IATA ${iata}`, icao && `OACI ${icao}`].filter(Boolean).join(' · '),
    cargo: 'Fret cargo', mail: 'Courrier', movements: 'Mouvements cargo', capacity: 'Capacité annuelle',
    area: 'Terminal cargo', routesCount: 'Lignes cargo régulières', utilisation: 'Taux d’utilisation',
    utilisationSub: (a) => `fret ${a} / capacité`,
    identity: "Identité et infrastructure cargo",
    name: 'Nom', country: 'Pays', iata: 'Code IATA', icao: 'Code OACI', gps: 'Coordonnées GPS',
    areaFull: 'Surface du terminal cargo', capacityFull: 'Capacité annuelle de traitement', notes: 'Notes',
    identityText: "Code IATA : code à trois lettres de l'aéroport, utilisé sur les lettres de transport aérien (LTA). Code OACI : code à quatre lettres de l'aviation civile. Capacité annuelle : tonnage de fret que les installations cargo peuvent traiter en un an ; le taux d'utilisation rapporte le fret de la dernière année à cette capacité.",
    history: 'Statistiques historiques',
    hCols: { year: 'Année', cargo: 'Fret (t)', mail: 'Courrier (t)', movements: 'Mouvements cargo', source: 'Source' },
    historyText: "Fret : marchandises chargées et déchargées, en tonnes. Courrier : envois postaux. Mouvements cargo : décollages et atterrissages d'avions tout-cargo.",
    noHistory: 'Aucune donnée historique publiée par la source.',
    actors: 'Acteurs du fret aérien',
    acCols: { name: 'Acteur', type: 'Catégorie', group: 'Groupe' },
    actorTypes: { airline: 'Compagnie cargo', handler: 'Assistance au sol (handler)', forwarder: 'Transitaire' },
    actorsText: 'Compagnies cargo : transporteurs aériens de fret. Handlers : sociétés d’assistance au sol qui chargent, déchargent et entreposent le fret. Transitaires : organisent le transport et les formalités pour le compte du chargeur.',
    noActors: 'Aucun acteur référencé par la source.',
    routes: 'Lignes cargo régulières',
    rCols: { carrier: 'Opérateur', route: 'Liaison', rotation: 'Rotation', frequency: 'Fréquence', aircraft: "Type d'avion" },
    noRoutes: 'Aucune ligne cargo régulière référencée par la source.',
    network: 'Réseau logistique aérien',
    nAirlines: 'Compagnies cargo mondiales présentes', nIntegrators: 'Intégrateurs (express)', nHandlers: 'Handlers présents', nProviders: 'Prestataires disponibles',
    noticeData: "Données reprises des sources publiques citées (IATA, ACI, gestionnaires d'aéroports, autorités de l'aviation civile), à la date indiquée pour chacune ; une valeur absente est notée « non publié ». Les services de l'autorité aéroportuaire ne sont pas repris : la source ne publie pas leurs coordonnées directes.",
    sourceFooter: (org) => [org, "IATA, ACI, autorités de l'aviation civile"].filter(Boolean).join(' ; '),
    file: 'Aeroport',
  },
  en: {
    badge: 'AIRPORT PROFILE',
    subtitle: (pays, iata, icao) => [pays, iata && `IATA ${iata}`, icao && `ICAO ${icao}`].filter(Boolean).join(' · '),
    cargo: 'Air cargo', mail: 'Mail', movements: 'Cargo movements', capacity: 'Annual capacity',
    area: 'Cargo terminal', routesCount: 'Regular cargo routes', utilisation: 'Utilisation rate',
    utilisationSub: (a) => `cargo ${a} / capacity`,
    identity: 'Identity and cargo infrastructure',
    name: 'Name', country: 'Country', iata: 'IATA code', icao: 'ICAO code', gps: 'GPS coordinates',
    areaFull: 'Cargo terminal area', capacityFull: 'Annual handling capacity', notes: 'Notes',
    identityText: "IATA code: the airport's three-letter code, used on air waybills (AWB). ICAO code: the four-letter civil aviation code. Annual capacity: tonnage of cargo the facilities can handle in a year; the utilisation rate compares the latest year's cargo with that capacity.",
    history: 'Historical statistics',
    hCols: { year: 'Year', cargo: 'Cargo (t)', mail: 'Mail (t)', movements: 'Cargo movements', source: 'Source' },
    historyText: 'Cargo: goods loaded and unloaded, in tonnes. Mail: postal items. Cargo movements: take-offs and landings of all-cargo aircraft.',
    noHistory: 'No historical data published by the source.',
    actors: 'Air cargo actors',
    acCols: { name: 'Actor', type: 'Category', group: 'Group' },
    actorTypes: { airline: 'Cargo airline', handler: 'Ground handler', forwarder: 'Freight forwarder' },
    actorsText: 'Cargo airlines: air carriers of freight. Handlers: ground-handling companies that load, unload and store cargo. Freight forwarders: arrange transport and formalities on behalf of the shipper.',
    noActors: 'No actor listed by the source.',
    routes: 'Regular cargo routes',
    rCols: { carrier: 'Carrier', route: 'Route', rotation: 'Rotation', frequency: 'Frequency', aircraft: 'Aircraft type' },
    noRoutes: 'No regular cargo route listed by the source.',
    network: 'Air logistics network',
    nAirlines: 'Global cargo airlines present', nIntegrators: 'Integrators (express)', nHandlers: 'Ground handlers present', nProviders: 'Service providers available',
    noticeData: 'Data taken from the public sources cited (IATA, ACI, airport operators, civil aviation authorities), as of the date shown for each; a missing value is shown as "not published". The airport authority departments are not listed: the source does not publish their direct contact details.',
    sourceFooter: (org) => [org, 'IATA, ACI, civil aviation authorities'].filter(Boolean).join(' ; '),
    file: 'Airport',
  },
  ar: {
    badge: 'بطاقة مطار',
    subtitle: (pays, iata, icao) => [pays, iata && `IATA ${iata}`, icao && `ICAO ${icao}`].filter(Boolean).join(' · '),
    cargo: 'شحن البضائع', mail: 'البريد', movements: 'حركات الشحن', capacity: 'الطاقة السنوية',
    area: 'محطة الشحن', routesCount: 'خطوط الشحن المنتظمة', utilisation: 'نسبة الاستخدام',
    utilisationSub: (a) => `شحن ${a} / الطاقة`,
    identity: 'الهوية والبنية التحتية للشحن',
    name: 'الاسم', country: 'البلد', iata: 'رمز IATA', icao: 'رمز ICAO', gps: 'إحداثيات GPS',
    areaFull: 'مساحة محطة الشحن', capacityFull: 'الطاقة السنوية للمعالجة', notes: 'ملاحظات',
    identityText: 'رمز IATA: رمز المطار المكوّن من ثلاثة أحرف، ويُستعمل في بوالص الشحن الجوي. رمز ICAO: رمز الطيران المدني المكوّن من أربعة أحرف. الطاقة السنوية: حمولة البضائع التي تستطيع منشآت الشحن معالجتها في سنة؛ وتقارن نسبة الاستخدام شحن السنة الأخيرة بهذه الطاقة.',
    history: 'الإحصائيات التاريخية',
    hCols: { year: 'السنة', cargo: 'الشحن (طن)', mail: 'البريد (طن)', movements: 'حركات الشحن', source: 'المصدر' },
    historyText: 'الشحن: البضائع المحمّلة والمفرّغة بالطن. البريد: المراسلات البريدية. حركات الشحن: إقلاع وهبوط طائرات الشحن الخالص.',
    noHistory: 'لا توجد بيانات تاريخية منشورة لدى المصدر.',
    actors: 'فاعلو الشحن الجوي',
    acCols: { name: 'الفاعل', type: 'الفئة', group: 'المجموعة' },
    actorTypes: { airline: 'شركة شحن جوي', handler: 'خدمات المناولة الأرضية', forwarder: 'وكيل عبور وشحن' },
    actorsText: 'شركات الشحن الجوي: الناقلون الجويون للبضائع. شركات المناولة: تحمّل البضائع وتفرّغها وتخزّنها. وكلاء العبور: ينظّمون النقل والإجراءات لحساب الشاحن.',
    noActors: 'لا يوجد فاعلون مسجلون لدى المصدر.',
    routes: 'خطوط الشحن المنتظمة',
    rCols: { carrier: 'المشغّل', route: 'الخط', rotation: 'الدورة', frequency: 'التواتر', aircraft: 'نوع الطائرة' },
    noRoutes: 'لا توجد خطوط شحن منتظمة مسجلة لدى المصدر.',
    network: 'الشبكة اللوجستية الجوية',
    nAirlines: 'شركات الشحن العالمية الحاضرة', nIntegrators: 'شركات النقل السريع المتكاملة', nHandlers: 'شركات المناولة الحاضرة', nProviders: 'مقدمو الخدمات المتاحون',
    noticeData: 'بيانات مأخوذة من المصادر العامة المذكورة (IATA، ACI، مسيّرو المطارات، هيئات الطيران المدني) في التاريخ المبيّن لكل منها؛ والقيمة الغائبة تُكتب «غير منشور». لم تُدرج مصالح سلطة المطار لأن المصدر لا ينشر بيانات الاتصال المباشرة بها.',
    sourceFooter: (org) => [org, 'IATA, ACI'].filter(Boolean).join(' ; '),
    file: 'Aeroport_ar',
  },
};

export function specFicheAeroportPdf(airport, langue = 'fr') {
  const t = T_AERO[langue] || T_AERO.fr;
  const { c, na, num, txt, liste, pays, an } = outils(langue);
  const u = c.u;
  // Même ordre que l'écran : la série arrive de la plus récente à la plus ancienne.
  const histo = (airport.historical_stats || []).slice().sort((a, b) => b.year - a.year);
  const dernier = histo[0] || {};
  const routes = airport.routes || [];
  const nom = txt(airport.airport_name);
  const nomPays = pays(airport.country_iso, airport.country_name);
  const [titre, suite] = decouperTitre(nom);
  const utilisation = estNombre(dernier.cargo_throughput_tons) && estNombre(airport.annual_capacity_tons) && airport.annual_capacity_tons > 0
    ? `${num((dernier.cargo_throughput_tons / airport.annual_capacity_tons) * 100)} %` : na;

  const kpis = [
    { label: t.cargo, value: num(dernier.cargo_throughput_tons), sub: [u.t, an(dernier.year)].filter(Boolean).join(' · '), accent: 'gold' },
    { label: t.mail, value: num(dernier.mail_throughput_tons), sub: [u.t, an(dernier.year)].filter(Boolean).join(' · '), accent: 'gold' },
    { label: t.movements, value: num(dernier.cargo_aircraft_movements), sub: an(dernier.year), accent: 'terra' },
    { label: t.capacity, value: num(airport.annual_capacity_tons), sub: u.tYear, accent: 'green' },
    { label: t.utilisation, value: utilisation, sub: an(dernier.year) ? t.utilisationSub(dernier.year) : '', accent: 'green' },
    { label: t.area, value: estNombre(airport.cargo_terminal_area_sqm) ? `${num(airport.cargo_terminal_area_sqm)} ${u.sqm}` : na, accent: 'terra' },
    { label: t.routesCount, value: String(routes.length), accent: 'red' },
  ];

  const sections = [
    {
      title: t.identity,
      keyValues: [
        { label: t.name, value: nom },
        { label: t.country, value: nomPays },
        { label: t.iata, value: publiee(airport.iata_code) ? airport.iata_code : na },
        { label: t.icao, value: publiee(airport.icao_code) ? airport.icao_code : na },
        { label: t.gps, value: estNombre(airport.geo_lat) && estNombre(airport.geo_lon) ? `${airport.geo_lat.toFixed(4)}, ${airport.geo_lon.toFixed(4)}` : na },
        { label: t.areaFull, value: estNombre(airport.cargo_terminal_area_sqm) ? `${num(airport.cargo_terminal_area_sqm)} ${u.sqm}` : na },
        { label: t.capacityFull, value: estNombre(airport.annual_capacity_tons) ? `${num(airport.annual_capacity_tons)} ${u.tYear}` : na },
        publiee(airport.cargo_infra_notes) && { label: t.notes, value: txt(airport.cargo_infra_notes) },
      ].filter(Boolean),
    },
    { paragraphs: [t.identityText] },
  ];

  if (histo.length) {
    sections.push({
      title: t.history,
      table: {
        columns: [
          { key: 'year', label: t.hCols.year, width: 0.7 },
          { key: 'cargo_throughput_tons', label: t.hCols.cargo, width: 1.1, align: 'right', fmt: (v) => num(v) },
          { key: 'mail_throughput_tons', label: t.hCols.mail, width: 1.1, align: 'right', fmt: (v) => num(v) },
          { key: 'cargo_aircraft_movements', label: t.hCols.movements, width: 1.2, align: 'right', fmt: (v) => num(v) },
          { key: 'source', label: t.hCols.source, width: 2.2 },
        ],
        rows: histo.map((h) => ({
          ...h,
          year: String(h.year),
          source: [h.source_org, h.source_url && h.source_url.replace(/^https?:\/\//, '').replace(/\/$/, '')].filter(publiee).map(propre).join(' — ') || na,
        })),
      },
    });
    sections.push({ paragraphs: [t.historyText] });
  } else {
    sections.push({ title: t.history, paragraphs: [t.noHistory] });
  }

  const acteurs = airport.actors || [];
  if (acteurs.length) {
    // Même regroupement que l'écran : compagnies, puis handlers, puis transitaires.
    const ordre = { airline: 0, handler: 1, forwarder: 2 };
    sections.push({
      title: t.actors,
      table: {
        columns: [
          { key: 'name', label: t.acCols.name, width: 2.4 },
          { key: 'type', label: t.acCols.type, width: 1.6 },
          { key: 'group', label: t.acCols.group, width: 2 },
        ],
        rows: acteurs.slice()
          .sort((a, b) => (ordre[a.actor_type] ?? 3) - (ordre[b.actor_type] ?? 3))
          .map((a) => ({
            name: publiee(a.actor_name) ? propre(a.actor_name) : na,
            type: t.actorTypes[a.actor_type] || txt(a.actor_type),
            group: txt(a.group),
          })),
      },
    });
    sections.push({ paragraphs: [t.actorsText] });
  } else {
    sections.push({ title: t.actors, paragraphs: [t.noActors] });
  }

  if (routes.length) {
    sections.push({
      title: t.routes,
      table: {
        columns: [
          { key: 'carrier', label: t.rCols.carrier, width: 1.5 },
          { key: 'route', label: t.rCols.route, width: 1.9 },
          { key: 'rotation', label: t.rCols.rotation, width: 1.6 },
          { key: 'frequency', label: t.rCols.frequency, width: 1 },
          { key: 'aircraft', label: t.rCols.aircraft, width: 1.1 },
        ],
        // Champs de la source (carrier, route_description, aircraft_types) ou
        // anciens noms (airline, destination_airport, aircraft_type).
        rows: routes.map((r) => ({
          carrier: txt(r.carrier || r.airline),
          route: txt(r.route_description || r.destination_airport),
          rotation: publiee(r.rotation) ? propre(r.rotation) : na,
          frequency: txt(r.frequency),
          aircraft: txt(r.aircraft_types || r.aircraft_type),
        })),
      },
    });
  } else {
    sections.push({ title: t.routes, paragraphs: [t.noRoutes] });
  }

  const net = airport.logistics_network || {};
  const netKv = [
    publiee(net.global_cargo_airlines_present) && { label: t.nAirlines, value: liste(net.global_cargo_airlines_present) },
    publiee(net.integrators_present) && { label: t.nIntegrators, value: liste(net.integrators_present) },
    publiee(net.ground_handlers_present) && { label: t.nHandlers, value: liste(net.ground_handlers_present) },
    publiee(net.service_providers_available) && { label: t.nProviders, value: liste(net.service_providers_available) },
  ].filter(Boolean);
  if (netKv.length) sections.push({ title: t.network, keyValues: netKv });

  sections.push({ title: c.warning, notice: [t.noticeData, c.contactsNotice] });

  return {
    moduleLabel: c.module,
    badge: t.badge,
    title: titre,
    subtitle: [suite, t.subtitle(nomPays, airport.iata_code, airport.icao_code)].filter(Boolean).join(' · '),
    kpis,
    sections,
    source: t.sourceFooter(publiee(dernier.source_org) ? propre(dernier.source_org) : ''),
    filename: nomFichier(t.file, airport.iata_code || airport.airport_id),
  };
}

// ──────────────────────────── CORRIDOR ────────────────────────────

const T_CORR = {
  fr: {
    badge: 'FICHE CORRIDOR',
    types: { road: 'Routier', rail: 'Ferroviaire', multimodal: 'Multimodal' },
    importance: { high: 'Prioritaire PIDA', medium: 'Importance moyenne', low: 'Importance faible' },
    length: 'Longueur', freight: 'Fret annuel', transit: 'Temps de transit', border: 'Passage frontière',
    trucks: 'Trafic quotidien', osbp: 'Postes OSBP', countries: 'Pays traversés', status: 'Statut',
    osbpSub: (n) => `sur ${n} nœud${n > 1 ? 's' : ''} logistique${n > 1 ? 's' : ''}`,
    route: 'Tracé et infrastructure',
    type: 'Type', priority: 'Priorité', countriesFull: 'Pays traversés', ends: 'Départ — arrivée',
    technical: 'Détails techniques', description: 'Description', source: 'Source',
    routeText: "PIDA : Programme pour le développement des infrastructures en Afrique (Union africaine), qui désigne les corridors prioritaires. Temps de transit : durée moyenne du trajet complet d'un camion ou d'un train, attentes comprises. Passage frontière : temps moyen d'attente et de formalités à un poste-frontière.",
    stats: 'Statistiques du corridor',
    year: 'Année', transitFull: 'Temps de transit moyen', borderFull: 'Temps moyen de passage frontière',
    freightFull: 'Fret transporté par an', trucksFull: 'Camions par jour', link: 'Lien source',
    noStats: "Aucune statistique de trafic n'est publiée pour ce corridor : les indicateurs sont notés « non publié ».",
    nodes: 'Nœuds logistiques et postes-frontières',
    nCols: { name: 'Nœud', country: 'Pays', type: 'Type', osbp: 'OSBP', notes: 'Notes' },
    nodeTypes: { border_crossing: 'Poste-frontière', dry_port: 'Port sec', rail_terminal: 'Terminal ferroviaire', intermodal_hub: 'Plateforme intermodale', logistics_hub: 'Plateforme logistique', rail_terminus: 'Terminus ferroviaire', rail_station: 'Gare ferroviaire' },
    nodesText: "OSBP (One-Stop Border Post, poste-frontière à arrêt unique) : les douanes des deux pays contrôlent ensemble, en un seul arrêt, ce qui réduit le temps de passage. Port sec : terminal intérieur où les conteneurs sont dédouanés loin du port maritime.",
    noNodes: 'Aucun nœud logistique référencé par la source.',
    operators: 'Opérateurs de transport',
    oCols: { name: 'Opérateur', type: 'Type', group: 'Groupe', country: 'Pays', fleet: 'Flotte' },
    operatorTypes: { rail_operator: 'Opérateur ferroviaire', trucking_company: 'Transporteur routier', trans_national_authority: 'Autorité transnationale', infrastructure_authority: "Gestionnaire d'infrastructure" },
    fleetUnit: (rail) => (rail ? 'locomotives' : 'camions'),
    noOperators: 'Aucun opérateur référencé par la source.',
    network: 'Réseau logistique',
    n3pl: '3PL mondiaux', nTrucking: 'Transport routier régional', nRail: 'Opérateurs ferroviaires', nBodies: 'Organismes de gestion du corridor', nProviders: 'Prestataires disponibles',
    networkText: '3PL (third-party logistics) : prestataire qui prend en charge tout ou partie de la chaîne logistique (transport, entreposage, dédouanement) pour le compte du chargeur.',
    agents: 'Agents locaux',
    agCols: { agent: 'Agent', country: 'Pays', activity: 'Services', contact: 'Contact' },
    agentTypes: { freight_forwarder: 'Transitaire', logistics_provider: 'Prestataire logistique', port_logistics: 'Logistique portuaire', rail_port_operator: 'Opérateur ferroviaire et portuaire' },
    noticeData: "Données reprises des sources publiques citées (PIDA, communautés économiques régionales, autorités de corridor, opérateurs), à la date indiquée pour chacune ; une valeur absente est notée « non publié ». Les temps de transit et de passage frontière sont des moyennes : ils varient selon la saison, la marchandise et les contrôles. La source ne publie pas de coût de transport par corridor.",
    file: 'Corridor',
  },
  en: {
    badge: 'CORRIDOR PROFILE',
    types: { road: 'Road', rail: 'Rail', multimodal: 'Multimodal' },
    importance: { high: 'PIDA priority', medium: 'Medium importance', low: 'Low importance' },
    length: 'Length', freight: 'Annual freight', transit: 'Transit time', border: 'Border crossing',
    trucks: 'Daily traffic', osbp: 'OSBP posts', countries: 'Countries crossed', status: 'Status',
    osbpSub: (n) => `out of ${n} logistics node${n > 1 ? 's' : ''}`,
    route: 'Route and infrastructure',
    type: 'Type', priority: 'Priority', countriesFull: 'Countries crossed', ends: 'Start — end',
    technical: 'Technical details', description: 'Description', source: 'Source',
    routeText: 'PIDA: Programme for Infrastructure Development in Africa (African Union), which designates priority corridors. Transit time: average duration of the full trip for a truck or train, waiting included. Border crossing: average waiting and formalities time at a border post.',
    stats: 'Corridor statistics',
    year: 'Year', transitFull: 'Average transit time', borderFull: 'Average border crossing time',
    freightFull: 'Freight carried per year', trucksFull: 'Trucks per day', link: 'Source link',
    noStats: 'No traffic statistics are published for this corridor: indicators are shown as "not published".',
    nodes: 'Logistics nodes and border posts',
    nCols: { name: 'Node', country: 'Country', type: 'Type', osbp: 'OSBP', notes: 'Notes' },
    nodeTypes: { border_crossing: 'Border post', dry_port: 'Dry port', rail_terminal: 'Rail terminal', intermodal_hub: 'Intermodal hub', logistics_hub: 'Logistics hub', rail_terminus: 'Rail terminus', rail_station: 'Rail station' },
    nodesText: 'OSBP (One-Stop Border Post): customs of both countries inspect together, in a single stop, which cuts crossing time. Dry port: inland terminal where containers are cleared away from the seaport.',
    noNodes: 'No logistics node listed by the source.',
    operators: 'Transport operators',
    oCols: { name: 'Operator', type: 'Type', group: 'Group', country: 'Country', fleet: 'Fleet' },
    operatorTypes: { rail_operator: 'Rail operator', trucking_company: 'Trucking company', trans_national_authority: 'Transnational authority', infrastructure_authority: 'Infrastructure manager' },
    fleetUnit: (rail) => (rail ? 'locomotives' : 'trucks'),
    noOperators: 'No operator listed by the source.',
    network: 'Logistics network',
    n3pl: 'Global 3PLs', nTrucking: 'Regional trucking', nRail: 'Rail operators', nBodies: 'Corridor management bodies', nProviders: 'Service providers available',
    networkText: '3PL (third-party logistics): a provider that handles all or part of the supply chain (transport, warehousing, customs clearance) on behalf of the shipper.',
    agents: 'Local agents',
    agCols: { agent: 'Agent', country: 'Country', activity: 'Services', contact: 'Contact' },
    agentTypes: { freight_forwarder: 'Freight forwarder', logistics_provider: 'Logistics provider', port_logistics: 'Port logistics', rail_port_operator: 'Rail and port operator' },
    noticeData: 'Data taken from the public sources cited (PIDA, regional economic communities, corridor authorities, operators), as of the date shown for each; a missing value is shown as "not published". Transit and border crossing times are averages: they vary with the season, the goods and inspections. The source does not publish transport costs per corridor.',
    file: 'Corridor',
  },
  ar: {
    badge: 'بطاقة ممر',
    types: { road: 'طريق بري', rail: 'سكك حديدية', multimodal: 'متعدد الوسائط' },
    importance: { high: 'ذو أولوية في PIDA', medium: 'أهمية متوسطة', low: 'أهمية ضعيفة' },
    length: 'الطول', freight: 'الشحن السنوي', transit: 'مدة العبور', border: 'العبور الحدودي',
    trucks: 'الحركة اليومية', osbp: 'مراكز OSBP', countries: 'البلدان المعبورة', status: 'الحالة',
    osbpSub: (n) => `من أصل ${n} عقدة لوجستية`,
    route: 'المسار والبنية التحتية',
    type: 'النوع', priority: 'الأولوية', countriesFull: 'البلدان المعبورة', ends: 'الانطلاق — الوصول',
    technical: 'التفاصيل التقنية', description: 'الوصف', source: 'المصدر',
    routeText: 'PIDA: برنامج تطوير البنية التحتية في أفريقيا (الاتحاد الأفريقي)، الذي يحدّد الممرات ذات الأولوية. مدة العبور: متوسط مدة الرحلة الكاملة لشاحنة أو قطار، بما في ذلك الانتظار. العبور الحدودي: متوسط مدة الانتظار والإجراءات في المركز الحدودي.',
    stats: 'إحصائيات الممر',
    year: 'السنة', transitFull: 'متوسط مدة العبور', borderFull: 'متوسط مدة العبور الحدودي',
    freightFull: 'البضائع المنقولة سنويًا', trucksFull: 'شاحنة في اليوم', link: 'رابط المصدر',
    noStats: 'لا تُنشر إحصائيات حركة لهذا الممر: تُكتب المؤشرات «غير منشور».',
    nodes: 'العُقد اللوجستية والمراكز الحدودية',
    nCols: { name: 'العقدة', country: 'البلد', type: 'النوع', osbp: 'OSBP', notes: 'ملاحظات' },
    nodeTypes: { border_crossing: 'معبر حدودي', dry_port: 'ميناء جاف', rail_terminal: 'محطة سكك حديدية', intermodal_hub: 'منصة متعددة الوسائط', logistics_hub: 'منصة لوجستية', rail_terminus: 'محطة نهائية للسكك الحديدية', rail_station: 'محطة قطار' },
    nodesText: 'OSBP (مركز حدودي موحد): تُجري جمارك البلدين المراقبة معًا في توقف واحد، مما يقلّص مدة العبور. الميناء الجاف: محطة داخلية تُخلَّص فيها الحاويات بعيدًا عن الميناء البحري.',
    noNodes: 'لا توجد عُقد لوجستية مسجلة لدى المصدر.',
    operators: 'مشغلو النقل',
    oCols: { name: 'المشغّل', type: 'النوع', group: 'المجموعة', country: 'البلد', fleet: 'الأسطول' },
    operatorTypes: { rail_operator: 'مشغّل سكك حديدية', trucking_company: 'شركة نقل بري', trans_national_authority: 'هيئة عابرة للحدود', infrastructure_authority: 'مسيّر البنية التحتية' },
    fleetUnit: (rail) => (rail ? 'قاطرة' : 'شاحنة'),
    noOperators: 'لا يوجد مشغلون مسجلون لدى المصدر.',
    network: 'الشبكة اللوجستية',
    n3pl: 'مزودو الخدمات اللوجستية العالميون (3PL)', nTrucking: 'النقل البري الإقليمي', nRail: 'مشغلو السكك الحديدية', nBodies: 'هيئات إدارة الممر', nProviders: 'مقدمو الخدمات المتاحون',
    networkText: '3PL (الخدمات اللوجستية للطرف الثالث): مزوّد يتولى كل سلسلة الإمداد أو جزءًا منها (النقل، التخزين، التخليص الجمركي) لحساب الشاحن.',
    agents: 'الوكلاء المحليون',
    agCols: { agent: 'الوكيل', country: 'البلد', activity: 'الخدمات', contact: 'الاتصال' },
    agentTypes: { freight_forwarder: 'وكيل عبور وشحن', logistics_provider: 'مزوّد خدمات لوجستية', port_logistics: 'لوجستيك مينائي', rail_port_operator: 'مشغّل سككي ومينائي' },
    noticeData: 'بيانات مأخوذة من المصادر العامة المذكورة (PIDA، المجموعات الاقتصادية الإقليمية، هيئات الممرات، المشغّلون) في التاريخ المبيّن لكل منها؛ والقيمة الغائبة تُكتب «غير منشور». مدد العبور والعبور الحدودي متوسطات تتغير بحسب الموسم والبضاعة وعمليات المراقبة. لا ينشر المصدر تكلفة النقل لكل ممر.',
    file: 'Corridor_ar',
  },
};

export function specFicheCorridorPdf(corridor, langue = 'fr') {
  const t = T_CORR[langue] || T_CORR.fr;
  const { c, na, num, txt, unite, liste, pays, site, an } = outils(langue);
  const u = c.u;
  const stats = corridor.stats || {};
  const nodes = corridor.nodes || [];
  const operators = corridor.operators || [];
  const osbp = nodes.filter((n) => n.is_osbp).length;
  const paysTraverses = (corridor.countries_spanned || []).map((iso) => pays(iso));
  const nom = txt(corridor.corridor_name);
  const [titre, suite] = decouperTitre(nom);
  const type = t.types[corridor.corridor_type] || txt(corridor.corridor_type);

  const kpis = [
    { label: t.length, value: estNombre(corridor.length_km) ? `${num(corridor.length_km)} ${u.km}` : na, accent: 'gold' },
    { label: t.freight, value: num(stats.freight_throughput_tons), sub: estNombre(stats.freight_throughput_tons) ? [u.t, an(stats.year)].filter(Boolean).join(' · ') : '', accent: 'gold' },
    { label: t.transit, value: unite(stats.avg_transit_time_hours, u.h, 0), accent: 'terra' },
    { label: t.border, value: unite(stats.avg_border_crossing_time_hours, u.h, 0), accent: 'red' },
    { label: t.trucks, value: num(stats.truck_volumes_daily), sub: estNombre(stats.truck_volumes_daily) ? u.trucksDay : '', accent: 'terra' },
    { label: t.osbp, value: String(osbp), sub: t.osbpSub(nodes.length), accent: 'green' },
    { label: t.countries, value: String(paysTraverses.length), accent: 'green' },
    { label: t.status, value: txt(corridor.status), accent: 'red' },
  ];

  const sections = [
    {
      title: t.route,
      keyValues: [
        { label: t.type, value: type },
        { label: t.status, value: txt(corridor.status) },
        { label: t.priority, value: t.importance[corridor.importance] || txt(corridor.importance) },
        { label: t.length, value: estNombre(corridor.length_km) ? `${num(corridor.length_km)} ${u.km}` : na },
        { label: t.countriesFull, value: paysTraverses.length ? paysTraverses.join(' - ') : na },
        { label: t.ends, value: `${txt(corridor.start_node)} — ${txt(corridor.end_node)}` },
        { label: t.technical, value: txt(corridor.infra_details) },
        publiee(corridor.description) && { label: t.description, value: txt(corridor.description) },
        { label: t.source, value: publiee(corridor.source_org) ? propre(corridor.source_org) : na },
      ].filter(Boolean),
    },
    { paragraphs: [t.routeText] },
  ];

  // Statistiques : toujours les quatre indicateurs, « non publié » quand la source ne les donne pas.
  sections.push({
    title: t.stats,
    keyValues: [
      { label: t.year, value: an(stats.year) || na },
      { label: t.freightFull, value: estNombre(stats.freight_throughput_tons) ? `${num(stats.freight_throughput_tons)} ${u.t}` : na },
      { label: t.transitFull, value: unite(stats.avg_transit_time_hours, u.h, 0) },
      { label: t.borderFull, value: unite(stats.avg_border_crossing_time_hours, u.h, 0) },
      { label: t.trucksFull, value: num(stats.truck_volumes_daily) },
      publiee(stats.source_org) && { label: t.source, value: propre(stats.source_org) },
      publiee(stats.source_url) && { label: t.link, value: site(stats.source_url) },
    ].filter(Boolean),
  });
  if (!corridor.stats) sections.push({ paragraphs: [t.noStats] });

  if (nodes.length) {
    sections.push({
      title: t.nodes,
      table: {
        columns: [
          { key: 'name', label: t.nCols.name, width: 2.2 },
          { key: 'country', label: t.nCols.country, width: 1.1 },
          { key: 'type', label: t.nCols.type, width: 1.3 },
          { key: 'osbp', label: t.nCols.osbp, width: 0.6 },
          { key: 'notes', label: t.nCols.notes, width: 2.6 },
        ],
        rows: nodes.map((n) => ({
          name: publiee(n.node_name) ? txt(n.node_name) : na,
          country: publiee(n.country_iso) ? pays(n.country_iso) : na,
          type: t.nodeTypes[n.node_type] || txt(n.node_type),
          osbp: n.is_osbp ? c.yes : c.no,
          notes: publiee(n.notes) ? txt(n.notes) : na,
        })),
      },
    });
    sections.push({ paragraphs: [t.nodesText] });
  } else {
    sections.push({ title: t.nodes, paragraphs: [t.noNodes] });
  }

  if (operators.length) {
    sections.push({
      title: t.operators,
      table: {
        columns: [
          { key: 'name', label: t.oCols.name, width: 2.4 },
          { key: 'type', label: t.oCols.type, width: 1.5 },
          { key: 'group', label: t.oCols.group, width: 1.1 },
          { key: 'country', label: t.oCols.country, width: 1.1 },
          { key: 'fleet', label: t.oCols.fleet, width: 1.1, align: 'right' },
        ],
        rows: operators.map((o) => ({
          name: publiee(o.operator_name) ? propre(o.operator_name) : na,
          type: t.operatorTypes[o.operator_type] || txt(o.operator_type),
          group: txt(o.group),
          country: publiee(o.country_iso) ? pays(o.country_iso) : na,
          // Une flotte à 0 ou absente : la source ne la publie pas.
          fleet: estNombre(o.fleet_size) && o.fleet_size > 0 ? `${num(o.fleet_size)} ${t.fleetUnit(o.operator_type === 'rail_operator')}` : na,
        })),
      },
    });
  } else {
    sections.push({ title: t.operators, paragraphs: [t.noOperators] });
  }

  const net = corridor.logistics_network;
  if (net) {
    const netKv = [
      publiee(net.global_3pl_present) && { label: t.n3pl, value: liste(net.global_3pl_present) },
      publiee(net.regional_trucking_operators) && { label: t.nTrucking, value: liste(net.regional_trucking_operators) },
      publiee(net.rail_operators_present) && { label: t.nRail, value: liste(net.rail_operators_present) },
      publiee(net.corridor_management_bodies) && { label: t.nBodies, value: liste(net.corridor_management_bodies, ' ; ') },
      publiee(net.service_providers_available) && { label: t.nProviders, value: liste(net.service_providers_available) },
    ].filter(Boolean);
    if (netKv.length) sections.push({ title: t.network, keyValues: netKv }, { paragraphs: [t.networkText] });

    const agents = Object.entries(net.local_agents_by_country || {})
      .flatMap(([iso, liste_]) => (liste_ || []).map((a) => ({ ...a, iso })));
    if (agents.length) {
      sections.push({
        title: t.agents,
        table: {
          columns: [
            { key: 'agent', label: t.agCols.agent, width: 2.2 },
            { key: 'country', label: t.agCols.country, width: 0.9 },
            { key: 'activity', label: t.agCols.activity, width: 2.3 },
            { key: 'contact', label: t.agCols.contact, width: 2.1 },
          ],
          rows: agents.map((a) => ({
            agent: [
              publiee(a.company_name) ? propre(a.company_name) : na,
              t.agentTypes[a.agent_type] || (publiee(a.agent_type) && txt(a.agent_type)),
              [publiee(a.city) && txt(a.city), publiee(a.address) && propre(a.address)].filter(Boolean).join(' – '),
            ].filter(Boolean).join('\n'),
            country: pays(a.iso.toUpperCase(), a.iso),
            activity: [
              publiee(a.services) && liste(a.services),
              publiee(a.operating_hours) && txt(a.operating_hours),
              publiee(a.certifications) && liste(a.certifications),
            ].filter(Boolean).join('\n') || na,
            // Un contact par ligne, sans libellé : le téléphone reste seul dans son texte.
            contact: [a.phone, a.email, publiee(a.website) && site(a.website)].filter(publiee).map(propre).join('\n') || na,
          })),
        },
      });
    }
  }

  sections.push({ title: c.warning, notice: [t.noticeData, c.contactsNotice] });

  const sources = [corridor.source_org, stats.source_org].filter(publiee).map(propre);
  return {
    moduleLabel: c.module,
    badge: t.badge,
    title: titre,
    subtitle: [suite, type, paysTraverses.join(' - ')].filter(Boolean).join(' · '),
    kpis,
    sections,
    source: [...new Set(sources)].join(' ; ') || 'PIDA',
    filename: nomFichier(t.file, corridor.corridor_id),
  };
}
