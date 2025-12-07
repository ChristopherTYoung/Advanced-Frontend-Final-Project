const API_BASE_URL = import.meta.env.VITE_DISCORD_BOT_URL || window.ENV?.VITE_DISCORD_BOT_URL

export function api(path: string): string {
  const isDev = import.meta.env.DEV
  
  if (isDev) {
    console.log('API Request (dev, proxied):', path)
    return path
  } else {
    const baseUrl = API_BASE_URL?.replace(/\/$/, '') || ''
    const fullUrl = `${baseUrl}${path}`
    console.log('API Request (prod):', fullUrl)
    return fullUrl
  }
}
