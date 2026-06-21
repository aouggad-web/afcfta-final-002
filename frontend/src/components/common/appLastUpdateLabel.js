export function getAppLastUpdateLabel(language) {
  if (language === 'fr') return 'Dernière mise à jour :';
  if (language === 'en') return 'Last update:';
  return 'Last update:';
}
