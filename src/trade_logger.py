"""
Magellan Trade Logger
Detailed logging of all trading decisions and executions
"""

import csv
import os
from datetime import datetime
from pathlib import Path
import json

class TradeLogger:
    """Logs all trading decisions with full context"""
    
    def __init__(self, strategy_name, log_dir="/home/ssm-user/magellan/logs"):
        self.strategy_name = strategy_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dated log files
        self.date_str = datetime.now().strftime("%Y%m%d")
        
        # Trade execution log
        self.trade_log_path = self.log_dir / f"{strategy_name}_trades_{self.date_str}.csv"
        self._init_trade_log()
        
        # Signal evaluation log
        self.signal_log_path = self.log_dir / f"{strategy_name}_signals_{self.date_str}.csv"
        self._init_signal_log()
        
        # Decision log (why we didn't trade)
        self.decision_log_path = self.log_dir / f"{strategy_name}_decisions_{self.date_str}.csv"
        self._init_decision_log()
        
    def _init_trade_log(self):
        """Initialize trade execution log"""
        if not self.trade_log_path.exists():
            with open(self.trade_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'symbol',
                    'action',  # ENTRY, EXIT, SCALE_OUT
                    'side',  # BUY, SELL
                    'quantity',
                    'price',
                    'order_id',
                    'position_size_before',
                    'position_size_after',
                    'entry_reason',
                    'exit_reason',
                    'pnl_dollars',
                    'pnl_percent',
                    'hold_time_minutes',
                    'market_conditions',
                    'indicators',
                    'risk_metrics'
                ])
    
    def _init_signal_log(self):
        """Initialize signal evaluation log"""
        if not self.signal_log_path.exists():
            with open(self.signal_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'symbol',
                    'signal_type',  # BUY, SELL, HOLD
                    'signal_strength',
                    'indicator_values',
                    'entry_criteria_met',
                    'exit_criteria_met',
                    'risk_gates_passed',
                    'action_taken',  # EXECUTED, SKIPPED, PENDING
                    'skip_reason'
                ])
    
    def _init_decision_log(self):
        """Initialize decision log (rejections)"""
        if not self.decision_log_path.exists():
            with open(self.decision_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'symbol',
                    'decision_type',  # SKIP_ENTRY, SKIP_EXIT, HOLD
                    'reason',
                    'details',
                    'current_price',
                    'indicator_values',
                    'risk_status'
                ])
    
    def log_trade(self, **kwargs):
        """
        Log a trade execution
        
        Args:
            timestamp: datetime
            symbol: str
            action: str (ENTRY, EXIT, SCALE_OUT)
            side: str (BUY, SELL)
            quantity: int
            price: float
            order_id: str
            position_size_before: int
            position_size_after: int
            entry_reason: str
            exit_reason: str
            pnl_dollars: float
            pnl_percent: float
            hold_time_minutes: int
            market_conditions: dict
            indicators: dict
            risk_metrics: dict
        """
        with open(self.trade_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                kwargs.get('timestamp', datetime.now()).isoformat(),
                kwargs.get('symbol'),
                kwargs.get('action'),
                kwargs.get('side'),
                kwargs.get('quantity'),
                kwargs.get('price'),
                kwargs.get('order_id'),
                kwargs.get('position_size_before', 0),
                kwargs.get('position_size_after', 0),
                kwargs.get('entry_reason', ''),
                kwargs.get('exit_reason', ''),
                kwargs.get('pnl_dollars', 0),
                kwargs.get('pnl_percent', 0),
                kwargs.get('hold_time_minutes', 0),
                json.dumps(kwargs.get('market_conditions', {})),
                json.dumps(kwargs.get('indicators', {})),
                json.dumps(kwargs.get('risk_metrics', {}))
            ])
    
    def log_signal(self, **kwargs):
        """
        Log a signal evaluation
        
        Args:
            timestamp: datetime
            symbol: str
            signal_type: str (BUY, SELL, HOLD)
            signal_strength: float
            indicator_values: dict
            entry_criteria_met: bool
            exit_criteria_met: bool
            risk_gates_passed: bool
            action_taken: str (EXECUTED, SKIPPED, PENDING)
            skip_reason: str
        """
        with open(self.signal_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                kwargs.get('timestamp', datetime.now()).isoformat(),
                kwargs.get('symbol'),
                kwargs.get('signal_type'),
                kwargs.get('signal_strength', 0),
                json.dumps(kwargs.get('indicator_values', {})),
                kwargs.get('entry_criteria_met', False),
                kwargs.get('exit_criteria_met', False),
                kwargs.get('risk_gates_passed', False),
                kwargs.get('action_taken'),
                kwargs.get('skip_reason', '')
            ])
    
    def log_decision(self, **kwargs):
        """
        Log a decision (especially rejections/skips)
        
        Args:
            timestamp: datetime
            symbol: str
            decision_type: str (SKIP_ENTRY, SKIP_EXIT, HOLD)
            reason: str
            details: str
            current_price: float
            indicator_values: dict
            risk_status: dict
        """
        with open(self.decision_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                kwargs.get('timestamp', datetime.now()).isoformat(),
                kwargs.get('symbol'),
                kwargs.get('decision_type'),
                kwargs.get('reason'),
                kwargs.get('details', ''),
                kwargs.get('current_price'),
                json.dumps(kwargs.get('indicator_values', {})),
                json.dumps(kwargs.get('risk_status', {}))
            ])
    
    def log_market_scan(self, symbol, scan_results):
        """Log market scan results"""
        self.log_decision(
            symbol=symbol,
            decision_type='MARKET_SCAN',
            reason='Periodic scan',
            details=json.dumps(scan_results),
            current_price=scan_results.get('price'),
            indicator_values=scan_results.get('indicators', {}),
            risk_status=scan_results.get('risk_status', {})
        )
    
    def log_risk_gate_failure(self, symbol, gate_name, gate_details):
        """Log when a risk gate prevents trading"""
        self.log_decision(
            symbol=symbol,
            decision_type='RISK_GATE_FAILURE',
            reason=f'Risk gate failed: {gate_name}',
            details=json.dumps(gate_details),
            risk_status={'gate': gate_name, 'details': gate_details}
        )
    
    def create_daily_summary(self):
        """Create end-of-day summary report"""
        summary_path = self.log_dir / f"{self.strategy_name}_summary_{self.date_str}.json"
        
        # Read trade log and create summary
        trades = []
        if self.trade_log_path.exists():
            with open(self.trade_log_path, 'r') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
        
        summary = {
            'date': self.date_str,
            'strategy': self.strategy_name,
            'total_trades': len(trades),
            'total_pnl': sum(float(t.get('pnl_dollars', 0)) for t in trades),
            'winning_trades': len([t for t in trades if float(t.get('pnl_dollars', 0)) > 0]),
            'losing_trades': len([t for t in trades if float(t.get('pnl_dollars', 0)) < 0]),
            'symbols_traded': list(set(t['symbol'] for t in trades)),
            'log_files': {
                'trades': str(self.trade_log_path),
                'signals': str(self.signal_log_path),
                'decisions': str(self.decision_log_path)
            }
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
