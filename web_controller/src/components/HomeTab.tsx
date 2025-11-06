interface HomeTabProps {
  username?: string
  email?: string
  getAvatarUrl: () => string
}

export function HomeTab({ username, email, getAvatarUrl }: HomeTabProps) {
  return (
    <div className="welcome-page">
      <div className="avatar-card">
        <div className='avatar-container'>
          <img className="avatar" src={getAvatarUrl()} alt={`${username} avatar`} />
        </div>
        <h1>Welcome, {username}</h1>
        <p className="user-email">{email}</p>
      </div>
    </div>
  )
}
