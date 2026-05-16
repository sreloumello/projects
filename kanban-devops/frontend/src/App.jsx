// src/App.jsx — root component with auth-based routing

import { useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import BoardPage from './pages/BoardPage'

function LoadingScreen() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--muted)',
      fontSize: '0.9rem',
    }}>
      loading...
    </div>
  )
}

export default function App() {
  const { user, loading } = useAuth()

  if (loading) return <LoadingScreen />
  if (!user)   return <LoginPage />
  return <BoardPage />
}
