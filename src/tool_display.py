import json
import threading

import sys
import time

from markdown import CYAN, RESET, GREEN, YELLOW, DIM, MAGENTA, GRAY


class Spinner:
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str) -> None:
        self._message = message
        self._frame_index = 0
        self._running = False
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
            
    def succeed(self, message: str | None = None) -> None:
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


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."

def format_tool_call(name: str, input: dict) -> str:
    params = format_params(input)
    return f"{MAGENTA}🔧 {name}{RESET}{DIM}({params}){RESET}"

def format_params(input: dict, max_len: int = 80) -> str:
    if not input:
        return ""
    
    parts = []
    for key, value in input.items():
        val = f'"{truncate(value, 40)}"' if isinstance(value, str) else json.dumps(value)
        parts.append(f"{key}: {val}")
        
    joined = ", ".join(parts)
    return joined if len(joined) <= max_len else joined[:max_len - 3] + "..."

def format_duration(ms: float) -> str:
    if ms < 1000:
        return f"{round(ms)}ms"
    if ms < 60000:
        return f"{ms / 1000:.1f}s"
    return f"{ms / 60000:.1f}m"

def format_tool_result(
        result: str,
        max_lines: int = 5,
        max_line_len: int = 120,
) -> str:
    lines = result.split("\n")
    total_lines = len(lines)
    
    shown = [
        line if len(line) < max_line_len else line[:max_line_len - 3] + "..."
        for line in lines[:max_lines]
    ]
    
    if total_lines > max_lines:
        shown.append(f"{GRAY}... ({total_lines - max_lines} more lines){RESET}")
        
    return "\n".join(shown)

def format_tool_cycle(
        name: str,
        input: dict,
        result: str,
        duration: float,
) -> str:
    header = format_tool_call(name, input)
    time_duration = format_duration(duration)
    body = format_tool_result(result)
    return f"{header} {time_duration}\n{body}"