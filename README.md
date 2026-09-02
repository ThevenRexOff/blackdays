# Los Piratas de Trebol — Dashboard

Sistema de verificación de tarjetas con dashboard administrativo. Plataforma web con autenticación, gestión de créditos, múltiples gates de verificación, y panel de administración completo.

## Tech Stack

| Capa | Tecnología |
|---|---|
| Framework | Next.js 16 (App Router) |
| Lenguaje | TypeScript 5.7 |
| UI | React 19 + Tailwind CSS v4 + shadcn/ui |
| Base de Datos | PostgreSQL + Prisma ORM v7 |
| Autenticación | NextAuth v5 (Credentials + JWT) |
| Validación | Zod + react-hook-form |
| Iconos | Lucide React |
| Gráficos | Recharts |
| Tema | Ciberpunk oscuro (rojo/negro) |

## Estructura del Proyecto

```
├── app/                      # Next.js App Router
│   ├── api/                  # API Routes (REST)
│   │   ├── auth/             # Registro + NextAuth
│   │   ├── user/             # Créditos, perfil, canje
│   │   ├── gates/            # Gates públicos + check
│   │   ├── admin/            # Admin: gates, keys, usuarios
│   │   ├── tempmail/         # Proxy de correos temporales
│   │   └── dashboard/        # Stats agregadas
│   ├── auth/                 # Login / Sign-up
│   └── dashboard/            # Panel principal
│       ├── gates/            # Lista + checker individual
│       ├── perfil/           # Perfil de usuario
│       ├── tempmail/         # Cliente de correo temporal
│       └── admin/            # Panel de administración
├── components/               # Componentes reutilizables
│   ├── ui/                   # shadcn/ui (57+ componentes)
│   ├── dashboard/            # Sidebar, Header, Stats
│   └── auth/                 # Particle network
├── hooks/                    # useSound, useCounter, useMobile
├── lib/                      # auth, prisma, toast, utils
├── prisma/                   # Schema + seed data
├── php/                      # API PHP mock para testing
└── public/                   # Imágenes, iconos
```

## Requisitos

- Node.js 20+
- pnpm
- PostgreSQL

## Instalación

```bash
# Clonar e instalar
pnpm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus credenciales:
#   DATABASE_URL="postgresql://user:pass@localhost:5432/db"
#   AUTH_SECRET="base64-random-string"

# Crear base de datos y migrar
pnpm prisma db push

# Seed de datos de prueba (opcional)
pnpm prisma db seed

# Iniciar en desarrollo
pnpm dev
```

## Variables de Entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | URL de conexión PostgreSQL |
| `AUTH_SECRET` | Sí | Secreto para firmar tokens JWT |
| `AUTH_TRUST_HOST` | Sí | Confiar en host (necesario para proxies/ngrok) |

## Comandos

| Comando | Descripción |
|---|---|
| `pnpm dev` | Servidor de desarrollo |
| `pnpm build` | Build de producción |
| `pnpm start` | Iniciar en producción |
| `pnpm prisma db push` | Sincronizar schema con BD |
| `pnpm prisma db seed` | Insertar datos de prueba |
| `pnpm prisma generate` | Regenerar cliente Prisma |

## Jerarquía de Rangos

```
baneado < user < premium < vip < seller < moderador < admin
```

- **user**: Sin membresía activa, no puede usar gates
- **premium**: Acceso a gates básicos
- **vip**: Acceso a gates intermedios
- **seller**: Acceso a gates avanzados + panel admin
- **moderador**: Gestión de usuarios y keys
- **admin**: Control total del sistema

## Funcionalidades Principales

### Verificación de Tarjetas (Gates)
- 5 categorías: auth, charged, ccn, special, shopify
- Procesamiento multi-thread (1-4 hilos)
- Costos configurables por resultado (live/dead)
- Restricción por rango mínimo
- Estadísticas globales en tiempo real

### Shopify Checkout
- Configuración de sitio y producto
- Selección de producto con búsqueda y paginación (5 por página)
- Envío de dirección de envío (solo US)

### Administración
- CRUD completo de gates, usuarios y keys
- Keys de activación (formato TRBL-XXXX-XXXX-XXXX)
- Gestión de créditos y membresías

### Correo Temporal
- 4 servicios: Mail.tm, Guerrilla Mail, TempMail.lol, DropMail.me
- Persistencia de cuenta por usuario

## Documentación Adicional

- [Arquitectura del Sistema](./ARCHITECTURE.md)
- [API Reference](./API.md)
