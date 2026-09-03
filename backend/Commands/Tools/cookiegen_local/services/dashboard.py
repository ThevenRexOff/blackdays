"""Textual dashboard for the registration flow — obsidian & gold theme.

`Log` (services/logger.py) routes into an instance of this app when one is
attached via `Log.attach(dashboard)`. All existing call sites (flow.py,
metadata.py, main.py, captcha.py, mailtm.py) are untouched —
`Log.info/success/warn/error/debug/detail/spinner/banner/result` keep their
exact signatures; only where the output goes changes.

Instead of three scrolling log boxes, the centerpiece is an animated
`Stepper`: a pipeline of named stages (Email → WAF → Landing → Register →
Captcha → OTP → Billing) that lights up as the flow progresses, inferred
from the free-text step labels flow.py already passes to Log.spinner() —
no changes needed there. A single-line ticker shows the current sub-step
with a live elapsed timer; a slim tail keeps the last few log lines for
anyone who wants them. On success, the whole body is replaced by a result
screen with a read-only, selectable/copyable TextArea holding the FULL
cookie string (never truncated) — and main.py also prints it to the real
terminal after the app exits, as a copy-paste-proof fallback.

The actual registration flow is synchronous/blocking (curl_cffi, requests),
so it runs in a worker thread (`run_worker(..., thread=True)`); every widget
update from that thread goes through `call_from_thread` to stay safe on
Textual's event loop.
"""
from __future__ import annotations

import time

from rich.markup import escape
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, RichLog, Static, TextArea

# ── Obsidian & gold theme (registered in on_mount, cascades to every
# built-in widget via CSS $variables). Royal violet stays the brand color
# (borders, frames, secondary text); gold is the accent reserved for what's
# ALIVE right now — the active pipeline node, the success title — so it
# reads as a highlight, not wallpaper. NOTE: these are Textual *theme*
# tokens, only valid inside the CSS = """...""" block below — Rich's own
# Text/markup styling (used everywhere else in this file) doesn't know
# about them and needs literal color values instead, hence the C_*
# constants that mirror the same palette for use in Text.from_markup()/
# style= calls.
OBSIDIAN_GOLD = Theme(
    name="obsidian-gold",
    primary="#6d28d9",      # royal violet — brand, frames
    secondary="#9c86c9",    # muted lavender-grey — secondary text/labels
    accent="#d4af37",       # metallic gold — the one thing that gets to glow
    warning="#c9962c",      # burnished amber
    error="#a53860",        # deep wine
    success="#2f9e6e",      # muted emerald
    foreground="#ede6d9",   # warm ivory
    background="#09080b",   # true near-black
    surface="#14121a",
    panel="#1c1824",
    dark=True,
)

C_PRIMARY = "#6d28d9"
C_ACCENT  = "#d4af37"
C_SUCCESS = "#2f9e6e"
C_WARNING = "#c9962c"
C_ERROR   = "#a53860"
C_MUTED   = "#9c86c9"
C_GOLD_BAND = ["#8a6d1f", "#b8934a", "#e8c874", "#fff3d0", "#e8c874", "#b8934a", "#8a6d1f"]

LEVEL_STYLE = {
    'info':    ('›', C_MUTED),
    'success': ('✓', C_SUCCESS),
    'warn':    ('⚠', C_WARNING),
    'error':   ('✗', C_ERROR),
    'debug':   ('·', 'dim'),
}

# Pipeline stages, in chronological order. Matched against the free-text
# spinner labels flow.py/main.py already use, by keyword — never regresses
# to an earlier stage once a later one has activated.
STAGES = [
    ("Number",   ["phone number"]),
    ("WAF",      ["waf"]),
    ("Landing",  ["registration page", "sign-in page"]),
    ("Register", ["registration form"]),
    ("Captcha",  ["captcha"]),
    ("OTP",      ["verification code", "sms", "otp"]),
    ("Billing",  ["billing", "wallet"]),
]

PULSE_FRAMES = ["◐", "◓", "◑", "◒"]


def _match_stage(text: str, current_index: int) -> int | None:
    """Return the stage index `text` advances to, or None if it stays put."""
    lowered = text.lower()
    for i in range(max(current_index, 0), len(STAGES)):
        _, keywords = STAGES[i]
        if any(k in lowered for k in keywords):
            return i
    return None


def _gold_shimmer(text: str) -> Text:
    """One-off gold sweep across `text` — the single flourish reserved for
    the moment that actually deserves it: the success title."""
    out = Text()
    band = C_GOLD_BAND
    for i, ch in enumerate(text):
        if ch == ' ':
            out.append(ch)
        else:
            out.append(ch, style=f"bold {band[i % len(band)]}")
    return out


class Stepper(Static):
    """Animated horizontal pipeline: ○ pending → pulsing active → ● done / ✕ failed."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.statuses     = ['pending'] * len(STAGES)   # pending|active|done|caution|failed
        self.active_index = -1
        self._frame       = 0

    def on_mount(self) -> None:
        self.set_interval(0.12, self._animate)

    def _animate(self) -> None:
        if self.active_index >= 0 and self.statuses[self.active_index] == 'active':
            self._frame += 1
            self.refresh()

    def activate(self, index: int) -> None:
        if self.active_index >= 0 and self.statuses[self.active_index] == 'active':
            self.statuses[self.active_index] = 'done'
        self.active_index = index
        self.statuses[index] = 'active'
        self.refresh()

    def finish_current(self, status: str) -> None:
        """status: 'done' | 'caution' | 'failed'"""
        if self.active_index >= 0:
            self.statuses[self.active_index] = status
        self.refresh()

    def render(self) -> Text:
        out = Text()
        for i, (name, _) in enumerate(STAGES):
            status = self.statuses[i]
            if status == 'pending':
                symbol, style = "○", "dim"
            elif status == 'active':
                symbol, style = PULSE_FRAMES[self._frame % len(PULSE_FRAMES)], f"bold {C_ACCENT}"
            elif status == 'done':
                symbol, style = "●", f"bold {C_SUCCESS}"
            elif status == 'caution':
                symbol, style = "▲", f"bold {C_WARNING}"
            else:
                symbol, style = "✕", f"bold {C_ERROR}"

            label_style = "dim" if status == 'pending' else ("bold" if status == 'active' else style)
            out.append(f"{symbol} ", style=style)
            out.append(f"{name}", style=label_style)
            if i < len(STAGES) - 1:
                line_style = C_SUCCESS if status in ('done', 'caution') else "dim"
                out.append("  ──  ", style=line_style)
        return out


class RegistrationDashboard(App):
    """Live dashboard: animated stage pipeline, ticker, details, result screen."""

    TITLE = "Amazon PWA"

    CSS = """
    Screen { align: center top; }
    #pipeline_card {
        margin: 1 2;
        padding: 1 2;
        border: round $primary;
        height: auto;
    }
    #stepper { height: 1; content-align: center middle; }
    #ticker { height: 1; margin-top: 1; color: $text-muted; content-align: center middle; }
    #lower { height: 1fr; margin: 0 2 1 2; }
    #details { width: 2fr; border: round $primary-darken-1; }
    #tail_col { width: 3fr; height: 1fr; }
    #tail { border: round $primary-darken-1; height: 1fr; }
    #result_panel { display: none; margin: 1 2; padding: 1 2; border: heavy $success; height: 1fr; }
    #result_panel.show { display: block; }
    #result_panel.failed { border: heavy $error; }
    #result_title { height: 1; content-align: center middle; text-style: bold; margin-bottom: 1; }
    #result_fields { height: auto; margin-bottom: 1; }
    #cookie_label { height: 1; color: $text-muted; margin-bottom: 1; }
    #cookie_box { height: 1fr; border: round $primary; }
    #body_wrap.hidden { display: none; }
    """

    BINDINGS = [("q", "quit", "Quit"), ("escape", "cancel", "Cancel")]

    def __init__(self, on_start=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._on_start       = on_start
        self._step_text      = ""
        self._step_start     = 0.0
        self._step_active    = False
        self._current_step_stage = None
        self._result_shown   = False   # True once _show_result() has rendered the result screen
        self._full_cookie_value = None
        self.escape_pressed  = False   # polled by services/esc_listener.py's EscListener.check()
        self.final_result    = None    # {'success': bool, 'data': dict, 'cookie': str|None} — read by main.py after run()

    def action_cancel(self) -> None:
        # Runs on the app's own event-loop thread (Textual action dispatch) —
        # call the private helper directly, NOT log_message()/call_from_thread()
        # (that raises if called from the app's own thread).
        self.escape_pressed = True
        self._log_message('warn', "ESC pressed — cancelling...")

    # ── layout ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="body_wrap"):
            with Vertical(id="pipeline_card"):
                yield Stepper(id="stepper")
                yield Static(id="ticker")
            with Horizontal(id="lower"):
                yield DataTable(id="details")
                with Vertical(id="tail_col"):
                    yield RichLog(id="tail", wrap=True, markup=True, auto_scroll=True, max_lines=200)
        with Vertical(id="result_panel"):
            yield Static(id="result_title")
            yield Static(id="result_fields")
            yield Static("Cookie (select + Ctrl+C to copy; also printed to the terminal on exit):", id="cookie_label")
            yield TextArea(id="cookie_box", read_only=True, soft_wrap=True, show_line_numbers=False)
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(OBSIDIAN_GOLD)
        self.theme = "obsidian-gold"

        self.query_one("#pipeline_card").border_title = "COOKIEGEN"
        self.query_one("#result_panel").border_title = "COOKIEGEN"

        table = self.query_one("#details", DataTable)
        table.add_columns(("Field", "field"), ("Value", "value"))
        table.cursor_type = "none"
        table.show_header = True

        self.set_interval(0.1, self._tick)
        if self._on_start:
            self.run_worker(lambda: self._on_start(self), thread=True)

    def _tick(self) -> None:
        if self._step_active:
            elapsed = time.time() - self._step_start
            ticker = self.query_one("#ticker", Static)
            ticker.update(Text.from_markup(f"[dim]{escape(self._step_text)} ({elapsed:.1f}s)[/]"))

    # ── thread-safe API used by services/logger.py ──────────────────

    def set_banner(self, lines: list[str]) -> None:
        self.call_from_thread(self._set_banner, lines)

    def _set_banner(self, lines: list[str]) -> None:
        self.title     = lines[0] if lines else self.TITLE
        self.sub_title = " · ".join(lines[1:]) if len(lines) > 1 else ""

    def log_message(self, level: str, msg: str) -> None:
        self.call_from_thread(self._log_message, level, msg)

    def _log_message(self, level: str, msg: str) -> None:
        icon, style = LEVEL_STYLE.get(level, ('·', 'dim'))
        ts   = time.strftime("%H:%M:%S")
        tail = self.query_one("#tail", RichLog)
        tail.write(Text.from_markup(f"[dim]{ts}[/] [{style}]{icon}[/] [{style}]{escape(msg)}[/]"))

    def set_detail(self, key: str, value) -> None:
        self.call_from_thread(self._set_detail, key, str(value))

    def _set_detail(self, key: str, value: str) -> None:
        # Full cookies get their own copyable panel further down — never
        # truncated there — but still get a short pointer row in the table.
        if key.lower().startswith("cookie"):
            self.set_full_cookie(key, value)
            value = f"({len(value)} chars — see cookie box below)"
        elif len(value) > 60:
            value = value[:57] + "..."

        table = self.query_one("#details", DataTable)
        value = escape(value)
        if key in table.rows:
            table.update_cell(key, "value", value)
        else:
            table.add_row(escape(key), value, key=key)

    def set_full_cookie(self, label: str, cookie: str) -> None:
        self._full_cookie_label = label
        self._full_cookie_value = cookie
        # main.py calls Log.result() BEFORE Log.detail("Cookies...") — if the
        # result screen already rendered (and hid the box, assuming no cookie
        # was coming), patch it in now instead of requiring callers to get
        # the order right.
        if getattr(self, '_result_shown', False):
            self._populate_cookie_box(cookie)
            if self.final_result is not None:
                self.final_result['cookie'] = cookie

    def _populate_cookie_box(self, cookie: str) -> None:
        cookie_box = self.query_one("#cookie_box", TextArea)
        cookie_label = self.query_one("#cookie_label", Static)
        cookie_box.text = cookie
        cookie_box.display = True
        cookie_label.display = True

    def start_step(self, text: str) -> None:
        self.call_from_thread(self._start_step, text)

    def _start_step(self, text: str) -> None:
        self._step_text   = text
        self._step_start  = time.time()
        self._step_active = True
        stepper = self.query_one("#stepper", Stepper)
        # Only steps that actually match a NEW stage should move the
        # pipeline — otherwise finish_step() below would blindly re-stamp
        # whatever stage was last active (e.g. a captcha resubmit "stealing"
        # a caution mark that belongs to a stage already marked done).
        stage = _match_stage(text, stepper.active_index)
        self._current_step_stage = stage
        if stage is not None:
            stepper.activate(stage)
        ticker = self.query_one("#ticker", Static)
        ticker.update(Text.from_markup(f"[dim]{escape(text)}[/]"))

    def finish_step(self, text: str, symbol: str = '✓', style: str = 'green') -> None:
        self.call_from_thread(self._finish_step, text, symbol, style)

    def _finish_step(self, text: str, symbol: str, style: str) -> None:
        self._step_active = False
        status = {'✓': 'done', '▲': 'caution', '✗': 'failed'}.get(symbol, 'done')
        if getattr(self, '_current_step_stage', None) is not None:
            self.query_one("#stepper", Stepper).finish_current(status)
        icon_style = {'done': C_SUCCESS, 'caution': C_WARNING, 'failed': C_ERROR}[status]
        tail = self.query_one("#tail", RichLog)
        tail.write(Text.from_markup(f"[{icon_style}]{escape(symbol)}[/] {escape(text)}"))
        ticker = self.query_one("#ticker", Static)
        ticker.update(Text.from_markup(f"[{icon_style}]{escape(text)}[/]"))

    def show_result(self, success: bool, data: dict) -> None:
        self.call_from_thread(self._show_result, success, data)

    def _show_result(self, success: bool, data: dict) -> None:
        panel = self.query_one("#result_panel", Vertical)
        self.query_one("#body_wrap", Vertical).add_class("hidden")
        panel.add_class("show")
        if not success:
            panel.add_class("failed")

        title = self.query_one("#result_title", Static)
        if success:
            title.update(_gold_shimmer("✓  ACCOUNT CREATED  ✓"))
        else:
            title.update(Text.from_markup(f"[bold {C_ERROR}]✗ REGISTRATION FAILED[/]"))

        fields = self.query_one("#result_fields", Static)
        lines = [f"[bold {C_MUTED}]{escape(str(k))}[/]: {escape(str(v))}" for k, v in data.items()]
        fields.update(Text.from_markup("\n".join(lines)))

        self._result_shown = True
        full_cookie = getattr(self, '_full_cookie_value', None)
        if full_cookie:
            self._populate_cookie_box(full_cookie)
        else:
            # Nothing yet — hide for now; set_full_cookie() un-hides this
            # if a cookie detail arrives after the result was already shown.
            self.query_one("#cookie_box", TextArea).display = False
            self.query_one("#cookie_label", Static).display = False
        self.final_result = {'success': success, 'data': data, 'cookie': full_cookie}
