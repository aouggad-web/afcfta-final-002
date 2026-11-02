import React from 'react';
import { pick } from '../../i18n/lang';

/**
 * SACU — accord de 2002, art. 19.
 *
 * Une marchandise d'origine tierce déjà dédouanée dans un autre État de la
 * SACU (au port de Durban, par exemple, avant d'être acheminée au Botswana)
 * n'acquitte à destination ni droit de douane ni accise : seuls la TVA et les
 * prélèvements nationaux restent dus. Le calculateur ne peut pas distinguer ce
 * cas d'un transit sous douane : il le demande ici, pour une destination SACU
 * seulement.
 */
export default function DedouanementSacuQuestion({ checked = false, onChange, language = 'fr' }) {
  return (
    <fieldset
      data-testid="dedouanement-sacu-question"
      className="rounded-xl border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-4 space-y-3"
    >
      <label className="flex items-start gap-2 text-sm font-semibold text-[var(--info)]">
        <input
          type="checkbox"
          className="mt-1"
          checked={checked}
          onChange={(e) => onChange?.(e.target.checked)}
        />
        {pick(language,
          'Marchandise déjà dédouanée dans un autre pays de la SACU (Afrique du Sud, Botswana, Lesotho, Namibie, Eswatini)',
          'Goods already cleared in another SACU country (South Africa, Botswana, Lesotho, Namibia, Eswatini)',
          'بضاعة سبق تخليصها جمركيًا في بلد آخر من الاتحاد الجمركي للجنوب الأفريقي (SACU) (جنوب أفريقيا، بوتسوانا، ليسوتو، ناميبيا، إسواتيني)')}
      </label>
      <div className="text-xs text-[var(--afcfta-muted)] space-y-1" data-testid="dedouanement-sacu-cadre">
        <p>
          {pick(language,
            'À cocher si les droits ont déjà été acquittés au port ou au point d’entrée d’un autre pays membre : ni droit de douane ni accise ne sont perçus une seconde fois. La TVA du pays de destination et ses prélèvements nationaux restent dus. Ne pas cocher pour une marchandise en transit sous douane jusqu’à la frontière.',
            'Tick if duties were already paid at the port or point of entry of another member country: neither customs duty nor excise is charged a second time. The destination country’s VAT and national levies remain payable. Do not tick for goods in bonded transit up to the border.',
            'يُؤشَّر عليه إذا سبق أداء الرسوم في الميناء أو نقطة الدخول لبلد عضو آخر: لا يُحصَّل الرسم الجمركي ولا رسم الاستهلاك مرة ثانية. وتظل ضريبة القيمة المضافة لبلد المقصد ورسومه الوطنية مستحقة. لا يُؤشَّر عليه لبضاعة في عبور تحت المراقبة الجمركية حتى الحدود.')}
        </p>
        <p>
          {pick(language, 'Cadre réglementaire : ', 'Legal framework: ', 'الإطار التنظيمي: ')}
          Southern African Customs Union Agreement 2002, art. 19 et 31.4.
        </p>
        <p>
          {pick(language,
            'Marchandise entrée dans la SACU à un taux préférentiel : la différence avec le droit normal est due (art. 31.4) et n’est pas calculée.',
            'Goods that entered SACU at a preferential rate: the difference with the normal duty is payable (art. 31.4) and is not computed.',
            'بضاعة دخلت الاتحاد الجمركي للجنوب الأفريقي بمعدل تفضيلي: الفرق مع الرسم العادي مستحق (المادة 31.4) ولا يُحتسب.')}
        </p>
      </div>
    </fieldset>
  );
}
