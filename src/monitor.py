"""
Magellan Live Monitor Dashboard
Real-time monitoring of account health, positions, and trade history.
Provides "Eyes on the Market" for the live trading session.
"""

import os
import time
from datetime import datetime
from typing import Optional
from alpaca_trade_api.rest import REST
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.text import Text


class MagellanMonitor:
    """Real-time dashboard for monitoring Magellan's live trading session."""

    def __init__(self, refresh_interval: int = 30):
        """
        Initialize the Magellan Monitor.

        Args:
            refresh_interval: Seconds between API polling (default: 30)
        """
        self.refresh_interval = refresh_interval
        self.api = REST(base_url="https://paper-api.alpaca.markets")
        self.console = Console()
        self.last_update = None

        # Verify connection
        try:
            account = self.api.get_account()
            self.console.print(f"[green]✓[/green] Connected to Alpaca Paper Trading (Account: {account.status})")
        except Exception as e:
            self.console.print(f"[red]✗[/red] Failed to connect to Alpaca: {e}")
            raise

    def _fetch_account_health(self) -> dict:
        """Fetch current account health metrics."""
        try:
            account = self.api.get_account()
            return {
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "pdt_status": "YES" if account.pattern_day_trader else "NO",
                "daytrade_count": int(account.daytrade_count) if hasattr(account, "daytrade_count") else 0,
                "status": account.status,
            }
        except Exception as e:
            return {"error": str(e)}

    def _fetch_positions(self) -> list:
        """Fetch current open positions."""
        try:
            positions = self.api.list_positions()
            result = []
            for pos in positions:
                result.append(
                    {
                        "symbol": pos.symbol,
                        "qty": int(pos.qty),
                        "avg_entry": float(pos.avg_entry_price),
                        "current_price": float(pos.current_price),
                        "unrealized_pl": float(pos.unrealized_pl),
                        "unrealized_plpc": float(pos.unrealized_plpc) * 100,  # Convert to percentage
                    }
                )
            return result
        except Exception as e:
            return [{"error": str(e)}]

    def _read_trade_history(self, num_lines: int = 5) -> list:
        """Read last N lines from live_trades.log."""
        log_file = "live_trades.log"

        if not os.path.exists(log_file):
            return ["No trade history yet"]

        try:
            with open(log_file, "r") as f:
                lines = f.readlines()

            # Get last N lines, reverse so most recent is first
            recent_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
            recent_lines.reverse()

            # Clean up lines (remove newlines)
            return [line.strip() for line in recent_lines if line.strip()]
        except Exception as e:
            return [f"Error reading log: {e}"]

    def _build_account_health_table(self, health: dict) -> Table:
        """Build account health display table."""
        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value", justify="right")

        if "error" in health:
            table.add_row("ERROR", f"[red]{health['error']}[/red]")
        else:
            # Equity with color coding
            equity_color = "green" if health["equity"] >= 25000 else "yellow"
            table.add_row("Equity", f"[{equity_color}]${health['equity']:,.2f}[/{equity_color}]")

            # Buying Power
            table.add_row("Buying Power", f"${health['buying_power']:,.2f}")

            # Cash
            table.add_row("Cash", f"${health['cash']:,.2f}")

            # PDT Status (highlight if flagged)
            pdt_color = "red" if health["pdt_status"] == "YES" else "green"
            table.add_row("PDT Flagged", f"[{pdt_color}]{health['pdt_status']}[/{pdt_color}]")

            # Day Trade Count
            table.add_row("Day Trades (5d)", f"{health['daytrade_count']}")

            # Account Status
            status_color = "green" if health["status"] == "ACTIVE" else "yellow"
            table.add_row("Account Status", f"[{status_color}]{health['status']}[/{status_color}]")

        return table

    def _build_positions_table(self, positions: list) -> Table:
        """Build active positions display table."""
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Symbol", width=8)
        table.add_column("Shares", justify="right", width=10)
        table.add_column("Entry Price", justify="right", width=12)
        table.add_column("Current Price", justify="right", width=12)
        table.add_column("Unrealized P&L", justify="right", width=20)

        if not positions:
            table.add_row("—", "—", "—", "—", "No Positions")
        elif "error" in positions[0]:
            table.add_row("ERROR", "—", "—", "—", f"[red]{positions[0]['error']}[/red]")
        else:
            for pos in positions:
                # Color code P&L
                pl_color = "green" if pos["unrealized_pl"] >= 0 else "red"
                pl_text = f"[{pl_color}]${pos['unrealized_pl']:+,.2f} ({pos['unrealized_plpc']:+.2f}%)[/{pl_color}]"

                table.add_row(
                    pos["symbol"],
                    f"{pos['qty']:,}",
                    f"${pos['avg_entry']:.2f}",
                    f"${pos['current_price']:.2f}",
                    pl_text,
                )

        return table

    def _build_trade_history_panel(self, history: list) -> Panel:
        """Build trade history display panel."""
        history_text = "\n".join(history) if history else "No trades yet"
        return Panel(
            Text(history_text, style="dim"),
            title="[bold yellow]Last 5 Trades[/bold yellow]",
            border_style="yellow",
            expand=True,
        )

    def _build_heartbeat_panel(self) -> Panel:
        """Build heartbeat indicator panel."""
        if self.last_update is None:
            status_text = "[yellow]Initializing...[/yellow]"
        else:
            elapsed = time.time() - self.last_update

            if elapsed < 60:
                status_text = f"[green]Last Update: {int(elapsed)}s ago ✓[/green]"
            else:
                status_text = f"[red]Last Update: {int(elapsed)}s ago ⚠ STALE[/red]"

        return Panel(
            Text(status_text, justify="center"),
            title="[bold green]System Heartbeat[/bold green]",
            border_style="green",
            expand=True,
        )

    def _build_emergency_panel(self) -> Panel:
        """Build emergency kill-switch instructions panel."""
        emergency_text = Text()
        emergency_text.append("Emergency Liquidation Command:\n", style="bold red")
        emergency_text.append("python src/executor.py --action liquid-all", style="bold white on red")

        return Panel(
            emergency_text,
            title="[bold red blink]⚠ EMERGENCY KILL-SWITCH ⚠[/bold red blink]",
            border_style="red",
            expand=True,
        )

    def _build_dashboard(self) -> Layout:
        """Build complete dashboard layout."""
        # Fetch live data
        health = self._fetch_account_health()
        positions = self._fetch_positions()
        history = self._read_trade_history()

        # Update last update timestamp
        self.last_update = time.time()

        # Build components
        health_table = self._build_account_health_table(health)
        positions_table = self._build_positions_table(positions)
        history_panel = self._build_trade_history_panel(history)
        heartbeat_panel = self._build_heartbeat_panel()
        emergency_panel = self._build_emergency_panel()

        # Create layout
        layout = Layout()

        # Header
        header_text = Text()
        header_text.append("🚀 MAGELLAN LIVE MONITOR 🚀", style="bold white on blue")
        header_text.append(f"\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", style="dim")
        header = Panel(header_text, style="bold blue")

        # Organize layout
        layout.split_column(
            Layout(header, size=4, name="header"),
            Layout(name="main"),
            Layout(emergency_panel, size=4, name="emergency"),
        )

        # Split main area into left and right
        layout["main"].split_row(Layout(name="left"), Layout(name="right"))

        # Left side: Account Health + Positions
        layout["left"].split_column(
            Layout(
                Panel(health_table, title="[bold cyan]Account Health[/bold cyan]", border_style="cyan"), name="health"
            ),
            Layout(
                Panel(positions_table, title="[bold magenta]Active Positions[/bold magenta]", border_style="magenta"),
                name="positions",
            ),
        )

        # Right side: Heartbeat + Trade History
        layout["right"].split_column(
            Layout(heartbeat_panel, size=4, name="heartbeat"), Layout(history_panel, name="history")
        )

        return layout

    def run(self):
        """Run the live monitoring dashboard."""
        self.console.print("\n[bold green]Starting Magellan Live Monitor...[/bold green]")
        self.console.print(f"Refresh interval: {self.refresh_interval} seconds")
        self.console.print("Press [bold red]Ctrl+C[/bold red] to exit\n")

        try:
            with Live(self._build_dashboard(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(self.refresh_interval)
                    live.update(self._build_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Monitor stopped by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n\n[red]Monitor error: {e}[/red]")
            raise


def main():
    """Entry point for the monitor dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Magellan Live Monitor Dashboard")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds (default: 30)")

    args = parser.parse_args()

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Verify required environment variables
    if not os.getenv("APCA_API_KEY_ID") or not os.getenv("APCA_API_SECRET_KEY"):
        print("[ERROR] Missing Alpaca API credentials in environment variables")
        print("Please ensure APCA_API_KEY_ID and APCA_API_SECRET_KEY are set in .env file")
        return 1

    # Run monitor
    monitor = MagellanMonitor(refresh_interval=args.interval)
    monitor.run()

    return 0


if __name__ == "__main__":
    exit(main())
