import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const ATLAS_PATH = '/tools/afcfta_business_atlas.html';

export default function BusinessAtlasModule({ language = 'fr' }) {
  const [showPreview, setShowPreview] = useState(true);

  const t = useMemo(() => {
    if (language === 'fr') {
      return {
        title: 'Atlas Business ZLECAf',
        subtitle: 'Module interactif des operateurs economiques africains',
        note: 'Integration du tableau de bord Atlas comme sous-module des outils.',
        open: 'Ouvrir en plein ecran',
        hide: 'Masquer la previsualisation',
        show: 'Afficher la previsualisation',
        iframeTitle: 'Atlas Business ZLECAf',
        status: 'Nouveau',
      };
    }

    return {
      title: 'AfCFTA Business Atlas',
      subtitle: 'Interactive module for African economic operators',
      note: 'Atlas dashboard integrated as a submodule of the tools section.',
      open: 'Open full screen',
      hide: 'Hide preview',
      show: 'Show preview',
      iframeTitle: 'AfCFTA Business Atlas',
      status: 'New',
    };
  }, [language]);

  return (
    <Card className="border-2 shadow-xl" style={{ borderColor: 'rgba(45,179,106,0.35)' }}>
      <CardHeader className="afcfta-dark-gradient" style={{ borderBottom: '1px solid rgba(45,179,106,0.25)' }}>
        <div className="flex items-center gap-3 flex-wrap">
          <CardTitle className="text-2xl text-green-400 flex items-center gap-2">
            <span>🧭</span>
            <span>{t.title}</span>
          </CardTitle>
          <Badge className="bg-green-600 text-white">{t.status}</Badge>
        </div>
        <CardDescription className="text-base font-medium">
          {t.subtitle}
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-6">
        <p className="text-sm mb-4" style={{ color: 'var(--afcfta-muted)' }}>
          {t.note}
        </p>

        <div className="flex flex-wrap gap-3 mb-4">
          <Button asChild className="bg-green-600 hover:bg-green-700 text-white">
            <a href={ATLAS_PATH} target="_blank" rel="noopener noreferrer">
              {t.open}
            </a>
          </Button>

          <Button variant="outline" onClick={() => setShowPreview((current) => !current)}>
            {showPreview ? t.hide : t.show}
          </Button>
        </div>

        {showPreview && (
          <div
            className="rounded-xl overflow-hidden border"
            style={{ borderColor: 'rgba(255,255,255,0.12)', height: '760px' }}
          >
            <iframe
              src={ATLAS_PATH}
              title={t.iframeTitle}
              className="w-full h-full"
              loading="lazy"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
