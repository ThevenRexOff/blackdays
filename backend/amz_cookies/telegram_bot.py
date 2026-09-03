import asyncio
import os
import sys
import io
import time
import html
import logging
import contextlib

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from amazon_v2 import create_email, COUNTRY_CONFIG

# ── Config ───────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ALLOWED_USERS = os.getenv("TG_ALLOWED_USERS", "")
MAX_CONCURRENT = int(os.getenv("TG_MAX_CONCURRENT", "5"))

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("amazon_bot")

# ── Suppress log.py console output during Telegram runs ──────────────────────

_NULL = io.StringIO()

@contextlib.contextmanager
def suppress_cli():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = _NULL
    sys.stderr = _NULL
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


def _esc(text: str) -> str:
    return html.escape(str(text))


# Track last text per message_id to avoid identical edits
_last_text: dict[int, str] = {}
_edit_locks: dict[int, asyncio.Lock] = {}


async def safe_edit(msg, text: str, **kwargs):
    """Edit only if text changed. Serializes per-message to avoid race conditions."""
    mid = msg.message_id
    if mid in _last_text and _last_text[mid] == text:
        return

    if mid not in _edit_locks:
        _edit_locks[mid] = asyncio.Lock()

    async with _edit_locks[mid]:
        # Double-check after acquiring lock
        if mid in _last_text and _last_text[mid] == text:
            return
        try:
            await msg.edit_text(text, **kwargs)
            _last_text[mid] = text
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                logger.debug("edit failed: %s", e)
        except Exception as e:
            logger.debug("edit failed: %s", e)


# ── Country list ─────────────────────────────────────────────────────────────

COUNTRY_LIST = [
    ("US", "🇺🇸 United States", ".com"),
    ("DE", "🇩🇪 Germany", ".de"),
    ("ES", "🇪🇸 Spain", ".es"),
    ("IT", "🇮🇹 Italy", ".it"),
    ("JP", "🇯🇵 Japan", ".co.jp"),
    ("CA", "🇨🇦 Canada", ".ca"),
    ("AU", "🇦🇺 Australia", ".com.au"),
    ("BR", "🇧🇷 Brazil", ".com.br"),
    ("MX", "🇲🇽 Mexico", ".com.mx"),
    ("IN", "🇮🇳 India", ".in"),
    ("NL", "🇳🇱 Netherlands", ".nl"),
    ("SG", "🇸🇬 Singapore", ".sg"),
    ("AE", "🇦🇪 UAE", ".ae"),
    ("SA", "🇸🇦 Saudi Arabia", ".sa"),
    ("TR", "🇹🇷 Turkey", ".com.tr"),
    ("SE", "🇸🇪 Sweden", ".se"),
    ("PL", "🇵🇱 Poland", ".pl"),
    ("EG", "🇪🇬 Egypt", ".eg"),
]

# ── State ────────────────────────────────────────────────────────────────────

user_sessions: dict[int, dict] = {}
PM = "HTML"


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    allowed = [int(x.strip()) for x in ALLOWED_USERS.split(",") if x.strip()]
    return user_id in allowed


# ── Commands ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return
    keyboard = [
        [InlineKeyboardButton("🚀 Create Account", callback_data="menu_create")],
        [InlineKeyboardButton("📊 Status", callback_data="menu_status")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ]
    await update.message.reply_text(
        "⚡ <b>Amazon Account Generator</b>\nSelect an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=PM,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        f"⚙️ <b>Commands</b>\n\n"
        f"/start — Menu\n"
        f"/create — 1x US\n"
        f"/create US 5 — 5x US\n"
        f"Max concurrent: <code>{MAX_CONCURRENT}</code>",
        parse_mode=PM,
    )


async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return
    args = context.args
    country = args[0].upper() if args else "US"
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    valid_codes = [c[0] for c in COUNTRY_LIST]
    if country not in valid_codes:
        await update.message.reply_text(f"Invalid: {_esc(country)}\nValid: {', '.join(valid_codes)}")
        return
    count = max(1, min(count, 20))
    await launch(update.effective_user.id, context, country, count, message=update.message)


# ── Menu callbacks ───────────────────────────────────────────────────────────

async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_allowed(q.from_user.id):
        await q.edit_message_text("Access denied.")
        return

    d = q.data
    if d == "menu_help":
        text = (
            "⚙️ <b>How to use</b>\n\n"
            "1. <b>Create Account</b>\n"
            "2. Pick country → count\n"
            "3. Accounts created <b>in parallel</b>\n"
            f"4. Max <code>{MAX_CONCURRENT}</code> simultaneous\n\n"
            "<code>/create US 5</code> — shortcut"
        )
        kb = [[InlineKeyboardButton("← Back", callback_data="menu_back")]]
        await q.edit_message_text(text, parse_mode=PM, reply_markup=InlineKeyboardMarkup(kb))

    elif d == "menu_status":
        s = user_sessions.get(q.from_user.id, {})
        active = s.get("active", 0)
        text = (
            f"📊 <b>Status</b>\n\n"
            f"Active workers: <code>{active}/{MAX_CONCURRENT}</code>\n"
            f"Total created: <code>{s.get('created', 0)}</code>\n"
            f"Total failed: <code>{s.get('failed', 0)}</code>"
        )
        kb = [[InlineKeyboardButton("← Back", callback_data="menu_back")]]
        await q.edit_message_text(text, parse_mode=PM, reply_markup=InlineKeyboardMarkup(kb))

    elif d == "menu_back":
        kb = [
            [InlineKeyboardButton("🚀 Create Account", callback_data="menu_create")],
            [InlineKeyboardButton("📊 Status", callback_data="menu_status")],
            [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
        ]
        await q.edit_message_text(
            "⚡ <b>Amazon Account Generator</b>\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode=PM,
        )

    elif d == "menu_create":
        await show_countries(q)


# ── Country / Count selection ────────────────────────────────────────────────

async def show_countries(query):
    rows, row = [], []
    for code, name, _ in COUNTRY_LIST:
        row.append(InlineKeyboardButton(name, callback_data=f"country_{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("← Back", callback_data="menu_back")])
    await query.edit_message_text("🌍 <b>Select Country</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM)


async def cb_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_allowed(q.from_user.id):
        return
    code = q.data.replace("country_", "")
    cfg = COUNTRY_CONFIG.get(code)
    if not cfg:
        await q.edit_message_text("Invalid country.")
        return
    user_sessions[q.from_user.id] = {"country": code}

    rows, row = [], []
    for n in range(1, 21):
        row.append(InlineKeyboardButton(str(n), callback_data=f"count_{n}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("← Back", callback_data="menu_create")])
    await q.edit_message_text(
        f"🌍 <b>{_esc(code)}</b> — <code>{_esc(cfg['domain'])}</code>\n\nHow many? (max 20)",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM,
    )


async def cb_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_allowed(q.from_user.id):
        return
    uid = q.from_user.id
    country = user_sessions.get(uid, {}).get("country", "US")
    count = int(q.data.replace("count_", ""))
    await q.edit_message_text(
        f"⏳ Starting <b>{count}x {_esc(country)}</b> (×{MAX_CONCURRENT} parallel)...",
        parse_mode=PM,
    )
    await launch(uid, context, country, count, message=q.message)


# ── CORE: parallel account creation ──────────────────────────────────────────

async def _create_one(sem: asyncio.Semaphore, country_code: str, idx: int) -> dict:
    async with sem:
        try:
            with suppress_cli():
                result = await create_email(country_code)
            if result:
                return {"ok": True, "idx": idx, "email": result.email,
                        "password": result.password, "name": result.name,
                        "cookie": result.cookie or "N/A"}
            return {"ok": False, "idx": idx, "error": "Returned None"}
        except Exception as e:
            return {"ok": False, "idx": idx, "error": str(e)[:120]}


async def launch(uid: int, context: ContextTypes.DEFAULT_TYPE,
                 country_code: str, count: int, message=None):
    config = COUNTRY_CONFIG.get(country_code, COUNTRY_CONFIG["US"])
    domain = config["domain"]

    session = user_sessions.get(uid, {})
    session.update({"running": True, "created": 0, "failed": 0,
                    "country": country_code, "active": min(count, MAX_CONCURRENT)})
    user_sessions[uid] = session

    start = time.time()
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    progress_msg = message
    if progress_msg is None:
        progress_msg = await context.bot.send_message(uid, "⏳ Starting...", parse_mode=PM)

    tasks = [asyncio.create_task(_create_one(sem, country_code, i)) for i in range(count)]

    done_count = 0

    async def _updater():
        nonlocal done_count
        while done_count < count:
            pct = int(done_count / count * 100)
            filled = done_count
            empty = count - done_count
            bar = "█" * filled + "░" * empty
            text = (
                f"⚡ <b>{_esc(country_code)}</b> — <code>{_esc(domain)}</code>\n\n"
                f"<code>{bar}</code> {pct}%\n\n"
                f"✅ <code>{session['created']}</code>  "
                f"❌ <code>{session['failed']}</code>  "
                f"⏳ <code>{count - done_count}</code>\n"
                f"🔧 Concurrency: <code>{MAX_CONCURRENT}</code>"
            )
            await safe_edit(progress_msg, text, parse_mode=PM)
            await asyncio.sleep(5)

    updater = asyncio.create_task(_updater())

    results = []
    for coro in asyncio.as_completed(tasks):
        r = await coro
        done_count += 1
        if r["ok"]:
            session["created"] += 1
        else:
            session["failed"] += 1
        results.append(r)

    updater.cancel()
    try:
        await updater
    except asyncio.CancelledError:
        pass

    elapsed = time.time() - start
    created = session["created"]
    failed = session["failed"]

    results.sort(key=lambda x: x["idx"])

    summary = (
        f"{'━' * 25}\n"
        f"🏁 <b>DONE — {_esc(country_code)}</b>\n\n"
        f"✅ Created: <code>{created}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"⏱ Time: <code>{elapsed:.1f}s</code>\n"
        f"⚡ Speed: <code>{elapsed / max(count, 1):.1f}s/account</code>\n"
        f"🔧 Workers: <code>{MAX_CONCURRENT}</code>\n"
        f"{'━' * 25}"
    )

    await safe_edit(progress_msg, summary, parse_mode=PM)

    # Each account as separate message
    for r in results:
        if r["ok"]:
            text = (
                f"✅ <b>Account #{r['idx']+1}</b>\n"
                f"📧 <code>{_esc(r['email'])}</code>\n"
                f"🔑 <code>{_esc(r['password'])}</code>\n"
                f"👤 <code>{_esc(r['name'])}</code>\n"
                f"🍪 <code>{_esc(r['cookie'])}</code>"
            )
        else:
            text = f"❌ <b>Account #{r['idx']+1}</b> — <code>{_esc(r['error'])}</code>"
        try:
            await context.bot.send_message(uid, text, parse_mode=PM)
        except Exception:
            pass

    kb = [
        [InlineKeyboardButton("🚀 Create More", callback_data="menu_create")],
        [InlineKeyboardButton("📊 Status", callback_data="menu_status")],
    ]
    await context.bot.send_message(uid, "What next?", reply_markup=InlineKeyboardMarkup(kb))

    session["running"] = False
    session["active"] = 0


# ── Error handler ────────────────────────────────────────────────────────────

async def error_handler(update, context):
    logger.error("Exception: %s", context.error, exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ Error. Try again.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set TG_BOT_TOKEN in .env or environment")
        return

    print(f"🤖 Bot started | Max concurrent: {MAX_CONCURRENT}")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("create", cmd_create))
    app.add_handler(CallbackQueryHandler(cb_country, pattern="^country_"))
    app.add_handler(CallbackQueryHandler(cb_count, pattern="^count_"))
    app.add_handler(CallbackQueryHandler(cb_menu, pattern="^menu_"))
    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
