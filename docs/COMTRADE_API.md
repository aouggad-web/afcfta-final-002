# UN Comtrade API Integration Guide

This document provides comprehensive information on integrating with the UN Comtrade API, including configuration, testing, and troubleshooting.

## Overview

The UN Comtrade API provides access to international trade statistics. This integration supports:

- **Primary and Secondary API Keys**: Automatic fallback to secondary key if primary fails
- **Rate Limiting**: 500 calls per day per key (free tier)
- **Automatic Retry Logic**: Seamless switching between keys on errors
- **Health Monitoring**: Built-in health check endpoints

## Obtaining API Keys

### Step 1: Register for a Comtrade Account

1. Visit [UN Comtrade Plus](https://comtradeplus.un.org/)
2. Click on "Sign Up" or "Register"
3. Complete the registration form with your details
4. Verify your email address

### Step 2: Generate API Keys

1. Log in to your Comtrade account
2. Navigate to your account settings or API section
3. Click "Generate API Key" or similar option
4. Copy your API key and store it securely
5. **Optional**: Generate a second key for fallback (recommended for production)

### API Tiers

- **Free Tier**: 500 calls/day, 100K records per call
- **Premium Tier**: Higher limits (contact Comtrade for details)

## Configuration

### GitHub Repository Secrets

Configure your API keys as GitHub repository secrets:

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `COMTRADE_API_KEY` | Primary API key | Yes |
| `COMTRADE_API_KEY_SECONDARY` | Secondary fallback API key | Recommended |

### Local Development

For local testing, create a `.env` file in the `backend` directory:

```bash
# backend/.env
COMTRADE_API_KEY=your_primary_key_here
COMTRADE_API_KEY_SECONDARY=your_secondary_key_here
```

**Important**: Never commit your `.env` file to version control!

## Testing the API

### Automated Tests

The repository includes a GitHub Actions workflow that automatically tests your API configuration:

```bash
# The workflow runs automatically on:
# - Push to main branch (when comtrade files change)
# - Manual trigger via workflow_dispatch
```

To manually trigger the test workflow:

1. Go to **Actions** tab in GitHub
2. Select "Test Comtrade API" workflow
3. Click "Run workflow"

### Local Testing

Test your API keys locally:

```bash
cd backend
python -c "
import sys
sys.path.insert(0, '.')
from services.comtrade_service import comtrade_service

# Test health check
health = comtrade_service.health_check()
print(f'Status: {health}')

# Get service status
status = comtrade_service.get_service_status()
print(f'Service Status: {status}')
"
```

### Health Check Endpoint

Once the server is running, you can check API health via HTTP:

```bash
curl http://localhost:8000/api/comtrade/health
```

Expected response:

```json
{
  "status": "operational",
  "using_key": "primary",
  "api_calls_today": 15,
  "rate_limit_remaining": 485,
  "last_error": null,
  "primary_key_configured": true,
  "secondary_key_configured": true,
  "timestamp": "2026-02-02T14:00:00.000Z"
}
```

## How Fallback Logic Works

### Automatic Key Switching

The service automatically switches to the secondary key when:

1. **Rate Limit Exceeded (HTTP 429)**: Primary key has reached daily limit
2. **Authentication Failed (HTTP 401)**: Primary key is invalid or expired
3. **Daily Limit Reached**: Internal counter reaches 500 calls

### Switching Process

```
Primary Key Request
     ↓
   [Error?]
     ↓ Yes
Check Secondary Available?
     ↓ Yes
Switch to Secondary Key
     ↓
Retry Request
```

### Example Code

```python
from services.comtrade_service import comtrade_service

# Get trade data - automatic fallback if primary fails
data = comtrade_service.get_bilateral_trade(
    reporter_code="KEN",
    partner_code="TZA", 
    period="2024"
)

if data:
    print(f"Data retrieved using: {data['api_key_used']} key")
```

## Rate Limits and Best Practices

### Rate Limits

- **Free Tier**: 500 calls per day per API key
- **Records per Call**: Up to 100,000 records
- **Timeout**: 30 seconds per request

### Best Practices

1. **Use Secondary Key**: Always configure a secondary key for production
2. **Rate Limiting**: Add delays between requests (0.2s recommended)
3. **Error Handling**: Always check for `None` return values
4. **Monitoring**: Regularly check health endpoint and logs
5. **Efficient Queries**: Request only the data you need

### Daily Update Strategy

For daily automated updates:

```python
# Request data for multiple countries efficiently
results = comtrade_service.get_african_trade_data(
    african_countries=["KEN", "GHA", "NGA"],
    period="2024"
)
```

The service automatically:
- Tracks calls per day
- Switches to secondary key when needed
- Adds delays between requests
- Stops when both keys reach limit

## Troubleshooting

### Common Issues

#### 1. "No COMTRADE API keys configured"

**Cause**: Environment variables not set

**Solution**:
- Ensure secrets are configured in GitHub (for Actions)
- Create `.env` file locally with keys
- Check spelling of environment variable names

#### 2. "Authentication failed with primary key"

**Cause**: Invalid or expired API key

**Solution**:
- Verify your API key is correct
- Check if key has been revoked
- Generate a new key from Comtrade portal
- Update the secret in GitHub

#### 3. "Rate limit exceeded on all keys"

**Cause**: Both keys reached 500 calls/day

**Solution**:
- Wait until next day (resets at midnight UTC)
- Consider premium tier for higher limits
- Optimize queries to use fewer calls

#### 4. Health check fails but keys are configured

**Cause**: Network issues or Comtrade API downtime

**Solution**:
- Check Comtrade API status
- Verify firewall/network settings
- Check server logs for detailed error messages

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from services.comtrade_service import comtrade_service

# Now all API calls will be logged
data = comtrade_service.get_bilateral_trade("KEN", "TZA", "2024")
```

### Checking Logs

View logs in GitHub Actions:

1. Go to **Actions** tab
2. Select the workflow run
3. Click on "Update UN COMTRADE Data" step
4. Review logs for:
   - Key being used
   - Number of calls made
   - Any errors or warnings

## Monitoring in Production

### Health Check Schedule

Set up monitoring to regularly check API health:

```yaml
# Example: Check every hour
schedule:
  - cron: '0 * * * *'

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check Comtrade Health
        run: curl https://your-api.com/api/comtrade/health
```

### Key Metrics to Monitor

1. **API Calls Per Day**: Should stay under 500 per key
2. **Success Rate**: Percentage of successful requests
3. **Active Key**: Which key is currently in use
4. **Error Rate**: Number of failed requests
5. **Last Error**: Most recent error message

### Alerts

Consider setting up alerts for:

- Both keys approaching rate limit (>450 calls)
- Authentication failures
- Extended periods of API unavailability
- Switch to secondary key (indicates primary issue)

## API Reference

### Service Methods

#### `health_check() -> Dict`

Checks API connectivity and returns status.

**Returns:**
```python
{
    "connected": bool,
    "using_secondary": bool,
    "calls_today": int,
    "rate_limit_remaining": int,
    "last_error": str or None,
    "primary_key_configured": bool,
    "secondary_key_configured": bool,
    "timestamp": str
}
```

#### `get_bilateral_trade(reporter_code, partner_code, period, hs_code=None) -> Dict`

Get trade data between two countries.

**Parameters:**
- `reporter_code` (str): ISO3 country code (e.g., "KEN")
- `partner_code` (str): ISO3 country code or "all"
- `period` (str): Year (YYYY) or month (YYYYMM)
- `hs_code` (str, optional): HS product code

**Returns:** Trade data dict or None on error

#### `get_service_status() -> Dict`

Get current service configuration and status.

**Returns:**
```python
{
    "primary_key_configured": bool,
    "secondary_key_configured": bool,
    "current_key": str,
    "calls_today": int,
    "calls_remaining": int,
    "can_switch_to_secondary": bool
}
```

### HTTP Endpoints

#### `GET /api/comtrade/health`

Health check endpoint.

**Response:** 200 OK
```json
{
  "status": "operational" | "error",
  "using_key": "primary" | "secondary",
  "api_calls_today": 15,
  "rate_limit_remaining": 485,
  "last_error": null,
  "primary_key_configured": true,
  "secondary_key_configured": true,
  "timestamp": "2026-02-02T14:00:00Z"
}
```

## Security Considerations

1. **Never commit API keys**: Always use environment variables or secrets
2. **Rotate keys regularly**: Generate new keys periodically
3. **Use HTTPS only**: Never send keys over unencrypted connections
4. **Restrict access**: Limit who can view/edit repository secrets
5. **Monitor usage**: Watch for unusual API call patterns

## Support

### Resources

- [UN Comtrade Plus Documentation](https://comtradeplus.un.org/docs/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- Repository Issues: Report problems via GitHub Issues

### Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review GitHub Actions logs
3. Check the health endpoint
4. Open an issue with:
   - Error message
   - Steps to reproduce
   - Relevant log output (without exposing keys)

## Changelog

### Version 2.0 (Current)
- Added secondary key support
- Implemented automatic fallback logic
- Added health check endpoint
- Enhanced error tracking
- Improved logging and monitoring

### Version 1.0
- Initial Comtrade API integration
- Basic trade data retrieval
- Rate limiting
