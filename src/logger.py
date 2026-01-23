"""
Optimized Logging System with Clear Signal-to-Noise Ratio

Provides three verbosity levels:
- QUIET (0): Only critical events (errors, warnings, trades)
- NORMAL (1): Major milestones and progress
- VERBOSE (2): Detailed step-by-step flow

All debug/backend details are redirected to debug_vault.log
"""

import os
import sys
from datetime import datetime
from typing import Optional


class SystemLogger:
    """
    Optimized logging with clear hierarchy and minimal noise.

    Philosophy:
    - Terminal should stay dark unless something important happens
    - Backend details belong in files, not terminal
    - Users care about: trades, errors, progress
    - Developers need: debug logs in files
    """

    # Verbosity levels
    QUIET = 0  # Only critical (errors, warnings, trades)
    NORMAL = 1  # + Major events (initialization, completion)
    VERBOSE = 2  # + Process flow (what's happening step-by-step)

    def __init__(self, verbosity: int = NORMAL):
        self.verbosity = verbosity
        self.debug_file_path = os.path.join(os.getcwd(), "debug_vault.log")

        # Initialize/Clear debug file
        with open(self.debug_file_path, "w") as f:
            f.write(f"=== Magellan Debug Log - {datetime.now().isoformat()} ===\n\n")

        # Track state changes for edge-triggered logging
        self.last_status = {}

    def set_verbosity(self, level: int):
        """Set verbosity level (0=quiet, 1=normal, 2=verbose)."""
        self.verbosity = level
        if level == self.QUIET:
            self.event("[LOG] Quiet mode enabled (critical events only)")
        elif level == self.VERBOSE:
            self.event("[LOG] Verbose mode enabled (detailed flow)")

    def _clean_ascii(self, text: str) -> str:
        """Ensure ASCII-only output."""
        return text.encode("ascii", "ignore").decode("ascii")

    def _timestamp(self) -> str:
        """Generate timestamp for debug logs."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # =========================================================================
    # TERMINAL OUTPUT (based on verbosity level)
    # =========================================================================

    def critical(self, message: str):
        """
        ALWAYS shown: Errors, warnings, trade execution.
        Verbosity level: 0+
        """
        print(self._clean_ascii(message))
        self._write_debug(f"[CRITICAL] {message}")

    def event(self, message: str):
        """
        Major milestones: Initialization, ticker completion, reports.
        Verbosity level: 1+ (NORMAL)
        """
        if self.verbosity >= self.NORMAL:
            print(self._clean_ascii(message))
        self._write_debug(f"[EVENT] {message}")

    def flow(self, message: str):
        """
        Process flow: Step-by-step progress updates.
        Verbosity level: 2+ (VERBOSE)
        """
        if self.verbosity >= self.VERBOSE:
            print(self._clean_ascii(message))
        self._write_debug(f"[FLOW] {message}")

    def debug(self, message: str):
        """
        Backend details: API calls, data transformations, internals.
        NEVER shown in terminal, always written to debug_vault.log
        """
        self._write_debug(f"[DEBUG] {message}")

    # =========================================================================
    # BACKWARDS COMPATIBILITY ALIASES (for gradual migration)
    # =========================================================================

    def info(self, message: str):
        """Alias: Maps to flow() for backwards compat."""
        self.flow(message)

    def warning(self, message: str):
        """Alias: Maps to critical()."""
        self.critical(f"⚠️  {message}")

    def error(self, message: str):
        """Alias: Maps to critical()."""
        self.critical(f"❌ {message}")

    def success(self, message: str):
        """Alias: Maps to event()."""
        self.event(f"✓ {message}")

    def system(self, message: str):
        """Alias: Maps to event()."""
        self.event(message)

    def stats(self, message: str):
        """Alias: Maps to critical() (trade stats are important)."""
        self.critical(message)

    def config(self, message: str):
        """Alias: Maps to debug() (config details are backend noise)."""
        self.debug(message)

    def metric(self, message: str):
        """Alias: Maps to debug()."""
        self.debug(message)

    def ic_matrix(self, message: str):
        """Alias: Maps to debug()."""
        self.debug(message)

    def ensemble(self, message: str):
        """Alias: Maps to event()."""
        self.event(message)

    def phase_lock(self, message: str):
        """
        Edge-triggered logging for signal state changes.
        Only logs when status actually changes (prevents spam).
        """
        try:
            # Parse ticker and status
            parts = message.split("|")
            ticker_part = [p for p in parts if "Ticker:" in p]
            status_part = [p for p in parts if "Status:" in p]

            if ticker_part and status_part:
                ticker = ticker_part[0].split(":")[1].strip()
                status = status_part[0].split(":")[1].strip()

                last_state = self.last_status.get(ticker)

                # Only log if status changed
                if status != last_state:
                    self.last_status[ticker] = status
                    self.critical(message)  # Status changes are critical
                else:
                    self.debug(f"[PHASE_LOCK] {ticker} status unchanged: {status}")
            else:
                # Fallback: Only log BUY/SELL
                if "Status: BUY" in message or "Status: SELL" in message:
                    self.critical(message)
                else:
                    self.debug(message)
        except Exception as e:
            self.debug(f"[PHASE_LOCK] Parse error: {e}")
            # Safety: Log BUY/SELL signals
            if "Status: BUY" in message or "Status: SELL" in message:
                self.critical(message)

    def cryogen(self, message: str):
        """Edge-triggered logging for VSS (cryogen) signals."""
        try:
            ticker = "VSS"
            parts = message.split("|")
            status_part = [p for p in parts if "Status:" in p]

            if status_part:
                status = status_part[0].split(":")[1].strip()
                last_state = self.last_status.get(ticker)

                if status != last_state:
                    self.last_status[ticker] = status
                    self.critical(message)
                else:
                    self.debug(f"[CRYOGEN] VSS status unchanged: {status}")
            else:
                if "Status: BUY" in message or "Status: SELL" in message:
                    self.critical(message)
                else:
                    self.debug(message)
        except Exception as e:
            self.debug(f"[CRYOGEN] Parse error: {e}")
            if "Status: BUY" in message or "Status: SELL" in message:
                self.critical(message)

    def symmetry(self, message: str):
        """Alias: Maps to event()."""
        self.event(message)

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _write_debug(self, message: str):
        """Write to debug log file."""
        try:
            with open(self.debug_file_path, "a") as f:
                f.write(f"{self._timestamp()} {message}\n")
        except Exception:
            pass  # Fail silently if debug log fails


# Global instance (backwards compatible)
LOG = SystemLogger()


# Convenience function for setting verbosity from CLI
def set_log_level(quiet: bool = False, verbose: bool = False):
    """
    Set global log level based on CLI flags.

    Args:
        quiet: If True, show only critical events
        verbose: If True, show detailed flow
    """
    if quiet:
        LOG.set_verbosity(SystemLogger.QUIET)
    elif verbose:
        LOG.set_verbosity(SystemLogger.VERBOSE)
    else:
        LOG.set_verbosity(SystemLogger.NORMAL)
