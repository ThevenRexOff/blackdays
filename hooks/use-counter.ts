import { useEffect, useState } from 'react'

export function useCounter(target: number, duration = 1500) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    let animationFrameId: number
    const start = performance.now()
    const startValue = value

    function tick(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      // Easing function for smoother animation (easeOutQuad)
      const easeProgress = progress * (2 - progress)
      setValue(Math.floor(startValue + easeProgress * (target - startValue)))
      if (progress < 1) {
        animationFrameId = requestAnimationFrame(tick)
      }
    }

    animationFrameId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(animationFrameId)
  }, [target, duration])

  return value
}
