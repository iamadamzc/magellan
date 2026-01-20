#!/bin/bash
# Magellan AWS EC2 Deployment Script
# Run this on EC2 instance after connecting via SSM

set -e  # Exit on error

echo "========================================="
echo "Magellan AWS Deployment Script"
echo "========================================="
echo ""

# Navigate to project directory
cd /home/ec2-user/magellan

# Pull latest code
echo "1. Pulling latest code from GitHub..."
git fetch origin
git checkout deployment/aws-paper-trading-setup
git pull origin deployment/aws-paper-trading-setup
echo "✓ Code updated"
echo ""

# Verify files exist
echo "2. Verifying deployment files..."
ls -la deployable_strategies/bear_trap/aws_deployment/ | grep -E "(config.json|run_strategy.py|.service)"
ls -la deployable_strategies/daily_trend_hysteresis/aws_deployment/ | grep -E "(config.json|run_strategy.py|.service)"
ls -la deployable_strategies/hourly_swing/aws_deployment/ | grep -E "(config.json|run_strategy.py|.service)"
echo "✓ All files present"
echo ""

# Activate virtual environment and install dependencies
echo "3. Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install rich boto3 pytz --quiet
echo "✓ Dependencies installed"
echo ""

# Install systemd services
echo "4. Installing systemd services..."
sudo cp deployable_strategies/bear_trap/aws_deployment/magellan-bear-trap.service /etc/systemd/system/
sudo cp deployable_strategies/daily_trend_hysteresis/aws_deployment/magellan-daily-trend.service /etc/systemd/system/
sudo cp deployable_strategies/hourly_swing/aws_deployment/magellan-hourly-swing.service /etc/systemd/system/

sudo chmod 644 /etc/systemd/system/magellan-*.service
sudo systemctl daemon-reload
echo "✓ Services installed"
echo ""

# Enable services for auto-start
echo "5. Enabling services for auto-start..."
sudo systemctl enable magellan-bear-trap
sudo systemctl enable magellan-daily-trend
sudo systemctl enable magellan-hourly-swing
echo "✓ Services enabled"
echo ""

# Test SSM credential retrieval
echo "6. Testing AWS SSM credential retrieval..."
aws ssm get-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --with-decryption --region us-east-2 --query 'Parameter.Value' --output text > /dev/null
echo "✓ SSM credentials accessible"
echo ""

# Start services one by one
echo "7. Starting services..."
echo ""

echo "Starting Bear Trap..."
sudo systemctl start magellan-bear-trap
sleep 3
sudo systemctl status magellan-bear-trap --no-pager | head -15
echo ""

echo "Starting Daily Trend..."
sudo systemctl start magellan-daily-trend
sleep 3
sudo systemctl status magellan-daily-trend --no-pager | head -15
echo ""

echo "Starting Hourly Swing..."
sudo systemctl start magellan-hourly-swing
sleep 3
sudo systemctl status magellan-hourly-swing --no-pager | head -15
echo ""

# Final status check
echo "========================================="
echo "DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "All services status:"
sudo systemctl status magellan-* --no-pager | grep -E "(magellan-|Active:)"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u magellan-bear-trap -f"
echo "  sudo journalctl -u magellan-daily-trend -f"
echo "  sudo journalctl -u magellan-hourly-swing -f"
echo ""
echo "To view monitoring dashboard:"
echo "  cd /home/ec2-user/magellan"
echo "  source .venv/bin/activate"
echo "  python scripts/monitor_dashboard.py"
echo ""
