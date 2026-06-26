/**
 * Opportunities Tab — main container
 * 5 sub-tabs: Analyse IA · Substitution · Chaînes de Valeur · Par Produit · Comparaison
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, ArrowLeftRight, Layers, Package, BarChart3, Scale, Calculator } from 'lucide-react';

import AIAnalysis from './AIAnalysis';
import SubstitutionAnalysis from './SubstitutionAnalysis';
import ValueChains from './ValueChains';
import ProductAnalysisView from './ProductAnalysisView';
import CountryComparison from './CountryComparison';
import OpportunitySummary from './OpportunitySummary';
import ZlecafImpactSimulator from './ZlecafImpactSimulator';

const TABS = {
  fr: [
    { id: 'ai',           label: 'Analyse IA',         icon: Sparkles },
    { id: 'substitution', label: 'Substitution',        icon: ArrowLeftRight },
    { id: 'simulator',    label: 'Simulateur ZLECAf',   icon: Calculator },
    { id: 'summary',      label: "Vue d'ensemble",      icon: BarChart3 },
    { id: 'valueChains',  label: 'Chaînes de Valeur',   icon: Layers },
    { id: 'byProduct',    label: 'Par Produit',          icon: Package },
    { id: 'comparison',   label: 'Comparaison',          icon: Scale },
  ],
  en: [
    { id: 'ai',           label: 'AI Analysis',         icon: Sparkles },
    { id: 'substitution', label: 'Substitution',        icon: ArrowLeftRight },
    { id: 'simulator',    label: 'AfCFTA Simulator',    icon: Calculator },
    { id: 'summary',      label: 'Overview',             icon: BarChart3 },
    { id: 'valueChains',  label: 'Value Chains',         icon: Layers },
    { id: 'byProduct',    label: 'By Product',           icon: Package },
    { id: 'comparison',   label: 'Comparison',           icon: Scale },
  ],
};

export default function OpportunitiesTab({ language = 'fr' }) {
  const { i18n } = useTranslation();
  const lang = i18n.language || language;
  const [active, setActive] = useState('ai');

  const tabs = TABS[lang] || TABS.fr;

  const renderContent = () => {
    switch (active) {
      case 'ai':           return <AIAnalysis language={lang} />;
      case 'substitution': return <SubstitutionAnalysis language={lang} />;
      case 'simulator':    return <ZlecafImpactSimulator language={lang} />;
      case 'summary':      return <OpportunitySummary language={lang} />;
      case 'valueChains':  return <ValueChains language={lang} />;
      case 'byProduct':    return <ProductAnalysisView language={lang} />;
      case 'comparison':   return <CountryComparison language={lang} />;
      default:             return null;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} data-testid="opportunities-tab">
      {/* Sub-tab navigation */}
      <div style={{
        display: 'flex',
        gap: 4,
        padding: '4px',
        background: 'var(--afcfta-bg)',
        borderRadius: 12,
        border: '1px solid var(--afcfta-border)',
        flexWrap: 'wrap',
      }}>
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActive(id)}
            data-testid={`opportunities-${id}-tab`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 14px',
              borderRadius: 9,
              fontSize: 13,
              fontWeight: active === id ? 700 : 500,
              border: 'none',
              cursor: 'pointer',
              background: active === id ? 'var(--afcfta-card)' : 'transparent',
              color: active === id ? 'var(--text)' : 'var(--afcfta-muted)',
              boxShadow: active === id ? '0 1px 4px rgba(0,0,0,0.12)' : 'none',
              transition: 'all 0.15s',
              whiteSpace: 'nowrap',
            }}
          >
            <Icon style={{ width: 14, height: 14, flexShrink: 0, color: active === id ? 'var(--gold)' : 'inherit' }} />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div key={active} className="afcfta-fadeIn">
        {renderContent()}
      </div>
    </div>
  );
}
