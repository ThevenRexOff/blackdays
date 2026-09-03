import sys, os, time, threading, shutil

# ── Windows compatibility ────────────────────────────────────────────
# Enable ANSI color codes in Windows terminals (cmd.exe / PowerShell pre-v7)
# by forcing a call through the Win32 console API.
_IS_WINDOWS = sys.platform == 'win32'
if _IS_WINDOWS:
    os.system('')  # triggers ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # Detect if terminal can render Unicode (UTF-8 output works)
    try:
        _UNICODE_OK = sys.stdout.encoding and sys.stdout.encoding.lower().startswith('utf')
    except Exception:
        _UNICODE_OK = False
else:
    _UNICODE_OK = True


class _Colors:
    RESET     = "\033[0m"
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    ITALIC    = "\033[3m"
    UNDERLINE = "\033[4m"

    # ── Core palette (Purple Neon theme) ───────────────────────────
    CYAN      = "\033[38;5;183m"   # lavender (primary accent)
    GREEN     = "\033[38;5;114m"   # semantic: success
    YELLOW    = "\033[38;5;222m"   # semantic: warning
    RED       = "\033[38;5;203m"   # semantic: error
    MAGENTA   = "\033[38;5;177m"   # soft neon magenta
    BLUE      = "\033[38;5;141m"   # soft purple
    ORANGE    = "\033[38;5;215m"
    GRAY      = "\033[38;5;242m"
    WHITE     = "\033[38;5;252m"
    DARK      = "\033[38;5;238m"
    MINT      = "\033[38;5;189m"   # light lavender
    PINK      = "\033[38;5;183m"   # lavender-pink
    LIME      = "\033[38;5;156m"
    PURPLE    = "\033[38;5;135m"   # vivid purple
    LAVENDER  = "\033[38;5;183m"   # soft lavender
    GOLD      = "\033[38;5;220m"
    TEAL      = "\033[38;5;141m"   # purple accent
    CORAL     = "\033[38;5;209m"

    # ── Gradient palettes (soft purple neon) ────────────────────────
    CYBER_GRAD = [
        "\033[38;5;55m",  "\033[38;5;56m",  "\033[38;5;93m",  "\033[38;5;129m",
        "\033[38;5;135m", "\033[38;5;141m", "\033[38;5;147m", "\033[38;5;183m",
        "\033[38;5;189m", "\033[38;5;183m", "\033[38;5;147m", "\033[38;5;141m",
    ]
    NEON_GRAD = [
        "\033[38;5;93m",  "\033[38;5;129m", "\033[38;5;165m", "\033[38;5;171m",
        "\033[38;5;177m", "\033[38;5;183m", "\033[38;5;177m", "\033[38;5;171m",
        "\033[38;5;165m", "\033[38;5;129m", "\033[38;5;93m",  "\033[38;5;129m",
    ]
    SPIN_GRAD = [
        "\033[38;5;129m", "\033[38;5;135m", "\033[38;5;141m", "\033[38;5;147m",
        "\033[38;5;183m", "\033[38;5;189m", "\033[38;5;183m", "\033[38;5;147m",
        "\033[38;5;141m", "\033[38;5;135m", "\033[38;5;129m", "\033[38;5;93m",
        "\033[38;5;129m", "\033[38;5;135m", "\033[38;5;141m", "\033[38;5;147m",
    ]
    SUCCESS_GRAD = [
        "\033[38;5;22m",  "\033[38;5;28m",  "\033[38;5;34m",  "\033[38;5;40m",
        "\033[38;5;46m",  "\033[38;5;82m",  "\033[38;5;118m", "\033[38;5;154m",
    ]
    FAIL_GRAD = [
        "\033[38;5;52m",  "\033[38;5;88m",  "\033[38;5;124m", "\033[38;5;160m",
        "\033[38;5;196m", "\033[38;5;203m", "\033[38;5;210m", "\033[38;5;217m",
    ]
    GOLD_GRAD = [
        "\033[38;5;93m",  "\033[38;5;129m", "\033[38;5;141m", "\033[38;5;183m",
        "\033[38;5;189m", "\033[38;5;183m", "\033[38;5;141m", "\033[38;5;129m",
    ]

    # ── Shimmer highlight colors (white → lavender falloff) ─────────
    SHIMMER = [
        "\033[38;5;231m",  # pure white (center)
        "\033[38;5;189m",  # very light lavender
        "\033[38;5;183m",  # lavender
        "\033[38;5;147m",  # soft purple
    ]

    # ── Background ──────────────────────────────────────────────────
    BG_GREEN   = "\033[48;5;22m"
    BG_RED     = "\033[48;5;52m"
    BG_CYAN    = "\033[48;5;53m"
    BG_DARK    = "\033[48;5;235m"
    BG_SUCCESS = "\033[48;5;28m"
    BG_FAIL    = "\033[48;5;124m"
    BG_ACCENT  = "\033[48;5;53m"


# ════════════════════════════════════════════════════════════════════
#  Spinner: Braille animation + gradient color cycling + pulse dots
# ════════════════════════════════════════════════════════════════════

class _Spinner:
    # Braille spinner for UTF-8 terminals, ASCII fallback for legacy Windows
    if _UNICODE_OK:
        FRAMES = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    else:
        FRAMES = ["|", "/", "-", "\\", "|", "/", "-", "\\"]
    PULSES = ["   ", ".  ", ".. ", "..."]

    def __init__(self, text, color):
        self._text    = text
        self._color   = color
        self._running = False
        self._thread  = None
        self._lock    = threading.Lock()
        self._start   = time.time()

    def start(self):
        self._running = True
        self._start   = time.time()
        self._thread  = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def _format_time(self, elapsed):
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        m, s = divmod(int(elapsed), 60)
        return f"{m}m{s:02d}s"

    def _spin(self):
        i = 0
        grad = _Colors.SPIN_GRAD
        while self._running:
            frame   = self.FRAMES[i % len(self.FRAMES)]
            c       = grad[i % len(grad)]
            elapsed = time.time() - self._start
            dots    = self.PULSES[(i // 4) % len(self.PULSES)]
            timer   = f"{_Colors.DARK}[{self._format_time(elapsed)}]{_Colors.RESET}"
            with self._lock:
                sys.stdout.write(
                    f"\r\033[2K  {c}{_Colors.BOLD}{frame}{_Colors.RESET} "
                    f"{_Colors.WHITE}{self._text}{_Colors.DARK}{dots}{_Colors.RESET} {timer}"
                )
                sys.stdout.flush()
            time.sleep(0.07)
            i += 1

    def stop(self, final_text=None, symbol=None, color=None):
        self._running = False
        if self._thread:
            self._thread.join()
        elapsed = time.time() - self._start
        sym   = symbol or "✓"
        col   = color or _Colors.GREEN
        txt   = final_text or self._text
        timer = f"{_Colors.DARK}({self._format_time(elapsed)}){_Colors.RESET}"
        with self._lock:
            sys.stdout.write(f"\r\033[2K  {col}{_Colors.BOLD}{sym}{_Colors.RESET} {txt} {timer}\n")
            sys.stdout.flush()

    def fail(self, final_text=None):
        self.stop(final_text, symbol="✗", color=_Colors.RED)


class _SilentSpinner:
    """No-op spinner for verbose=False mode."""
    def start(self):              return self
    def stop(self, *a, **k):      pass
    def fail(self, *a, **k):      pass


class _DashboardSpinner:
    """Routes a step's start/stop/fail into a RegistrationDashboard (Textual)."""

    def __init__(self, dashboard, text):
        self._dashboard = dashboard
        self._text      = text

    def start(self):
        self._dashboard.start_step(self._text)
        return self

    def stop(self, final_text=None, symbol=None, color=None):
        # Only the "caution" path (flow.py) ever overrides symbol/color today —
        # any override renders as the caution style; otherwise it's a plain success.
        sym   = symbol or '✓'
        style = 'yellow' if (symbol or color) else 'green'
        self._dashboard.finish_step(final_text or self._text, sym, style)

    def fail(self, final_text=None):
        self._dashboard.finish_step(final_text or self._text, '✗', 'red')


# ════════════════════════════════════════════════════════════════════
#  Log: Full terminal UI system — centered, full-width, purple neon
# ════════════════════════════════════════════════════════════════════

MARGIN = 4

class Log:

    _c         = _Colors
    verbose    = True
    _dashboard = None   # set via Log.attach(dashboard) — a RegistrationDashboard instance

    @classmethod
    def attach(cls, dashboard):
        """Route all subsequent Log.* calls into a running Textual dashboard."""
        cls._dashboard = dashboard

    @classmethod
    def detach(cls):
        cls._dashboard = None

    # ── Internal helpers ────────────────────────────────────────────

    @staticmethod
    def _ts():
        return time.strftime("%H:%M:%S")

    @staticmethod
    def _tw():
        try:
            cols = shutil.get_terminal_size().columns
        except Exception:
            cols = 80
        return cols - (MARGIN * 2)

    @staticmethod
    def _margin():
        return " " * MARGIN

    @staticmethod
    def _gradient_text(text, colors):
        """Apply color gradient to visible characters only."""
        out, ci = [], 0
        for ch in text:
            if ch == ' ':
                out.append(ch)
            else:
                out.append(f"{colors[ci % len(colors)]}{ch}")
                ci += 1
        out.append(_Colors.RESET)
        return "".join(out)

    @staticmethod
    def _gradient_line(text, colors):
        """Apply color gradient to every character."""
        out = []
        for i, ch in enumerate(text):
            out.append(f"{colors[i % len(colors)]}{ch}")
        out.append(_Colors.RESET)
        return "".join(out)

    @staticmethod
    def _shimmer_frame(text, colors, shimmer_colors, pos):
        """Build one frame of shimmer: gradient text with a white glow at `pos`."""
        out, ci = [], 0
        sw = len(shimmer_colors)
        for ch in text:
            if ch == ' ':
                out.append(ch)
            else:
                dist = abs(pos - ci)
                if dist < sw:
                    out.append(f"{shimmer_colors[dist]}{ch}")
                else:
                    out.append(f"{colors[ci % len(colors)]}{ch}")
                ci += 1
        out.append(_Colors.RESET)
        return "".join(out)

    @classmethod
    def _center_text(cls, text, width):
        pad_l = (width - len(text)) // 2
        pad_r = width - len(text) - pad_l
        return (" " * pad_l, " " * pad_r)

    @classmethod
    def _prefix(cls, icon, color):
        m  = cls._margin()
        ts = f"{cls._c.DARK}{cls._ts()}{cls._c.RESET}"
        ic = f"{color}{cls._c.BOLD}{icon}{cls._c.RESET}"
        return f"{m}{ts} {ic}"

    # ── Standard log levels ─────────────────────────────────────────

    @classmethod
    def info(cls, msg):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.log_message('info', msg)
        print(f"{cls._prefix('›', cls._c.CYAN)} {cls._c.WHITE}{msg}{cls._c.RESET}")

    @classmethod
    def success(cls, msg):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.log_message('success', msg)
        print(f"{cls._prefix('✓', cls._c.GREEN)} {cls._c.GREEN}{msg}{cls._c.RESET}")

    @classmethod
    def warn(cls, msg):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.log_message('warn', msg)
        print(f"{cls._prefix('⚠', cls._c.YELLOW)} {cls._c.YELLOW}{msg}{cls._c.RESET}")

    @classmethod
    def error(cls, msg):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.log_message('error', msg)
        print(f"{cls._prefix('✗', cls._c.RED)} {cls._c.RED}{msg}{cls._c.RESET}")

    @classmethod
    def debug(cls, msg):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.log_message('debug', msg)
        print(f"{cls._prefix('·', cls._c.DARK)} {cls._c.DIM}{msg}{cls._c.RESET}")

    # ── Structural elements ─────────────────────────────────────────

    @classmethod
    def detail(cls, key, value):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.set_detail(key, value)
        m = cls._margin()
        print(
            f"{m}{cls._c.DARK}│{cls._c.RESET} "
            f"{cls._c.BLUE}{key:<15}{cls._c.RESET} "
            f"{cls._c.DARK}·{cls._c.RESET} "
            f"{cls._c.WHITE}{value}{cls._c.RESET}"
        )

    @classmethod
    def divider(cls):
        if not cls.verbose: return
        m = cls._margin()
        w = cls._tw()
        line = cls._gradient_line("─" * w, cls._c.CYBER_GRAD)
        print(f"{m}{line}")

    @classmethod
    def header(cls, msg):
        if not cls.verbose: return
        m = cls._margin()
        w = cls._tw()
        line = cls._gradient_line("─" * w, cls._c.CYBER_GRAD)
        title = cls._gradient_text(msg, cls._c.CYBER_GRAD)
        lp, _ = cls._center_text(msg, w)
        print(f"\n{m}{line}")
        print(f"{m}{lp}{cls._c.BOLD}{title}{cls._c.RESET}")
        print(f"{m}{line}\n")

    @classmethod
    def step(cls, current, total, msg):
        if not cls.verbose: return
        m = cls._margin()
        bar_len = 28
        filled  = int(bar_len * current / total)
        empty   = bar_len - filled

        bar_chars = ""
        grad = cls._c.CYBER_GRAD
        for i in range(filled):
            bar_chars += f"{grad[i % len(grad)]}█"
        bar_chars += cls._c.RESET
        bar_empty = f"{cls._c.DARK}{'░' * empty}{cls._c.RESET}"

        pct = int(100 * current / total)
        pct_color = cls._c.GREEN if pct >= 80 else (cls._c.YELLOW if pct >= 40 else cls._c.CYAN)
        print(
            f"{m}{bar_chars}{bar_empty} "
            f"{pct_color}{cls._c.BOLD}{pct:>3}%{cls._c.RESET} "
            f"{cls._c.DIM}{msg}{cls._c.RESET}"
        )

    # ── Spinner factory ─────────────────────────────────────────────

    @classmethod
    def spinner(cls, text, color=None):
        if not cls.verbose:
            return _SilentSpinner()
        if cls._dashboard:
            return _DashboardSpinner(cls._dashboard, text)
        return _Spinner(text, color or cls._c.CYAN)

    # ── Banner (full-width, centered, shimmer on title) ─────────────

    @staticmethod
    def _spaced(text):
        """Add letter spacing: 'Hello' → 'H E L L O'"""
        return " ".join(text)

    @classmethod
    def _empty_row(cls, m, inner, border=None):
        b = border or cls._c.DARK
        print(f"{m}{b}│{cls._c.RESET}{' ' * inner}{b}│{cls._c.RESET}")

    @classmethod
    def _centered_row(cls, m, inner, content_ansi, content_vis_len, border=None):
        b = border or cls._c.DARK
        lp = (inner - content_vis_len) // 2
        rp = inner - content_vis_len - lp
        print(f"{m}{b}│{cls._c.RESET}{' ' * lp}{content_ansi}{' ' * rp}{b}│{cls._c.RESET}")

    @classmethod
    def banner(cls, lines):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.set_banner(lines)

        m     = cls._margin()
        w     = cls._tw()
        grad  = cls._c.CYBER_GRAD
        neon  = cls._c.NEON_GRAD
        inner = w - 2
        D     = cls._c.DARK
        R     = cls._c.RESET

        # ── Parse first line: "Amazon Account Creator (United States)"
        #    Split into brand + subtitle for a layered layout
        first   = lines[0]
        brand   = "Amazon"
        subtitle = first.replace("Amazon ", "", 1) if first.startswith("Amazon ") else first

        # ── Spaced brand: "A M A Z O N"
        brand_spaced     = cls._spaced(brand.upper())
        brand_spaced_vis = f"✦  {brand_spaced}  ✦"

        # ── Underline: gradient dashes under the brand
        underline_w   = len(brand_spaced) + 6
        underline_vis = "─" * underline_w

        # ── Subtitle
        sub_vis = subtitle

        # ── Info lines (lines[1:])
        info_lines = lines[1:]

        # ═══════════════ DRAW ═══════════════

        # Precompute title row parts for shimmer
        lp_t = (inner - len(brand_spaced_vis)) // 2
        rp_t = inner - len(brand_spaced_vis) - lp_t
        row_pre = f"{m}{D}│{R}{' ' * lp_t}{cls._c.BOLD}"
        row_suf = f"{R}{' ' * rp_t}{D}│{R}"

        # ╭─ top ─╮
        print(f"\n{m}{cls._gradient_line(f'╭{chr(0x2500) * inner}╮', grad)}")

        # │ empty │
        cls._empty_row(m, inner)

        # │ ✦  A M A Z O N  ✦ │  — shimmer inline then newline
        char_count = sum(1 for ch in brand_spaced_vis if ch != ' ')
        shimmer    = cls._c.SHIMMER
        sw         = len(shimmer)

        for pos in range(-sw, char_count + sw + 1):
            frame = cls._shimmer_frame(brand_spaced_vis, grad, shimmer, pos)
            sys.stdout.write(f"\r\033[2K{row_pre}{frame}{row_suf}")
            sys.stdout.flush()
            time.sleep(0.018)

        # Final: write the normal gradient and end the line
        brand_ansi = cls._gradient_text(brand_spaced_vis, grad)
        sys.stdout.write(f"\r\033[2K{row_pre}{brand_ansi}{R}{' ' * rp_t}{D}│{R}\n")
        sys.stdout.flush()

        # │ ──────────────── │  (gradient underline)
        cls._centered_row(m, inner, cls._gradient_line(underline_vis, neon), underline_w)

        # │ Account Creator (US) │  (white, centered)
        cls._centered_row(m, inner, f"{cls._c.WHITE}{sub_vis}{R}", len(sub_vis))

        # │ empty │
        cls._empty_row(m, inner)

        # │ info lines │
        for i, line in enumerate(info_lines):
            visible = f"◇ {line}"
            if i == len(info_lines) - 1:
                ansi = f"{cls._c.TEAL}◇{R} {cls._c.MINT}{cls._c.ITALIC}{line}{R}"
            else:
                ansi = f"{D}◇{R} {cls._c.WHITE}{line}{R}"
            cls._centered_row(m, inner, ansi, len(visible))

        # │ empty │
        cls._empty_row(m, inner)

        # ╰─ bottom ─╯
        print(f"{m}{cls._gradient_line(f'╰{chr(0x2500) * inner}╯', grad)}")
        print()

    # ── Result card (original style) ──────────────────────────────────

    @classmethod
    def result(cls, success, data: dict):
        if not cls.verbose: return
        if cls._dashboard: return cls._dashboard.show_result(success, data)
        w = 52
        if success:
            label = f"{cls._c.BG_GREEN}{cls._c.BOLD} ✓ SUCCESS {cls._c.RESET}"
        else:
            label = f"{cls._c.BG_RED}{cls._c.BOLD} ✗ FAILED {cls._c.RESET}"
        print(f"\n  {label}")
        print(f"  {cls._c.DARK}{'─' * w}{cls._c.RESET}")
        for k, v in data.items():
            cls.detail(k, v)
        print(f"  {cls._c.DARK}{'─' * w}{cls._c.RESET}\n")
