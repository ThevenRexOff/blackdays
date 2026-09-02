import { toast as hotToast } from 'react-hot-toast'
import type { ToastOptions as RHToastOptions } from 'react-hot-toast'
import { X, CheckCircle2, XCircle, Info, AlertTriangle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

type Variant = 'success' | 'error' | 'info' | 'warning' | 'blank'

interface ToastOptions extends RHToastOptions {
  description?: string
}

const variantStyles: Record<Variant, { border: string; Icon: LucideIcon | null; text: string }> = {
  success: { border: 'rgba(34,197,94,0.5)', Icon: CheckCircle2, text: '#4ade80' },
  error: { border: 'rgba(239,68,68,0.5)', Icon: XCircle, text: '#f87171' },
  info: { border: 'rgba(59,130,246,0.5)', Icon: Info, text: '#60a5fa' },
  warning: { border: 'rgba(250,204,21,0.5)', Icon: AlertTriangle, text: '#facc15' },
  blank: { border: 'rgba(239,68,68,0.4)', Icon: null, text: '#e5e7eb' },
}

function createToast(message: string, variant: Variant, options?: ToastOptions) {
  const v = variantStyles[variant]
  const customIcon = options?.icon
  const duration = options?.duration ?? 4000

  const IconComp = v.Icon

  return hotToast(
    (t) => (
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, minWidth: 200 }}>
        {customIcon ? (
          <span style={{ fontSize: 14, flexShrink: 0, lineHeight: '18px' }}>{customIcon}</span>
        ) : IconComp ? (
          <span style={{ flexShrink: 0, lineHeight: 0, marginTop: 1 }}>
            <IconComp size={16} color={v.text} />
          </span>
        ) : null}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, color: v.text, wordBreak: 'break-word', lineHeight: '18px' }}>
            {message}
          </div>
          {options?.description && (
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 3 }}>
              {options.description}
            </div>
          )}
        </div>
        <button
          onClick={() => hotToast.dismiss(t.id)}
          style={{
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 4,
            color: 'rgba(255,255,255,0.3)',
            cursor: 'pointer',
            padding: '2px 4px',
            display: 'flex',
            alignItems: 'center',
            flexShrink: 0,
            marginTop: 1,
            transition: 'color 0.15s, border-color 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'rgba(255,255,255,0.8)'
            e.currentTarget.style.borderColor = 'rgba(239,68,68,0.5)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'rgba(255,255,255,0.3)'
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
          }}
        >
          <X size={14} />
        </button>
      </div>
    ),
    {
      duration,
      style: {
        background: '#0a0a0a',
        border: `1px solid ${v.border}`,
        borderRadius: 4,
        padding: '10px 14px',
        maxWidth: 500,
        boxShadow: '0 0 15px rgba(239,68,68,0.08)',
        ...(options?.style || {}),
      },
    }
  )
}

const _toast = (message: string, options?: ToastOptions) => createToast(message, 'blank', options)

_toast.success = (message: string, options?: ToastOptions) => createToast(message, 'success', options)
_toast.error = (message: string, options?: ToastOptions) => createToast(message, 'error', options)
_toast.info = (message: string, options?: ToastOptions) => createToast(message, 'info', options)
_toast.warning = (message: string, options?: ToastOptions) => createToast(message, 'warning', options)
_toast.dismiss = hotToast.dismiss

const toast = _toast as typeof _toast & typeof hotToast

export { toast }
