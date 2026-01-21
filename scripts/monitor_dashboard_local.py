#!/usr/bin/env python3
"""
Magellan Local Monitoring Dashboard
Runs on your local machine, fetches data from Alpaca API
"""

import os
import sys
import time
import boto3
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from alpaca.trading.client import TradingClient

console = Console()

# Strategy configurations
STRATEGIES = [
    {"name": "Bear Trap", "account_id": "PA3DDLQCBJSE", "symbols": ["MULN", "ONDS", "AMC", "NKLA", "WKHS"]},
    {
        "name": "Daily Trend",
        "account_id": "PA3A2699UCJM",
        "symbols": ["GOOGL", "GLD", "META", "AAPL", "QQQ", "SPY", "MSFT", "TSLA", "AMZN", "IWM"],
    },
    {"name": "Hourly Swing", "account_id": "PA3ASNTJV624", "symbols": ["TSLA", "NVDA"]},
]


def get_alpaca_credentials(account_id):
    """Retrieve credentials from AWS SSM"""
    try:
        ssm = boto3.client("ssm", region_name="us-east-2")
        api_key_path = f"/magellan/alpaca/{account_id}/API_KEY"
        api_secret_path = f"/magellan/alpaca/{account_id}/API_SECRET"

        api_key = ssm.get_parameter(Name=api_key_path, WithDecryption=True)["Parameter"]["Value"]
        api_secret = ssm.get_parameter(Name=api_secret_path, WithDecryption=True)["Parameter"]["Value"]

        return api_key, api_secret
    except Exception as e:
        console.print(f"[red]Error retrieving credentials for {account_id}: {e}[/red]")
        return None, None


def get_account_data(strategy):
    """Fetch account data from Alpaca"""
    try:
        api_key, api_secret = get_alpaca_credentials(strategy["account_id"])
        if not api_key:
            return None

        # Initialize Alpaca client
        client = TradingClient(api_key, api_secret, paper=True)

        # Get account info
        account = client.get_account()

        # Get positions
        positions = client.get_all_positions()

        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "positions_count": len(positions),
            "positions": positions,
            "pnl_today": float(account.equity) - float(account.last_equity) if hasattr(account, "last_equity") else 0,
            "status": account.status,
        }
    except Exception as e:
        console.print(f"[red]Error fetching data for {strategy['name']}: {e}[/red]")
        return None


def create_dashboard():
    """Create the monitoring dashboard"""

    # Main portfolio table
    portfolio_table = Table(title="📊 Magellan Portfolio Monitor", show_header=True, header_style="bold magenta")
    portfolio_table.add_column("Strategy", style="cyan", width=20)
    portfolio_table.add_column("Account", style="white", width=15)
    portfolio_table.add_column("Status", justify="center", width=10)
    portfolio_table.add_column("Equity", justify="right", width=15)
    portfolio_table.add_column("Cash", justify="right", width=15)
    portfolio_table.add_column("Positions", justify="center", width=10)
    portfolio_table.add_column("P&L Today", justify="right", width=15)

    total_equity = 0
    total_cash = 0
    total_positions = 0
    total_pnl = 0

    for strategy in STRATEGIES:
        data = get_account_data(strategy)

        if data:
            status_icon = "🟢" if data["status"] == "ACTIVE" else "🔴"
            pnl_color = "green" if data["pnl_today"] >= 0 else "red"

            portfolio_table.add_row(
                strategy["name"],
                strategy["account_id"],
                status_icon,
                f"${data['equity']:,.2f}",
                f"${data['cash']:,.2f}",
                str(data["positions_count"]),
                f"[{pnl_color}]${data['pnl_today']:+,.2f}[/{pnl_color}]",
            )

            total_equity += data["equity"]
            total_cash += data["cash"]
            total_positions += data["positions_count"]
            total_pnl += data["pnl_today"]
        else:
            portfolio_table.add_row(
                strategy["name"], strategy["account_id"], "❌", "ERROR", "ERROR", "-", "ERROR", style="dim"
            )

    # Add totals
    pnl_color = "green" if total_pnl >= 0 else "red"
    portfolio_table.add_row(
        "[bold]TOTAL[/bold]",
        "-",
        "-",
        f"[bold]${total_equity:,.2f}[/bold]",
        f"[bold]${total_cash:,.2f}[/bold]",
        f"[bold]{total_positions}[/bold]",
        f"[bold {pnl_color}]${total_pnl:+,.2f}[/bold {pnl_color}]",
        style="bold yellow",
    )

    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return Panel(portfolio_table, title=f"[bold cyan]Last Updated: {timestamp}[/bold cyan]", border_style="blue")


def main():
    """Main monitoring loop"""
    console.clear()
    console.print("[bold cyan]Magellan Local Monitor[/bold cyan]", justify="center")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n", justify="center")

    try:
        with Live(create_dashboard(), refresh_per_second=1, screen=False) as live:
            while True:
                live.update(create_dashboard())
                time.sleep(10)  # Update every 10 seconds
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


if __name__ == "__main__":
    main()
