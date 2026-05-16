// src/pages/BoardPage.jsx — placeholder

import { useAuth } from '../context/AuthContext'

export default function BoardPage() {
  const { user, logout } = useAuth()
  return (
    <div style={{ padding: '2rem', color: 'var(--text)' }}>
      <p>welcome, {user.name}!</p>
      <button onClick={logout} style={{ marginTop: '1rem', color: 'var(--accent)', background: 'none', border: 'none' }}>
        logout
      </button>
    </div>
  )
}
