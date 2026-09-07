import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * cn — fusionne des classes conditionnelles (clsx) puis dédoublonne les
 * classes Tailwind conflictuelles (tailwind-merge). Helper standard shadcn/ui.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
