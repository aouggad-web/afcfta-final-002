import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Alert, AlertTitle, AlertDescription } from '../ui/alert';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '../ui/collapsible';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { regulatoryApi } from '../../services/api-v2';
import { toast } from '../../hooks/use-toast';

const TEXTS = {
  fr: {
    title: 'Qualité des données réglementaires',
    subtitle:
      "Rapport de couverture, contradictions et péremption (contrôles LOT 6) — informations de gouvernance sur le jeu de données, jamais un calcul.",
    publishedOf: (published, total) => `${published} / ${total} pays publiés`,
    noIssues: 'Aucune contradiction et aucun dataset périmé détecté.',
    contradictionsTitle: (n) => `${n} contradiction${n > 1 ? 's' : ''} détectée${n > 1 ? 's' : ''}`,
    contradictionsDesc:
      "Une mesure revendique plus de confiance que la source légale qu'elle cite — à corriger.",
    staleTitle: (n) => `${n} pays avec dataset${n > 1 ? 's' : ''} périmé${n > 1 ? 's' : ''}`,
    staleDesc: "Le seuil de péremption est dépassé — à revérifier, jamais renouvelé automatiquement.",
    country: 'Pays',
    asOf: 'Situation au',
    measures: 'Mesures',
    actors: 'Prestataires',
    terminated: 'Mandats terminés',
    loadError: 'Impossible de charger le rapport qualité',
  },
  en: {
    title: 'Regulatory data quality',
    subtitle:
      'Coverage, contradiction and staleness report (LOT 6 controls) — dataset governance information, never a calculation.',
    publishedOf: (published, total) => `${published} / ${total} countries published`,
    noIssues: 'No contradiction and no stale dataset detected.',
    contradictionsTitle: (n) => `${n} contradiction${n > 1 ? 's' : ''} detected`,
    contradictionsDesc:
      'A measure claims more confidence than the legal source it cites — needs a fix.',
    staleTitle: (n) => `${n} countr${n > 1 ? 'ies' : 'y'} with a stale dataset${n > 1 ? 's' : ''}`,
    staleDesc: 'The staleness threshold is exceeded — flagged for re-verification, never auto-renewed.',
    country: 'Country',
    asOf: 'As of',
    measures: 'Measures',
    actors: 'Providers',
    terminated: 'Terminated mandates',
    loadError: 'Unable to load the quality report',
  },
};

export default function RegulatoryQAPanel({ language = 'fr' }) {
  const t = TEXTS[language] || TEXTS.fr;
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [coverage, setCoverage] = useState(null);
  const [contradictions, setContradictions] = useState([]);
  const [staleCountries, setStaleCountries] = useState([]);

  useEffect(() => {
    if (!open || loaded) return;
    let cancelled = false;
    (async () => {
      try {
        const [coverageResp, contradictionsResp, staleResp] = await Promise.all([
          regulatoryApi.getQACoverageReport(),
          regulatoryApi.getQAContradictions(),
          regulatoryApi.getQAStaleCountries(),
        ]);
        if (cancelled) return;
        setCoverage(coverageResp?.report || null);
        setContradictions(contradictionsResp?.contradictions || []);
        setStaleCountries(staleResp?.stale_countries || []);
        setLoaded(true);
      } catch (error) {
        console.error('Error loading regulatory QA report:', error);
        toast({
          title: t.loadError,
          description: String(error?.message || error),
          variant: 'destructive',
        });
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, loaded]);

  const hasIssues = contradictions.length > 0 || staleCountries.length > 0;

  return (
    <Card className="border border-slate-700 bg-slate-900/40">
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger
          className="w-full text-left cursor-pointer select-none flex flex-row items-center justify-between gap-2 p-6 rounded-t-xl"
          style={{ background: 'linear-gradient(135deg, rgba(193,122,43,0.15), rgba(212,175,55,0.08))' }}
        >
          <div>
            <CardTitle className="text-base text-slate-200 flex items-center gap-2">
              {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              {t.title}
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">{t.subtitle}</CardDescription>
          </div>
          {loaded && coverage && (
            <Badge
              variant="outline"
              className={
                hasIssues
                  ? 'bg-red-600/20 text-red-300 border-red-500/40'
                  : 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40'
              }
            >
              {t.publishedOf(coverage.published_country_count, coverage.total_tracked_countries)}
            </Badge>
          )}
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-4 text-sm">
            {!loaded && <p className="text-slate-400">…</p>}

            {loaded && !hasIssues && (
              <Alert>
                <AlertTitle>{language === 'fr' ? 'Statut' : 'Status'}</AlertTitle>
                <AlertDescription>{t.noIssues}</AlertDescription>
              </Alert>
            )}

            {contradictions.length > 0 && (
              <Alert variant="destructive">
                <AlertTitle>{t.contradictionsTitle(contradictions.length)}</AlertTitle>
                <AlertDescription>
                  {t.contradictionsDesc}
                  <ul className="mt-2 list-disc pl-5">
                    {contradictions.map((c) => (
                      <li key={`${c.country_iso3}-${c.record_id}`}>
                        {c.country_iso3} — {c.record_id}: {c.measure_verification_status} vs{' '}
                        {c.source_verification_status} ({c.source_id})
                      </li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {staleCountries.length > 0 && (
              <Alert variant="destructive">
                <AlertTitle>{t.staleTitle(staleCountries.length)}</AlertTitle>
                <AlertDescription>
                  {t.staleDesc}
                  <ul className="mt-2 list-disc pl-5">
                    {staleCountries.map((s) => (
                      <li key={s.country_iso3}>
                        {s.country_iso3} — {t.asOf.toLowerCase()} {s.as_of || 'N/A'} ({s.reason})
                      </li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {loaded && coverage && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.country}</TableHead>
                    <TableHead>{t.asOf}</TableHead>
                    <TableHead>{t.measures}</TableHead>
                    <TableHead>{t.actors}</TableHead>
                    <TableHead>{t.terminated}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(coverage.countries || []).map((c) => (
                    <TableRow key={c.country_iso3}>
                      <TableCell className="font-medium">{c.country_iso3}</TableCell>
                      <TableCell>{c.as_of}</TableCell>
                      <TableCell>{c.measure_count}</TableCell>
                      <TableCell>{c.mandated_actor_count}</TableCell>
                      <TableCell>{c.terminated_actor_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
