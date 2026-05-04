// Helper functions
const hasValue = (value) => value !== null && value !== undefined && value !== '';

const formatPercent = (value, digits = 1) => hasValue(value) ? `${Number(value).toFixed(digits)}%` : 'N/A';

// Existing code...

// Use hasValue helper function for inflation_rate, unemployment_rate, total_debt_pct_gdp, etc.

const inflation_rate = hasValue(countryProfile.inflation_rate) ? formatPercent(countryProfile.inflation_rate) : 'N/A';
const unemployment_rate = hasValue(countryProfile.unemployment_rate) ? formatPercent(countryProfile.unemployment_rate) : 'N/A';
const total_debt_pct_gdp = hasValue(countryProfile.total_debt_pct_gdp) ? formatPercent(countryProfile.total_debt_pct_gdp) : 'N/A';
const external_debt_pct_gdp = hasValue(countryProfile.external_debt_pct_gdp) ? formatPercent(countryProfile.external_debt_pct_gdp) : 'N/A';
const domestic_debt_pct_gdp = hasValue(countryProfile.domestic_debt_pct_gdp) ? formatPercent(countryProfile.domestic_debt_pct_gdp) : 'N/A';
const hdi_rank = hasValue(countryProfile.hdi_rank) ? countryProfile.hdi_rank : 'N/A';
const population_millions = hasValue(countryProfile.population_millions) ? countryProfile.population_millions : 'N/A';
const population = hasValue(countryProfile.population) ? countryProfile.population : 'N/A';

// Update Guard for Public Debt Section
const showPublicDebtSection = hasValue(countryProfile.total_debt_pct_gdp) || hasValue(countryProfile.external_debt_pct_gdp) || hasValue(countryProfile.domestic_debt_pct_gdp);

// Update World Bank Indicator Cards
const gini_index_2024 = hasValue(countryProfile.gini_index_2024) ? countryProfile.gini_index_2024 : 'N/A';
const urban_population_pct_2024 = hasValue(countryProfile.urban_population_pct_2024) ? countryProfile.urban_population_pct_2024 : 'N/A';
const internet_users_pct_2024 = hasValue(countryProfile.internet_users_pct_2024) ? countryProfile.internet_users_pct_2024 : 'N/A';
const cybersecurity_index_2024 = hasValue(countryProfile.cybersecurity_index_2024) ? countryProfile.cybersecurity_index_2024 : 'N/A';
const electricity_access_2022 = hasValue(countryProfile.electricity_access_2022) ? countryProfile.electricity_access_2022 : 'N/A';
const mobile_3g_coverage_2024 = hasValue(countryProfile.mobile_3g_coverage_2024) ? countryProfile.mobile_3g_coverage_2024 : 'N/A';
const female_labor_force_pct_2024 = hasValue(countryProfile.female_labor_force_pct_2024) ? countryProfile.female_labor_force_pct_2024 : 'N/A';
const water_stress_2022 = hasValue(countryProfile.water_stress_2022) ? countryProfile.water_stress_2022 : 'N/A';
const ghg_emissions_mt_2022 = hasValue(countryProfile.ghg_emissions_mt_2022) ? countryProfile.ghg_emissions_mt_2022 : 'N/A';
const learning_poverty_2023 = hasValue(countryProfile.learning_poverty_2023) ? countryProfile.learning_poverty_2023 : 'N/A';

// Update Guard for Infrastructure Section
const hasEntries = (obj) => obj && Object.keys(obj).length > 0;

// Rest of the component code...