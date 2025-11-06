import React, { createContext, useContext, useEffect, useState } from 'react'

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
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const size = 240
    const storageKey = 'discord_user'

    const apiBase = import.meta.env.VITE_DISCORD_BOT_URL || (window as any)?.ENV?.VITE_DISCORD_BOT_URL
    const api = (path: string) => apiBase ? `${apiBase.replace(/\/$/, '')}${path}` : `/bot${path}`

    useEffect(() => {
        // 1) Restore user from localStorage immediately
        const raw = localStorage.getItem(storageKey)
        if (raw) {
            try {
                const parsed = JSON.parse(raw)
                setUser(parsed)
            } catch (e) {
                // ignore parse errors
            }
        }

        // 2) Check if we just returned from OAuth (server redirected with ?auth=success)
        const params = new URLSearchParams(window.location.search)
        const authSuccess = params.get('auth')
        
        if (authSuccess === 'success') {
            // Clean up URL
            const url = new URL(window.location.href)
            url.searchParams.delete('auth')
            ;(window.history as any).replaceState({}, document.title, url.toString())
            
            // Fetch user from backend session
            setIsLoading(true)
            ;(async () => {
                try {
                    const res = await fetch(api('/api/me'), { credentials: 'include' })
                    if (res.ok) {
                        const data = await res.json()
                        if (data.user) {
                            setUser(data.user)
                            localStorage.setItem(storageKey, JSON.stringify(data.user))
                        }
                    }
                } catch (err) {
                    console.error('Error fetching user after auth', err)
                } finally {
                    setIsLoading(false)
                }
            })()
        } else {
            // 3) Normal page load - reconcile with backend session
            ;(async () => {
                try {
                    const res = await fetch(api('/api/me'), { credentials: 'include' })
                    if (res.ok) {
                        const data = await res.json()
                        if (data.user) {
                            setUser(data.user)
                            localStorage.setItem(storageKey, JSON.stringify(data.user))
                        }
                    }
                } catch (err) {
                    // ignore - backend may not be available
                }
            })()
        }
    }, [])


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
        // Navigate to server-side login endpoint which will redirect to Discord
        setIsLoading(true)
        window.location.href = api('/api/auth/login')
    }

    function logout() {
        setUser(null);
        localStorage.removeItem(storageKey);
        (async () => {
            await fetch(api('/api/logout'), { method: 'POST', credentials: 'include' })
        })()
    }

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout, getAvatarUrl }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
