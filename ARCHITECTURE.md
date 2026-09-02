# Arquitectura del Sistema

## Diagrama General

```
┌─────────────────────────────────────────────────────────────┐
│                     Navegador (Cliente)                       │
│  React 19 + Next.js App Router + Tailwind CSS + shadcn/ui    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    proxy.ts (Middleware)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /dashboard/*  → requiere autenticación               │   │
│  │  /auth/*       → redirige si ya autenticado           │   │
│  │  /api/auth/*   → excluido                             │   │
│  │  /api/*        → sin restricción                      │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Pages (RSC) │ │ API Routes│ │  PHP API     │
│  Server      │ │ (REST)   │ │  (Mock)      │
│  Components  │ │          │ │              │
└──────┬───────┘ └────┬─────┘ └──────────────┘
       │              │
       └──────┬───────┘
              ▼
┌─────────────────────────┐
│     Prisma Client v7     │
│  (@prisma/adapter-pg)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     PostgreSQL           │
│  Tablas: users, gates,   │
│  keys, temp_mails        │
└─────────────────────────┘
```

## Modelo de Datos

### User (users)
```
┌──────────────────────────────────────┐
│ User                                 │
├──────────────────────────────────────┤
│ id: String (PK, cuid)                │
│ username: String (unique)            │
│ password: String (bcrypt)            │
│ telegramId: String                   │
│ rank: String (default: "user")       │
│ credits: Int (default: 0)            │
│ lives: Int                           │
│ deads: Int                           │
│ membershipExpiresAt: DateTime?       │
│ createdAt / updatedAt                │
├──────────────────────────────────────┤
│ HasMany: Key[] (redeemedKeys)        │
│ HasMany: Key[] (createdKeys)         │
└──────────────────────────────────────┘
```

### Key (keys)
```
┌──────────────────────────────────────┐
│ Key                                  │
├──────────────────────────────────────┤
│ id: String (PK, cuid)                │
│ key: String (unique, TRBL-...-...-...) │
│ credits: Int                         │
│ days: Int                            │
│ rank: String                         │
│ isUsed: Boolean (default: false)     │
│ usedById: String? (FK → User)        │
│ createdById: String? (FK → User)     │
│ createdAt / usedAt                   │
└──────────────────────────────────────┘
```

### Gate (gates)
```
┌──────────────────────────────────────┐
│ Gate                                 │
├──────────────────────────────────────┤
│ id: String (PK, cuid)                │
│ name: String                         │
│ category: String                     │
│   (auth|charged|ccn|special|shopify) │
│ description: String                  │
│ isActive: Boolean (default: true)    │
│ apiUrl: String (API endpoint)        │
│ creditsLive: Int (costo por live)    │
│ creditsDead: Int (costo por dead)    │
│ minRank: String (rango mínimo)       │
│ threads: Int (max hilos, 1-4)        │
│ stats: JSON (lives/deads/total/rate) │
│ createdAt                            │
└──────────────────────────────────────┘
```

### TempMail (temp_mails)
```
┌──────────────────────────────────────┐
│ TempMail                             │
├──────────────────────────────────────┤
│ id: String (PK, cuid)                │
│ userId: String (FK → User, indexed)  │
│ service: String (mailtm|guerrilla|...)  │
│ email: String                        │
│ type: String (jwt|sid|token|drop)    │
│ token / password / domain            │
│ sidToken / dropToken / sessionId     │
│ createdAt / updatedAt                │
└──────────────────────────────────────┘
```

## Flujo de Autenticación

```
1. POST /api/auth/register
   ├── Valida username (único)
   ├── Verifica key de activación
   ├── Crea usuario (bcrypt password)
   └── Marca key como usada (transacción)

2. POST /api/auth/callback/credentials
   ├── Busca usuario por username
   ├── Compara contraseña (bcrypt)
   ├── Verifica membresía (expiración)
   │   ├── Rango "baneado" → bloqueado
   │   └── Membresía expirada → rank: "user", credits: 0
   ├── Genera JWT { id, rank, membershipExpiresAt }
   └── Retorna session
```

## Flujo de Verificación de Tarjeta (Gate Check)

```
1. Cliente: POST /api/gates/[id]/check
   Body: { card, website, address, product }

2. Servidor: Validaciones en orden
   ├── Session válida ✓
   ├── Gate existe ✓
   ├── Usuario existe ✓
   ├── Gate activo o usuario admin ✓
   ├── Usuario no baneado ✓
   ├── Usuario con membresía (rank ≠ "user") ✓
   ├── Rango suficiente (userRank ≥ minRank) ✓
   └── Créditos suficientes (≥ min(creditsLive, creditsDead)) ✓

3. Forward a API externa (PHP o endpoint configurado)
   POST gate.apiUrl { card, website, address, product }
   Timeout: 15s

4. Procesar resultado
   ├── live  → deduct creditsLive,  user.lives++,  gate.lives++
   ├── dead  → deduct creditsDead,  user.deads++,  gate.deads++
   └── error → sin cambios

5. Actualizar estadísticas
   gate.stats = {
     lives: prev + 1,
     deads: prev + 1,
     total: prev + 1,
     successRate: round(lives / total * 100)
   }

6. Retornar { status, card, response, time_taken, creditsDeducted, creditsRemaining }
```

## Procesamiento Multi-Thread

El frontend procesa tarjetas en paralelo usando el número de hilos configurado:

```
const threadCount = gate.threads  // 1-4, configurable por admin

// Pool de procesamiento:
while (hay tarjetas pendientes) {
  const batch = tomar hasta threadCount tarjetas
  await Promise.all(batch.map(card => procesarTarjeta(card)))
  delay(200ms entre batches)
}
```

Cada tarjeta consume créditos individualmente. El multi-thread acelera el procesamiento pero no afecta el costo.

## Shopify Checkout Flow

```
1. Usuario ingresa URL del sitio Shopify
2. GET /api/gates/shopify-products → /products.json (limit=250)
3. Cliente: búsqueda y paginación (5 por página) en memoria
4. Usuario selecciona producto
5. Usuario configura dirección (opcional, solo US)
6. Al hacer check:
   POST /api/gates/[id]/check {
     card: "4111...|12|26|123",
     website: "https://tienda.myshopify.com",
     address: { street, city, state, zip, phone } | false,
     product: { id, handle, title, variant } | false
   }
```

## Sistema de Créditos

- Los créditos se descuentan por cada verificación
- Costo configurable por gate: `creditsLive` y `creditsDead`
- Si créditos < min(creditsLive, creditsDead), no se permite iniciar
- Si créditos < worstCase (n tarjetas × max costo), se muestra advertencia
- Recarga mediante keys de activación (TRBL-XXXX-XXXX-XXXX)

## Middleware y Seguridad

```
proxy.ts (Edge Middleware)
├── Rutas protegidas: /dashboard/*
│   └── Sin token → redirect /auth/login
├── Rutas de auth: /auth/login, /auth/sign-up
│   └── Con token → redirect /dashboard
└── Rutas excluidas: static, _next, api/auth

API Routes
├── Admin routes: checkAdmin() rank === "admin"
├── Manager routes: checkManager() rank in [admin, moderador, seller]
└── User routes: session.user.id (cualquier autenticado)
```

## PHP Mock API

```
POST php/api.php
Body: { card: "4111222233334444|12|26|123" }

Reglas determinísticas:
├── 4111 → live
├── 4000  → dead
├── 3 → error
└── Otros → random (60% live)

Response: {
  status: "live" | "dead",
  response: "mensaje descriptivo",
  time_taken: milisegundos,
  timestamp: ISO string,
  card_hash: sha256
}
```

## Estilo Visual (Cyberpunk Theme)

- Fondo: negro profundo (#050505)
- Acentos: rojo/cyan/naranja con glow effects
- Tipografía: monoespaciada (font-mono-cyber)
- Efectos: scanline animado, circuitos, glitch, matrix rain
- Bordes: cyber-clip (polígonos angulares)
- Estados: colores semánticos (verde=live, rojo=dead, amarillo=warning)
