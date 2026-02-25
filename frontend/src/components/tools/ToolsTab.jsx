import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import MonitoringDashboard from './MonitoringDashboard';
import TariffDownloads from './TariffDownloads';

export default function ToolsTab({ language = 'fr' }) {
  const texts = {
    fr: {
      title: "Outils et Ressources ZLECAf",
      subtitle: "Plateformes officielles, protocoles et initiatives",
      ntbTitle: "Obstacles Non Tarifaires",
      ntbDesc: "Signalez ou consultez les obstacles non tarifaires (NTB) sur la plateforme officielle ZLECAf. Mécanisme de résolution continentale.",
      ntbStatus: "Opérationnel",
      ntbCountries: "Pays couverts:",
      ntbBtn: "Accéder à la plateforme NTB",
      digitalTitle: "Protocole Commerce Digital",
      digitalDesc: "Adopté le 18 février 2024. Harmonisation des règles sur les flux transfrontières, confiance numérique et identité digitale.",
      digitalAdoption: "Adoption:",
      digitalStatus: "Adopté",
      digitalBtn: "Voir le protocole UA",
      gtiTitle: "Guided Trade Initiative",
      gtiDesc: "Initiative pilote de mise en œuvre progressive. Suivez les pays actifs, corridors commerciaux et routes prioritaires ZLECAf.",
      gtiStatus: "Actif",
      gtiFocus: "Focus:",
      gtiCorridors: "8 corridors prioritaires",
      gtiBtn: "Voir les pays GTI",
      papssTitle: "PAPSS - Système Panafricain de Paiements",
      papssSubtitle: "Infrastructure de paiements et règlements transfrontaliers",
      papssAbout: "À propos de PAPSS",
      papssDesc: "Le Pan-African Payment and Settlement System (PAPSS) permet les transactions instantanées en monnaies locales entre pays africains, réduisant la dépendance au dollar USD et les coûts de change.",
      papssBenefit1: "Réduction des coûts de transaction",
      papssBenefit2: "Paiements instantanés 24/7",
      papssBenefit3: "Support des monnaies locales",
      papssAdvantages: "Avantages pour le Commerce",
      papssCost: "Économies de coûts",
      papssCostDesc: "Jusqu'à 80% de réduction sur les frais bancaires",
      papssSpeed: "Rapidité",
      papssSpeedDesc: "Règlements en temps réel vs 3-7 jours",
      papssSecurity: "Sécurité",
      papssSecurityDesc: "Standards internationaux ISO 20022",
      papssDeployment: "Déploiement en cours",
      resourcesTitle: "Ressources Additionnelles",
      secretariat: "Secrétariat ZLECAf",
      secretariatDesc: "Union Africaine - Site officiel",
      tralac: "tralac",
      tralacDesc: "Centre de droit commercial",
      worldBank: "Banque Mondiale",
      worldBankDesc: "Études et projections",
      uneca: "UNECA",
      unecaDesc: "Commission économique pour l'Afrique",
      sourceLabel: "Sources: Union Africaine, PAPSS, tralac, Banque Mondiale, UNECA"
    },
    en: {
      title: "AfCFTA Tools and Resources",
      subtitle: "Official platforms, protocols and initiatives",
      ntbTitle: "Non-Tariff Barriers",
      ntbDesc: "Report or check non-tariff barriers (NTB) on the official AfCFTA platform. Continental resolution mechanism.",
      ntbStatus: "Operational",
      ntbCountries: "Countries covered:",
      ntbBtn: "Access NTB platform",
      digitalTitle: "Digital Trade Protocol",
      digitalDesc: "Adopted on February 18, 2024. Harmonization of rules on cross-border flows, digital trust and digital identity.",
      digitalAdoption: "Adoption:",
      digitalStatus: "Adopted",
      digitalBtn: "View AU protocol",
      gtiTitle: "Guided Trade Initiative",
      gtiDesc: "Pilot initiative for progressive implementation. Track active countries, trade corridors and AfCFTA priority routes.",
      gtiStatus: "Active",
      gtiFocus: "Focus:",
      gtiCorridors: "8 priority corridors",
      gtiBtn: "View GTI countries",
      papssTitle: "PAPSS - Pan-African Payment System",
      papssSubtitle: "Cross-border payments and settlements infrastructure",
      papssAbout: "About PAPSS",
      papssDesc: "The Pan-African Payment and Settlement System (PAPSS) enables instant transactions in local currencies between African countries, reducing dependence on the USD and exchange costs.",
      papssBenefit1: "Transaction cost reduction",
      papssBenefit2: "24/7 instant payments",
      papssBenefit3: "Local currency support",
      papssAdvantages: "Trade Benefits",
      papssCost: "Cost savings",
      papssCostDesc: "Up to 80% reduction in banking fees",
      papssSpeed: "Speed",
      papssSpeedDesc: "Real-time settlements vs 3-7 days",
      papssSecurity: "Security",
      papssSecurityDesc: "International ISO 20022 standards",
      papssDeployment: "Deployment in progress",
      resourcesTitle: "Additional Resources",
      secretariat: "AfCFTA Secretariat",
      secretariatDesc: "African Union - Official website",
      tralac: "tralac",
      tralacDesc: "Trade law center",
      worldBank: "World Bank",
      worldBankDesc: "Studies and projections",
      uneca: "UNECA",
      unecaDesc: "Economic Commission for Africa",
      sourceLabel: "Sources: African Union, PAPSS, tralac, World Bank, UNECA"
    }
  };

  const t = texts[language];

  return (
    <div className="space-y-6">
      {/* En-tête Outils */}
      <Card className="bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-600 text-white shadow-2xl border-none">
        <CardHeader>
          <CardTitle className="text-3xl flex items-center gap-3">
            <span>🛠️</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="text-yellow-100 text-lg font-semibold">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      <TariffDownloads language={language} />

      {/* Widgets des outils */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="afcfta-dark-gradient border-l-4 border-l-orange-500 shadow-xl hover:shadow-2xl transition-shadow">          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-4xl">🚧</span>
              <h3 className="font-bold text-xl text-orange-400">{t.ntbTitle}</h3>
            </div>
            <p className="text-sm mb-4 leading-relaxed" style={{color:'var(--afcfta-muted)'}}>
              {t.ntbDesc}
            </p>
            <div className="p-3 rounded-lg mb-3" style={{background:'rgba(255,255,255,0.06)'}}>
              <p className="text-xs" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>Status:</strong> <Badge className="bg-green-600 ml-2">{t.ntbStatus}</Badge></p>
              <p className="text-xs mt-1" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>{t.ntbCountries}</strong> 55 {language === 'fr' ? 'membres ZLECAf' : 'AfCFTA members'}</p>
            </div>
            <a 
              href="https://tradebarriers.africa" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-block w-full text-center bg-orange-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-orange-700 transition shadow-lg"
            >
              🔗 {t.ntbBtn}
            </a>
          </CardContent>
        </Card>

        <Card className="afcfta-dark-gradient border-l-4 border-l-blue-500 shadow-xl hover:shadow-2xl transition-shadow">          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-4xl">💻</span>
              <h3 className="font-bold text-xl text-blue-400">{t.digitalTitle}</h3>
            </div>
            <p className="text-sm mb-4 leading-relaxed" style={{color:'var(--afcfta-muted)'}}>
              {t.digitalDesc}
            </p>
            <div className="p-3 rounded-lg mb-3" style={{background:'rgba(255,255,255,0.06)'}}>
              <p className="text-xs" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>{t.digitalAdoption}</strong> 18 {language === 'fr' ? 'février' : 'February'} 2024</p>
              <p className="text-xs mt-1" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>Status:</strong> <Badge className="bg-green-600 ml-2">{t.digitalStatus}</Badge></p>
            </div>
            <a 
              href="https://au.int/en/treaties/protocol-digital-trade" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-block w-full text-center bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow-lg"
            >
              📄 {t.digitalBtn}
            </a>
          </CardContent>
        </Card>

        <Card className="afcfta-dark-gradient border-l-4 border-l-green-500 shadow-xl hover:shadow-2xl transition-shadow">          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-4xl">🚀</span>
              <h3 className="font-bold text-xl text-green-400">{t.gtiTitle}</h3>
            </div>
            <p className="text-sm mb-4 leading-relaxed" style={{color:'var(--afcfta-muted)'}}>
              {t.gtiDesc}
            </p>
            <div className="p-3 rounded-lg mb-3" style={{background:'rgba(255,255,255,0.06)'}}>
              <p className="text-xs" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>Status:</strong> <Badge className="bg-green-600 ml-2">{t.gtiStatus}</Badge></p>
              <p className="text-xs mt-1" style={{color:'var(--afcfta-muted)'}}><strong style={{color:'var(--text)'}}>{t.gtiFocus}</strong> {t.gtiCorridors}</p>
            </div>
            <a 
              href="https://www.tralac.org/news/article/afcfta-guided-trade-initiative.html" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-block w-full text-center bg-green-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-green-700 transition shadow-lg"
            >
              🌍 {t.gtiBtn}
            </a>
          </CardContent>
        </Card>
      </div>

      {/* Section PAPSS */}
      <Card className="shadow-2xl border-t-4 border-t-purple-600">
        <CardHeader className="afcfta-dark-gradient" style={{borderBottom:'1px solid rgba(192,132,252,0.2)'}}>
          <CardTitle className="text-2xl font-bold text-purple-400 flex items-center gap-2">
            <span>💳</span>
            <span>{t.papssTitle}</span>
          </CardTitle>
          <CardDescription className="text-lg font-semibold">
            {t.papssSubtitle}
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-bold text-lg text-purple-400 mb-3">{t.papssAbout}</h4>
              <p style={{color:'var(--afcfta-muted)'}} className="mb-4">
                {t.papssDesc}
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600">✓</Badge>
                  <span className="text-sm">{t.papssBenefit1}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600">✓</Badge>
                  <span className="text-sm">{t.papssBenefit2}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600">✓</Badge>
                  <span className="text-sm">{t.papssBenefit3}</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-bold text-lg text-purple-400 mb-3">{t.papssAdvantages}</h4>
              <div className="p-4 rounded-lg space-y-3" style={{background:'rgba(192,132,252,0.08)', border:'1px solid rgba(192,132,252,0.2)'}}>
                <div>
                  <p className="text-sm font-semibold text-purple-400">💰 {t.papssCost}</p>
                  <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.papssCostDesc}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-purple-400">⚡ {t.papssSpeed}</p>
                  <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.papssSpeedDesc}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-purple-400">🔒 {t.papssSecurity}</p>
                  <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.papssSecurityDesc}</p>
                </div>
              </div>
              <Badge className="mt-4 bg-yellow-600">{t.papssDeployment}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section Ressources Additionnelles */}
      <Card className="shadow-xl">
        <CardHeader className="afcfta-dark-gradient" style={{borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            <span>📚</span>
            <span>{t.resourcesTitle}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="https://au.int/en/cfta" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-lg transition"
              style={{background:'rgba(59,130,246,0.1)', border:'1px solid rgba(59,130,246,0.25)'}}
            >
              <span className="text-blue-400 text-2xl">🌐</span>
              <div>
                <p className="font-semibold text-blue-400">{t.secretariat}</p>
                <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.secretariatDesc}</p>
              </div>
            </a>

            <a 
              href="https://www.tralac.org/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-lg transition"
              style={{background:'rgba(74,222,128,0.1)', border:'1px solid rgba(74,222,128,0.25)'}}
            >
              <span className="text-green-400 text-2xl">⚖️</span>
              <div>
                <p className="font-semibold text-green-400">{t.tralac}</p>
                <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.tralacDesc}</p>
              </div>
            </a>

            <a 
              href="https://www.worldbank.org/en/topic/trade/publication/the-african-continental-free-trade-area" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-lg transition"
              style={{background:'rgba(192,132,252,0.1)', border:'1px solid rgba(192,132,252,0.25)'}}
            >
              <span className="text-purple-400 text-2xl">🏛️</span>
              <div>
                <p className="font-semibold text-purple-400">{t.worldBank}</p>
                <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.worldBankDesc}</p>
              </div>
            </a>

            <a 
              href="https://www.uneca.org/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-lg transition"
              style={{background:'rgba(251,146,60,0.1)', border:'1px solid rgba(251,146,60,0.25)'}}
            >
              <span className="text-orange-400 text-2xl">📈</span>
              <div>
                <p className="font-semibold text-orange-400">{t.uneca}</p>
                <p className="text-xs" style={{color:'var(--afcfta-muted)'}}>{t.unecaDesc}</p>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>

      <MonitoringDashboard language={language} />

      {/* Footer with Source Indicator */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-3">
          <p className="text-xs text-gray-500 text-center">
            {t.sourceLabel}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
