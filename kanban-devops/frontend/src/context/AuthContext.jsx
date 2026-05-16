// src/context/AuthContext.jsx — global auth state

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { auth, setAccessToken, clearAccessToken } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true) // true while checking session

  // on mount — try to restore session via refresh_token cookie
  useEffect(() => {
    auth.refresh()
      .then(data => {
        setAccessToken(data.access_token)
        setUser(data.user)
      })
      .catch(() => {
        // no valid session — stay logged out
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await auth.login(email, password)
    setAccessToken(data.access_token)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    await auth.logout().catch(() => {})
    clearAccessToken()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
