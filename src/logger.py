
import os
import sys

class Logger:
    def __init__(self):
        self.research_mode = False
        self.debug_file_path = os.path.join(os.getcwd(), "debug_vault.log")
        # Initialize/Clear debug file
        with open(self.debug_file_path, 'w') as f:
            f.write("")
        self.last_status = {}

    def set_research_mode(self, enabled: bool):
        self.research_mode = enabled
        if enabled:
            # Telemetry requested by user
            print(self._clean_ascii("[SYSTEM] Digital Squelch Active: Event-Only Logging Enabled."))

    def _clean_ascii(self, text: str) -> str:
        return text.encode('ascii', 'ignore').decode('ascii')

    def info(self, message: str):
        """General info logs that are suppressed in research mode unless critical."""
        if not self.research_mode:
            print(self._clean_ascii(message))

    def system(self, message: str):
        """System messages - suppressed in research mode."""
        if not self.research_mode:
            print(self._clean_ascii(message))
            
    def metric(self, message: str):
        """Fundamental metrics - suppressed in research mode."""
        if not self.research_mode:
            print(self._clean_ascii(message))

    def ic_matrix(self, message: str):
        """IC Matrix logs - suppressed in research mode."""
        if not self.research_mode:
            print(self._clean_ascii(message))

    # CRITICAL LOGS - Always Printed
    def phase_lock(self, message: str):
        # Edge-Logging: Only print if Status changes for this Ticker
        # STRICT RULE: Terminal MUST remain dark if system is in stable state
        try:
            # Parse Ticker and Status
            parts = message.split('|')
            ticker_part = [p for p in parts if "Ticker:" in p]
            status_part = [p for p in parts if "Status:" in p]
            
            if ticker_part and status_part:
                ticker = ticker_part[0].split(':')[1].strip()
                status = status_part[0].split(':')[1].strip()
                
                # Create composite key for ticker+status tracking
                state_key = f"{ticker}:{status}"
                last_state = self.last_status.get(ticker)
                
                # Print ONLY if status changed for this ticker
                # Stable states (BUY->BUY, FILTER->FILTER) are SILENT
                if status != last_state:
                    self.last_status[ticker] = status
                    print(self._clean_ascii(message))
                # else: SQUELCH - terminal remains dark
            else:
                # Fallback: Only print BUY or SELL signals (not FILTER/HOLD)
                if "Status: BUY" in message or "Status: SELL" in message:
                    print(self._clean_ascii(message))
        except Exception:
            # Safety net: Only print actionable signals
            if "Status: BUY" in message or "Status: SELL" in message:
                print(self._clean_ascii(message))

        
    def cryogen(self, message: str):
        # Edge-Logging: Only print if Status changes for VSS
        # STRICT RULE: Terminal MUST remain dark if system is in stable state
        try:
            ticker = 'VSS'
            parts = message.split('|')
            status_part = [p for p in parts if "Status:" in p]
            
            if status_part:
                status = status_part[0].split(':')[1].strip()
                last_state = self.last_status.get(ticker)
                
                # Print ONLY if status changed
                # Stable states (DAMP->DAMP, FILTER->FILTER) are SILENT
                if status != last_state:
                    self.last_status[ticker] = status
                    print(self._clean_ascii(message))
                # else: SQUELCH - terminal remains dark
            else:
                # Fallback: Only print BUY or SELL signals (not DAMP/FILTER)
                if "Status: BUY" in message or "Status: SELL" in message:
                    print(self._clean_ascii(message))
        except Exception:
            # Safety net: Only print actionable signals
            if "Status: BUY" in message or "Status: SELL" in message:
                print(self._clean_ascii(message))

        
    def symmetry(self, message: str):
        print(self._clean_ascii(message))
        
    def stats(self, message: str):
        print(self._clean_ascii(message))
        
    def warning(self, message: str):
        print(self._clean_ascii(message))
        
    def error(self, message: str):
        print(self._clean_ascii(message))

    def ensemble(self, message: str):
        """Ensemble synchronization messages - Always Printed."""
        print(self._clean_ascii(message))

    # REDIRECTED LOGS
    def debug(self, message: str):
        """Redirects [DEBUG] and similar to file."""
        with open(self.debug_file_path, "a") as f:
            f.write(f"{self._clean_ascii(message)}\n")
            
    def success(self, message: str):
        """Redirects [SUCCESS] to file."""
        with open(self.debug_file_path, "a") as f:
            f.write(f"{self._clean_ascii(message)}\n")
            
    def config(self, message: str):
        """Redirects [CONFIG] and [NODE] to file."""
        with open(self.debug_file_path, "a") as f:
            f.write(f"{self._clean_ascii(message)}\n")

# Global instance
LOG = Logger()
