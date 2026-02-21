# UN COMTRADE v1 API Integration

This document describes the integration with the UN COMTRADE v1 API for accessing international trade statistics.

## Overview

The UN COMTRADE (United Nations International Trade Statistics Database) v1 API provides access to comprehensive international trade data. The AfCFTA project integrates this API to retrieve bilateral trade data between African countries.

**API Base URL:** `https://comtradeapi.un.org/data/v1`

**Documentation:** https://uncomtrade.org/docs/

**Subscription:** Required - Learn more at https://uncomtrade.org/docs/subscriptions/

## Features

- ✅ Bilateral trade data retrieval
- ✅ Support for multiple trade classifications (HS, SITC, BEC, EBOPS)
- ✅ Annual and monthly frequency options
- ✅ Commodity-specific queries
- ✅ Automatic API key failover (primary/secondary)
- ✅ Rate limiting and quota management
- ✅ Metadata and live updates access

## Configuration

### Environment Variables

Set the following environment variables for API authentication:

```bash
# Primary API key (required)
COMTRADE_API_KEY=your_primary_key_here

# Secondary API key (optional, for automatic failover)
COMTRADE_API_KEY_SECONDARY=your_secondary_key_here
```

### API Key Management

The service automatically manages API keys:
- Uses primary key by default
- Switches to secondary key on rate limit or authentication failure
- Tracks daily API call quota (500 calls/day per key)
- Provides status information via `get_service_status()`

## Usage

### Python Service

```python
from services.comtrade_service import comtrade_service

# Get bilateral trade data
data = comtrade_service.get_bilateral_trade(
    reporter_code="404",  # Kenya (M49 code)
    partner_code="834",   # Tanzania (M49 code)
    period="2023",
    hs_code="080300"      # Optional: specific HS code (Bananas)
)

# Get data for all African countries
african_data = comtrade_service.get_african_trade_data(
    african_countries=["404", "288", "566"],  # Kenya, Ghana, Nigeria
    period="2023"
)

# Get metadata
metadata = comtrade_service.get_metadata(
    type_code="C",    # Commodities
    freq_code="A",    # Annual
    cl_code="HS"      # HS Classification
)

# Check service status
status = comtrade_service.get_service_status()
print(f"Calls remaining: {status['calls_remaining']}")
```

### REST API Endpoints

The service is exposed via FastAPI endpoints:

#### Get Latest Trade Data (Smart Selection)
```http
GET /api/trade-data/latest?reporter=KEN&partner=TZA&hs_code=080300
```

#### Get COMTRADE Data Directly
```http
GET /api/trade-data/comtrade/KEN/TZA?period=2023&hs_code=080300
```

#### Compare Data Sources
```http
GET /api/trade-data/compare-sources?countries=KEN,GHA,NGA
```

## API Parameters

### Trade Type Codes
- `C` - Commodities (goods)
- `S` - Services

### Frequency Codes
- `A` - Annual data
- `M` - Monthly data

### Classification Codes
- `HS` - Harmonized System (default)
- `H6` - HS 6-digit
- `H4` - HS 4-digit
- `H2` - HS 2-digit
- `SITC` - Standard International Trade Classification
- `BEC` - Broad Economic Categories
- `EBOPS` - Extended Balance of Payments Services

### Flow Codes
- `M` - Imports
- `X` - Exports
- `RX` - Re-exports
- `RM` - Re-imports

### Country Codes

The API uses M49 (UN Standard Country Codes). Common African countries:

| Country | M49 Code | ISO3 |
|---------|----------|------|
| Kenya   | 404      | KEN  |
| Ghana   | 288      | GHA  |
| Nigeria | 566      | NGA  |
| South Africa | 710 | ZAF  |
| Egypt   | 818      | EGY  |
| Tanzania | 834     | TZA  |

Full list: https://unstats.un.org/unsd/methodology/m49/

## Rate Limits

- **Calls per day:** 500 (per API key)
- **Records per call:** 100,000
- **Automatic throttling:** 0.2 seconds between calls
- **Failover:** Automatic switch to secondary key when primary limit reached

## Error Handling

The service handles common errors gracefully:

### 401 Unauthorized
- Invalid or expired API key
- Automatically switches to secondary key if available

### 429 Rate Limit Exceeded
- Daily quota reached
- Switches to secondary key if available
- Returns error if all keys exhausted

### 404 Not Found
- No data available for specified parameters
- Check period and country codes

### Network Errors
- Automatic retry with exponential backoff
- Logs error details for debugging

## Data Format

### Response Structure

```json
{
  "source": "UN_COMTRADE",
  "data": [
    {
      "reporterCode": "404",
      "partnerCode": "834",
      "period": "2023",
      "cmdCode": "080300",
      "flowCode": "M",
      "tradeValue": 1250000,
      "netWeight": 5000,
      "quantityName": "Weight in kilograms",
      "qty": 5000
    }
  ],
  "metadata": {
    "recordCount": 1,
    "lastUpdated": "2024-01-15"
  },
  "timestamp": "2024-02-02T16:48:00Z",
  "latest_period": "2023",
  "api_key_used": "primary"
}
```

## Automated Updates

The system automatically updates trade data via GitHub Actions:

**Workflow:** `.github/workflows/auto_update_data.yml`

**Schedule:** Daily at 2:00 AM UTC

**Script:** `scripts/update_comtrade_data.py`

The workflow:
1. Fetches latest data for all 54 African countries
2. Stores data in MongoDB (if configured)
3. Compares data freshness across sources
4. Commits updated data files to the repository

## Testing

Run the test suite:

```bash
cd /home/runner/work/afcfta-final-001/afcfta-final-001
python3 -m pytest backend/tests/test_comtrade_service.py -v
```

Test coverage:
- ✅ Service initialization
- ✅ Bilateral trade data retrieval
- ✅ HS code filtering
- ✅ API error handling
- ✅ Rate limit enforcement
- ✅ Multiple country fetching
- ✅ Latest period detection

## Migration from Old API

### Changes from Comtrade Plus to v1 API

| Aspect | Old API | New v1 API |
|--------|---------|------------|
| Base URL | `comtradeplus.un.org` | `comtradeapi.un.org` |
| Endpoint | `/api/get` | `/get/{type}/{freq}/{class}` |
| Auth Method | Query parameter | Header (Ocp-Apim-Subscription-Key) |
| Country Codes | ISO3 | M49 |
| World Partner | `wld` | `0` |

### Code Changes Required

```python
# Old API
data = comtrade_service.get_bilateral_trade("KEN", "TZA", "2023")

# New v1 API (backward compatible)
data = comtrade_service.get_bilateral_trade("404", "834", "2023")
```

The service maintains backward compatibility where possible, but M49 codes are now preferred.

## OpenAPI Specification

The complete OpenAPI 3.0.1 specification is available at:
- `docs/comtrade_openapi.yaml`
- Official: https://comtradeapi.un.org/data/v1/openapi.json

## Troubleshooting

### No API Key Configured

**Symptom:** Warning message "⚠️ No COMTRADE API keys configured"

**Solution:** Set `COMTRADE_API_KEY` environment variable

### Authentication Failure

**Symptom:** 401 Unauthorized errors

**Solution:** 
1. Verify API key is valid and active
2. Check subscription status at https://uncomtrade.org/
3. Ensure key has proper permissions

### No Data Returned

**Symptom:** Empty data array in response

**Solution:**
1. Check if data exists for the specified period
2. Verify country codes are correct M49 codes
3. Try different periods (some countries lag in reporting)

### Rate Limit Reached

**Symptom:** 429 errors or "daily limit reached" message

**Solution:**
1. Configure secondary API key for automatic failover
2. Reduce call frequency
3. Wait until next day for quota reset
4. Consider upgrading subscription for higher limits

## Best Practices

1. **Use M49 codes:** Always use M49 country codes, not ISO3
2. **Enable secondary key:** Configure a second key for high-availability
3. **Monitor quota:** Check `get_service_status()` regularly
4. **Cache results:** Store frequently accessed data to reduce API calls
5. **Handle errors:** Always check for None returns and handle gracefully
6. **Rate limit:** Add delays between bulk requests
7. **Test queries:** Start with single country queries before bulk operations

## Related Documentation

- [AUTO_UPDATE_DATA.md](AUTO_UPDATE_DATA.md) - Automated data update system
- [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) - Data architecture overview
- [Official UN COMTRADE Docs](https://uncomtrade.org/docs/)

## Support

For issues or questions:
- Check logs in GitHub Actions workflow runs
- Review test cases in `backend/tests/test_comtrade_service.py`
- Consult official UN COMTRADE documentation
- Open an issue on GitHub

## API Status

Check API status and availability:
- Service health: `/api/health/status`
- Live updates: `comtrade_service.get_live_update()`
- Official status: https://uncomtrade.org/status/
