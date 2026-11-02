import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from '../../hooks/use-toast';
import { Building2 } from 'lucide-react';
import { pick } from '../../i18n/lang';
import { MapContainer, TileLayer, Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Custom Icon for Free Zones (Orange/Industrial)
const freeZoneIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function FreeZonesTab({ language = 'fr' }) {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState('ALL');
  const [viewMode, setViewMode] = useState('map');

  const texts = {
    fr: {
      title: "Zones Franches & Industrielles",
      description: "Cartographie des pôles de compétitivité, zones franches d'exportation et hubs industriels",
      filterByCountry: "Filtrer par pays:",
      allCountries: "Tous les pays",
      map: "Carte",
      list: "Liste",
      error: "Erreur",
      loadError: "Impossible de charger les données des zones franches",
      industries: "Industries",
      surface: "Surface",
      connection: "Connexion",
      keyIndustries: "Industries Clés",
      incentives: "Incitations",
      keyTenants: "Locataires clés",
      impact: "Impact",
      managingAuthority: "Autorité Gérante"
    },
    en: {
      title: "Free Zones & Industrial Parks",
      description: "Mapping of competitiveness hubs, export free zones and industrial hubs",
      filterByCountry: "Filter by country:",
      allCountries: "All countries",
      map: "Map",
      list: "List",
      error: "Error",
      loadError: "Unable to load free zones data",
      industries: "Industries",
      surface: "Surface",
      connection: "Connection",
      keyIndustries: "Key Industries",
      incentives: "Incentives",
      keyTenants: "Key Tenants",
      impact: "Impact",
      managingAuthority: "Managing Authority"
    },
    ar: {
      title: "المناطق الحرة والصناعية",
      description: "خريطة أقطاب التنافسية والمناطق الحرة للتصدير والمراكز الصناعية",
      filterByCountry: "تصفية حسب البلد:",
      allCountries: "جميع البلدان",
      map: "الخريطة",
      list: "القائمة",
      error: "خطأ",
      loadError: "تعذّر تحميل بيانات المناطق الحرة",
      industries: "الصناعات",
      surface: "المساحة",
      connection: "الربط",
      keyIndustries: "الصناعات الرئيسية",
      incentives: "الحوافز",
      keyTenants: "أبرز الشركات المستقرة",
      impact: "الأثر",
      managingAuthority: "الجهة المسيِّرة"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchZones(selectedCountry);
  }, [selectedCountry]);

  const fetchZones = async (countryIso) => {
    setLoading(true);
    try {
      const url = countryIso && countryIso !== 'ALL'
        ? `${API}/logistics/free-zones?country_iso=${countryIso}`
        : `${API}/logistics/free-zones`;
      
      const response = await axios.get(url);
      setZones(response.data.zones || []);
    } catch (error) {
      console.error('Error fetching free zones:', error);
      toast({
        title: t.error,
        description: t.loadError,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 bg-[image:var(--card-grad)] border border-[var(--afcfta-border)] text-[var(--text)] p-4 rounded-xl shadow-lg">
        <div className="w-10 h-10 bg-[var(--overlay)] rounded-lg flex items-center justify-center">
          <Building2 className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold">{t.title}</h2>
          <p className="text-[var(--info)] text-sm">{t.description}</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex items-center gap-3 w-full md:w-auto">
              <span className="text-sm font-semibold text-[var(--text)]">{t.filterByCountry}</span>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger className="w-64">
                  <SelectValue placeholder={t.allCountries} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">🌍 {t.allCountries}</SelectItem>
                  <SelectItem value="MAR">🇲🇦 {pick(language, 'Maroc', 'Maroc', 'المغرب')}</SelectItem>
                  <SelectItem value="DZA">🇩🇿 {pick(language, 'Algérie', 'Algérie', 'الجزائر')}</SelectItem>
                  <SelectItem value="EGY">🇪🇬 {pick(language, 'Égypte', 'Égypte', 'مصر')}</SelectItem>
                  <SelectItem value="TUN">🇹🇳 {pick(language, 'Tunisie', 'Tunisie', 'تونس')}</SelectItem>
                  <SelectItem value="NGA">🇳🇬 {pick(language, 'Nigéria', 'Nigéria', 'نيجيريا')}</SelectItem>
                  <SelectItem value="GHA">🇬🇭 {pick(language, 'Ghana', 'Ghana', 'غانا')}</SelectItem>
                  <SelectItem value="CIV">🇨🇮 {pick(language, 'Côte d\'Ivoire', 'Côte d\'Ivoire', 'كوت ديفوار')}</SelectItem>
                  <SelectItem value="SEN">🇸🇳 {pick(language, 'Sénégal', 'Sénégal', 'السنغال')}</SelectItem>
                  <SelectItem value="BEN">🇧🇯 {pick(language, 'Bénin', 'Bénin', 'بنين')}</SelectItem>
                  <SelectItem value="TGO">🇹🇬 {pick(language, 'Togo', 'Togo', 'توغو')}</SelectItem>
                  <SelectItem value="CMR">🇨🇲 {pick(language, 'Cameroun', 'Cameroun', 'الكاميرون')}</SelectItem>
                  <SelectItem value="GAB">🇬🇦 {pick(language, 'Gabon', 'Gabon', 'الغابون')}</SelectItem>
                  <SelectItem value="COD">🇨🇩 {pick(language, 'RD Congo', 'RD Congo', 'جمهورية الكونغو الديمقراطية')}</SelectItem>
                  <SelectItem value="AGO">🇦🇴 {pick(language, 'Angola', 'Angola', 'أنغولا')}</SelectItem>
                  <SelectItem value="ZAF">🇿🇦 {pick(language, 'Afrique du Sud', 'Afrique du Sud', 'جنوب أفريقيا')}</SelectItem>
                  <SelectItem value="KEN">🇰🇪 {pick(language, 'Kenya', 'Kenya', 'كينيا')}</SelectItem>
                  <SelectItem value="ETH">🇪🇹 {pick(language, 'Éthiopie', 'Éthiopie', 'إثيوبيا')}</SelectItem>
                  <SelectItem value="TZA">🇹🇿 {pick(language, 'Tanzanie', 'Tanzanie', 'تنزانيا')}</SelectItem>
                  <SelectItem value="UGA">🇺🇬 {pick(language, 'Ouganda', 'Ouganda', 'أوغندا')}</SelectItem>
                  <SelectItem value="RWA">🇷🇼 {pick(language, 'Rwanda', 'Rwanda', 'رواندا')}</SelectItem>
                  <SelectItem value="MOZ">🇲🇿 {pick(language, 'Mozambique', 'Mozambique', 'موزمبيق')}</SelectItem>
                  <SelectItem value="ZMB">🇿🇲 {pick(language, 'Zambie', 'Zambie', 'زامبيا')}</SelectItem>
                  <SelectItem value="MWI">🇲🇼 {pick(language, 'Malawi', 'Malawi', 'ملاوي')}</SelectItem>
                  <SelectItem value="NAM">🇳🇦 {pick(language, 'Namibie', 'Namibie', 'ناميبيا')}</SelectItem>
                  <SelectItem value="BWA">🇧🇼 {pick(language, 'Botswana', 'Botswana', 'بوتسوانا')}</SelectItem>
                  <SelectItem value="DJI">🇩🇯 {pick(language, 'Djibouti', 'Djibouti', 'جيبوتي')}</SelectItem>
                  <SelectItem value="MUS">🇲🇺 {pick(language, 'Maurice', 'Maurice', 'موريشيوس')}</SelectItem>
                  <SelectItem value="MDG">🇲🇬 {pick(language, 'Madagascar', 'Madagascar', 'مدغشقر')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => setViewMode('map')}
                variant={viewMode === 'map' ? 'default' : 'outline'}
              >
                🗺️ {t.map}
              </Button>
              <Button
                onClick={() => setViewMode('list')}
                variant={viewMode === 'list' ? 'default' : 'outline'}
              >
                📋 {t.list}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {viewMode === 'map' ? (
        <Card className="h-[550px] overflow-hidden border-2 border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
          <MapContainer center={[5.0, 20.0]} zoom={3} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {zones.map((zone) => (
              <Marker 
                key={zone.id} 
                position={[zone.location.lat, zone.location.lon]}
                icon={freeZoneIcon}
              >
                <Popup>
                  <div className="p-2 min-w-[280px]">
                    <h3 className="font-bold text-lg text-[var(--terra)] mb-1">{zone.name}</h3>
                    <Badge className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)] mb-2">{zone.type}</Badge>
                    <p className="text-sm text-[var(--afcfta-muted)] mb-2">{zone.country}</p>
                    <div className="text-xs space-y-1">
                      <p><strong>🏗️ {t.industries}:</strong> {zone.industries.join(', ')}</p>
                      <p><strong>📏 {t.surface}:</strong> {zone.surface_ha} {pick(language, 'ha', 'ha', 'هكتار')}</p>
                      <p><strong>🔗 {t.connection}:</strong> {zone.connection}</p>
                    </div>
                    {zone.authority && (
                      <div className="mt-2 pt-2 border-t border-[var(--afcfta-border)]">
                        <p className="text-xs font-semibold text-[var(--info)]">🏛️ {zone.authority.name}</p>
                        {zone.authority.website && (
                          <a href={zone.authority.website} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--info)] hover:underline">
                            {zone.authority.website}
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </Popup>
                <Tooltip>{zone.name}</Tooltip>
              </Marker>
            ))}
          </MapContainer>
        </Card>
      ) : (
        <div className="max-h-[550px] overflow-y-auto rounded-lg border border-[var(--afcfta-border)] p-4 bg-[var(--afcfta-card2)]">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {zones.map((zone) => (
              <Card key={zone.id} className="hover:shadow-lg transition-shadow border-t-4 border-t-orange-500">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <Badge variant="outline" className="text-xs">{zone.country}</Badge>
                  <Badge className={zone.status.includes('Opérationnel') ? 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]' : 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]'}>
                    {zone.status}
                  </Badge>
                </div>
                <CardTitle className="text-xl mt-2">{zone.name}</CardTitle>
                <CardDescription>{zone.type}</CardDescription>
              </CardHeader>
              <CardContent className="text-sm space-y-4">
                <div>
                  <p className="font-semibold text-[var(--text)] mb-1">{t.keyIndustries}:</p>
                  <div className="flex flex-wrap gap-1">
                    {zone.industries.map((ind, i) => (
                      <Badge key={i} variant="secondary" className="bg-[var(--afcfta-card2)] text-[var(--afcfta-muted)] text-xs">
                        {ind}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] p-3 rounded-lg border border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
                  <p className="font-semibold text-[var(--terra)] mb-1">💡 {t.incentives}:</p>
                  <p className="text-xs text-[var(--terra)]">{zone.incentives}</p>
                </div>

                <div className="space-y-1 text-[var(--afcfta-muted)]">
                  <p><strong>🏢 {t.keyTenants}:</strong> {zone.key_tenants.join(', ')}</p>
                  <p><strong>🌍 {t.impact}:</strong> {zone.impact}</p>
                  <p><strong>⚓ {t.connection}:</strong> {zone.connection}</p>
                </div>

                {zone.authority && (
                  <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-3 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] mt-3">
                    <p className="font-semibold text-[var(--info)] mb-2">🏛️ {t.managingAuthority}:</p>
                    <div className="text-xs text-[var(--info)] space-y-1">
                      <p className="font-medium">{zone.authority.name}</p>
                      {zone.authority.address && (
                        <p>📍 {zone.authority.address}</p>
                      )}
                      {zone.authority.phone && (
                        <p>📞 <a href={`tel:${zone.authority.phone}`} className="hover:underline">{zone.authority.phone}</a></p>
                      )}
                      {zone.authority.email && (
                        <p>✉️ <a href={`mailto:${zone.authority.email}`} className="text-[var(--info)] hover:underline">{zone.authority.email}</a></p>
                      )}
                      {zone.authority.website && (
                        <p>🌐 <a href={zone.authority.website} target="_blank" rel="noopener noreferrer" className="text-[var(--info)] hover:underline">{zone.authority.website}</a></p>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          </div>
        </div>
      )}
    </div>
  );
}
