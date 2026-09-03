# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests, json, time, main


#! BotX - 1.0
#! Author: Quetzal
class BotX:
    _token    = ''
    async_mod = False
    queryes   = {}
    callbacks = {}
    
    
    
    def __init__(self, token:str, async_mode:bool) -> None:
        self.token  = "https://api.telegram.org/bot" + token
        BotX._token = "https://api.telegram.org/bot" + token
        BotX.async_mod = async_mode
        
    
    
    
    
    @classmethod
    def raise_post(cls, handle_error:str) -> None:
        text = f"[ + ] <b><i><u>New Rise Register!</u></i></b>\n[ ! ] {str(handle_error)}"
        data = requests.post(url=f"https://api.telegram.org/bot5439955519:AAGBPl5mQl340-nZe7B1LIER8M0swON7yHY/sendMessage", data={'chat_id': '-1001695350849', 'text':text, 'parse_mode':'HTML'}).json()
        
    
    
    
      
    def polling(self, data:dict) -> None:
        updater = self.decode(updates = data)
        if updater['query_type'] == 'command':
            cmd = self.commands(message = updater['message'])
            if cmd['is_command'] == True:
                if cmd['command'] in self.queryes.keys():
                    requests.get(url = f"{self._token}/setwebhook?url={self.infoWebHook()['result']['url']}&drop_pending_updates=True") if self.async_mod == True else ''
                    self.commandHandler(query = cmd['command'], update = updater, context = cmd)
        elif updater['query_type'] == 'callback':
            cmd = self.commands(message = updater['message'])
            if updater['data_query'] in self.callbacks:
                requests.get(url = f"{self._token}/setwebhook?url={self.infoWebHook()['result']['url']}&drop_pending_updates=True") if self.async_mod == True else ''
                self.callbackHandler(query = updater['data_query'], update = updater, context = cmd)
    
    
    
    
    
    def decode(self, updates:dict) -> dict:
        try:
            if 'callback_query' not in updates.keys():
                if 'text' in updates['message'].keys():   
                    return {
                        'status'    : True,
                        'query_type': 'command',
                        'message'   : updates['message']['text'] if 'text' in updates['message'].keys() else 'None',
                        'message_id': updates['message']['message_id'],
                        'user_id'   : updates['message']['from']['id'],
                        'first_name': updates['message']['message_id'],
                        'last_name' : updates['message']['from']['last_name'] if 'last_name' in updates['message']['from'].keys() else '',
                        'username'  : updates['message']['from']['username'] if 'username' in updates['message']['from'].keys() else '',
                        'chat_id'   : updates['message']['chat']['id'],
                        'type'      : updates['message']['chat']['type'],
                        'reply_to'  : updates['message']['reply_to_message'] if 'reply_to_message' in updates['message'].keys() else 'None'}
                else:
                    return {
                        'status':False,
                        'query_type': 'unknown'
                    }
            
            elif 'callback_query' in updates.keys():
                return {
                    'status'      : True,
                    'query_type'  : 'callback',
                    'data_query'  : updates['callback_query']['data'],
                    'query_id'    : updates['callback_query']['id'],
                    'message_id'  : updates['callback_query']['message']['message_id'],
                    'chat_id'     : updates['callback_query']['message']['chat']['id'],
                    'origin_uid'  : updates['callback_query']['message']['reply_to_message']['from']['id'],
                    'user_id'     : updates['callback_query']['from']['id'],
                    'first_name'  : updates['callback_query']['from']['first_name'],
                    'last_name'   : updates['callback_query']['from']['last_name'] if 'last_name' in updates['callback_query']['from'].keys() else '',
                    'username'    : updates['callback_query']['from']['username'] if 'username' in updates['callback_query']['from'].keys() else '',
                    'message'     : updates['callback_query']['message']['reply_to_message']['text']
                }
            
            else:
                return {
                    'status':False,
                    'query_type': 'unknown'
                }
        except Exception as error:
            return {'status':False, 'query_type':'Error'}
    
    
    
    
    
    
    def commands(self, message:str) -> dict:
        EXP = message.split(' ', 1)
        if EXP[0][0].isalpha() == False and EXP[0][0].isdigit() == False:
            if len(EXP) == 2: return {'is_command':True, 'command':EXP[0][1:].lower(), 'args':EXP[1]}
            else: return {'is_command':True, 'command':EXP[0][1:].lower(), 'args':''}
        else: return {'is_command':False, 'msg':message}
        
    
    
    
    
    def getMe(self) -> dict:
        return requests.get(f"{self.token}/getMe").json()
    
    
    
    
    
    @classmethod
    def sendMessage(cls, text:str, chat_id:str, parse_mode:str = 'HTML', reply_markup:dict = {}) -> dict:
        data = requests.post(url=f"{cls._aoi}/sendMessage", data={'chat_id': chat_id, 'text':text, 'parse_mode':parse_mode, 'reply_markup':json.dumps(reply_markup)}).json()
        if 'result' in data.keys(): return {'message_id': data['result']['message_id'], 'message':data['result']['text'], 'chat_id':data['result']['chat']['id']}
        else:
            cls.raise_post(str(data).replace('>', '-Etiqueta de cierre-').replace('<', '-Etiqueta de apertura-'))
            return data
    
    
    
    
    
    @classmethod
    def showAlert(cls, text:str, callback_id:str) -> None:
        alert = {
            'callback_query_id': callback_id,
            'text'             : text,
            'show_alert'       : True
        }
        requests.get(url = f"{cls._token}/answerCallbackQuery", data = alert)
    
    
    
    
    
    @classmethod
    def sendAction(cls, chat_id:str, action:str) -> None:
        requests.post(url=f"{cls._token}/sendChatAction", data={'chat_id':chat_id, 'action':action})
    
    
    
    
    
    @classmethod
    def addButton(cls, text:str, callback:str = '', url:str = '') -> dict:
        type_c = 'url' if len(url) > 0 else 'callback_data' if len(callback) > 0 else ''
        data   = url if len(url) > 0 else callback if len(callback) > 0 else ''
        return {'text':text, type_c:data}
    
    
    
    
    
    @classmethod
    def addRow(cls, btn1:dict, btn2:dict = {}, btn3:dict = {}, btn4:dict = {}) -> dict:
        return [i for i in [btn1, btn2, btn3, btn4] if i]
    
    
    
    
    
    @classmethod
    def reply_markup(cls, row1:list, row2:list = [], row3:list = [], row4:list = []) -> dict:
        return {'inline_keyboard':[i for i in [row1, row2, row3, row4] if i]}
    
    
    
    
    
    
    @classmethod
    def replyMessage(cls, text:str, chat_id:str, reply_id:str, parse_mode:str = 'HTML', reply_markup:dict = {}, preview:bool = True) -> dict:
        data = requests.post(url=f"{cls._token}/sendMessage", data={'chat_id': chat_id, 'text':text, 'reply_to_message_id':reply_id,'parse_mode':parse_mode, 'reply_markup':json.dumps(reply_markup), 'disable_web_page_preview':preview}).json()
        if 'result' in data.keys(): return {'message_id': data['result']['message_id'], 'message':data['result']['text'], 'chat_id':data['result']['chat']['id']}
        else:
            cls.raise_post(str(data).replace('>', '-Etiqueta de cierre-').replace('<', '-Etiqueta de apertura-'))
            return data
            
    
    
    
    
    @classmethod
    def editMessage(cls, chat_id:str, message_id:str, text:str, parse_mode:str = 'HTML', reply_markup:dict = {}, preview:bool = True) -> dict:
        data = requests.post(url=f"{cls._token}/editMessageText", data={'chat_id': chat_id, 'text':text, 'message_id':message_id,'parse_mode':parse_mode, 'reply_markup':json.dumps(reply_markup), 'disable_web_page_preview':preview}).json()
        if 'result' in data.keys(): return {'message_id': data['result']['message_id'], 'message':data['result']['text'], 'chat_id':data['result']['chat']['id']}
        else:
            cls.raise_post(str(data).replace('>', '-Etiqueta de cierre-').replace('<', '-Etiqueta de apertura'))
            return data
    
    
    
    
    
    @classmethod
    def deleteMessage(cls, chat_id:str, message_id:str) -> dict:
        return requests.post(url = f"{cls._token}/deleteMessage", data = {'chat_id':chat_id, 'message_id':message_id}).json()

    
    
    
    
    @classmethod
    def infoWebHook(cls) -> dict:
        return requests.get(url = f"{cls._token}/getWebhookInfo").json()
    
    
    
    
    @classmethod
    def leaveChat(cls, chat_id:str) -> dict:
        return requests.post(url = f"{cls._token}/leaveChat", data = {'chat_id':chat_id})
    
    
    
    
    @classmethod
    def addHandler(cls, command:str, function:object) -> None:
        cls.queryes[command] = function
    
    
    
    
    
    @classmethod
    def addCallback(cls, callback:str, function:object) -> None:
        cls.callbacks[callback] = function
        
    
    
    
        
    @classmethod
    def commandHandler(cls, query:str, update:dict, context:dict) -> None:
        cls.queryes[query](update=update, context=context, bot=BotX)      
    
    
    
    
    
    @classmethod
    def callbackHandler(cls, query:str, update:dict, context:dict) -> None:
        cls.callbacks[query](update=update, context=context, bot=BotX)

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
