/**
 * Detailed Calculation Breakdown Component
 * Displays step-by-step tax calculation for NPF vs ZLECAf
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Separator } from '../ui/separator';
import { 
  Calculator, TrendingDown, ArrowRight, CheckCircle2,
  AlertCircle, DollarSign, Percent, Info
} from 'lucide-react';

// Format currency
const formatCurrency = (value, currency = 'USD') => {
  if (value === null || value === undefined) return '-';
  const formatted = value.toLocaleString('fr-FR', { 
    minimumFractionDigits: 0, 
    maximumFractionDigits: 0 
  });
  return `$${formatted}`;
};

// Tax line component
const TaxLineRow = ({ tax, language }) => {
  const isExempt = tax.is_zlecaf_exempt;
  const hasAmount = tax.amount > 0;
  
  return (
    <TableRow className={isExempt ? 'bg-emerald-50/50' : ''}>
      <TableCell className="font-medium">
        <div className="flex items-center gap-2">
          <span>{language === 'fr' ? tax.name_fr : tax.name_en}</span>
          {isExempt && (
            <Badge variant="outline" className="text-xs bg-emerald-100 text-emerald-700 border-emerald-300">
              Exonéré ZLECAf
            </Badge>
          )}
        </div>
        <span className="text-xs text-slate-500">{tax.code}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className={`font-mono ${isExempt ? 'line-through text-slate-400' : ''}`}>
          {tax.rate_pct}
        </span>
      </TableCell>
      <TableCell className="text-right text-slate-600">
        {formatCurrency(tax.base_value)}
        <span className="text-xs text-slate-400 ml-1">
          ({tax.base_type === 'cif_plus_dd' ? 'CIF+DD' : 'CIF'})
        </span>
      </TableCell>
      <TableCell className={`text-right font-bold ${isExempt ? 'text-emerald-600' : 'text-slate-900'}`}>
        {formatCurrency(tax.amount)}
      </TableCell>
    </TableRow>
  );
};

// Single regime breakdown
const RegimeBreakdown = ({ calculation, language, isZlecaf = false }) => {
  const bgColor = isZlecaf ? 'bg-emerald-50' : 'bg-blue-50';
  const borderColor = isZlecaf ? 'border-emerald-200' : 'border-blue-200';
  const headerColor = isZlecaf ? 'text-emerald-700' : 'text-blue-700';
  const accentColor = isZlecaf ? 'bg-emerald-100' : 'bg-blue-100';
  
  const texts = {
    fr: {
      cifBreakdown: "Décomposition CIF",
      fob: "Valeur FOB",
      freight: "Fret",
      insurance: "Assurance",
      cifTotal: "Valeur CIF",
      taxBreakdown: "Détail des Taxes",
      tax: "Taxe",
      rate: "Taux",
      base: "Base",
      amount: "Montant",
      totalTaxes: "Total Taxes",
      totalToPay: "Total à Payer"
    },
    en: {
      cifBreakdown: "CIF Breakdown",
      fob: "FOB Value",
      freight: "Freight",
      insurance: "Insurance",
      cifTotal: "CIF Value",
      taxBreakdown: "Tax Details",
      tax: "Tax",
      rate: "Rate",
      base: "Base",
      amount: "Amount",
      totalTaxes: "Total Taxes",
      totalToPay: "Total to Pay"
    }
  };
  
  const txt = texts[language] || texts.fr;
  
  return (
    <Card className={`shadow-lg ${bgColor} ${borderColor} border-2`}>
      <CardHeader className="pb-2">
        <CardTitle className={`text-lg ${headerColor} flex items-center gap-2`}>
          {isZlecaf ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <AlertCircle className="h-5 w-5" />
          )}
          {language === 'fr' ? calculation.regime_name_fr : calculation.regime_name_en}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* CIF Breakdown */}
        <div className={`${accentColor} rounded-lg p-3`}>
          <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1">
            <Calculator className="h-4 w-4" />
            {txt.cifBreakdown}
          </h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-slate-600">{txt.fob}:</span>
            <span className="text-right font-mono">{formatCurrency(calculation.fob_value)}</span>
            <span className="text-slate-600">{txt.freight}:</span>
            <span className="text-right font-mono">{formatCurrency(calculation.freight)}</span>
            <span className="text-slate-600">{txt.insurance}:</span>
            <span className="text-right font-mono">{formatCurrency(calculation.insurance)}</span>
            <Separator className="col-span-2 my-1" />
            <span className="font-semibold text-slate-800">{txt.cifTotal}:</span>
            <span className="text-right font-mono font-bold">{formatCurrency(calculation.cif_value)}</span>
          </div>
        </div>
        
        {/* Tax Details Table */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1">
            <Percent className="h-4 w-4" />
            {txt.taxBreakdown}
          </h4>
          <div className="rounded-lg overflow-hidden border border-slate-200 bg-white">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>{txt.tax}</TableHead>
                  <TableHead className="text-center">{txt.rate}</TableHead>
                  <TableHead className="text-right">{txt.base}</TableHead>
                  <TableHead className="text-right">{txt.amount}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {calculation.tax_lines.map((tax, idx) => (
                  <TaxLineRow key={idx} tax={tax} language={language} />
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
        
        {/* Totals */}
        <div className={`${accentColor} rounded-lg p-3`}>
          <div className="flex justify-between items-center">
            <span className="text-sm text-slate-600">{txt.totalTaxes}:</span>
            <span className="font-mono font-bold">{formatCurrency(calculation.total_taxes)}</span>
          </div>
          <Separator className="my-2" />
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-800">{txt.totalToPay}:</span>
            <span className={`text-xl font-bold ${isZlecaf ? 'text-emerald-700' : 'text-blue-700'}`}>
              {formatCurrency(calculation.total_to_pay)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main comparison component
export default function DetailedCalculationBreakdown({ result, language = 'fr' }) {
  if (!result) return null;
  
  const texts = {
    fr: {
      title: "Détail du Calcul",
      subtitle: "Comparaison complète NPF vs ZLECAf",
      product: "Produit",
      country: "Pays",
      savings: "Économies avec ZLECAf",
      savingsAmount: "Montant économisé",
      savingsPercent: "Pourcentage d'économie",
      methodology: "Méthodologie de calcul",
      methodologyText: "Les droits de douane (DD) sont exonérés sous le régime ZLECAf. La TVA est calculée sur la valeur CIF + DD pour le régime NPF, et sur la valeur CIF seule pour ZLECAf."
    },
    en: {
      title: "Calculation Details",
      subtitle: "Complete NPF vs AfCFTA comparison",
      product: "Product",
      country: "Country",
      savings: "Savings with AfCFTA",
      savingsAmount: "Amount saved",
      savingsPercent: "Savings percentage",
      methodology: "Calculation Methodology",
      methodologyText: "Customs duties (DD) are exempt under the AfCFTA regime. VAT is calculated on CIF + DD for MFN regime, and on CIF only for AfCFTA."
    }
  };
  
  const txt = texts[language] || texts.fr;
  
  return (
    <div className="space-y-6" data-testid="detailed-calculation-breakdown">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-xl font-bold text-slate-900 flex items-center justify-center gap-2">
          <Calculator className="h-6 w-6 text-purple-600" />
          {txt.title}
        </h3>
        <p className="text-sm text-slate-500">{txt.subtitle}</p>
      </div>
      
      {/* Product Info */}
      <div className="flex flex-wrap gap-4 justify-center">
        <Badge variant="outline" className="px-3 py-1">
          <span className="text-slate-500 mr-2">{txt.product}:</span>
          <span className="font-mono font-bold">{result.hs_code}</span>
          {result.hs_code_description_fr && (
            <span className="ml-2 text-slate-600">
              - {language === 'fr' ? result.hs_code_description_fr : result.hs_code_description_en}
            </span>
          )}
        </Badge>
        <Badge variant="outline" className="px-3 py-1">
          <span className="text-slate-500 mr-2">{txt.country}:</span>
          <span className="font-bold">
            {language === 'fr' ? result.country_name_fr : result.country_name_en}
          </span>
        </Badge>
      </div>
      
      {/* Savings Banner */}
      <Card className="bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-xl">
        <CardContent className="py-6">
          <div className="flex items-center justify-center gap-8 flex-wrap">
            <div className="text-center">
              <TrendingDown className="h-8 w-8 mx-auto mb-2 opacity-90" />
              <p className="text-sm opacity-90">{txt.savingsAmount}</p>
              <p className="text-3xl font-bold">{formatCurrency(result.savings_amount)}</p>
            </div>
            <div className="text-6xl font-thin opacity-50">|</div>
            <div className="text-center">
              <Percent className="h-8 w-8 mx-auto mb-2 opacity-90" />
              <p className="text-sm opacity-90">{txt.savingsPercent}</p>
              <p className="text-3xl font-bold">{result.savings_percent}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Side by Side Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RegimeBreakdown 
          calculation={result.npf_calculation} 
          language={language} 
          isZlecaf={false} 
        />
        <RegimeBreakdown 
          calculation={result.zlecaf_calculation} 
          language={language} 
          isZlecaf={true} 
        />
      </div>
      
      {/* Methodology Note */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-2">
            <Info className="h-5 w-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-slate-700">{txt.methodology}</p>
              <p className="text-xs text-slate-500 mt-1">{txt.methodologyText}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
