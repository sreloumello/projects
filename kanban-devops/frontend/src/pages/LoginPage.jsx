// src/pages/LoginPage.jsx — login, register and confirm screens

import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { auth } from '../services/api'
import './LoginPage.css'

const SCREENS = {
  LOGIN:    'login',
  REGISTER: 'register',
  CONFIRM:  'confirm',
}

export default function LoginPage() {
  const { login }                   = useAuth()
  const [screen, setScreen]         = useState(SCREENS.LOGIN)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')
  const [pendingEmail, setPending]  = useState('')

  // form fields
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [name,     setName]     = useState('')
  const [code,     setCode]     = useState('')

  function clearError() { setError('') }

  async function handleLogin(e) {
    e.preventDefault()
    setLoading(true)
    clearError()
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setLoading(true)
    clearError()
    try {
      await auth.register(email, password, name)
      setPending(email)
      setScreen(SCREENS.CONFIRM)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleConfirm(e) {
    e.preventDefault()
    setLoading(true)
    clearError()
    try {
      await auth.confirm(pendingEmail, code)
      setScreen(SCREENS.LOGIN)
      setEmail(pendingEmail)
      setPassword('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-bg">
      <div className="login-card">

        <div className="login-header">
          <h1 className="login-logo">Luan's Kanban</h1>
          <p className="login-tagline">organize your work</p>
        </div>

        {error && (
          <div className="login-error" onClick={clearError}>
            {error}
          </div>
        )}

        {/* ── LOGIN ── */}
        {screen === SCREENS.LOGIN && (
          <form className="login-form" onSubmit={handleLogin}>
            <div className="field">
              <label>email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                autoFocus
              />
            </div>
            <div className="field">
              <label>password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'signing in...' : 'sign in'}
            </button>
            <p className="login-switch">
              don't have an account?{' '}
              <button type="button" className="btn-link"
                onClick={() => { setScreen(SCREENS.REGISTER); clearError() }}>
                sign up
              </button>
            </p>
          </form>
        )}

        {/* ── REGISTER ── */}
        {screen === SCREENS.REGISTER && (
          <form className="login-form" onSubmit={handleRegister}>
            <div className="field">
              <label>name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="your name"
                required
                autoFocus
              />
            </div>
            <div className="field">
              <label>email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div className="field">
              <label>password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="min. 8 characters"
                minLength={8}
                required
              />
            </div>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'creating account...' : 'create account'}
            </button>
            <p className="login-switch">
              already have an account?{' '}
              <button type="button" className="btn-link"
                onClick={() => { setScreen(SCREENS.LOGIN); clearError() }}>
                sign in
              </button>
            </p>
          </form>
        )}

        {/* ── CONFIRM ── */}
        {screen === SCREENS.CONFIRM && (
          <form className="login-form" onSubmit={handleConfirm}>
            <p className="confirm-msg">
              we sent a confirmation code to <strong>{pendingEmail}</strong>
            </p>
            <div className="field">
              <label>confirmation code</label>
              <input
                type="text"
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder="123456"
                required
                autoFocus
              />
            </div>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'confirming...' : 'confirm email'}
            </button>
          </form>
        )}

      </div>
    </div>
  )
}
