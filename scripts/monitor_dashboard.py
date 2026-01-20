#!/usr/bin/env python3
"""
Magellan Multi-Strategy Monitoring Dashboard
Real-time monitoring for all 3 deployed strategies
"""

import sys
import time
import json
import boto3
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

sys.path.insert(0, '/home/ec2-user/magellan')

console = Console()

STRATEGIES = [
    {
        'name': 'Bear Trap',
        'account': 'PA3DDLQCBJSE',
        'config': '/home/ec2-user/magellan/deployable_strategies/bear_trap/aws_deployment/config.json',
        'service': 'magellan-bear-trap'
    },
    {
        'name': 'Daily Trend',
        'account': 'REPLACE_WITH_ACCOUNT_ID',
        'config': '/home/ec2-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/config.json',
        'service': 'magellan-daily-trend'
    },
    {
        'name': 'Hourly Swing',
        'account': 'REPLACE_WITH_ACCOUNT_ID',
        'config': '/home/ec2-user/magellan/deployable_strategies/hourly_swing/aws_deployment/config.json',
        'service': 'magellan-hourly-swing'
    }
]

def get_service_status(service_name):
    """Check if systemd service is running"""
    import subprocess
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def get_alpaca_account_info(account_id):
    """Fetch account info from Alpaca API"""
    try:
        ssm = boto3.client('ssm', region_name='us-east-2')
        api_key_path = f'/magellan/alpaca/{account_id}/API_KEY'
        api_secret_path = f'/magellan/alpaca/{account_id}/API_SECRET'
        
        api_key = ssm.get_parameter(Name=api_key_path, WithDecryption=True)['Parameter']['Value']
        api_secret = ssm.get_parameter(Name=api_secret_path, WithDecryption=True)['Parameter']['Value']
        
        # TODO: Call Alpaca API to get account details
        # For now, return mock data
        return {
            'equity': 100000.00,
            'cash': 50000.00,
            'positions': 2,
            'pnl_today': 1250.50,
            'pnl_total': 5000.00
        }
    except Exception as e:
        return {
            'equity': 0,
            'cash': 0,
            'positions': 0,
            'pnl_today': 0,
            'pnl_total': 0,
            'error': str(e)
        }

def create_dashboard():
    """Create rich dashboard layout"""
    
    # Portfolio Summary Table
    portfolio_table = Table(title="📊 Portfolio Summary", show_header=True, header_style="bold magenta")
    portfolio_table.add_column("Strategy", style="cyan", width=20)
    portfolio_table.add_column("Account", style="white", width=15)
    portfolio_table.add_column("Status", justify="center", width=10)
    portfolio_table.add_column("Equity", justify="right", width=15)
    portfolio_table.add_column("Positions", justify="center", width=10)
    portfolio_table.add_column("P&L Today", justify="right", width=15)
    portfolio_table.add_column("P&L Total", justify="right", width=15)
    
    total_equity = 0
    total_pnl_today = 0
    total_pnl_total = 0
    
    for strategy in STRATEGIES:
        # Get service status
        is_running = get_service_status(strategy['service'])
        status_icon = "🟢" if is_running else "🔴"
        
        # Get account info
        account_info = get_alpaca_account_info(strategy['account'])
        
        # Add row
        portfolio_table.add_row(
            strategy['name'],
            strategy['account'],
            status_icon,
            f"${account_info['equity']:,.2f}",
            str(account_info['positions']),
            f"${account_info['pnl_today']:,.2f}",
            f"${account_info['pnl_total']:,.2f}"
        )
        
        total_equity += account_info['equity']
        total_pnl_today += account_info['pnl_today']
        total_pnl_total += account_info['pnl_total']
    
    # Add totals row
    portfolio_table.add_row(
        "[bold]TOTAL[/bold]",
        "-",
        "-",
        f"[bold]${total_equity:,.2f}[/bold]",
        "-",
        f"[bold]${total_pnl_today:,.2f}[/bold]",
        f"[bold]${total_pnl_total:,.2f}[/bold]",
        style="bold yellow"
    )
    
    # System Health Table
    health_table = Table(title="🏥 System Health", show_header=True, header_style="bold green")
    health_table.add_column("Component", style="cyan", width=25)
    health_table.add_column("Status", justify="center", width=15)
    health_table.add_column("Details", width=40)
    
    # Check each service
    for strategy in STRATEGIES:
        is_running = get_service_status(strategy['service'])
        health_table.add_row(
            strategy['service'],
            "🟢 Running" if is_running else "🔴 Stopped",
            "Active" if is_running else "Service not running"
        )
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(Panel(portfolio_table, border_style="blue"), name="portfolio"),
        Layout(Panel(health_table, border_style="green"), name="health")
    )
    
    return layout

def main():
    """Main monitoring loop"""
    console.clear()
    console.print("[bold cyan]Magellan Multi-Strategy Monitor[/bold cyan]", justify="center")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n", justify="center")
    
    try:
        with Live(create_dashboard(), refresh_per_second=1, screen=False) as live:
            while True:
                live.update(create_dashboard())
                time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")

if __name__ == '__main__':
    main()
