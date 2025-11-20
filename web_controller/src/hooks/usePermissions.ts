import { useMemo } from 'react'
import { useGuildSettings } from './useApi'
import { useAuth } from '../auth'

export type Permission = 'change_nickname' | 'change_personality' | 'make_events' | 'manage_proposals'

interface UsePermissionsResult {
  hasPermission: (permission: Permission) => boolean
  isOwner: boolean
  isLoading: boolean
}

export function usePermissions(guildId: string | null): UsePermissionsResult {
  const { user } = useAuth()
  const { data: settings, isLoading } = useGuildSettings(guildId)

  return useMemo(() => {
    if (!guildId || !user || isLoading) {
      return {
        hasPermission: () => false,
        isOwner: false,
        isLoading: isLoading || !user,
      }
    }

    const isOwner = false

    const roleSettings = settings?.settings?.role_settings?.roles || []

    const hasPermission = (permission: Permission): boolean => {
      if (isOwner) return true

      for (const role of roleSettings) {
        const perm = role.permissions.find(p => p.permission_name === permission)
        return perm?.allowed ?? false;
      }

      return false
    }

    return {
      hasPermission,
      isOwner,
      isLoading: false,
    }
  }, [guildId, user, settings, isLoading])
}
