import { useRef, useCallback } from 'react'

export function useSound() {
  const ctxRef = useRef<AudioContext | null>(null)
  return useCallback((type: 'start' | 'done') => {
    try {
      if (!ctxRef.current) ctxRef.current = new AudioContext()
      const ctx = ctxRef.current
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      gain.gain.value = 0.08
      if (type === 'start') {
        osc.frequency.setValueAtTime(523, ctx.currentTime)
        osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 0.1)
        osc.start(ctx.currentTime)
        osc.stop(ctx.currentTime + 0.12)
      } else {
        osc.frequency.setValueAtTime(659, ctx.currentTime)
        osc.frequency.setValueAtTime(784, ctx.currentTime + 0.12)
        osc.frequency.setValueAtTime(1047, ctx.currentTime + 0.24)
        osc.start(ctx.currentTime)
        osc.stop(ctx.currentTime + 0.36)
      }
    } catch { }
  }, [])
}
