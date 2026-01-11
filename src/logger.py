
import os
import sys

class Logger:
    def __init__(self):
        self.research_mode = False
        self.debug_file_path = os.path.join(os.getcwd(), "debug_vault.log")
        # Initialize/Clear debug file
        with open(self.debug_file_path, 'w') as f:
            f.write("")

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
        # Digital Squelch: ONLY print BUY or SELL events
        if "Status: BUY" in message or "Status: SELL" in message:
            print(self._clean_ascii(message))
        
    def cryogen(self, message: str):
        # Digital Squelch: ONLY print BUY or SELL events
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
