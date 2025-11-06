// Global type declarations for the application

declare global {
    interface Window {
        ENV?: {
            VITE_DISCORD_BOT_URL?: string
            VITE_DISCORD_CLIENT_ID?: string
        }
    }
}

export {}
