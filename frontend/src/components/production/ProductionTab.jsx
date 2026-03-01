import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import ProductionMacro from './ProductionMacro';
import ProductionAgriculture from './ProductionAgriculture';
import ProductionManufacturing from './ProductionManufacturing';
import ProductionMining from './ProductionMining';
import { PDFExportButton } from '../common/ExportTools';
import { TrendingUp, Wheat, Factory, Pickaxe, BarChart3, Database, Globe } from 'lucide-react';

function ProductionTab({ language = 'fr' }) {
  const { t } = useTranslation();
  const [activeSubTab, setActiveSubTab] = useState('macro');
  const contentRef = useRef(null);

  return (
    <div className="space-y-5">
      {/* Compact Header with Export */}
      <div className="flex items-center justify-between bg-gradient-to-r from-[#1B232C] to-[#0F1419] border border-[rgba(212,175,55,0.2)] text-white p-4 rounded-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold">{t('production.title')}</h1>
            <p className="text-purple-100 text-sm">{t('production.subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2">
            <Badge className="bg-white/20 text-white text-xs">
              <Globe className="w-3 h-3 mr-1" />
              55 pays
            </Badge>
            <Badge className="bg-white/20 text-white text-xs">
              <Database className="w-3 h-3 mr-1" />
              2024
            </Badge>
          </div>
          <PDFExportButton
            targetRef={contentRef}
            filename="production"
            title={t('production.title')}
            language={language}
          />
        </div>
      </div>

      <div ref={contentRef}>
        {/* Sub-tabs Navigation - Enhanced boxed style */}
        <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-5">
          <TabsList className="tabs-list-boxed cols-4">
            <TabsTrigger 
              value="macro" 
              className="tab-trigger-enhanced tab-purple"
            >
              <TrendingUp className="tab-icon" />
              <span>{t('production.macro.title')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="agriculture" 
              className="tab-trigger-enhanced tab-green"
            >
              <Wheat className="tab-icon" />
              <span>{t('production.agriculture.title')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="manufacturing" 
              className="tab-trigger-enhanced tab-blue"
            >
              <Factory className="tab-icon" />
              <span>{t('production.manufacturing.title')}</span>
            </TabsTrigger>
            <TabsTrigger 
              value="mining" 
              className="tab-trigger-enhanced tab-orange"
            >
              <Pickaxe className="tab-icon" />
              <span>{t('production.mining.title')}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="macro" className="tab-content-enhanced mt-0">
            <ProductionMacro language={language} />
          </TabsContent>

          <TabsContent value="agriculture" className="tab-content-enhanced mt-0">
            <ProductionAgriculture language={language} />
          </TabsContent>

          <TabsContent value="manufacturing" className="tab-content-enhanced mt-0">
            <ProductionManufacturing language={language} />
          </TabsContent>

          <TabsContent value="mining" className="tab-content-enhanced mt-0">
            <ProductionMining language={language} />
          </TabsContent>
        </Tabs>

        {/* Data Sources - Compact footer */}
        <Card className="border-0 shadow-sm mt-6" style={{background:'rgba(27,35,44,0.7)'}}>
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px] border-purple-300 text-purple-600">Macro</Badge>
                World Bank • IMF WEO 2024
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px] border-green-300 text-green-600">Agri</Badge>
                FAOSTAT 2023
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px] border-blue-300 text-blue-600">Manuf</Badge>
                UNIDO 2023
              </span>
              <span className="text-gray-300">|</span>
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="h-5 text-[10px] border-orange-300 text-orange-600">Mining</Badge>
                USGS • AfDB
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ProductionTab;
