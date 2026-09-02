'use client'

import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
}

export function ParticleNetwork() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const cvs = canvas
    const c = ctx
    let animId: number
    let particles: Particle[] = []
    const particleCount = 60
    const connectionDist = 150
    const mouse = { x: -1000, y: -1000 }

    function resize() {
      cvs.width = window.innerWidth
      cvs.height = window.innerHeight
    }

    function initParticles() {
      particles = Array.from({ length: particleCount }, () => ({
        x: Math.random() * cvs.width,
        y: Math.random() * cvs.height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.5 + 0.3,
      }))
    }

    function draw() {
      c.clearRect(0, 0, cvs.width, cvs.height)

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]
        p.x += p.vx
        p.y += p.vy

        if (p.x < 0 || p.x > cvs.width) p.vx *= -1
        if (p.y < 0 || p.y > cvs.height) p.vy *= -1

        c.beginPath()
        c.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        c.fillStyle = `rgba(239, 68, 68, ${p.opacity})`
        c.fill()

        const dx = mouse.x - p.x
        const dy = mouse.y - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 200) {
          p.vx -= dx * 0.00005
          p.vy -= dy * 0.00005
          c.beginPath()
          c.moveTo(p.x, p.y)
          c.lineTo(mouse.x, mouse.y)
          c.strokeStyle = `rgba(239, 68, 68, ${0.15 * (1 - dist / 200)})`
          c.lineWidth = 0.5
          c.stroke()
        }

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j]
          const dx = p.x - p2.x
          const dy = p.y - p2.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < connectionDist) {
            c.beginPath()
            c.moveTo(p.x, p.y)
            c.lineTo(p2.x, p2.y)
            c.strokeStyle = `rgba(239, 68, 68, ${0.12 * (1 - dist / connectionDist)})`
            c.lineWidth = 0.5
            c.stroke()
          }
        }
      }

      animId = requestAnimationFrame(draw)
    }

    function onMouseMove(e: MouseEvent) {
      mouse.x = e.clientX
      mouse.y = e.clientY
    }

    function onTouchMove(e: TouchEvent) {
      const touch = e.touches[0]
      if (touch) {
        mouse.x = touch.clientX
        mouse.y = touch.clientY
      }
    }

    function onMouseLeave() {
      mouse.x = -1000
      mouse.y = -1000
    }

    resize()
    initParticles()
    draw()

    window.addEventListener('resize', resize)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('touchmove', onTouchMove)
    window.addEventListener('mouseleave', onMouseLeave)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('touchmove', onTouchMove)
      window.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-10"
      style={{ opacity: 0.8 }}
    />
  )
}
