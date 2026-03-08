"""
AfCFTA Platform - GraphQL Schema Definition
============================================
Comprehensive schema for flexible, efficient queries across the platform.

This module defines all GraphQL types and operations. The schema is consumed
by the Strawberry-based resolver layer (schema.py).
"""

GRAPHQL_SCHEMA_SDL = '''
"""AfCFTA Platform GraphQL API"""

scalar JSON
scalar DateTime

# ===========================================================================
# Common / Utility types
# ===========================================================================

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
  totalCount: Int!
}

input PaginationInput {
  page: Int = 1
  perPage: Int = 20
  after: String
}

type ConfidenceInterval {
  lower: Float!
  upper: Float!
}

# ===========================================================================
# Country & Region types
# ===========================================================================

enum RegionalBloc {
  ECOWAS
  CEMAC
  EAC
  SADC
  UMA
  COMESA
  IGAD
}

type Country {
  isoCode: String!
  nameEn: String!
  nameFr: String!
  regionalBloc: RegionalBloc
  gdpBnUsd: Float
  populationMn: Float
  active: Boolean!
}

type RegionalBlocSummary {
  bloc: RegionalBloc!
  fullName: String!
  memberCount: Int!
  countries: [String!]!
  gdpBnUsd: Float!
  populationMn: Float!
  intraTradePercent: Float!
  metrics: JSON
}

# ===========================================================================
# Tariff types
# ===========================================================================

type TariffLine {
  hsCode: String!
  countryCode: String!
  tariffRate: Float!
  effectiveDate: String
  active: Boolean!
}

input TariffCalculationInput {
  originCountry: String!
  destinationCountry: String!
  hsCode: String!
  goodsValueUsd: Float!
}

type TariffCalculationResult {
  originCountry: String!
  destinationCountry: String!
  hsCode: String!
  goodsValueUsd: Float!
  tariffRatePct: Float!
  dutyAmountUsd: Float!
  totalLandedCostUsd: Float!
  appliedScheme: String!
  notes: [String!]!
}

type BulkCalculationResult {
  operationId: String!
  totalRequests: Int!
  successCount: Int!
  errorCount: Int!
  results: [TariffCalculationResult!]!
  processingTimeMs: Float!
}

# ===========================================================================
# HS Code & Product Search types
# ===========================================================================

input ProductSearchFilters {
  chapter: String
  lang: String
  exactMatch: Boolean
}

type HSCodeMatch {
  hsCode: String!
  descriptionEn: String!
  descriptionFr: String
  matchType: String!
  similarity: Float
}

type ProductSearchResult {
  query: String!
  exactMatches: [HSCodeMatch!]!
  fuzzyMatches: [HSCodeMatch!]!
  semanticMatches: [HSCodeMatch!]!
  categorySuggestions: [JSON!]!
  totalMatches: Int!
}

# ===========================================================================
# Investment Intelligence types
# ===========================================================================

enum Sector {
  AGRICULTURE
  MANUFACTURING
  ICT
  ENERGY
  FINANCE
  TOURISM
  LOGISTICS
  MINING
  TEXTILES
  AUTOMOTIVE
  GENERAL
}

enum RiskLevel {
  LOW
  MEDIUM
  HIGH
}

type ComponentScore {
  name: String!
  rawScore: Float!
  weightedScore: Float!
  weight: Float!
}

type RiskFactor {
  name: String!
  description: String!
  severity: String!
  score: String!
}

type InvestmentScore {
  country: String!
  sector: String!
  overallScore: Float!
  grade: String!
  componentScores: [ComponentScore!]!
  confidenceInterval: ConfidenceInterval!
  recommendationStrength: String!
  riskFactors: [RiskFactor!]!
  successProbability: Float!
}

type InvestmentRecommendation {
  rank: Int!
  country: String!
  sector: String!
  score: InvestmentScore!
  rationale: String!
  keyAdvantages: [String!]!
  actionItems: [String!]!
}

type PersonalizedRecommendations {
  userId: String
  sector: String!
  riskTolerance: String!
  recommendations: [InvestmentRecommendation!]!
  generatedAt: String!
}

input UserProfile {
  sector: String
  riskTolerance: String
  preferredRegions: [String!]
  investmentSizePref: String
}

input InvestmentCriteria {
  countries: [String!]
  regions: [String!]
  sectors: [String!]
  investmentSize: String
  riskTolerance: String
  minScore: Float
  requiredIncentives: [String!]
}

type InvestmentSearchResult {
  criteria: JSON!
  totalCount: Int!
  opportunities: [JSON!]!
  facets: JSON!
  relatedSearches: [String!]!
}

type RiskAssessment {
  country: String!
  sector: String!
  overallRiskScore: Float!
  riskLevel: RiskLevel!
  identifiedRisks: [RiskFactor!]!
  mitigationStrategies: [String!]!
}

# ===========================================================================
# Trade Flow Prediction types
# ===========================================================================

type TradeFlowPrediction {
  originCountry: String!
  destinationCountry: String!
  productCategory: String!
  timeframeMonths: Int!
  predictedVolumeT: Float!
  predictedValueUsd: Float!
  confidenceInterval: ConfidenceInterval!
  keyFactors: [String!]!
  risks: [String!]!
  opportunities: [String!]!
  trendDirection: String!
}

# ===========================================================================
# Regional Analytics types
# ===========================================================================

type RegionalMetric {
  metric: String!
  value: Float!
  unit: String
  benchmark: Float
}

type TradeCorridorInfo {
  origin: String!
  destination: String!
  tradeValueBn: Float!
  growthPct: Float!
  keyProducts: [String!]!
  mainRoute: String!
}

type RegionalComparison {
  blocs: JSON!
  rankings: JSON!
  bestPerformer: JSON!
}

type InvestmentHeatmapEntry {
  bloc: String!
  fullName: String!
  investmentScore: Float!
  tradeIntegration: Float!
  infrastructure: Float!
  countryCount: Int!
  gdpBnUsd: Float!
  opportunityTier: String!
}

# ===========================================================================
# Country Comparison
# ===========================================================================

type CountryComparison {
  countries: [String!]!
  scores: [InvestmentScore!]!
  ranking: [JSON!]!
}

# ===========================================================================
# Real-time / Live types
# ===========================================================================

type LiveRegionalMetrics {
  bloc: String!
  metrics: [RegionalMetric!]!
  lastUpdated: String!
}

type TariffUpdate {
  countryCode: String!
  hsCode: String!
  oldRate: Float!
  newRate: Float!
  effectiveDate: String!
}

type CalculationProgress {
  operationId: String!
  progressPercent: Float!
  processedCount: Int!
  totalCount: Int!
  status: String!
}

# ===========================================================================
# Saved searches & alerts
# ===========================================================================

type SavedSearch {
  id: String!
  name: String!
  searchParams: JSON!
  createdAt: String!
}

type InvestmentAlert {
  id: String!
  userId: String!
  criteria: JSON!
  active: Boolean!
  createdAt: String!
}

# ===========================================================================
# Performance metrics
# ===========================================================================

type CacheStats {
  l1HotData: JSON!
  l2RegionalIntel: JSON!
  l3Calculations: JSON!
  l4Realtime: JSON!
  timestamp: String!
}

type PerformanceSummary {
  uptimeSeconds: Float!
  slowQueriesCount: Int!
  recentSlowQueries: [JSON!]!
  operations: JSON!
}

# ===========================================================================
# Queries
# ===========================================================================

type Query {
  # Health
  health: JSON!

  # Product / HS code search
  searchProducts(
    query: String!
    filters: ProductSearchFilters
    pagination: PaginationInput
  ): ProductSearchResult!

  # Investment search
  searchInvestmentOpportunities(
    criteria: InvestmentCriteria!
  ): InvestmentSearchResult!

  # Investment scoring
  getInvestmentScore(
    country: String!
    sector: String = "general"
    investmentSize: String = "medium"
    userProfile: UserProfile
  ): InvestmentScore!

  # Country comparison
  compareCountries(
    countries: [String!]!
    sector: String = "general"
  ): CountryComparison!

  # Regional comparison
  compareRegions(
    regions: [RegionalBloc!]!
    metrics: [String!]
  ): RegionalComparison!

  # Bulk tariff calculation
  bulkTariffCalculation(
    calculations: [TariffCalculationInput!]!
  ): BulkCalculationResult!

  # Personalized recommendations
  getPersonalizedRecommendations(
    userProfile: UserProfile!
    limit: Int = 10
  ): PersonalizedRecommendations!

  # Trade flow prediction
  predictTradeFlows(
    originCountry: String!
    destinationCountry: String!
    productCategory: String!
    timeframeMonths: Int = 12
  ): TradeFlowPrediction!

  # Risk assessment
  getRiskAssessment(
    country: String!
    sector: String = "general"
    investmentSize: String = "medium"
  ): RiskAssessment!

  # Regional analytics
  getRegionalBlocSummary(bloc: RegionalBloc!): RegionalBlocSummary!
  getInvestmentHeatmap: [InvestmentHeatmapEntry!]!
  getTradeCorridors(originBloc: String): [TradeCorridorInfo!]!
  getLiveRegionalMetrics(bloc: RegionalBloc!): LiveRegionalMetrics!

  # Performance monitoring
  getCacheStats: CacheStats!
  getPerformanceSummary: PerformanceSummary!
}

# ===========================================================================
# Mutations
# ===========================================================================

type Mutation {
  saveSearch(searchParams: JSON!, name: String!): SavedSearch!
  createInvestmentAlert(criteria: JSON!, userId: String!): InvestmentAlert!
  invalidateCache(countryCode: String): JSON!
  warmCache: JSON!
}

# ===========================================================================
# Subscriptions
# ===========================================================================

type Subscription {
  tariffUpdates(countries: [String!]): TariffUpdate!
  investmentAlerts(userId: ID!): InvestmentAlert!
  calculationProgress(operationId: ID!): CalculationProgress!
  liveRegionalData(bloc: RegionalBloc!): LiveRegionalMetrics!
}
'''
