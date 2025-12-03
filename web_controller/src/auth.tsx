import React, { createContext, useContext, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

type User = {
    id?: string
    username?: string
    email?: string
    avatar: string
    discriminator: string
}

type AuthContextType = {
    user: User | null
    isLoading: boolean
    login: () => void
    logout: () => void
    getAvatarUrl: () => string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const size = 240
    const storageKey = 'discord_user'
    const queryClient = useQueryClient()

    const apiBase = import.meta.env.VITE_DISCORD_BOT_URL || window.ENV?.VITE_DISCORD_BOT_URL
    const api = useCallback((path: string) => apiBase ? `${apiBase.replace(/\/$/, '')}${path}` : path, [apiBase])

    // Use React Query for /api/me with longer stale time to prevent excessive requests
    const { data: userData, isLoading } = useQuery({
        queryKey: ['auth', 'me'],
        queryFn: async () => {
            const res = await fetch(api('/api/me'), { credentials: 'include' })
            if (res.ok) {
                const data = await res.json()
                if (data.user) {
                    localStorage.setItem(storageKey, JSON.stringify(data.user))
                    return data.user as User
                }
            }
            return null
        },
        staleTime: 5 * 60 * 1000, // 5 minutes - same as other queries
        retry: 1,
        refetchOnWindowFocus: false,
        // Load initial data from localStorage if available
        initialData: () => {
            const raw = localStorage.getItem(storageKey)
            if (raw) {
                try {
                    return JSON.parse(raw) as User
                } catch {
                    return null
                }
            }
            return null
        }
    })

    const user = userData ?? null

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const authSuccess = params.get('auth')

        if (authSuccess === 'success') {
            // Clean up URL
            const url = new URL(window.location.href)
            url.searchParams.delete('auth')
            window.history.replaceState({}, document.title, url.toString())

            queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
        }
    }, [queryClient])


    function getAvatarUrl() {
        if (!user) return ''
        const avatar = user.avatar
        const id = user.id
        const disc = user.discriminator ?? '0'
        if (avatar) {
            const isAnimated = avatar.startsWith('a_')
            const ext = isAnimated ? 'gif' : 'webp'
            return `https://cdn.discordapp.com/avatars/${id}/${avatar}.${ext}?size=${size}`
        }
        const idx = (parseInt(disc, 10) || 0) % 5
        return `https://cdn.discordapp.com/embed/avatars/${idx}.png?size=${size}`
    }

    function login() {
        window.location.href = api('/api/auth/login')
    }

    function logout() {
        localStorage.removeItem(storageKey)
        queryClient.setQueryData(['auth', 'me'], null)
        ;(async () => {
            await fetch(api('/api/logout'), { method: 'POST', credentials: 'include' })
        })()
    }

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout, getAvatarUrl }}>
            {children}
        </AuthContext.Provider>
    )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
