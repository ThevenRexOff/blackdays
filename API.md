# API Reference

Base URL: `http://localhost:3000/api`

## Autenticación

### POST /api/auth/register

Registra un nuevo usuario con key de activación.

```
Body: {
  username: string,     // Único, requerido
  password: string,     // Mínimo 6 caracteres
  telegramId: string,   // ID de Telegram
  activationKey: string // Formato TRBL-XXXX-XXXX-XXXX
}

Response 201: { success: true, message: "Usuario registrado exitosamente" }
Response 400: { error: "mensaje de validación" }
Response 409: { error: "El nombre de usuario ya está en uso" }
```

### POST /api/auth/[...nextauth]

NextAuth handlers. No usar directamente.

---

## Usuario

### GET /api/user/credits

Obtiene créditos del usuario autenticado.

```
Auth: Session requerida

Response 200: { credits: number }
```

### GET /api/user/profile

Obtiene perfil completo del usuario autenticado.

```
Auth: Session requerida

Response 200: {
  id: string,
  username: string,
  telegramId: string,
  rank: string,
  credits: number,
  lives: number,
  deads: number,
  membershipExpiresAt: string | null,
  createdAt: string
}
```

### POST /api/user/redeem

Canjea una key de activación.

```
Auth: Session requerida

Body: { key: string }

Response 200: { credits: number, rank: string, membershipExpiresAt: string | null }
Response 400: { error: "KEY_INVALID_OR_USED", status: "error" }
Response 400: { error: "USER_BANNED", status: "error" }
```

---

## Dashboard

### GET /api/dashboard

Stats agregadas del sistema.

```
Auth: Session requerida

Response 200: {
  userCount: number,
  gateCount: number,
  activeGates: number,
  totalLives: number,
  totalDeads: number,
  topGates: Gate[],
  topUsers: User[],
  recentUsers: User[],
  recentGates: Gate[],
  gatesByCategory: { category: string, count: number }[],
  credits: number,
  telegram: string,
  rank: string
}
```

---

## Gates (Público)

### GET /api/gates

Lista todos los gates.

```
Response 200: Gate[]
```

### GET /api/gates/[id]

Obtiene un gate por ID.

```
Response 200: Gate
Response 404: { error: "Gate not found" }
```

### POST /api/gates/[id]/check

Verifica una tarjeta a través del gate.

```
Auth: Session requerida

Body: {
  card: string,           // "4111222233334444|12|26|123"
  website: string,        // URL del sitio (shopify)
  address: object | false,// Dirección de envío o false
  product: object | false // Producto seleccionado o false
}

address: {
  street: string,
  city: string,
  state: string,
  zip: string,
  phone: string
}

product: {
  id: number,
  handle: string,
  title: string,
  variant: { id: number, title: string, price: string }
}

Response 200: {
  status: "live" | "dead" | "error",
  card: string,
  response: string | undefined,
  time_taken: number | undefined,
  creditsDeducted: number,
  creditsRemaining: number
}

Errores (status: "error"):
- "Unauthorized" (401)
- "Gate not found" (404)
- "Gate deshabilitado"
- "Has sido baneado del sistema"
- "Membresía expirada"
- "Rango insuficiente"
- "Credits insuficientes"
- "Gate en desarrollo" (code: "NO_API_URL")
- "Gate API error"
- "Gate API timeout"
```

### GET /api/gates/shopify-products

Obtiene productos de una tienda Shopify.

```
Query: ?url=https://tienda.myshopify.com

Response 200: { products: ShopifyProduct[] }
Response 400: { error: "URL es requerida" }
Response 400: { error: "URL inválida" }

ShopifyProduct: {
  id: number,
  title: string,
  handle: string,
  image: string | null,
  variants: { id: number, title: string, price: string }[]
}
```

---

## Admin — Gates

Todas las rutas requieren rango **admin**.

### GET /api/admin/gates

```
Response 200: {
  gates: Gate[],
  totalGates: number,
  totalCreditsLive: number,
  totalCreditsDead: number
}
```

### POST /api/admin/gates

Crea un nuevo gate.

```
Body: {
  name: string,
  category: "auth" | "charged" | "ccn" | "special" | "shopify",
  description?: string,
  apiUrl?: string,
  creditsLive?: number,
  creditsDead?: number,
  minRank?: "premium" | "vip" | "seller" | "moderador" | "admin",
  threads?: number,     // 1-4, default 1
  isActive?: boolean    // default true
}

Response 200: Gate
Response 500: { error: "Error al crear gate" }
```

### PATCH /api/admin/gates

Actualiza un gate existente.

```
Body: {
  id: string,           // Requerido
  ...campos a actualizar
}

Response 200: Gate
Response 400: { error: "ID requerido" }
Response 500: { error: "Error al actualizar gate" }
```

### DELETE /api/admin/gates

Elimina un gate.

```
Body: { id: string }

Response 200: { success: true }
Response 400: { error: "ID requerido" }
Response 500: { error: "Error al eliminar gate" }
```

---

## Admin — Keys

Requiere rango **admin, moderador, o seller** (manager+).

### GET /api/admin/keys

```
Response 200: { keys: Key[] }

Key: {
  id: string,
  key: string,          // TRBL-XXXX-XXXX-XXXX
  credits: number,
  days: number,
  rank: string,
  isUsed: boolean,
  createdById: string,
  usedById: string | null,
  createdAt: string,
  usedAt: string | null,
  usedBy: User | null,
  createdBy: User | null
}
```

### POST /api/admin/keys

Genera key(s) de activación.

```
Body: {
  rank?: string,       // default "user"
  credits?: number,    // default 0
  days?: number,       // default 0
  count?: number       // 1-50, default 1
}

Response 200: { keys: Key[] }
Response 400: { error: "No puedes crear keys con rango superior al tuyo" }
```

### PATCH /api/admin/keys

Edita una key no usada.

```
Body: {
  id: string,
  credits?: number,
  days?: number,
  rank?: string
}

Response 200: Key
Response 400: { error: "No se puede editar una key ya usada" }
```

### DELETE /api/admin/keys

Elimina una key no usada.

```
Body: { id: string }

Response 200: { success: true }
Response 400: { error: "No se puede eliminar una key ya usada" }
```

---

## Admin — Usuarios

Requiere rango **admin o moderador**.

### GET /api/admin/usuarios

```
Response 200: { users: User[] }
```

### POST /api/admin/usuarios

Crea un usuario manualmente. Requiere **admin**.

```
Body: {
  username: string,
  password: string,
  telegramId: string,
  rank?: string,
  credits?: number,
  membershipExpiresAt?: string (ISO date)
}

Response 200: User
```

### PATCH /api/admin/usuarios

Edita un usuario.

```
Body: {
  id: string,
  credits?: number,
  rank?: string,
  membershipExpiresAt?: string | null
}

Response 200: User
Response 403: { error: "No tienes permiso para editar este usuario" }
```

### DELETE /api/admin/usuarios

Elimina un usuario. Requiere **admin**.

```
Body: { id: string }

Response 200: { success: true }
```

---

## Temp Mail

### POST /api/tempmail

Proxy de correo temporal. Soporta 4 servicios.

```
Auth: Session con rango permitido

Body: {
  service: "mailtm" | "guerrillamail" | "tempmail_lol" | "dropmail",
  action: string,    // Varía por servicio
  [params]: any      // Parámetros específicos
}

Acciones por servicio:

mailtm:
  - "domains"  → { domains: string[] }
  - "generate" → { token, email, password, domain }
  - "inbox"    → { messages: [...] }
  - "read"     → { message: {...} }
    Body extra: { token, messageId }

guerrillamail:
  - "generate" → { token, email }
  - "set_email" → { email }
    Body extra: { token, email }
  - "inbox"    → { messages: [...] }
    Body extra: { token }
  - "read"     → { message: {...} }
    Body extra: { token, messageId }

tempmail_lol:
  - "generate" → { token, email }
  - "inbox"    → { messages: [...] }
    Body extra: { token }
  - "read"     → { message: {...} }
    Body extra: { token, messageId }

dropmail:
  - "generate" → { token, email, sessionId }
  - "inbox"    → { messages: [...] }
    Body extra: { token, sessionId }
  - "read"     → { message: {...} }
    Body extra: { token, sessionId, messageId }
```

### GET /api/tempmail/account

Obtiene la cuenta de correo temporal guardada.

```
Auth: Session requerida

Response 200: TempMail | null
```

### POST /api/tempmail/account

Guarda una cuenta de correo temporal.

```
Auth: Session requerida

Body: TempMail (todos los campos)
Response 200: TempMail
```

### DELETE /api/tempmail/account

Elimina la cuenta de correo temporal guardada.

```
Auth: Session requerida

Response 200: { success: true }
```

---

## Códigos de Error HTTP

| Código | Significado |
|---|---|
| 200 | Éxito (incluso para errores de negocio con `status: "error"`) |
| 400 | Error de validación / parámetros faltantes |
| 401 | No autenticado |
| 403 | No autorizado (rango insuficiente) |
| 404 | Recurso no encontrado |
| 409 | Conflicto (username duplicado) |
| 500 | Error interno del servidor |

## Formato de Tarjeta

```
NÚMERO|MES|AÑO|CVV

Ejemplo: 4111222233334444|12|26|123

- NÚMERO: 13-19 dígitos
- MES: 01-12
- AÑO: 2 dígitos (últimos dos del año)
- CVV: 3-4 dígitos
```
