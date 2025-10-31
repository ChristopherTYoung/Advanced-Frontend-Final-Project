import './App.css'
import { useAuth } from './auth'

function App() {
  const { user, isLoading, login, logout, getAvatarUrl } = useAuth()

  function handleLogin() {
    login()
  }

  const isCallback = user != null

  if (isCallback) {
    return (
      <div className="welcome-page">
        {isLoading ? (
          <div className="spinner">Loading...</div>
        ) : user ? (
          <div className="avatar-card">
            <button className="logout-btn" onClick={logout}>Logout</button>
            <div className='avatar-container'>
              <img className="avatar" src={getAvatarUrl()} alt={`${user.username} avatar`} />
            </div>
            <h1>Welcome, {user.username}</h1>
          </div>
        ) : (
          <div className="avatar-card">
            <h2>No user information available</h2>
            <p>Please return to the app and click Login.</p>
            <button onClick={handleLogin}>Login</button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <button className="login-btn" onClick={handleLogin} aria-label="Login with Discord">
        Login
      </button>

      <main className="card">
        <h1>Welcome</h1>
        <p className="read-the-docs">Click the Login button to sign in with Discord.</p>
      </main>
    </div>
  )
}

export default App
