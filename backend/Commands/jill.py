# Central design system for JILL_BOT — import with: from Commands.jill import *
from Model import BotX
import html as _html_mod

bi  = BotX.bi   # exported via import *
_bi = bi         # internal alias for jill's own functions

# NewsEmoji (animated=True) — animate for Premium viewers
E_RAINBOW = '<tg-emoji emoji-id="5103122966779004034">🌈</tg-emoji>'
E_BOLT    = '<tg-emoji emoji-id="5456140674028019486">⚡️</tg-emoji>'
E_CHECK   = '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji>'
E_LETTER  = '<tg-emoji emoji-id="5253742260054409879">✉️</tg-emoji>'
E_CHART   = '<tg-emoji emoji-id="5246762912428603768">📉</tg-emoji>'
E_MONITOR = '<tg-emoji emoji-id="5282843764451195532">🖥</tg-emoji>'
E_GLOBE   = '<tg-emoji emoji-id="5447410659077661506">🌐</tg-emoji>'
E_STAR    = '<tg-emoji emoji-id="4974574243422406122">🤩</tg-emoji>'

# DecorationEmojiPack (video=True) — visible as premium for all users when bot owner has Premium
E_RED     = '<tg-emoji emoji-id="5215642288071387368">❌</tg-emoji>'
E_HDR_END = '<tg-emoji emoji-id="5102628843676501227">👤</tg-emoji>'
E_USER    = '<tg-emoji emoji-id="5102628843676501227">👤</tg-emoji>'

DIV_STARS = E_STAR * 13


def loading(title: str = 'Fetching Data') -> str:
    return (
        f"{E_RAINBOW}{_bi(title)} [ {E_BOLT} ]{E_HDR_END}\n"
        f"{E_BOLT} {_bi('Status')}: <code>Waiting...</code>"
    )

def error(reason: str) -> str:
    return f"{E_RED} {_bi('Wrong Data')}\n{DIV_STARS}\n{E_LETTER} {_bi('Raise')}: <code>{_html_mod.escape(str(reason))}</code>"

def ok(title: str, *lines) -> str:
    out = f"{E_CHECK} {_bi(title)}\n{DIV_STARS}\n"
    for item in lines:
        if isinstance(item, tuple):
            out += f"{E_LETTER} {_bi(item[0])}: <code>{_html_mod.escape(str(item[1]))}</code>\n"
        else:
            out += str(item) + '\n'
    return out + DIV_STARS

def confirm(title: str, uid: str, body: str) -> str:
    return (
        f"{E_RAINBOW}{_bi(title)} [ {E_BOLT} ]{E_HDR_END}\n{DIV_STARS}\n"
        f"{E_LETTER} {_bi('Target')}: <code>{_html_mod.escape(str(uid))}</code>\n"
        f"{E_LETTER} {_bi('Important')}: <code>{_html_mod.escape(str(body))}</code>\n{DIV_STARS}"
    )

def panel(title: str, *fields) -> str:
    out = f"{E_RAINBOW}{_bi(title)} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
    for item in fields:
        if isinstance(item, tuple):
            out += f"{E_LETTER} {_bi(item[0])}: <code>{_html_mod.escape(str(item[1]))}</code>\n"
        else:
            out += str(item) + '\n'
    return out + DIV_STARS
