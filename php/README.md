# Shopify Checkout Automation

Automatización del flujo de checkout de Shopify vía GraphQL (Proposal → SubmitForCompletion → PollForReceipt). Construye los payloads dinámicamente extrayendo datos del HTML del checkout (`serialized-graphql`), eliminando la necesidad de hardcodear valores por tienda.

## Arquitectura

```
php/
├── shopify_gate.php          # Endpoint HTTP (POST) que recibe card+website y ejecuta checkout
├── stress_test.php           # Cliente de pruebas con curl_multi (requests simultáneos)
├── extract_checkout.php      # Debug: extrae y muestra serialized-graphql del HTML
├── composer.json             # Dependencias (fakerphp, capsolver) + classmap src/
├── proxies.txt               # Lista de proxies rotativos
├── gate_log.txt              # Log del flujo de checkout
├── php_errors.log            # Log de errores PHP
├── cache_geo.json            # Caché de geocodificación (LocationIQ)
├── src/
│   ├── CheckoutDataExtractor.php   # Parser del serialized-graphql + builders de payloads
│   ├── Checkout.php                # Fluent Builder pattern: Checkout::create($site)->card(...)->execute()
│   ├── ShopifyAPi.php              # Orquestador del flujo completo (checkout())
│   ├── CurlX.php                   # Cliente HTTP con proxy, cookies, headers
│   ├── FakeGenerator.php           # Generación de datos falsos (address, email, phone, UA)
│   ├── ProxyManager.php            # Rotación de proxies desde archivo
│   ├── userAgent.php               # User agents aleatorios
│   ├── Cache/                      # Cookies temporales por sesión
│   └── AddressRandom/              # Datos de direcciones
└── responses/                      # Payloads y respuestas de depuración
    ├── checkout.html               # HTML de checkout de referencia
    ├── payload.json                # Payload de Proposal de referencia
    ├── 2.json                      # Log de requests/responses de Proposal
    ├── 3.json                      # Log de requests/responses de SubmitForCompletion
    └── test_html.php               # Test unitario del extractor
```

## Flujo de Checkout

```
1. GEOCODING
   └── LocationIQ API → lat/lon de la dirección

2. PRODUCT
   └── GET /products.json → selecciona el producto más barato >= $1.00
       (filtra productos add-on: "return", "protection", "exchange", etc.)

3. CART ADD
   └── GET /cart/:variantId:1 → añade al carrito, obtiene HTML del checkout

4. EXTRACT
   └── Parsea serialized-graphql del HTML
   ├── session token, queue token, checkout token
   ├── operation IDs desde actions.js (Proposal, SubmitForCompletion)
   ├── currency, payment method identifier
   └── web build ID

5. CC TOKEN
   └── POST deposit.shopifycs.com/sessions → tokeniza la tarjeta

6. PROPOSAL (GraphQL)
   └── Construye payload con:
   ├── delivery (con destination address si requiere shipping)
   ├── merchandise (producto con stableId)
   ├── payment (paymentLines vacío, billing address)
   ├── buyerIdentity (currency, country, email)
   └── taxes (proposedAllocations: null)
   └── Envía Proposal → recibe sellerProposal con delivery handles

7. SUBMIT (GraphQL)
   └── Construye payload con datos del Proposal response
   ├── delivery con handle y amount
   ├── payment con CC token y amount
   ├── buyerIdentity
   └── taxes
   └── Envía SubmitForCompletion → recibe receipt ID

8. POLL
   └── PollForReceipt cada 2s hasta ProcessedReceipt o error

9. CLASSIFY
   ├── SUCCESS → "Live: Charged successfully"
   ├── INSUFFICIENT_FUNDS → "Live: INSUFFICIENT_FUNDS"
   ├── INCORRECT_CVC → "Live: INCORRECT_CVC"
   ├── 3D Secure → "Dead: 3D"
   ├── processingError.code → "Dead: {code}"
   └── Otro → "Dead: GENERIC_ERROR"
```

## GraphQL Endpoints

| Operación | Endpoint | ID Source |
|-----------|----------|-----------|
| `Proposal` | `/checkouts/internal/graphql/persisted?operationName=Proposal` | `actions.js` |
| `SubmitForCompletion` | `/checkouts/internal/graphql/persisted?operationName=SubmitForCompletion` | `actions.js` |
| `PollForReceipt` | `/checkouts/internal/graphql/persisted?operationName=PollForReceipt` | `hydrate.js` |

Los IDs de query (64 chars hex) se extraen de los archivos JS del checkout web (`actions.js`, `hydrate.js`) referenciados en el `systemjs-importmap`.

## Estrategia de Delivery

- **Proposal**: usa `deliveryStrategyMatchingConditions` (matching condicional)
- **SubmitForCompletion**: usa `deliveryStrategyByHandle` (handle específico)
- Si `buyerProposal.delivery.deliveryLines` está vacío (stores con shipping), se construye una línea por defecto:
  - `deliveryMethodTypes: ["SHIPPING"]` si `isShippingRequired = true`
  - `deliveryMethodTypes: ["NONE"]` si `isShippingRequired = false`
  - Incluye `destination` con la dirección completa + coordenadas cuando requiere shipping

## Problemas Encontrados y Soluciones

### 1. VALIDATION_CUSTOM — "This item may not be purchased by itself"
- **Causa**: El selector de producto más barato elegía productos add-on/return-protection (ej: "Free Unlimited Return for Store Credit or Exchanges" $1.98 en odionmenswear.com)
- **Fix**: `getMinimumPriceProductDetails()` ahora filtra productos cuyo título contenga palabras clave: `return`, `protection`, `exchange`, `warranty`, `insurance`, `gift card`, `store credit`, etc.
- **Manejo**: `VALIDATION_CUSTOM` en Proposal → agrega producto a `bad_products` + lanza retryable → el retry excluye el producto

### 2. TAX_NEW_TAX_MUST_BE_ACCEPTED
- **Causa**: Las tax allocations cambian entre Proposal y Submit. El Submit enviaba `proposedAllocations: null`
- **Fix**: Manejar como retryable — reintenta todo el flujo desde el principio con un nuevo Proposal

### 3. REQUIRED_ARTIFACTS_UNAVAILABLE + DESTINATION_ADDRESS_REQUIRED
- **Causa**: `buildProposalDelivery()` devolvía líneas de delivery vacías cuando `buyerProposal.delivery.deliveryLines` estaba vacío (común en productos físicos que requieren shipping)
- **Fix**: 
  - Si `deliveryLines` está vacío, construir línea por defecto con stableIds de merchandiseLines
  - Si `isShippingRequired = true`, incluir `destination` con address + coordenadas
  - `REQUIRED_ARTIFACTS_UNAVAILABLE` tratado como no-retryable

### 4. Delivery Handle vacío después de Proposal
- **Causa**: `getDeliveryHandle()` leía del extractor (inicializado con checkout HTML), pero los delivery handles solo están disponibles en la respuesta del Proposal API
- **Fix**: 
  - `sendProposal()` ahora retorna el `sellerProposal` actualizado
  - `updateFromProposalResponse()` actualiza el extractor con los datos frescos

### 5. PAYMENTS_UNACCEPTABLE_PAYMENT_AMOUNT en Proposal
- **Causa**: El Proposal envía `paymentLines: []` y `totalAmount: {any: true}`. Algunas stores devuelven este error como warning no-bloqueante
- **Solución**: Se deja pasar (fall-through) — no es un error fatal, el sellerProposal igual contiene datos válidos

### 6. WAITING_PENDING_TERMS en Proposal
- **Causa**: El Proposal necesita tiempo para procesarse (especialmente en stores con shipping)
- **Solución**: Retry automático hasta 3 veces con sleep(2) entre intentos

### 7. BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH
- **Causa**: La moneda detectada no coincide con la moneda de la tienda
- **Solución**: Extraer `presentmentCurrency` del response, forzar la moneda correcta, retry

### 8. MERCHANDISE_OUT_OF_STOCK
- **Causa**: Producto agotado
- **Solución**: Agregar a `bad_products` y retry con otro producto (hasta 2 intentos)

### 9. PAYMENTS_CREDIT_CARD_SESSION_ID (CC Token expirado)
- **Causa**: El token de tarjeta expira si el Submit tarda demasiado
- **Solución**: Obtener nuevo token, reemplazar en payload, retry

### 10. meta() quote stripping
- **Causa**: Los meta tags del checkout HTML pueden tener `&quot;` escapando comillas dobles
- **Fix**: `CheckoutDataExtractor::meta()` hace `trim($val, '"')` para limpiar

## Errores de Shopify y su Significado

| Código | Significado | Acción |
|--------|-------------|--------|
| `GENERIC_ERROR` | Decline genérico del banco | Card dead |
| `INSUFFICIENT_FUNDS` | Fondos insuficientes | Card live pero sin saldo |
| `INCORRECT_CVC` / `INCORRECT_CVV` | CVC incorrecto | Card live (datos erróneos) |
| `INVALID_CVC` | CVC inválido | Card live |
| 3D Secure (`/stripe/authentications/`) | Requiere autenticación 3D | Card dead (3D) |
| `CompletePaymentChallenge` | Challenge 3D Secure | Card dead (3D) |
| `VALIDATION_CUSTOM` | Producto no puede comprarse solo | Retry con otro producto |
| `TAX_NEW_TAX_MUST_BE_ACCEPTED` | Tax allocations cambiaron | Retry desde Proposal |
| `REQUIRED_ARTIFACTS_UNAVAILABLE` | Artifactos requeridos faltan | Fatal (no retry) |
| `DESTINATION_ADDRESS_REQUIRED` | Dirección de envío requerida | Fatal (fix code) |
| `DELIVERY_NO_DELIVERY_STRATEGY_AVAILABLE` | Sin estrategias de delivery | Fatal (fix code) |
| `MERCHANDISE_OUT_OF_STOCK` | Producto agotado | Retry con otro producto |
| `PAYMENTS_CREDIT_CARD_SESSION_ID` | Token de tarjeta expirado | Renew CC token, retry |
| `BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH` | Moneda incorrecta | Force currency, retry |
| `WAITING_PENDING_TERMS` | Proposal en proceso | Retry automático |
| `DELIVERY_DELIVERY_LINE_DETAIL_CHANGED` | Detalles de delivery cambiaron | Retry automático |
| `PAYMENTS_UNACCEPTABLE_PAYMENT_AMOUNT` | Monto no cubre total | Warning no-bloqueante |

## Uso

### Servidor (shopify_gate.php)

```bash
# Iniciar servidor PHP con logs activados (default)
php -S localhost:8080 shopify_gate.php

# Iniciar servidor PHP sin logs (producción)
SHOPIFY_DEBUG=false php -S 0.0.0.0:8080 shopify_gate.php
```

### Respuesta

```json
{
  "status": "dead",
  "response": "Dead: GENERIC_ERROR - [0/3]",
  "card": "5264120005531427|07|27|897",
  "time_taken": 32029
}
```

### Stress Test

```bash
php stress_test.php http://localhost:8080/shopify_gate.php
```

### Parámetros opcionales de shopify_gate.php

```json
{
  "card": "cc|mes|ano|cvv",
  "website": "https://ejemplo.com",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "phone": "+12125551234"
  },
  "email": "cliente@ejemplo.com",
  "product": {
    "id": 123,
    "handle": "product-handle",
    "title": "Product Name",
    "variant": {
      "id": 456,
      "title": "Variant Title",
      "price": "19.99"
    }
  }
}
```

### Fluent Builder (Checkout.php)

```php
$result = Checkout::create('https://ejemplo.com')
    ->card('5264120005531427', '07', '27', '897')
    ->address('123 Main St', 'New York', 'NY', '10001')
    ->phone('+12125551234')
    ->name('John', 'Doe')
    ->email('cliente@ejemplo.com')
    ->execute();

echo $result; // "Dead: GENERIC_ERROR - [0/3]"
```

## Proxy

Los proxies se configuran en `proxies.txt` con formato `user:pass@host:port`. El `ProxyManager` rota automáticamente en cada retry.

## Debug / Producción

Controlado por la constante `SHOPIFY_DEBUG` (variable de entorno):

| Entorno | Logs (gate_log.txt) | Responses (2.json, 3.json, poll.json) | Error log PHP |
|---------|-------------------|---------------------------------------|---------------|
| `SHOPIFY_DEBUG=true` o no definido | ✅ Escribe | ✅ Escribe | ✅ Activo |
| `SHOPIFY_DEBUG=false` | ❌ No escribe | ❌ No escribe | ❌ Inactivo |

`cache_geo.json` siempre se escribe (mejora rendimiento evitando geocoding repetido).

Para producción:
```bash
SHOPIFY_DEBUG=false php -S 0.0.0.0:8080 shopify_gate.php
```

## Dependencias

- PHP 8.1+
- `fakerphp/faker` — generación de datos falsos
- `greezlu/capsolver-php` — resolución de captchas (opcional)
- LocationIQ API gratuita — geocodificación de direcciones

## Estructura de Datos Clave

### serialized-graphql (checkout HTML)

El HTML contiene un meta tag `<meta name="serialized-graphql" content="...">` con JSON. Este JSON tiene 5+ top-level keys; se itera para encontrar la que contiene `session.negotiate.result`:

```json
{
  "[key]": {
    "session": {
      "checkoutSessionIdentifier": "...",
      "negotiate": {
        "result": {
          "queueToken": "...",
          "buyerProposal": { ... },
          "sellerProposal": { ... }
        }
      }
    },
    "shop": { ... }
  }
}
```

### buyerProposal vs sellerProposal

- `buyerProposal` — estado inicial del checkout (lo que el comprador propone)
- `sellerProposal` — respuesta del vendedor (contiene payment methods, delivery handles, tax, totals)
- Ambos son necesarios para construir los payloads de Proposal y Submit
