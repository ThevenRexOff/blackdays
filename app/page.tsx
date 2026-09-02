'use client'

import { useSession } from 'next-auth/react'
import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import {
  Zap,
  Shield,
  Users,
  Activity,
  CheckCircle2,
  Terminal,
  ArrowRight,
  Cpu,
  Server,
  Lock,
  Radio,
  Flame,
  HelpCircle,
  Menu,
  X
} from 'lucide-react'
import { DashboardParticles } from '@/components/dashboard/dashboard-particles'

export default function LandingPage() {
  const { data: session, status } = useSession()
  const [isYearly, setIsYearly] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeFaq, setActiveFaq] = useState<number | null>(null)

  const toggleFaq = (index: number) => {
    setActiveFaq(activeFaq === index ? null : index)
  }

  // Pricing Plans
  const plans = [
    {
      name: 'Cabina de Grumete',
      tag: 'Básico',
      description: 'Ideal para exploradores novatos y entusiastas de las redes.',
      priceMonthly: 0,
      priceYearly: 0,
      features: [
        '1 Gateway básico activo',
        'Estadísticas con delay de 5 min',
        'Soporte comunitario en Telegram',
        'Cifrado de datos básico',
        'Ancho de banda limitado a 5MB/s'
      ],
      cta: 'Empezar Gratis',
      popular: false,
      color: 'border-gray-800'
    },
    {
      name: 'Navío de Oficial',
      tag: 'Recomendado',
      description: 'Optimizado para navegantes frecuentes con flujos constantes.',
      priceMonthly: 49,
      priceYearly: 39,
      features: [
        '10 Gateways avanzados activos',
        'Estadísticas en tiempo real',
        'Acceso prioritario a nuevos Gates',
        'Canal de soporte exclusivo 24/7',
        'Ancho de banda de 50MB/s',
        'Logs históricos guardados por 7 días'
      ],
      cta: 'Adquirir Patente',
      popular: true,
      color: 'border-purple-900/50'
    },
    {
      name: 'Galeón de Capitán',
      tag: 'Flota Élite',
      description: 'Para comandantes de flotas enteras y operaciones masivas.',
      priceMonthly: 149,
      priceYearly: 119,
      features: [
        'Gateways ilimitados',
        'Prioridad de ejecución ultra-alta',
        'Logs históricos ilimitados',
        'Acceso API directa sin restricciones',
        'Panel de control de amenazas avanzado',
        'Soporte dedicado personalizado'
      ],
      cta: 'Comandar Flota',
      popular: false,
      color: 'border-gray-800'
    }
  ]

  const faqs = [
    {
      q: '¿Qué es JILL CHK - Dashboard?',
      a: 'Es una plataforma centralizada de monitoreo y administración de gateways de red con un enfoque de alto rendimiento, diseñada con una interfaz cyberpunk futurista inspirada en la navegación pirata digital.'
    },
    {
      q: '¿Puedo cambiar de plan en cualquier momento?',
      a: '¡Por supuesto, marinero! Puedes ascender o descender de rango (plan) en cualquier momento desde tu panel de facturación. Los cambios se prorratearán inmediatamente.'
    },
    {
      q: '¿Cómo garantizan la seguridad de mis datos?',
      a: 'Toda nuestra red opera bajo protocolos criptográficos avanzados con enrutamiento dinámico. Tu conexión y credenciales están seguras detrás de nuestro escudo de cifrado cuántico-pirata.'
    },
    {
      q: '¿Qué formas de pago aceptan?',
      a: 'Aceptamos tarjetas de crédito tradicionales, transferencias y la mayoría de criptomonedas populares como BTC, ETH, USDT y SOL a través de nuestro gateway de pago seguro.'
    }
  ]

  return (
    <div className="relative min-h-screen bg-[#050505] text-white overflow-hidden selection:bg-purple-600/30 selection:text-white">
      {/* Background Grid & Scanline */}
      <div className="absolute inset-0 circuit-bg opacity-40 pointer-events-none z-0" />
      <div className="absolute inset-0 animate-scan-line bg-gradient-to-b from-transparent via-purple-600/3 to-transparent h-[10px] w-full pointer-events-none z-0" />

      {/* Glow Effects */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-3xl pointer-events-none z-0" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-purple-900/5 rounded-full blur-3xl pointer-events-none z-0" />

      {/* Dynamic Background Particles */}
      {/* <DashboardParticles /> */}

      {/* Top Header / Navigation */}
      <header className="relative z-50 border-b border-purple-900/30 bg-[#0a0a0fc0] backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center">
              <svg className="absolute inset-0 h-full w-full" viewBox="0 0 56 56">
                <path d="M28,2 L52,15 L52,41 L28,54 L4,41 L4,15 Z" fill="rgba(147, 51, 234, 0.1)" stroke="rgba(147, 51, 234, 0.6)" strokeWidth="1.5" />
              </svg>
              <Flame className="h-5 w-5 text-purple-500 animate-pulse" />
            </div>
            <div>
              <span className="font-mono-cyber font-black tracking-widest text-lg bg-gradient-to-r from-white via-gray-300 to-purple-500 bg-clip-text text-transparent">
                JILL
              </span>
              <span className="font-mono-cyber text-[9px] block text-purple-500 tracking-[0.3em] -mt-1 font-bold">
                CC CHECKER
              </span>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-mono-cyber">
            <a href="#preview" className="text-gray-400 hover:text-purple-500 transition-colors">Ver</a>
            <a href="#features" className="text-gray-400 hover:text-purple-500 transition-colors">Características</a>
            <a href="#pricing" className="text-gray-400 hover:text-purple-500 transition-colors">Precios</a>
            <a href="#faq" className="text-gray-400 hover:text-purple-500 transition-colors">FAQ</a>
          </nav>

          <div className="hidden md:flex items-center gap-4">
            {status !== 'loading' && (
              <>
                {session ? (
                  <Link
                    href="/dashboard"
                    className="font-mono-cyber text-xs uppercase px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold border border-purple-500 transition-all duration-300 hover:shadow-[0_0_20px_rgba(147,51,234,0.5)] cyber-clip-alt"
                  >
                    Ir al Dashboard
                  </Link>
                ) : (
                  <>
                    <Link
                      href="/auth/login"
                      className="font-mono-cyber text-xs uppercase px-4 py-2 text-gray-300 hover:text-white transition-colors"
                    >
                      Iniciar Sesión
                    </Link>
                    <Link
                      href="/auth/login"
                      className="font-mono-cyber text-xs uppercase px-5 py-2.5 bg-[#0e0e13] hover:bg-purple-950/20 text-purple-500 font-bold border border-purple-900/50 hover:border-purple-500 transition-all duration-300 cyber-clip"
                    >
                      Registrarse
                    </Link>
                  </>
                )}
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-400 hover:text-purple-500 transition-colors"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-purple-900/30 bg-[#0a0a0f] px-4 pt-2 pb-6 space-y-3 flex flex-col font-mono-cyber text-sm">
            <a
              href="#preview"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-purple-950/20 text-gray-300 hover:text-purple-500 transition-colors"
            >
              Ver
            </a>
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-purple-950/20 text-gray-300 hover:text-purple-500 transition-colors"
            >
              Características
            </a>
            <a
              href="#pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-purple-950/20 text-gray-300 hover:text-purple-500 transition-colors"
            >
              Precios
            </a>
            <a
              href="#faq"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-purple-950/20 text-gray-300 hover:text-purple-500 transition-colors"
            >
              FAQ
            </a>
            <hr className="border-purple-950/30 my-2" />
            <div className="flex flex-col gap-2 pt-2">
              {session ? (
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-center font-mono-cyber text-xs uppercase px-5 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold border border-purple-500 transition-all duration-300 cyber-clip-alt"
                >
                  Ir al Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/auth/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="text-center font-mono-cyber text-xs uppercase px-4 py-3 text-gray-300 hover:text-white border border-gray-800 rounded transition-colors"
                  >
                    Iniciar Sesión
                  </Link>
                  <Link
                    href="/auth/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="text-center font-mono-cyber text-xs uppercase px-5 py-3 bg-[#0e0e13] text-purple-500 font-bold border border-purple-900/50 transition-all duration-300 cyber-clip"
                  >
                    Registrarse
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 border border-purple-500/30 bg-purple-950/10 px-3 py-1 rounded-full text-xs font-mono-cyber text-purple-400 mb-6 animate-pulse-glow">
          <Radio className="h-3.5 w-3.5" />
          <span>SISTEMA OPERATIVO v4.2 ONLINE</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-mono-cyber font-black tracking-tight leading-none mb-6">
          JILL Card Checker <br />
          <span className="bg-gradient-to-r from-purple-600 via-orange-500 to-purple-400 bg-clip-text text-transparent text-glow">
            Service
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-gray-400 font-sans mb-10">
          Verificación de tarjetas en tiempo real a través de múltiples pasarelas de pago. Comprueba la validez de tu tarjeta con la integración de Stripe, Braintree y Adyen.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
          {session ? (
            <Link
              href="/dashboard"
              className="group flex items-center gap-2 font-mono-cyber text-sm uppercase px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold border border-purple-500 transition-all duration-300 hover:shadow-[0_0_30px_rgba(147,51,234,0.6)] cyber-clip-alt w-full sm:w-auto justify-center"
            >
              Acceder al Dashboard <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          ) : (
            <>
              <Link
                href="/auth/login"
                className="group flex items-center gap-2 font-mono-cyber text-sm uppercase px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold border border-purple-500 transition-all duration-300 hover:shadow-[0_0_30px_rgba(147,51,234,0.6)] cyber-clip-alt w-full sm:w-auto justify-center"
              >
                Comenzar Operación <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="#preview"
                className="font-mono-cyber text-sm uppercase px-8 py-4 bg-[#0e0e13]/85 hover:bg-purple-950/20 text-gray-300 hover:text-purple-500 font-bold border border-purple-900/40 hover:border-purple-500 transition-all duration-300 cyber-clip w-full sm:w-auto"
              >
                Ver Demostración
              </a>
            </>
          )}
        </div>

        {/* Premium Dashboard Image Preview */}
        <div id="preview" className="relative max-w-5xl mx-auto p-2 rounded-xl border border-purple-900/30 bg-[#0d0d12]/60 backdrop-blur-sm glow-purple-soft group">
          <div className="absolute -top-3 left-6 px-3 py-0.5 bg-[#050505] border border-purple-900/50 font-mono-cyber text-[10px] text-purple-500 uppercase tracking-widest">
            jill_sys_view.png
          </div>
          <div className="absolute top-2.5 right-6 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-purple-600 animate-ping" />
            <span className="h-2 w-2 rounded-full bg-purple-500" />
            <span className="font-mono-cyber text-[9px] text-gray-500">LIVE FEED</span>
          </div>

          <div className="overflow-hidden rounded-lg border border-purple-950">
            <Image
              src="/images/dashboard-mockup.png"
              alt="JILL CHK Cyberpunk Dashboard Mockup"
              width={1920}
              height={1080}
              className="w-full h-auto object-cover opacity-90 group-hover:opacity-100 group-hover:scale-[1.01] transition-all duration-700"
              priority
            />
          </div>
        </div>
      </section>

      {/* Features Grid Section */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 border-t border-purple-950/30">
        <div className="text-center mb-16">
          <h2 className="font-mono-cyber text-xs font-bold uppercase tracking-[0.2em] text-purple-500 mb-3">INFRAESTRUCTURA DE VANGUARDIA</h2>
          <p className="text-3xl sm:text-4xl font-mono-cyber font-black uppercase text-white">
            Características de Alto Rendimiento
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Card 1 */}
          <div className="group relative overflow-hidden rounded-lg border border-purple-900/20 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-6 hover:border-purple-600/50 hover:shadow-[0_0_20px_rgba(147,51,234,0.1)] transition-all duration-300">
            <div className="h-12 w-12 rounded bg-purple-950/40 border border-purple-900/30 flex items-center justify-center mb-5 text-purple-500 group-hover:scale-110 transition-transform">
              <Cpu className="h-6 w-6" />
            </div>
            <h3 className="font-mono-cyber text-lg font-bold text-white mb-2 uppercase">Live / Dead Check</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Verificación de la validez de la tarjeta en tiempo real mediante el procesamiento de la pasarela de pago.
            </p>
          </div>

          {/* Card 2 */}
          <div className="group relative overflow-hidden rounded-lg border border-purple-900/20 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-6 hover:border-purple-600/50 hover:shadow-[0_0_20px_rgba(147,51,234,0.1)] transition-all duration-300">
            <div className="h-12 w-12 rounded bg-purple-950/40 border border-purple-900/30 flex items-center justify-center mb-5 text-purple-500 group-hover:scale-110 transition-transform">
              <Server className="h-6 w-6" />
            </div>
            <h3 className="font-mono-cyber text-lg font-bold text-white mb-2 uppercase">Multi-Gateways</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Elige entre diferentes pasarelas para obtener los mejores resultados en tus checkeos
            </p>
          </div>

          {/* Card 3 */}
          <div className="group relative overflow-hidden rounded-lg border border-purple-900/20 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-6 hover:border-purple-600/50 hover:shadow-[0_0_20px_rgba(147,51,234,0.1)] transition-all duration-300">
            <div className="h-12 w-12 rounded bg-purple-950/40 border border-purple-900/30 flex items-center justify-center mb-5 text-purple-500 group-hover:scale-110 transition-transform">
              <Lock className="h-6 w-6" />
            </div>
            <h3 className="font-mono-cyber text-lg font-bold text-white mb-2 uppercase">Security</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Tus credenciales y llaves de acceso están protegidas bajo un estricto protocolo local de cifrado asimétrico.
            </p>
          </div>

          {/* Card 4 */}
          <div className="group relative overflow-hidden rounded-lg border border-purple-900/20 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-6 hover:border-purple-600/50 hover:shadow-[0_0_20px_rgba(147,51,234,0.1)] transition-all duration-300">
            <div className="h-12 w-12 rounded bg-purple-950/40 border border-purple-900/30 flex items-center justify-center mb-5 text-purple-500 group-hover:scale-110 transition-transform">
              <Activity className="h-6 w-6" />
            </div>
            <h3 className="font-mono-cyber text-lg font-bold text-white mb-2 uppercase">Real-time Results</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Obtén resultados instantáneos de tus checkeos, con información detallada sobre la validez de la tarjeta, el estado de la pasarela de pago
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-purple-950/30">
        <div className="text-center mb-16">
          <h2 className="font-mono-cyber text-xs font-bold uppercase tracking-[0.2em] text-purple-500 mb-3">PATENTES DE NAVEGACIÓN</h2>
          <p className="text-3xl sm:text-4xl font-mono-cyber font-black uppercase text-white mb-6">
            Planes de Suscripción
          </p>

          {/* Monthly / Yearly Switcher */}
          <div className="inline-flex items-center gap-3 border border-purple-900/30 bg-[#0d0d12]/80 p-1.5 rounded-lg">
            <button
              onClick={() => setIsYearly(false)}
              className={`px-4 py-2 font-mono-cyber text-xs uppercase transition-all duration-300 ${!isYearly ? 'bg-purple-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
            >
              Mensual
            </button>
            <button
              onClick={() => setIsYearly(true)}
              className={`px-4 py-2 font-mono-cyber text-xs uppercase transition-all duration-300 flex items-center gap-1.5 ${isYearly ? 'bg-purple-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
            >
              Anual <span className="bg-purple-950 text-purple-400 border border-purple-500/20 text-[9px] px-1 py-0.5 rounded uppercase font-black tracking-widest">-20%</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid gap-8 md:grid-cols-3">
          {plans.map((p, i) => {
            const price = isYearly ? p.priceYearly : p.priceMonthly
            return (
              <div
                key={i}
                className={`relative overflow-hidden rounded-xl border bg-[#0a0a0f] p-8 flex flex-col justify-between transition-all duration-300 hover:-translate-y-1 ${p.color} ${p.popular ? 'shadow-[0_0_30px_rgba(147,51,234,0.15)] border-purple-600/50' : 'hover:border-purple-900/40'}`}
              >
                {/* Popular Badge */}
                {p.popular && (
                  <div className="absolute top-4 right-4 bg-purple-600 border border-purple-500 font-mono-cyber text-[8px] font-bold tracking-widest uppercase px-2 py-0.5 rounded">
                    {p.tag}
                  </div>
                )}

                <div>
                  <h3 className="font-mono-cyber text-xl font-bold uppercase text-white mb-2">{p.name}</h3>
                  <p className="text-xs text-gray-500 mb-6 font-sans leading-relaxed">{p.description}</p>

                  <div className="flex items-baseline gap-2 mb-8">
                    <span className="font-mono-cyber text-4xl sm:text-5xl font-black text-white">${price}</span>
                    <span className="font-mono-cyber text-xs uppercase text-gray-500">
                      / {isYearly ? 'Año' : 'Mes'}
                    </span>
                  </div>

                  <hr className="border-purple-950/30 mb-6" />

                  <ul className="space-y-4 mb-8">
                    {p.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-sm text-gray-400">
                        <CheckCircle2 className="h-4.5 w-4.5 text-purple-500 shrink-0 mt-0.5" />
                        <span className="font-sans">{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <Link
                  href="/auth/login"
                  className={`text-center font-mono-cyber text-xs uppercase px-5 py-3.5 font-bold border transition-all duration-300 ${p.popular ? 'bg-purple-600 hover:bg-purple-700 border-purple-500 text-white hover:shadow-[0_0_20px_rgba(147,51,234,0.4)] cyber-clip-alt' : 'bg-[#0f0f15]/80 hover:bg-purple-950/15 border-purple-900/50 hover:border-purple-500 text-purple-500 cyber-clip'}`}
                >
                  {session ? 'Acceder al Dashboard' : p.cta}
                </Link>
              </div>
            )
          })}
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-purple-950/30">
        <div className="text-center mb-12">
          <h2 className="font-mono-cyber text-xs font-bold uppercase tracking-[0.2em] text-purple-500 mb-3">CONSOLA DE SOPORTE</h2>
          <p className="text-3xl font-mono-cyber font-black uppercase text-white">
            Preguntas Frecuentes
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((f, idx) => {
            const isOpen = activeFaq === idx
            return (
              <div
                key={idx}
                className="border border-purple-900/25 bg-[#0a0a0f] rounded-lg overflow-hidden transition-colors hover:border-purple-900/50"
              >
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left font-mono-cyber text-sm font-semibold uppercase text-white hover:text-purple-500 transition-colors"
                >
                  <span>{f.q}</span>
                  <HelpCircle className={`h-5 w-5 text-purple-600 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
                </button>
                <div
                  className={`transition-all duration-300 ease-in-out overflow-hidden ${isOpen ? 'max-h-40 border-t border-purple-950/40' : 'max-h-0'}`}
                >
                  <p className="px-6 py-4 text-sm text-gray-400 leading-relaxed font-sans">
                    {f.a}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Call to Action Footer Panel */}
      <section className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="relative overflow-hidden rounded-2xl border border-purple-600/30 bg-gradient-to-r from-purple-950/15 via-[#0d0d12] to-purple-950/15 p-8 sm:p-12 text-center cyber-clip-alt shadow-[0_0_50px_rgba(147,51,234,0.1)]">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-600/5 rounded-full blur-3xl pointer-events-none" />
          <h2 className="font-mono-cyber text-2xl sm:text-4xl font-black uppercase text-white mb-4">
            ¿Listo para comandar la red?
          </h2>
          <p className="max-w-xl mx-auto text-sm sm:text-base text-gray-400 mb-8 font-sans">
            Únete a JILL CHK y obtén los mejores resultados en tus checkeos.
          </p>

          <Link
            href={session ? "/dashboard" : "/auth/login"}
            className="inline-flex items-center gap-2 font-mono-cyber text-sm uppercase px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold border border-purple-500 transition-all duration-300 hover:shadow-[0_0_20px_rgba(147,51,234,0.5)] cyber-clip-alt"
          >
            {session ? 'Ir al Dashboard' : 'Crear Cuenta'} <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-purple-900/30 bg-[#050507] py-8 text-center text-xs font-mono-cyber text-gray-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 JILL CHK. TODOS LOS DERECHOS RESERVADOS.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-purple-500 transition-colors">TÉRMINOS</a>
            <a href="#" className="hover:text-purple-500 transition-colors">PRIVACIDAD</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
