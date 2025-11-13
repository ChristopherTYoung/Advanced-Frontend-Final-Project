import type { ReactNode } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import toast from 'react-hot-toast'
import { showErrorToast } from '../utils/toastUtils'

export function AppErrorBoundary({ children }: { children: ReactNode }) {
    function FallBackComponent() {
        return children
    }

    return (
        <ErrorBoundary
            onError={(error) => showErrorToast(error?.message)}
            FallbackComponent={FallBackComponent}
        >
            {children}
        </ErrorBoundary>
    )
}

export default AppErrorBoundary