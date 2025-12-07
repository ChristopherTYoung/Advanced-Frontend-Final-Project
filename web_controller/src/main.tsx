import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './contexts/auth.tsx'
import { queryClient } from './lib/queryClient'
import { Toaster } from 'react-hot-toast'
import AppErrorBoundary from './contexts/AppErrorBoundary.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
        </AuthProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </AppErrorBoundary>
    <Toaster position="top-right" containerClassName='toast-container'/>
  </StrictMode>,
)
