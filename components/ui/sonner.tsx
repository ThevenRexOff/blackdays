'use client'

import { Toaster as HotToaster } from 'react-hot-toast'

const Toaster = () => {
  return (
    <HotToaster
      position="bottom-center"
      toastOptions={{
        style: {
          background: '#0a0a0a',
          border: '1px solid rgba(168,85,247,0.4)',
          color: '#e5e7eb',
          fontSize: 13,
        },
      }}
    />
  )
}

export { Toaster }
