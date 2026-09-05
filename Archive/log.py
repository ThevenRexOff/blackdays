from __future__ import annotations
import sys
import time
import os

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.style import Style


console = Console()


COUNTRIES = {
    "1":  ("US", "United States",  "\U0001F1FA\U0001F1F8", ".com"),
    "2":  ("DE", "Germany",        "\U0001F1E9\U0001F1EA", ".de"),
    "3":  ("ES", "Spain",          "\U0001F1EA\U0001F1F8", ".es"),
    "4":  ("IT", "Italy",          "\U0001F1EE\U0001F1F9", ".it"),
    "5":  ("JP", "Japan",          "\U0001F1EF\U0001F1F5", ".co.jp"),
    "6":  ("CA", "Canada",         "\U0001F1E8\U0001F1E6", ".ca"),
    "7":  ("AU", "Australia",      "\U0001F1E6\U0001F1FA", ".com.au"),
    "8":  ("BR", "Brazil",         "\U0001F1E7\U0001F1F7", ".com.br"),
    "9":  ("MX", "Mexico",         "\U0001F1F2\U0001F1FD", ".com.mx"),
    "10": ("IN", "India",          "\U0001F1EE\U0001F1F3", ".in"),
    "11": ("NL", "Netherlands",    "\U0001F1F3\U0001F1F1", ".nl"),
    "12": ("SG", "Singapore",      "\U0001F1F8\U0001F1EC", ".sg"),
    "13": ("AE", "UAE",            "\U0001F1E6\U0001F1EA", ".ae"),
    "14": ("SA", "Saudi Arabia",   "\U0001F1F8\U0001F1E6", ".sa"),
    "15": ("TR", "Turkey",         "\U0001F1F9\U0001F1F7", ".com.tr"),
    "16": ("SE", "Sweden",         "\U0001F1F8\U0001F1EA", ".se"),
    "17": ("PL", "Poland",         "\U0001F1F5\U0001F1F1", ".pl"),
    "18": ("EG", "Egypt",          "\U0001F1EA\U0001F1EC", ".eg"),
}


def _gradient_rule(width=70):
    fade = ["#9b59b6", "#a855f7", "#b47cff", "#c084fc", "#d8b4fe", "#e9d5ff", "#f0e0ff"]
    text = Text()
    for i in range(width):
        text.append("━", style=fade[i % len(fade)])
    return text


def banner():
    os.system("cls" if os.name == "nt" else "clear")

    art = Text(justify="left")
    art.append("   ░▒▓██████▓▒░░▒▓██████████████▓▒░ ░▒▓██████▓▒░░▒▓████████▓▒░░▒▓██████▓▒░░▒▓███████▓▒░  \n", style="bold #9b59b6")
    art.append("  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n", style="bold #a855f7")
    art.append("  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░    ░▒▓██▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n", style="bold #b47cff")
    art.append("  ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░  ░▒▓██▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░\n", style="bold #d8b4fe")
    art.append("  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██▓▒░    ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░\n", style="bold #e9d5ff")
    art.append("  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░\n", style="bold #f0e0ff")
    art.append("  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░", style="bold #f5ebff")

    console.print()
    console.print(Align.center(_gradient_rule()))
    console.print(Align.center(art))
    console.print(Align.center(_gradient_rule()))
    console.print()

    sub = Text(justify="center")
    sub.append("Account Generator", style="dim #a855f7")
    sub.append("  ┃  ", style="dim #666")
    sub.append("Multi-Country", style="dim #a855f7")
    sub.append("  ┃  ", style="dim #666")
    sub.append("Bypass", style="dim #a855f7")
    console.print(Align.center(sub))
    console.print()


def select_country() -> str:
    console.print(Align.center(Text("Select Country", style="bold white")))
    console.print()

    table = Table(box=None, show_header=False, padding=(0, 1), expand=False)
    table.add_column(justify="right", style="bold #c084fc", no_wrap=True)
    table.add_column(justify="center", no_wrap=True)
    table.add_column(justify="left", style="cyan", no_wrap=True)
    table.add_column(justify="left", style="dim", no_wrap=True)
    table.add_column(justify="right", style="bold #c084fc", no_wrap=True)
    table.add_column(justify="center", no_wrap=True)
    table.add_column(justify="left", style="cyan", no_wrap=True)
    table.add_column(justify="left", style="dim", no_wrap=True)

    items = list(COUNTRIES.items())
    cols = 2
    for row_start in range(0, len(items), cols):
        row = []
        for idx in range(cols):
            gi = row_start + idx
            if gi < len(items):
                key, (code, name, flag, domain) = items[gi]
                row.extend([key, flag, f"{code}{domain}", name])
            else:
                row.extend(["", "", "", ""])
        table.add_row(*row)

    console.print(Align.center(table))
    console.print()

    while True:
        choice = console.input("  [bold #c084fc]▸ [/]")
        choice = choice.strip()
        if choice in COUNTRIES:
            code, name, flag, domain = COUNTRIES[choice]
            console.print(f"  [green]✓[/] {flag} [bold]{code}[/][dim]{domain}[/]  [dim]{name}[/]")
            return code
        console.print("  [red]✗[/] Invalid")


def ask_count() -> int:
    console.print()
    while True:
        raw = console.input("  [bold #c084fc]▸ Accounts:[/] ").strip()
        if raw.isdigit() and int(raw) > 0:
            n = int(raw)
            console.print(f"  [green]✓[/] {n} account{'s' if n > 1 else ''}")
            return n
        console.print("  [red]✗[/] Number?")


def step(num: int | str, title: str):
    console.print()
    console.print(f"  [bold #c084fc][{num}][/][bold] {title}[/]")


def info(msg: str, value: str = None):
    if value is not None:
        console.print(f"  [dim]{msg}:[/] [cyan]{value}[/]")
    else:
        console.print(f"  [dim]{msg}[/]")


def ok(msg: str):
    console.print(f"  [green]✓[/] {msg}")


def warn(msg: str):
    console.print(f"  [yellow]![/] [yellow]{msg}[/]")


def fail(msg: str):
    console.print(f"  [red]✗[/] [red]{msg}[/]")


def highlight(label: str, value: str, color: str = "cyan"):
    console.print(f"  [dim]{label}:[/] [bold {color}]{value}[/]")


def success(msg: str):
    console.print(f"  [bold green]★[/] {msg}")


def error(msg: str):
    console.print(f"  [bold red]✗[/] {msg}")


class Timer:
    def __init__(self, label: str):
        self.label = label
        self.start = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        info(self.label, f"{elapsed:.1f}s")


def dim(s: str) -> str:
    return f"[dim]{s}[/]"


def cyan(s: str) -> str:
    return f"[cyan]{s}[/]"


def green(s: str) -> str:
    return f"[green]{s}[/]"


def yellow(s: str) -> str:
    return f"[yellow]{s}[/]"


def magenta(s: str) -> str:
    return f"[#c084fc]{s}[/]"


class Loader:
    def __init__(self, desc="Processing..."):
        self.desc = desc
        self._task = None
        self._progress = None

    async def _spin(self):
        import asyncio
        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    async def __aenter__(self):
        import asyncio
        self._task = asyncio.create_task(self._spin())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._task:
            self._task.cancel()
            try:
                import asyncio
                await self._task
            except asyncio.CancelledError:
                pass

        if exc_type is not None:
            console.print(f"  [red]✗[/] [red]{self.desc}[/]")
        else:
            console.print(f"  [green]✓[/] [green]{self.desc}[/]")

        import asyncio
        await asyncio.sleep(0.05)

    def update(self, desc):
        self.desc = desc


def result_card(email: str, password: str, country: str, domain: str, cookie_len: int):
    table = Table(box=box.ROUNDED, border_style="#9b59b6", show_header=False, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Email", f"[bold]{email}[/]")
    table.add_row("Password", f"[bold]{password}[/]")
    table.add_row("Region", f"[cyan]{country} - {domain}[/]")
    table.add_row("Cookies", f"[green]{cookie_len} chars[/]")

    console.print()
    console.print(Panel(
        table,
        title="[bold green]★ Account Created[/]",
        border_style="#9b59b6",
        expand=False,
    ))
    console.print()


def summary(created: int, failed: int, total_time: float):
    console.print()
    console.print(Align.center(_gradient_rule()))
    text = Text()
    text.append("Created: ", style="dim")
    text.append(str(created), style="bold green")
    text.append("  Failed: ", style="dim")
    text.append(str(failed), style="bold red")
    text.append("  Time: ", style="dim")
    text.append(f"{total_time:.1f}s", style="bold")
    console.print(Align.center(text))
    console.print(Align.center(_gradient_rule()))
    console.print()
