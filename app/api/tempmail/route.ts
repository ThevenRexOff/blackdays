import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'

const ALLOWED_RANKS = ['user', 'premium', 'vip', 'moderador', 'seller', 'admin']

const BROWSER_HEADERS: HeadersInit = {
  'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
  Accept: 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.9',
}

// mail.tm blocks Vercel datacenter IPs (HTTP 500). We proxy it through the VPS,
// whose IP is not blocked. Vercel -> VPS -> api.mail.tm.
const MAILTM_PROXY = 'http://169.58.148.219:8080/apis/tmail_proxy'

async function safeFetch<T = Record<string, unknown>>(url: string, options: RequestInit = {}): Promise<T> {
  const merged: RequestInit = {
    ...options,
    signal: AbortSignal.timeout(15_000),
    headers: {
      ...BROWSER_HEADERS,
      ...(options.headers ?? {}),
    },
  }

  let res: Response
  try {
    res = await fetch(url, merged)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    throw new Error(`Error de red: ${msg}`)
  }

  if (!res.ok) {
    const hostname = new URL(url).hostname
    const text = await res.text()
    const body = text.slice(0, 300)
    throw new Error(`HTTP ${res.status} de ${hostname}: ${body}`)
  }

  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('json')) {
    return res.json() as Promise<T>
  }
  return (await res.text()) as unknown as T
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user?.rank || !ALLOWED_RANKS.includes(session.user.rank as string)) {
    return NextResponse.json({ error: 'Acceso denegado' }, { status: 403 })
  }

  const body = await req.json()
  const { service, action, params } = body

  try {
    // ─── mail.tm (proxied through VPS — see MAILTM_PROXY) ────────────
    if (service === 'mailtm') {
      const proxyRes = await fetch(MAILTM_PROXY, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, params }),
        signal: AbortSignal.timeout(20_000),
      })
      const proxyData = (await proxyRes.json()) as Record<string, unknown>

      if (!proxyData.status) {
        throw new Error((proxyData.error as string) || `Error de mail.tm vía proxy: HTTP ${proxyRes.status}`)
      }

      if (action === 'domains') {
        const d = (proxyData.domains ?? []) as { domain: string; isActive: boolean }[]
        return NextResponse.json({ domains: d })
      }

      if (action === 'generate') {
        return NextResponse.json({
          email: proxyData.email,
          token: proxyData.token,
          password: proxyData.password,
          domain: proxyData.domain,
          type: 'jwt',
        })
      }

      if (action === 'inbox') {
        return NextResponse.json({ messages: proxyData.messages ?? [], type: 'jwt' })
      }

      if (action === 'read') {
        return NextResponse.json({ message: proxyData.message, type: 'jwt' })
      }

      throw new Error(`Acción mail.tm no soportada: ${action}`)
    }

    // ─── Guerrilla Mail ────────────────────────────────────────────
    if (service === 'guerrillamail') {
      const base = 'https://api.guerrillamail.com/ajax.php'

      if (action === 'generate') {
        const url = `${base}?f=get_email_address`
        const data = await safeFetch<{ email_addr: string; sid_token: string; alias: string }>(url)
        return NextResponse.json({
          email: data.email_addr,
          sidToken: data.sid_token,
          alias: data.alias,
          type: 'sid',
        })
      }

      if (action === 'set_email') {
        const { sidToken, emailUser } = params as { sidToken: string; emailUser: string }
        const data = await safeFetch<{ email_addr: string; sid_token: string }>(
          `${base}?f=set_email_user&sid_token=${encodeURIComponent(sidToken)}&email_user=${encodeURIComponent(emailUser)}`
        )
        return NextResponse.json({ email: data.email_addr, sidToken: data.sid_token, type: 'sid' })
      }

      if (action === 'inbox') {
        const { sidToken } = params as { sidToken: string }
        const data = await safeFetch<{
          list: { mail_id: string; mail_from: string; mail_subject: string; mail_excerpt: string; mail_timestamp: string; read: number }[]
          sid_token: string
        }>(`${base}?f=get_email_list&sid_token=${encodeURIComponent(sidToken)}&offset=0`)
        const messages = (data.list ?? []).map((m) => ({
          id: m.mail_id,
          from: m.mail_from,
          subject: m.mail_subject,
          intro: m.mail_excerpt,
          date: new Date(Number(m.mail_timestamp) * 1000).toISOString(),
          seen: m.read === 1,
        }))
        return NextResponse.json({ messages, sidToken: data.sid_token, type: 'sid' })
      }

      if (action === 'read') {
        const { sidToken, id } = params as { sidToken: string; id: string }
        const data = await safeFetch<{
          mail_id: string
          mail_from: string
          mail_subject: string
          mail_excerpt: string
          mail_timestamp: string
          mail_body: string
          read: number
        }>(`${base}?f=fetch_email&sid_token=${encodeURIComponent(sidToken)}&email_id=${id}`)
        return NextResponse.json({
          message: {
            id: data.mail_id,
            from: data.mail_from,
            subject: data.mail_subject,
            intro: data.mail_excerpt,
            date: new Date(Number(data.mail_timestamp) * 1000).toISOString(),
            textBody: data.mail_body,
            seen: data.read === 1,
          },
          type: 'sid',
        })
      }
    }

    // ─── TempMail.lol ──────────────────────────────────────────────
    if (service === 'tempmail_lol') {
      if (action === 'generate') {
        const data = await safeFetch<{ address: string; token: string }>('https://api.tempmail.lol/v2/inbox/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}',
        })
        return NextResponse.json({ email: data.address, token: data.token, type: 'token' })
      }

      if (action === 'inbox') {
        const { token } = params as { token: string }
        const data = await safeFetch<{ emails: Record<string, unknown>[]; expired: boolean }>(
          `https://api.tempmail.lol/v2/inbox?token=${encodeURIComponent(token)}`
        )
        const messages = (data.emails ?? []).map((e: Record<string, unknown>) => ({
          id: e.id,
          from: e.from,
          subject: e.subject,
          textBody: e.body,
          html: e.html ? [e.html as string] : undefined,
          date: e.date,
          intro: typeof e.subject === 'string' ? (e.subject as string).slice(0, 80) : '',
        }))
        return NextResponse.json({ messages, type: 'token' })
      }

      if (action === 'read') {
        const { token } = params as { token: string }
        const data = await safeFetch<{ emails: Record<string, unknown>[]; expired: boolean }>(
          `https://api.tempmail.lol/v2/inbox?token=${encodeURIComponent(token)}`
        )
        const { id } = params as { id: string; token: string }
        const found = (data.emails ?? []).find((e: Record<string, unknown>) => e.id === id)
        if (!found) throw new Error('Mensaje no encontrado')
        return NextResponse.json({
          message: {
            id: found.id,
            from: found.from,
            subject: found.subject,
            textBody: found.body,
            html: found.html ? [found.html as string] : undefined,
            date: found.date,
          },
          type: 'token',
        })
      }
    }

    // ─── DropMail.me ────────────────────────────────────────────────
    if (service === 'dropmail') {
      if (action === 'generate') {
        const tokenRes = await safeFetch<{ token: string }>('https://dropmail.me/api/token/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: 'af', lifetime: '1h' }),
        })
        const dmToken = tokenRes.token

        const graphql = `mutation{introduceSession{id,expiresAt,addresses{address,restoreKey,id,domain{name}}}}`
        const sessData = await safeFetch<{ data: { introduceSession: { id: string; addresses: { address: string; domain: { name: string } }[] } } }>(
          `https://dropmail.me/api/graphql/${dmToken}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ query: graphql }),
          }
        )
        const session = sessData.data.introduceSession
        const addr = session.addresses[0]
        const email = addr.address.includes('@') ? addr.address : `${addr.address}@${addr.domain.name}`
        return NextResponse.json({
          email,
          dropToken: dmToken,
          sessionId: session.id,
          type: 'dropmail',
        })
      }

      if (action === 'inbox') {
        const { dropToken, sessionId } = params as { dropToken: string; sessionId: string }
        const query = `query($id: ID!){session(id:$id){id,expiresAt,mails{id,fromAddr,toAddr,headerSubject,text,html,receivedAt}}}`
        const data = await safeFetch<{ data: { session: { mails: Record<string, unknown>[] } } }>(
          `https://dropmail.me/api/graphql/${dropToken}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ query, variables: JSON.stringify({ id: sessionId }) }),
          }
        )
        const messages = (data.data.session.mails ?? []).map((m: Record<string, unknown>) => ({
          id: m.id,
          from: m.fromAddr,
          subject: m.headerSubject,
          textBody: m.text,
          html: m.html ? [m.html as string] : undefined,
          date: m.receivedAt,
          intro: typeof m.headerSubject === 'string' ? (m.headerSubject as string).slice(0, 80) : '',
        }))
        return NextResponse.json({ messages, type: 'dropmail' })
      }

      if (action === 'read') {
        const { dropToken, sessionId, id } = params as { dropToken: string; sessionId: string; id: string }
        const query = `query($id: ID!){session(id:$id){id,expiresAt,mails{id,fromAddr,toAddr,headerSubject,text,html,receivedAt}}}`
        const data = await safeFetch<{ data: { session: { mails: Record<string, unknown>[] } } }>(
          `https://dropmail.me/api/graphql/${dropToken}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ query, variables: JSON.stringify({ id: sessionId }) }),
          }
        )
        const found = (data.data.session.mails ?? []).find((m: Record<string, unknown>) => m.id === id)
        if (!found) throw new Error('Mensaje no encontrado')
        return NextResponse.json({
          message: {
            id: found.id,
            from: found.fromAddr,
            subject: found.headerSubject,
            textBody: found.text,
            html: found.html ? [found.html as string] : undefined,
            date: found.receivedAt,
          },
          type: 'dropmail',
        })
      }
    }

    return NextResponse.json({ error: 'Acción o servicio no soportado' }, { status: 400 })
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    console.error('tempmail error:', msg)
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
