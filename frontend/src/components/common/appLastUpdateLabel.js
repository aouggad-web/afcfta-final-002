export function getAppLastUpdateLabel(language) {
  return language === 'fr' ? 'Dernière mise à jour :' : 'Last update:';
}

export function getLastUpdateDateTime(lastUpdateValue) {
  const parsed = Date.parse(lastUpdateValue);
  if (Number.isNaN(parsed)) {
    return undefined;
  }
  return new Date(parsed).toISOString();
}
