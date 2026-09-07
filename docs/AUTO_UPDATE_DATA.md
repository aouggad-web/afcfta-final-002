# Automated Data Update System

This document describes the automated data update system for the AfCFTA project.

## Overview

The system automatically updates data from external sources on a daily schedule and can also be triggered manually. It fetches fresh data from:

- World Bank API (economic indicators)
- Country profiles and statistics
- JSON data files (ports, airports, production data)

## Components

### 1. Data Update Script (`backend/update_data_automated.py`)

A Python script that:
- Fetches latest data from World Bank API
- Updates country economic profiles
- Refreshes JSON data files with timestamps
- Generates detailed update reports

**Usage:**

```bash
# Run manually
python backend/update_data_automated.py
```

**Features:**
- Graceful error handling
- Detailed logging
- Update reports in JSON format
- Rate limiting to respect API limits

### 2. GitHub Actions Workflow (`.github/workflows/auto_update_data.yml`)

An automated workflow that:
- Runs daily at 2:00 AM UTC
- Can be triggered manually from the Actions tab
- Commits and pushes data changes automatically
- Uploads update reports as artifacts

**Schedule:** Daily at 2:00 AM UTC (configurable via cron expression)

**Manual Trigger:**
1. Go to the repository's Actions tab
2. Select "Auto Update Data" workflow
3. Click "Run workflow"
4. Choose the update type (all, worldbank, production, trade)
5. Click "Run workflow"

## Files Generated

The update process generates/updates the following files:

- `worldbank_data_latest.json` - Latest World Bank data for all African countries
- `data_update_report.json` - Detailed log of the update process (gitignored)
- `ports_africains.json` - Updated with timestamps
- `airports_africains.json` - Updated with timestamps
- `production_africaine.json` - Updated with timestamps

## Data Sources

### World Bank API

Fetches the following indicators for all 54 African countries:

- **GDP (NY.GDP.MKTP.CD)**: GDP in current US$
- **GDP per capita (NY.GDP.PCAP.CD)**: GDP per capita in current US$
- **Population (SP.POP.TOTL)**: Total population
- **GDP growth (NY.GDP.MKTP.KD.ZG)**: Annual GDP growth rate

Data is fetched for years 2020-2024 (most recent 5 years).

## Workflow Details

### Automatic Execution

The workflow runs automatically every day at 2:00 AM UTC:

```yaml
schedule:
  - cron: '0 2 * * *'
```

### Manual Execution

You can manually trigger the workflow with different update types:

- **all**: Update all data sources (default)
- **worldbank**: Update only World Bank data
- **production**: Update only production data
- **trade**: Update only trade data

### Workflow Steps

1. **Checkout**: Checks out the repository
2. **Setup Python**: Installs Python 3.11 with pip caching
3. **Install Dependencies**: Installs required packages (requests, openpyxl, pandas)
4. **Run Update Script**: Executes the data update script
5. **Check Changes**: Detects if any data was modified
6. **Commit & Push**: Commits changes, pulls latest remote changes (with rebase), and pushes
7. **Generate Summary**: Creates a summary in the workflow output
8. **Upload Report**: Uploads the update report as an artifact (retained for 30 days)

**Note on Step 6**: The workflow uses `git pull --rebase` before pushing to prevent non-fast-forward errors when the remote branch has been updated by another workflow or manual commit. If conflicts occur on data files, the workflow automatically resolves them by preferring the new data (our changes).

## Error Handling

The system is designed to be resilient:

- **API Errors**: Network errors are logged but don't fail the workflow
- **Rate Limiting**: Built-in delays between API calls
- **Graceful Degradation**: If external APIs fail, local updates still proceed
- **Detailed Logging**: All actions are logged for debugging

## Monitoring

### View Update Reports

Update reports are available in two ways:

1. **Workflow Summary**: Each workflow run generates a summary visible in the Actions tab
2. **Artifacts**: Detailed JSON reports are uploaded and retained for 30 days

### Check Update Status

```bash
# View the latest update report
cat data_update_report.json
```

The report includes:
- Timestamp
- Status (completed/failed)
- Number of updates performed
- Warnings and errors
- Detailed log of all operations

## Configuration

### Change Update Frequency

Edit the cron schedule in `.github/workflows/auto_update_data.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2:00 AM UTC
```

Examples:
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Weekly on Mondays
- `0 0 1 * *` - Monthly on the 1st

### Add New Data Sources

To add new data sources, edit `backend/update_data_automated.py`:

1. Add a new method to the `DataUpdater` class
2. Call the method in the `main()` function
3. Update the documentation

Example:

```python
def update_trade_data(self):
    """Update trade statistics"""
    self.log("Updating trade data...")
    # Your implementation here
```

## Integration with Existing Workflows

This workflow complements the existing `lyra_plus_ops.yml` workflow:

- **lyra_plus_ops.yml**: Updates AfCFTA-specific datasets (tariffs, rules of origin) weekly
- **auto_update_data.yml**: Updates general economic data (World Bank, country profiles) daily

Both workflows work independently and can run concurrently.

## Troubleshooting

### Workflow Not Running

- Check that GitHub Actions is enabled in repository settings
- Verify the cron schedule syntax
- Ensure the workflow file is in `.github/workflows/`

### API Errors

- World Bank API might be temporarily unavailable
- Check API status at https://data.worldbank.org/
- Review the update report for specific error messages

### No Data Changes

This is normal if:
- World Bank hasn't released new data
- The data is the same as the previous update
- The workflow will still run but not commit anything

### Permission Errors

Ensure the workflow has write permissions:

```yaml
permissions:
  contents: write
```

### Git Push Rejection (Non-Fast-Forward)

**Problem:** The workflow fails with error:
```
! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs
```

**Cause:** The remote branch has changed since the workflow started (e.g., another workflow or manual push occurred).

**Solution:** The workflow now includes automatic conflict resolution:

1. **Pull and Rebase**: Before pushing, the workflow pulls the latest changes and rebases local commits on top
2. **Fallback to Merge**: If rebase fails (e.g., conflicts), it falls back to a merge strategy
3. **Retry Logic**: If push still fails, it retries up to 3 times with a 2-second delay between attempts

This ensures that the automated workflow can handle concurrent changes without manual intervention.

**Implementation details:**
```bash
# Pull and rebase before pushing
git pull --rebase origin main || {
  # If rebase fails, abort and try merge
  git rebase --abort 2>/dev/null || true
  git pull --no-rebase origin main
}

# Retry push up to 3 times
# (with pull between retries to handle new remote changes)
```

This same fix has been applied to both:
- `.github/workflows/auto_update_data.yml` (daily data updates)
- `.github/workflows/lyra_plus_ops.yml` (weekly Lyra+ dataset updates)
### Push Rejected (Non-Fast-Forward)

If you see errors like "rejected (non-fast-forward)" or "failed to push some refs":

**This has been fixed!** The workflows now automatically:
1. Pull the latest changes from the remote branch before pushing
2. Rebase local commits on top of remote changes
3. Handle merge conflicts automatically for data files
4. Retry the push after synchronizing

The fix ensures that multiple workflows or manual commits don't cause push failures.

## Best Practices

1. **Monitor the first few runs** to ensure everything works as expected
2. **Review update reports** periodically to catch any issues
3. **Don't modify data files manually** - let the automation handle it
4. **Keep dependencies updated** in the workflow file
5. **Test changes locally** before pushing workflow modifications

## Future Enhancements

Potential improvements:

- [ ] Add email notifications on failure
- [ ] Integrate FAOSTAT for agricultural data
- [ ] Add UNCTAD for trade data
- [ ] Implement data validation checks
- [ ] Add Slack/Discord webhook notifications
- [ ] Create a dashboard for monitoring updates
- [x] Add retry logic for failed API calls (✅ Implemented for git push)
- [ ] Implement incremental updates (only changed data)

## Related Documentation

- [LYRA_OPS_IMPLEMENTATION.md](../LYRA_OPS_IMPLEMENTATION.md) - Lyra+ Ops system
- [World Bank API Documentation](https://datahelpdesk.worldbank.org/knowledgebase/topics/125589)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the Actions tab for workflow logs
- Review `data_update_report.json` for detailed error information
