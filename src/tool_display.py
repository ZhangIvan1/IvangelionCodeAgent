import threading

import sys
import time

from markdown import CYAN, RESET, GREEN, YELLOW


class Spinner:
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str) -> None:
        self._message = message
        self._frame_index = 0
        self._running = True
        self._thread: threading.Thread | None = None

    @property
    def message(self) -> str:
        return self._message
    
    def current_frame(self) -> str:
        return self.FRAMES[self._frame_index]
    
    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        
    def _spin(self) -> None:
        while self._running:
            frame = self.FRAMES[self._frame_index % len(self.FRAMES)]
            sys.stderr.write(f"\r{CYAN}{frame}{RESET} {self._message}")
            sys.stderr.flush()
            self._frame_index += 1
            time.sleep(0.08)
            
    def update(self, message: str) -> None:
        self._message = message
        
    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=0.2)
            self._thread = None
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()
            
    def success(self, message: str | None = None) -> None:
        self.stop()
        sys.stderr.write(f"{GREEN}✔{RESET} {message or self._message}\n")
        sys.stderr.flush()
        
    def fail(self, message: str | None = None) -> None:
        self.stop()
        sys.stderr.write(f"{YELLOW}✖{RESET} {message or self._message}\n")
        sys.stderr.flush()
        
    @property
    def is_running(self) -> bool:
        return self._running
