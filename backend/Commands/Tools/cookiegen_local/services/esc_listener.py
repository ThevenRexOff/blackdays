import os, sys, threading, select


class EscListener:
    """Listens for ESC key in a background thread. Sets .pressed = True on ESC."""

    def __init__(self):
        self.pressed = False
        self._thread = None
        self._running = False

    def start(self):
        if os.name == 'nt':
            return self
        # A Textual dashboard owns the terminal's raw input mode itself
        # (see services/dashboard.py's "escape" binding) — a second thread
        # doing tty.setcbreak()/reading stdin directly would fight it for
        # raw mode. Skip spawning ours; `check()` reads the dashboard's
        # own escape flag instead.
        from .logger import Log
        if Log._dashboard is not None:
            return self
        try:
            if not sys.stdin.isatty():
                return self
        except Exception:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        sys.stdout.write(f"\033[2m\033[3m    Press ESC to cancel and save credits\033[0m\n")
        sys.stdout.flush()
        return self

    def _listen(self):
        try:
            import tty, termios
        except ImportError:
            return
        try:
            stdinFd          = sys.stdin.fileno()
            originalSettings = termios.tcgetattr(stdinFd)
        except Exception:
            return
        try:
            tty.setcbreak(stdinFd)
            while self._running:
                if select.select([sys.stdin], [], [], 0.2)[0]:
                    char = sys.stdin.read(1)
                    if char == '\x1b':
                        self.pressed = True
                        self._running = False
                        return
        except Exception:
            pass
        finally:
            try:
                termios.tcsetattr(stdinFd, termios.TCSADRAIN, originalSettings)
            except Exception:
                pass

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)

    def check(self):
        """Raise KeyboardInterrupt if ESC was pressed (own listener, or the dashboard's)."""
        if self.pressed:
            raise KeyboardInterrupt("ESC pressed")
        from .logger import Log
        if Log._dashboard is not None and getattr(Log._dashboard, 'escape_pressed', False):
            raise KeyboardInterrupt("ESC pressed")
