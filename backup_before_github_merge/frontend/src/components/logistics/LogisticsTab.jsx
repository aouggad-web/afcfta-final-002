import React, { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import MaritimeLogisticsTab from './MaritimeLogisticsTab';
import AirLogisticsTab from './AirLogisticsTab';
import LandLogisticsTab from './LandLogisticsTab';
import FreeZonesTab from './FreeZonesTab';
import { PDFExportButton } from '../common/ExportTools';
import { Ship, Plane, Truck, Building2, Globe, Database } from 'lucide-react';

export default function LogisticsTab({ language = 'fr' }) {
  const { t } = useTranslation();
  const contentRef = useRef(null);

  return (
    <div className="space-y-5" data-testid="logistics-tab">
      {/* Compact Header with Export */}
      <div className="flex items-center justify-between bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-700 text-white p-4 rounded-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold">{t('logistics.title')}</h1>
            <p className="text-blue-100 text-sm">{t('logistics.subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge className="bg-white/20 text-white hidden md:flex">
            <Database className="w-3 h-3 mr-1" />
            68 ports • 120+ aéroports • 15 corridors
          </Badge>
          <PDFExportButton
            targetRef={contentRef}
            filename="logistics"
            title={t('logistics.title')}
            language={language}
          />
        </div>
      </div>

      <div ref={contentRef}>
        {/* Main Tabs with enhanced styling */}
        <Tabs defaultValue="maritime" className="space-y-5">
          <TabsList className="tabs-list-boxed cols-4">
            <TabsTrigger 
              value="maritime" 
              className="tab-trigger-enhanced tab-blue"
              data-testid="maritime-tab-trigger"
            >
              <Ship className="tab-icon" />
              <span>{t('logistics.maritime')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="air" 
              className="tab-trigger-enhanced tab-cyan"
              data-testid="air-tab-trigger"
            >
              <Plane className="tab-icon" />
              <span>{t('logistics.air')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="land" 
              className="tab-trigger-enhanced tab-orange"
              data-testid="land-tab-trigger"
            >
              <Truck className="tab-icon" />
              <span>{t('logistics.land')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="zones" 
              className="tab-trigger-enhanced tab-purple"
              data-testid="zones-tab-trigger"
            >
              <Building2 className="tab-icon" />
              <span>{t('logistics.freeZones')}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="maritime" className="tab-content-enhanced mt-0">
            <MaritimeLogisticsTab language={language} />
          </TabsContent>

          <TabsContent value="air" className="tab-content-enhanced mt-0">
            <AirLogisticsTab language={language} />
          </TabsContent>

          <TabsContent value="land" className="tab-content-enhanced mt-0">
            <LandLogisticsTab language={language} />
          </TabsContent>

          <TabsContent value="zones" className="tab-content-enhanced mt-0">
            <FreeZonesTab language={language} />
          </TabsContent>
        </Tabs>

        {/* Data Sources - Compact footer */}
        <Card className="border-0 shadow-sm mt-6" style={{background:'rgba(27,35,44,0.7)'}}>
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px]">TRS</Badge>
                WCO Time Release Studies
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px]">UNCTAD</Badge>
                Maritime Transport Review 2024
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px]">LPI</Badge>
                World Bank 2023
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px]">AfCFTA</Badge>
                Secretariat
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
