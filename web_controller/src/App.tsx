import './App.css'
import { useAuth } from './auth'
import { useState } from 'react'
import { HomeTab } from './components/HomeTab'
import { SetupTab } from './components/SetupTab'
import { MessagesTab } from './components/MessagesTab'
import EventsTab from './components/EventsTab'
import SettingsTab from './components/SettingsTab'
import { OffensesTab } from './components/OffensesTab'

function App() {
  const { user, isLoading, login, logout, getAvatarUrl } = useAuth()
  const [activeTab, setActiveTab] = useState<'home' | 'setup' | 'test' | 'messages' | 'settings' | 'events' | 'offenses'>('home')

  function handleLogin() {
    login()
  }

  const clientId = import.meta.env.VITE_DISCORD_CLIENT_ID || window.ENV?.VITE_DISCORD_CLIENT_ID
  const botInviteUrl = clientId 
    ? `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=8&scope=bot%20applications.commands`
    : ''

  if (!user) {
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

  return (
    <div>
      <button className="logout-btn" onClick={logout}>Logout</button>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => setActiveTab('home')}
        >
          Home
        </button>
        <button 
          className={`tab ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          Setup
        </button>
        <button 
          className={`tab ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          Messages
        </button>
        <button 
          className={`tab ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
        <button 
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
        <button 
          className={`tab ${activeTab === 'offenses' ? 'active' : ''}`}
          onClick={() => setActiveTab('offenses')}
        >
          Violations
        </button>
      </div>

      {isLoading ? (
        <div className="spinner">Loading...</div>
      ) : (
        <>
          {activeTab === 'home' && (
            <HomeTab 
              username={user.username}
              email={user.email}
              getAvatarUrl={getAvatarUrl}
            />
          )}

          {activeTab === 'setup' && (
            <SetupTab botInviteUrl={botInviteUrl} />
          )}

          {activeTab === 'messages' && (
            <MessagesTab />
          )}

          {activeTab === 'events' && (
            <EventsTab />
          )}

          {activeTab === 'settings' && (
            <SettingsTab />
          )}

          {activeTab === 'offenses' && (
            <OffensesTab />
          )}
        </>
      )}
    </div>
  )
}

export default App