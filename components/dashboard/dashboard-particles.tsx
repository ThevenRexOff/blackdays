'use client'

import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  life: number
  maxLife: number
}

export function DashboardParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const cvs = canvasRef.current!
    if (!cvs) return
    const c = cvs.getContext('2d')
    if (!c) return
    const ctx: CanvasRenderingContext2D = c

    let animId: number
    let particles: Particle[] = []
    const particleCount = 25
    const connectionDist = 120
    const mouse = { x: -1000, y: -1000 }

    function resize() {
      const parent = cvs.parentElement
      if (parent) {
        cvs.width = parent.offsetWidth
        cvs.height = parent.offsetHeight
      }
    }

    function initParticles() {
      particles = Array.from({ length: particleCount }, () => ({
        x: Math.random() * cvs.width,
        y: Math.random() * cvs.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        size: Math.random() * 1.5 + 0.3,
        opacity: Math.random() * 0.4 + 0.1,
        life: 0,
        maxLife: Math.random() * 200 + 100,
      }))
    }

    function draw() {
      const w = cvs.width
      const h = cvs.height
      if (w === 0 || h === 0) {
        animId = requestAnimationFrame(draw)
        return
      }

      ctx.clearRect(0, 0, w, h)

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]
        p.x += p.vx
        p.y += p.vy
        p.life++

        if (p.x < 0 || p.x > w) p.vx *= -1
        if (p.y < 0 || p.y > h) p.vy *= -1

        if (p.life > p.maxLife) {
          p.life = 0
          p.x = Math.random() * w
          p.y = Math.random() * h
          p.maxLife = Math.random() * 200 + 100
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(168, 85, 247, ${p.opacity})`
        ctx.fill()

        const dx = mouse.x - p.x
        const dy = mouse.y - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 150) {
          p.vx -= dx * 0.00002
          p.vy -= dy * 0.00002
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(mouse.x, mouse.y)
          ctx.strokeStyle = `rgba(168, 85, 247, ${0.08 * (1 - dist / 150)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j]
          const dx = p.x - p2.x
          const dy = p.y - p2.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < connectionDist) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(p2.x, p2.y)
            ctx.strokeStyle = `rgba(168, 85, 247, ${0.08 * (1 - dist / connectionDist)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      animId = requestAnimationFrame(draw)
    }

    function onMouseMove(e: MouseEvent) {
      const rect = cvs.getBoundingClientRect()
      mouse.x = e.clientX - rect.left
      mouse.y = e.clientY - rect.top
    }

    function onMouseLeave() {
      mouse.x = -1000
      mouse.y = -1000
    }

    resize()
    initParticles()
    draw()

    const ro = new ResizeObserver(resize)
    ro.observe(cvs.parentElement!)

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)

    return () => {
      cancelAnimationFrame(animId)
      ro.disconnect()
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-0"
      style={{ opacity: 1 }}
    />
  )
}
