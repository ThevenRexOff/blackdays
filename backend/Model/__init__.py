# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests, json, time, base64, pathlib, traceback, datetime, os, importlib, importlib.util, functools, threading
from colorama import Fore
from Model.gestion import gestion
from types import SimpleNamespace

# One persistent HTTPS session per worker thread — avoids TCP+TLS handshake to
# api.telegram.org on every update (saves ~47ms per command vs a new Session()).
# Same pattern as gestion._acquire() for DB connections.
_tls_curl = threading.local()

def _get_thread_curl() -> requests.Session:
    if not hasattr(_tls_curl, 'session'):
        s = requests.Session()
        s.headers.update({'Connection': 'keep-alive'})
        s.request = functools.partial(s.request, timeout=(5, 20))
        _tls_curl.session = s
    return _tls_curl.session

#//! BotX - 3.0  (King Ghidorah)
#//! Author: Nebula Claus
"""
BotX 3.0 — minimal webhook micro-framework for the King Ghidorah Telegram bot.

EXECUTION MODEL
    The bot runs one process PER Telegram update (webhook -> main.py -> BotX -> exit).
    There is no long-running loop: every message/callback spins up a fresh BotX,
    dispatches to exactly one handler, and the process dies. State lives in Postgres
    (via `gestion`), never in memory between updates.

TYPICAL USAGE (see main.py)
    bot = BotX(query=<base64 telegram update>)
    bot.addCommand('bin',  'Commands.Tools.binc:cmdBin')     # '/bin' -> module:function
    bot.addCallback('gates','Commands.Admin.callbacks:callback_gates')
    bot.compile_bot()                                         # parse + dispatch + exit

HANDLER CONTRACT
    Every command/callback handler is called as:  handler(bot, update, gestion)
      - bot     : this BotX instance (messaging + keyboard helpers below)
      - update  : the parsed update object (aka `self.updater`, see shape below)
      - gestion : the DB layer (Model/gestion.py)
    Handlers return nothing; they act by calling bot.replyMessage / bot.editMessage / etc.

THE `update` OBJECT (SimpleNamespace, produced by decode())
    Common fields (all query types):
      .status      bool   — False means the update was unparseable/ignored
      .query_type  str    — 'command' | 'callback' | 'inline' | 'unknown'
      .user_id     str    — sender's Telegram id (always a string)
      .first_name  str
      .last_name   str    — '' if absent
      .username    str    — '@handle' or '' if the user has none
    Command / edited_message updates also carry:
      .message     str    — text (or caption) of the message
      .message_id  int
      .chat_id     int
      .type        str    — chat type ('private' | 'group' | 'supergroup' | ...)
      .reply_to    obj|None — same shape (.message/.message_id/.user_id/.username/.chat_id)
                              when the command replies to another message, else None
    Callback (inline-button) updates carry instead:
      .data_query  str    — raw callback_data
      .query_id    str    — needed for bot.showAlert(...)
      .message_id  int    — the message the button lives on
      .chat_id     int
      .message     str    — text of the message the keyboard is attached to
      .origin_uid  str    — id of the user who triggered the ORIGINAL command
                            (used to stop other users from pressing your buttons)

    NOTE: posts without a sender (channel posts / anonymous admins send `sender_chat`,
    not `from`) are intentionally dropped as {status: False, query_type: 'unknown'}.

THE `self.cmd` OBJECT (set by commands(), only for 'command' updates)
      .is_command  bool
      .command     str    — command name, lowercased, without leading '/' or '@bot' suffix
      .args        str    — everything after the command (may be '')

THE `self.callback` OBJECT (set by callbacks_(), only for 'callback' updates)
      .command     str    — first token of callback_data
      .args        str    — the rest of callback_data (may be '')

MESSAGING RETURN SHAPE
    replyMessage / editMessage / sendMessage return a SimpleNamespace with:
      .message_id  int
      .message     str
      .chat_id     int
    ...or None if the Telegram API call failed (e.g. bot blocked, message too long).
    ALWAYS keep the returned object if you need to editMessage it later.
"""

class BotX:
    """Per-update webhook handler: decodes the update, registers and dispatches
    command/callback handlers, and wraps the Telegram Bot API + inline keyboards.
    See the module docstring above for the full data model and handler contract."""

    _CODER = "Coder: t.me/Vxsilisk - Shop: t.me/Sxgitario"   # do not remove — code attribution

    def __init__(self, query:str, error_logs_channel='') -> None:
        """Decode the incoming update, load config, and open the DB + HTTP sessions.

        query              : base64-encoded JSON of the raw Telegram update.
        error_logs_channel : chat id for #MessageError logs; falls back to
                             ERROR_CHANNEL then OWNER_ID from config.
        On any construction error it swallows the exception and reports it via raise_post()."""
        try:
            self.get_data()
            self.error_log_id = error_logs_channel or self.error_channel or self.owner_id
            self.commands_ = {}
            self.callbacks = {}
            self.cmd       = {}
            self.updater   = self.decode(updates=BotX.base64_decode(query))
            self.start     = time.time()
            self.raise_mes = None
            self.gestion   = gestion(self.db_host, self.db_name, self.db_user, self.db_pass, self.db_schema)
            self.curl      = _get_thread_curl()
        except Exception as error:
            self.raise_mes = str(error)
            self.raise_post()


    def __del__(self):
        # Close only the per-update DB cursor. Both the DB *connection* (gestion._acquire)
        # and the HTTP session (self.curl = _get_thread_curl) are thread-local and reused
        # across updates — closing them here would force a reconnect on every request.
        try:
            if hasattr(self, 'gestion') and self.gestion and hasattr(self.gestion, 'cursor'):
                self.gestion.cursor.close()
        except Exception: pass


    def _post_with_retry(self, url:str, data:dict=None, retries:int=3) -> dict:
        """POST to the Telegram API with automatic 429 retry (respects retry_after)."""
        result = {}
        for _ in range(retries):
            try:
                r = self.curl.post(url=url, data=data)
                result = r.json()
                if result.get('error_code') == 429:
                    wait = min(result.get('parameters', {}).get('retry_after', 10), 60)
                    time.sleep(wait + 1)
                    continue
                return result
            except Exception:
                time.sleep(2)
        return result


    def _load_env_file(self, file_path:pathlib.Path) -> None:
        """Load KEY=VALUE lines from an env file into os.environ (skips comments/blanks; never overrides an already-set var)."""
        if not file_path.exists() or not file_path.is_file(): return
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and os.getenv(key) is None:
                    os.environ[key] = value


    def get_data(self) -> None:
        """Read config from Model/config.env / .env into instance attrs: token URLs, DB creds,
        owner_id, error_channel, multi_mod (ASYNC_MODE), base_path. Raises if BOT_TOKEN is missing."""
        for env_path in [pathlib.Path().absolute() / 'Model' / 'config.env', pathlib.Path().absolute() / '.env']:
            self._load_env_file(env_path)
        token = os.getenv('BOT_TOKEN', '')
        if not token.strip(): raise Exception("BOT_TOKEN is empty, set Model/config.env")
        self.token    = "https://api.telegram.org/bot" + token
        self.filePath = "https://api.telegram.org/file/bot" + token + '/'
        self.db_host   = os.getenv('DB_HOST', '')
        self.db_name   = os.getenv('DB_NAME', '')
        self.db_user   = os.getenv('DB_USER', '')
        self.db_pass   = os.getenv('DB_PASS', '')
        self.db_schema = os.getenv('DB_SCHEMA', 'public')
        self.owner_id      = os.getenv('OWNER_ID', '')
        self.error_channel = os.getenv('ERROR_CHANNEL', '')
        self.multi_mod     = os.getenv('ASYNC_MODE', 'false').lower() in ['true', '1', 'yes']
        # JILL extras — tickets/references channels + public link buttons (set in config.env)
        self.support_channel = os.getenv('SUPPORT_CHANNEL', '') or self.error_channel or self.owner_id
        self.refs_channel    = os.getenv('REFS_CHANNEL', '')
        self.chat_url        = os.getenv('CHAT_URL', '')
        self.refs_url        = os.getenv('REFS_URL', '')
        self.base_path = pathlib.Path(__file__).resolve().parent.parent


    def compile_bot(self) -> None:
        """Main entrypoint: route the decoded update to its registered handler and exit.
        'command' updates dispatch to commandHandler(); 'callback' to callbackHandler().
        Unknown commands/callbacks are silently ignored. Any handler exception is caught,
        reported via raise_post(), and printed by out() so the process still exits cleanly."""
        try:
            if self.updater.query_type == 'command':
                self.commands()
                if self.cmd.is_command and self.cmd.command in self.commands_.keys():
                    self.commandHandler()
            elif self.updater.query_type == 'callback':
                self.callbacks_()
                if self.callback.command in self.callbacks.keys():
                    self.callbackHandler()
            return BotX.out(start=self.start)
        except Exception as error:
            if str(error) == "'NoneType' object has no attribute 'message_id'":
                return BotX.out(start=self.start)
            self.raise_mes = f"{traceback.format_exc().splitlines()[-3].replace('  ', '')}\n{traceback.format_exc().splitlines()[-2].replace('    ', '  ')}\n{traceback.format_exc().splitlines()[-1]}"
            self.raise_post()
            BotX.out(reason=self.raise_mes, start=self.start)


    def decode(self, updates:dict) -> object:
        """Turn a raw Telegram update dict into the `update` SimpleNamespace (see module docstring
        for every field per query_type). Posts without a 'from' sender are returned as
        {status: False, query_type: 'unknown'} so channel/anonymous posts are ignored, not crashed."""
        try:
            if 'callback_query' not in updates.keys() and 'inline_query' not in updates.keys() and 'edited_message' not in updates.keys():
                # Ignore posts without a sender (channel posts / anonymous admins use sender_chat, not 'from')
                if 'message' not in updates.keys() or 'from' not in updates['message']:
                    return self.dict_to_obj({'status': False, 'query_type': 'unknown'}, "update")
                return self.dict_to_obj({
                    'status'     : True,
                    'original'   : updates,
                    'query_type' : 'command',
                    'message'    : updates['message'].get('text', '') or updates['message'].get('caption', ''),
                    'message_id' : updates['message']['message_id'],
                    'user_id'    : str(updates['message']['from']['id']),
                    'first_name' : updates['message']['from']['first_name'],
                    'last_name'  : updates['message']['from'].get('last_name', ''),
                    'username'   : f"@{updates['message']['from']['username']}" if 'username' in updates['message']['from'] else '',
                    'chat_id'    : updates['message']['chat']['id'],
                    'type'       : updates['message']['chat']['type'],
                    'reply_to'   : self.dict_to_obj({
                        'message'    : updates['message']['reply_to_message'].get('text', ''),
                        'message_id' : updates['message']['reply_to_message']['message_id'],
                        'user_id'    : str(updates['message']['reply_to_message']['from']['id']),
                        'first_name' : updates['message']['reply_to_message']['from']['first_name'],
                        'last_name'  : updates['message']['reply_to_message']['from'].get('last_name', ''),
                        'username'   : f"@{updates['message']['reply_to_message']['from']['username']}" if 'username' in updates['message']['reply_to_message']['from'] else '',
                        'chat_id'    : updates['message']['reply_to_message']['chat']['id']}, 'reply_to') if ('reply_to_message' in updates['message'] and 'from' in updates['message']['reply_to_message']) else None}, "update")

            elif 'callback_query' in updates.keys():
                return self.dict_to_obj({
                    'status'    : True,
                    'original'  : updates,
                    'query_type': 'callback',
                    'data_query': updates['callback_query']['data'],
                    'query_id'  : updates['callback_query']['id'],
                    'message_id': updates['callback_query']['message']['message_id'],
                    'chat_id'   : updates['callback_query']['message']['chat']['id'],
                    'origin_uid': str(updates['callback_query']['message']['reply_to_message']['from']['id']) if ('reply_to_message' in updates['callback_query']['message'] and 'from' in updates['callback_query']['message']['reply_to_message']) else str(updates['callback_query']['from']['id']),
                    'user_id'   : str(updates['callback_query']['from']['id']),
                    'first_name': updates['callback_query']['from']['first_name'],
                    'last_name' : updates['callback_query']['from'].get('last_name', ''),
                    'username'  : f"@{updates['callback_query']['from']['username']}" if 'username' in updates['callback_query']['from'] else '',
                    'message'   : updates['callback_query']['message']['reply_to_message']['text'] if 'reply_to_message' in updates['callback_query']['message'] else ''}, "update")

            elif 'edited_message' in updates.keys() and 'from' in updates['edited_message']:
                return self.dict_to_obj({
                    'status'    : True,
                    'original'  : updates,
                    'query_type': 'command',
                    'message'   : updates['edited_message'].get('text', ''),
                    'message_id': updates['edited_message']['message_id'],
                    'user_id'   : str(updates['edited_message']['from']['id']),
                    'first_name': updates['edited_message']['from']['first_name'],
                    'last_name' : updates['edited_message']['from'].get('last_name', ''),
                    'username'  : f"@{updates['edited_message']['from']['username']}" if 'username' in updates['edited_message']['from'] else '',
                    'chat_id'   : updates['edited_message']['chat']['id'],
                    'type'      : updates['edited_message']['chat']['type'],
                    'reply_to'  : self.dict_to_obj({
                        'message'    : updates['edited_message']['reply_to_message'].get('text', ''),
                        'message_id' : updates['edited_message']['reply_to_message']['message_id'],
                        'user_id'    : str(updates['edited_message']['reply_to_message']['from']['id']),
                        'first_name' : updates['edited_message']['reply_to_message']['from']['first_name'],
                        'last_name'  : updates['edited_message']['reply_to_message']['from'].get('last_name', ''),
                        'username'   : f"@{updates['edited_message']['reply_to_message']['from']['username']}" if 'username' in updates['edited_message']['reply_to_message']['from'] else '',
                        'chat_id'    : updates['edited_message']['reply_to_message']['chat']['id']}, 'reply_to') if ('reply_to_message' in updates['edited_message'] and 'from' in updates['edited_message']['reply_to_message']) else None}, "update")

            else:
                return self.dict_to_obj({'status': False, 'query_type': 'unknown'}, "update")
        except Exception as error:
            self.raise_mes = f"{traceback.format_exc().splitlines()[-3].replace('  ', '')}\n{traceback.format_exc().splitlines()[-2].replace('    ', '  ')}\n{traceback.format_exc().splitlines()[-1]}"
            self.raise_post()
            return self.dict_to_obj({'status': False, 'query_type': 'Error', 'reason': error}, "update")


    def commands(self) -> None:
        """Parse self.updater.message into self.cmd (.is_command/.command/.args).
        A token is a command when its first char is not alphanumeric (e.g. '/bin 45'),
        the leading symbol and any '@botname' suffix are stripped, and the name is lowercased."""
        if self.updater.message:
            EXP = self.updater.message.split(' ', 1)
            if len(EXP[0]) > 0 and not EXP[0][0].isalpha() and not EXP[0][0].isdigit():
                command_raw = EXP[0][1:].lower()
                if '@' in command_raw: command_raw = command_raw.split('@')[0]
                self.cmd = self.dict_to_obj({'is_command': True, 'command': command_raw, 'args': EXP[1] if len(EXP) == 2 else ''}, "command")
            else:
                self.cmd = self.dict_to_obj({'is_command': False, 'msg': self.updater.message}, "command")
        else:
            self.cmd = self.dict_to_obj({'is_command': False, 'msg': ''}, "command")


    def callbacks_(self) -> None:
        """Split callback_data into self.callback (.command = first token, .args = the rest)."""
        EXP = self.updater.data_query.split(' ', 1)
        self.callback = self.dict_to_obj({'command': EXP[0], 'args': EXP[1] if len(EXP) > 1 else ''}, 'callback')


    def dict_to_obj(self, data:dict, name_class:str) -> object:
        """Wrap a dict as an attribute-access object. (name_class is unused; kept for call-site clarity.)"""
        return SimpleNamespace(**data)


    def addCommand(self, command:str, function:object) -> None:
        """Register a '/command' -> handler. `function` is a lazy 'module.path:func_name' route
        string (imported on first use) or a callable. Called as func(bot, update, gestion)."""
        self.commands_[command] = function


    def addCallback(self, callback:str, function:object) -> None:
        """Register an inline-button callback (matched on the first token of callback_data) -> handler.
        Same 'module:func' route / callable convention as addCommand."""
        self.callbacks[callback] = function


    def _load_handler(self, route:str) -> object:
        """Resolve a 'module.path:func_name' route to the callable, importing the module
        (falls back to loading it directly from its .py path if the dotted import fails)."""
        module_path, func_name = route.split(":")
        try:
            module = importlib.import_module(module_path)
        except Exception:
            file_path = pathlib.Path().absolute() / f"{module_path.replace('.', '/')}.py"
            if not file_path.exists(): raise
            spec = importlib.util.spec_from_file_location(module_path, str(file_path))
            if spec is None or spec.loader is None: raise
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return getattr(module, func_name)


    def commandHandler(self) -> None:
        """Resolve + invoke the command's handler, then sync the user's @username/name,
        then log the use (ONLY if the command exists in the `comandos` table — tools/gates;
        account commands like /start,/p,/myinfo are not counted). Errors are caught + reported."""
        try:
            handler = self.commands_[self.cmd.command]
            if isinstance(handler, str):
                handler = self._load_handler(handler)
                self.commands_[self.cmd.command] = handler
            handler(self, self.updater, self.gestion)
            self.gestion.sync_user(self.updater.user_id, self.updater.username, f"{self.updater.first_name} {self.updater.last_name}".strip())
            try:
                # Only count commands registered in the comandos table (toggleable tools + gates).
                # Account/bot commands (start, cmds, p, myinfo, cookie, info, admin panel...) are NOT counted.
                cmd_data = self.gestion.viewCmd(self.cmd.command)
                if isinstance(cmd_data, dict) and cmd_data.get('status') is True:
                    raw_type = cmd_data.get('type', 'unknown')
                    cmd_type = 'gate' if raw_type in ['auths', 'charged', 'specials', 'ccn', 'avs'] else raw_type
                    self.gestion.log_usage(self.updater.user_id, self.cmd.command, cmd_type)
            except Exception: pass
        except Exception:
            self.raise_mes = traceback.format_exc()
            self.raise_post()


    def callbackHandler(self) -> None:
        """Resolve + invoke the callback's handler, then sync the user's @username/name.
        Errors are caught + reported. (Callbacks are never counted in usage stats.)"""
        try:
            handler = self.callbacks[self.callback.command]
            if isinstance(handler, str):
                handler = self._load_handler(handler)
                self.callbacks[self.callback.command] = handler
            handler(self, self.updater, self.gestion)
            self.gestion.sync_user(self.updater.user_id, self.updater.username, f"{self.updater.first_name} {self.updater.last_name}".strip())
        except Exception:
            self.raise_mes = traceback.format_exc()
            self.raise_post()


    @classmethod
    def base64_decode(cls, arg) -> dict:
        """Decode the base64 CLI arg back into the raw Telegram update dict."""
        a = arg.encode('utf-8')
        b = base64.b64decode(a)
        return json.loads(b.decode('utf-8'))


    @classmethod
    def out(cls, start, reason:str = '') -> None:
        """Print the run outcome + elapsed time to stdout (green = OK, error text if `reason` given)."""
        if len(str(reason)):
            print("\n\n", Fore.MAGENTA + 'Bot Ejecutado Con Errores')
            print(Fore.WHITE + '------------------------------------')
            print(Fore.LIGHTCYAN_EX + ' Error pricipal:', Fore.YELLOW + str(reason))
            print(Fore.RED + ' Tiempo De Compilacion:', Fore.CYAN + str(round((time.time() - start), 1)), Fore.RED + 'segundos.', Fore.GREEN, "\n\n")
        else:
            print("\n\n", Fore.MAGENTA + 'Bot Ejecutado Correctamente')
            print(Fore.WHITE + '------------------------------------')
            print(Fore.CYAN + ' Tiempo De Compilacion:', Fore.YELLOW + str(round((time.time() - start), 1)), Fore.CYAN + 'segundos.', Fore.GREEN, "\n\n")


    @classmethod
    def getTime(cls) -> str:
        """Current local time as 'YYYY/MM/DD-HH:MM:SS' (used in error/audit logs)."""
        return datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S')


    @classmethod
    def bi(cls, text:str) -> str:
        """Convert ASCII letters to the sans-serif BOLD-ITALIC unicode font (𝙅𝙞𝙡𝙡).
        This is JILL_BOT's design-system font — use it for every label/title so the whole
        bot looks uniform. Non-letters (digits, symbols, emoji) pass through unchanged."""
        out = []
        for c in str(text):
            o = ord(c)
            if   65 <= o <= 90:  out.append(chr(0x1D63C + o - 65))   # A-Z
            elif 97 <= o <= 122: out.append(chr(0x1D656 + o - 97))   # a-z
            else:                out.append(c)
        return ''.join(out)


    #//! ── Inline keyboard builders ── compose as: replyMarkup(addRow(btn, btn), addRow(btn)) ──

    @classmethod
    def addButton(cls, text:str, callback:str = '', url:str = '', style:str = 'danger') -> dict:
        """Build one inline button. Pass `callback` for a callback_data button OR `url` for a link button."""
        type_c = 'url' if url else 'callback_data' if callback else ''
        data   = url if url else callback if callback else ''
        btn    = {'text': text, type_c: data}
        if style:
            btn['style'] = style
        return btn


    @classmethod
    def addRow(cls, *buttons) -> list:
        """Group buttons into one keyboard row (drops falsy buttons)."""
        return [b for b in buttons if b]


    @classmethod
    def replyMarkup(cls, *rows) -> dict:
        """Assemble rows into the reply_markup dict expected by replyMessage/editMessage."""
        return {'inline_keyboard': [r for r in rows if r]}


    #//! ── Telegram Bot API wrappers ──

    def getMe(self) -> object:
        """Return the bot's own account info (getMe) as an attribute-access object."""
        return self.dict_to_obj(self.curl.post(f"{self.token}/getMe").json(), "getme")


    def raise_post(self, message=None) -> None:
        """Send an error report (`message` or self.raise_mes) to the error/log channel. Never raises."""
        try:
            if message is not None: self.raise_mes = message
            raw = str(self.raise_mes) if self.raise_mes else 'Unknown error'
            if '429' in raw or 'Too Many Requests' in raw:
                return
            msg = raw.replace('>', '&#62;').replace('<', '&#60;')
            self.curl.post(url=f"{self.token}/sendMessage", data={'chat_id': self.error_log_id, 'text': f"#MessageError - {self.getTime()}\n\n<code>{msg}</code>", 'parse_mode': 'HTML'})
        except Exception: pass


    def sendAction(self, action:str) -> None:
        """Show a chat action in the current chat (e.g. 'typing'). Best-effort, never raises."""
        try: self._post_with_retry(url=f"{self.token}/sendChatAction", data={'chat_id': self.updater.chat_id, 'action': action})
        except Exception: pass


    def replyMessage(self, text:str, reply_markup:dict = None, preview:bool = True) -> object:
        """Reply (HTML) to the incoming message in its chat.
        Returns an object with .message_id/.message/.chat_id, or None if the API call failed.
        `reply_markup`: a replyMarkup(...) dict. `preview`: True disables link previews."""
        payload = {'chat_id': self.updater.chat_id, 'text': text, 'reply_to_message_id': self.updater.message_id, 'parse_mode': 'HTML', 'disable_web_page_preview': preview}
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        data = self._post_with_retry(url=f"{self.token}/sendMessage", data=payload)
        if 'result' in data:
            return self.dict_to_obj({'message_id': data['result']['message_id'], 'message': data['result'].get('text', ''), 'chat_id': data['result']['chat']['id']}, "return")
        if data.get('error_code') == 400 and 'message to be replied' in data.get('description', ''):
            payload.pop('reply_to_message_id', None)
            data = self._post_with_retry(url=f"{self.token}/sendMessage", data=payload)
            if 'result' in data:
                return self.dict_to_obj({'message_id': data['result']['message_id'], 'message': data['result'].get('text', ''), 'chat_id': data['result']['chat']['id']}, "return")
        self.raise_mes = str(data)
        self.raise_post()


    def editMessage(self, message_id:str, text:str, reply_markup:dict = None, preview:bool = True) -> object:
        """Edit a previous message's text/keyboard (HTML) in the current chat. `message_id` is the id
        returned by an earlier replyMessage/editMessage. Same return shape (or None on API failure)."""
        payload = {'chat_id': self.updater.chat_id, 'text': text, 'message_id': message_id, 'parse_mode': 'HTML', 'disable_web_page_preview': preview}
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        data = self._post_with_retry(url=f"{self.token}/editMessageText", data=payload)
        if 'result' in data:
            return self.dict_to_obj({'message_id': data['result']['message_id'], 'message': data['result'].get('text', ''), 'chat_id': data['result']['chat']['id']}, "return")
        if data.get('error_code') == 400 and 'message is not modified' in data.get('description', ''):
            return self.dict_to_obj({'message_id': message_id, 'message': text, 'chat_id': self.updater.chat_id}, "return")
        self.raise_mes = str(data)
        self.raise_post()


    def deleteMessage(self, chat_id:str, message_id:str) -> object:
        """Delete a message by chat_id + message_id. Returns the raw API response as an object."""
        return self.dict_to_obj(self._post_with_retry(url=f"{self.token}/deleteMessage", data={'chat_id': chat_id, 'message_id': message_id}), "return")


    def copyMessage(self, from_chat_id:str, message_id:str, to_chat_id:str, caption:str = None) -> object:
        """Copy ANY message (text/photo/doc…) into another chat WITHOUT the 'forwarded from' tag.
        Used to publish user references to the references channel. Returns the API response object."""
        payload = {'chat_id': to_chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
        if caption is not None:
            payload['caption'] = caption
            payload['parse_mode'] = 'HTML'
        return self.dict_to_obj(self._post_with_retry(url=f"{self.token}/copyMessage", data=payload), "return")


    def showAlert(self, text:str, callback_id:str, alert:bool = True) -> None:
        """Answer an inline-button tap. `callback_id` = update.query_id. alert=True shows a popup,
        alert=False a toast. Use it to reject presses (e.g. wrong user) or give quick feedback."""
        self._post_with_retry(url=f"{self.token}/answerCallbackQuery", data={'callback_query_id': callback_id, 'text': text, 'show_alert': alert})


    def sendMessage(self, text:str, chat_id:str, reply_markup:dict = None, preview:bool = True) -> object:
        """Send (HTML) to an ARBITRARY chat_id (unlike replyMessage which targets the current chat).
        Used by broadcast + audit logs. Returns an object with .message_id/.chat_id on success,
        or {status: False, error: ...} on failure — check `getattr(r, 'message_id', None)`."""
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': preview}
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        data = self._post_with_retry(url=f"{self.token}/sendMessage", data=payload)
        if 'result' in data:
            return self.dict_to_obj({'message_id': data['result']['message_id'], 'chat_id': data['result']['chat']['id']}, "return")
        return self.dict_to_obj({'status': False, 'error': data}, "return")


    def adminRegister(self, action:str, target:str = '', detail:str = '') -> None:
        """Audit trail: post a staff action to the log channel AND persist it to the `events`
        table (full queryable history — see /history). All fields are HTML-escaped; never raises."""
        u     = self.updater
        uname = f"@{u.username.lstrip('@')}" if getattr(u, 'username', '') else ''
        # Persist to the event history (survives even if the channel post fails)
        try:
            self.gestion.log_event(u.user_id, uname or u.user_id, action, target, detail)
        except Exception: pass
        try:
            if not self.error_log_id: return
            esc     = lambda s: str(s).replace('<', '&#60;').replace('>', '&#62;')
            command = getattr(getattr(self, 'cmd', None), 'command', '') or ''
            cargs   = getattr(getattr(self, 'cmd', None), 'args', '') or ''
            body = (
                f"#PanelAction - {self.getTime()}\n\n"
                f"<b><i>Admin:</i></b> <code>{u.user_id}</code> {esc(uname)}\n"
                f"<b><i>Action:</i></b> <code>{esc(action)}</code>\n"
            )
            if target: body += f"<b><i>Target:</i></b> <code>{esc(target)}</code>\n"
            body += f"<b><i>Command:</i></b> <code>/{esc(command)} {esc(cargs)}</code>"
            if detail: body += f"\n<b><i>Detail:</i></b> <code>{esc(detail)}</code>"
            self._post_with_retry(url=f"{self.token}/sendMessage", data={'chat_id': self.error_log_id, 'text': body, 'parse_mode': 'HTML'})
        except Exception: pass

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
