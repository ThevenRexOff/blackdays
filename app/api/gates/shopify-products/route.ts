import { NextRequest, NextResponse } from 'next/server'

const productBlacklist = [
  'return', 'protection', 'exchange', 'warranty', 'extended warranty',
  'insurance', 'plan', 'membership', 'subscription', 'gift card',
  'store credit', 'credit', 'add-on', 'addon', 'fee', 'service',
  'unlimited return', 'free unlimited',
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const url = searchParams.get('url')

    if (!url) {
      return NextResponse.json({ error: 'URL es requerida' }, { status: 400 })
    }

    let baseUrl: string
    try {
      baseUrl = new URL(url).origin
    } catch {
      return NextResponse.json({ error: 'URL inválida' }, { status: 400 })
    }

    const response = await fetch(`${baseUrl}/products.json?limit=250`, {
      signal: AbortSignal.timeout(10000),
    })

    if (!response.ok) {
      return NextResponse.json({
        error: 'No se pudo acceder al sitio. Verifica que sea una tienda Shopify válida.',
        status: 'error',
      })
    }

    const data = await response.json()

    if (!data.products || !Array.isArray(data.products)) {
      return NextResponse.json({
        error: 'El sitio no devolvió productos válidos.',
        status: 'error',
      })
    }

    const products = data.products
      .filter((p: any) => {
        const title = (p.title ?? '').toLowerCase()
        return !productBlacklist.some(kw => title.includes(kw))
      })
      .map((p: any) => ({
        id: p.id,
        title: p.title,
        handle: p.handle,
        image: p.images?.[0]?.src || null,
        variants: (p.variants || []).map((v: any) => ({
          id: v.id,
          title: v.title,
          price: v.price,
        })),
      }))

    return NextResponse.json({ products })
  } catch (err) {
    console.error('Shopify products error:', err)
    return NextResponse.json({
      error: 'Error al obtener productos del sitio.',
      status: 'error',
    })
  }
}
