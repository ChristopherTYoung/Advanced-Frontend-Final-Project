import { useState } from 'react'
import type { ReactElement } from 'react'

interface HomeTabProps {
  username?: string
  email?: string
  getAvatarUrl: () => string
}

function CrashTest(): ReactElement {
  // This component throws during render to test ErrorBoundary
  throw new Error('Test crash from CrashTest component')
}

export function HomeTab({ username, getAvatarUrl }: HomeTabProps) {
  const [crash, setCrash] = useState(false)

  return (
    <div className="welcome-page">
      <div className="avatar-card">
        <div className='avatar-container'>
          <img className="avatar" src={getAvatarUrl()} alt={`${username} avatar`} />
        </div>
        <h1>Welcome, {username}</h1>
        <button onClick={() => setCrash(true)}>
          Trigger Test Error
        </button>

        {crash && <CrashTest />}
      </div>
    </div>
  )
}
