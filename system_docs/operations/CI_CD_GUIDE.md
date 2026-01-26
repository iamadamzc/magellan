# Magellan CI/CD Pipeline

## Overview

This document describes the automated CI/CD pipeline for deploying trading strategies to AWS EC2 production environment.

## Pipeline Architecture

```
┌─────────────────┐
│  Push to GitHub │
│   (main/deploy) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              STAGE 1: Code Validation                    │
│  • Lint code (black, pylint)                            │
│  • Validate JSON configs                                │
│  • Run unit tests                                       │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│         STAGE 2: Test with Archived Data                │
│  • Run backtests using cached/archived data             │
│  • Validate strategy logic without live API calls       │
│  • Ensure strategies meet minimum performance criteria  │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           STAGE 3: Deploy to AWS EC2                    │
│  • Package deployment files                             │
│  • Upload to S3 (versioned)                             │
│  • Pull latest code on EC2 via git                      │
│  • Restart systemd services                             │
│  • Verify services are active                           │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│        STAGE 4: Post-Deployment Health Check            │
│  • Wait for services to stabilize (30s)                 │
│  • Check all services are active                        │
│  • Verify log files are being written                   │
│  • Create deployment summary                            │
└─────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Separation of Testing and Production**

**Testing (Stages 1-2):**
- Uses `USE_ARCHIVED_DATA=true` environment variable
- Strategies load data from cache/archived files
- No live API calls during testing
- Fast, repeatable, deterministic

**Production (Stages 3-4):**
- Strategies use live Alpaca API with SIP feed
- Real-time market data
- Actual trading decisions (paper trading)

### 2. **Automated Validation**

Before any code reaches production:
- ✅ Code linting (formatting, style)
- ✅ Configuration validation (JSON structure, required fields)
- ✅ Unit tests
- ✅ Backtests with archived data
- ✅ Performance criteria checks

### 3. **Safe Deployment**

- Atomic git pull on EC2 (no partial updates)
- Graceful service restarts
- Health checks after deployment
- Rollback capability (git reset)

### 4. **Visibility**

- Deployment summaries in GitHub Actions UI
- Service status verification
- Log file monitoring
- Artifact retention (backtest results for 30 days)

## Setup Instructions

### 1. GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_ACCESS_KEY_ID          # AWS credentials for magellan_deployer user
AWS_SECRET_ACCESS_KEY      # AWS secret key
ALPACA_TEST_API_KEY        # Alpaca paper trading API key (for testing)
ALPACA_TEST_API_SECRET     # Alpaca paper trading secret (for testing)
```

### 2. AWS IAM Permissions

The `magellan_deployer` IAM user needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:SendCommand",
        "ssm:GetCommandInvocation",
        "ssm:ListCommandInvocations",
        "ssm:DescribeInstanceInformation"
      ],
      "Resource": [
        "arn:aws:ec2:us-east-2:*:instance/i-0cd785630b55dd9a2",
        "arn:aws:ssm:us-east-2:*:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::magellan-deployments/*"
    }
  ]
}
```

### 3. EC2 Instance Setup

The EC2 instance needs:
- ✅ SSM Agent installed and running
- ✅ Git configured with repository access
- ✅ Python virtual environment at `/home/ssm-user/magellan/.venv`
- ✅ Systemd services configured
- ✅ Proper IAM role for SSM

### 4. Repository Structure

Required files:
```
.github/workflows/deploy-strategies.yml  # Main CI/CD workflow
scripts/validate_configs.py              # Config validator
scripts/run_backtest.py                  # Backtest runner
requirements.txt                         # Python dependencies
tests/                                   # Unit tests
deployable_strategies/     # Golden Strategy Code
  ├── bear_trap/
  │   └── runner.py
  ├── daily_trend/
  └── hourly_swing/
deployed/                  # Live Configurations
  ├── bear_trap/
  │   ├── config.json
  │   └── magellan-bear-trap.service

```

## Usage

### Automatic Deployment

Push to protected branches triggers automatic deployment:

```bash
# Deploy to production
git checkout deployment/aws-paper-trading-setup
git add deployable_strategies/ deployed/
git commit -m "Update Bear Trap config"
git push origin deployment/aws-paper-trading-setup
```

The pipeline will:
1. Validate code
2. Run tests with archived data
3. Deploy to EC2 if tests pass
4. Verify deployment health

### Manual Deployment

Trigger deployment manually via GitHub Actions UI:

1. Go to Actions → Deploy Trading Strategies
2. Click "Run workflow"
3. Select:
   - Branch: `deployment/aws-paper-trading-setup`
   - Strategy: `all` or specific strategy
   - Environment: `production`
4. Click "Run workflow"

### Monitoring Deployment

View deployment progress:
1. Go to Actions tab in GitHub
2. Click on the running workflow
3. Expand each job to see detailed logs

## Handling Failures

### Test Failures

If tests fail in Stage 1 or 2:
- ❌ Deployment is blocked
- Fix the issues locally
- Push the fix
- Pipeline re-runs automatically

### Deployment Failures

If deployment fails in Stage 3:
- EC2 instance state is unchanged (git pull failed)
- Check GitHub Actions logs for error
- Fix and re-deploy

### Service Failures

If services fail to start in Stage 4:
- SSH into EC2 to investigate:
  ```bash
  aws ssm start-session --target i-0cd785630b55dd9a2
  sudo journalctl -u magellan-bear-trap -n 50
  ```
- Fix the issue
- Manually restart services or re-deploy

## Rollback Procedure

If a deployment causes issues:

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2

# Rollback to previous commit
cd /home/ssm-user/magellan
git log --oneline -n 5  # Find previous good commit
git reset --hard <commit-hash>

# Restart services
sudo systemctl restart magellan-bear-trap
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing
```

## Best Practices

### 1. **Test Locally First**

Before pushing:
```bash
# Validate configs
python scripts/validate_configs.py

# Run backtest
python scripts/run_backtest.py \
  --strategy bear_trap \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --use-cache
```

### 2. **Use Feature Branches**

```bash
git checkout -b feature/update-bear-trap-symbols
# Make changes
git commit -m "Add new symbols to Bear Trap"
git push origin feature/update-bear-trap-symbols
# Create PR, review, then merge to deployment branch
```

### 3. **Monitor After Deployment**

After successful deployment:
- Check logs for first 5-10 minutes
- Verify decision logs are being written
- Confirm no errors in systemd logs

### 4. **Gradual Rollout**

For major changes:
1. Deploy to one strategy first
2. Monitor for 1 hour
3. If stable, deploy to remaining strategies

## Environment Variables

### Testing Environment

```bash
USE_ARCHIVED_DATA=true       # Use cached data instead of live API
ALPACA_API_KEY=<test_key>    # Paper trading credentials
ALPACA_API_SECRET=<test_secret>
```

### Production Environment

```bash
# No USE_ARCHIVED_DATA variable
# Credentials from AWS SSM Parameter Store:
# /magellan/alpaca/{account_id}/API_KEY
# /magellan/alpaca/{account_id}/API_SECRET
```

## Troubleshooting

### "Config validation failed"
- Check JSON syntax in config files
- Ensure all required fields are present
- Run `python scripts/validate_configs.py` locally

### "Backtest failed"
- Check if archived data exists for test period
- Verify strategy logic doesn't have errors
- Review test logs in GitHub Actions artifacts

### "SSM command timeout"
- EC2 instance may be unresponsive
- Check EC2 instance status in AWS Console
- Verify SSM Agent is running

### "Service failed to start"
- Check systemd service logs on EC2
- Verify Python dependencies are installed
- Check for syntax errors in strategy code

## Future Enhancements

- [ ] Add staging environment for pre-production testing
- [ ] Implement blue-green deployments
- [ ] Add Slack/Discord notifications
- [ ] Automated performance regression detection
- [ ] Integration with monitoring dashboard
- [ ] Automated rollback on service failures
- [ ] Multi-region deployment support

## Support

For issues with CI/CD pipeline:
1. Check GitHub Actions logs
2. Review this documentation
3. Check EC2 systemd logs
4. Consult `PRODUCTION_STATUS_2026-01-20.md` for infrastructure details
