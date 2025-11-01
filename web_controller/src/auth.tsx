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

    const clientId = import.meta.env.VITE_DISCORD_CLIENT_ID || (window as any)?.ENV?.VITE_DISCORD_CLIENT_ID
    const redirectUri = `${window.location.origin}`
    const scope = import.meta.env.VITE_DISCORD_SCOPE || 'identify email'
    const apiBase = import.meta.env.VITE_DISCORD_BOT_URL || (window as any)?.ENV?.VITE_DISCORD_BOT_URL
    const api = (path: string) => apiBase ? `${apiBase.replace(/\/$/, '')}${path}` : `/bot${path}`

    useEffect(() => {
        (async () => {
            const res = await fetch(api('/api/me'), { credentials: 'include' })
            if (res.ok) {
                const data = await res.json()
                if (data.user) setUser(data.user)
            }
        })()

        const params = new URLSearchParams(window.location.search)
        const code = params.get('code')
        if (code) {
            const url = new URL(window.location.href)
            url.searchParams.delete('code');
            (window.history as any).replaceState({}, document.title, url.toString());

            (async () => {
                setIsLoading(true)
                try {
                    const resp = await fetch(api('/api/auth/discord'), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ code, redirect_uri: redirectUri })
                    })
                    if (resp.ok) {
                        const data = await resp.json()
                        setUser(data.user ?? null)
                    } else {
                        console.warn('Token exchange failed', await resp.text())
                    }
                } catch (err) {
                    console.error('Error exchanging code', err)
                } finally {
                    setIsLoading(false)
                }
            })()
        }
    }, [redirectUri])


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
        if (!clientId) {
            alert('Discord client ID not set (VITE_DISCORD_CLIENT_ID)')
            return
        }
        const params = new URLSearchParams({
            client_id: clientId,
            redirect_uri: redirectUri,
            response_type: 'code',
            scope: scope,
            prompt: 'consent'
        })
        console.log(params.get("redirectUri"))
        setIsLoading(true)
        window.location.href = `https://discord.com/api/oauth2/authorize?${params.toString()}`
    }

    function logout() {
        setUser(null);
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
