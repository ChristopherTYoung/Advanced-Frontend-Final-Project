import { useQuery } from '@tanstack/react-query'
import { UserSchema, type User } from '../schemas'
import { api } from '../utils/api'

async function fetchUser(): Promise<User> {
  const response = await fetch(api('/api/user'), {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Failed to fetch user')
  }
  const data = await response.json()
  return UserSchema.parse(data)
}

export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: fetchUser,
  })
}
