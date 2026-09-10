/** A missing route may use the legacy endpoint; missing data must stay missing. */
export function shouldUseLegacyCalculator(error) {
  return error?.response?.status === 404
    && error.response.data?.detail === 'Not Found';
}
