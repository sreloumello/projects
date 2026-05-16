// src/services/api.js — api communication layer

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// in-memory token storage — never persisted to localStorage
let accessToken = null

export function setAccessToken(token) {
  accessToken = token
}

export function clearAccessToken() {
  accessToken = null
}

export function hasAccessToken() {
  return !!accessToken
}

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' }

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include', // sends refresh_token cookie automatically
    body: body ? JSON.stringify(body) : null,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'unknown error' }))
    throw new Error(error.detail || 'request failed')
  }

  if (res.status === 204) return null
  return res.json()
}

// ── auth ──────────────────────────────────────────────────────────────────────

export const auth = {
  register: (email, password, name) =>
    request('POST', '/auth/register', { email, password, name }),

  confirm: (email, code) =>
    request('POST', '/auth/confirm', { email, code }),

  login: (email, password) =>
    request('POST', '/auth/login', { email, password }),

  refresh: () =>
    request('POST', '/auth/refresh'),

  logout: () =>
    request('POST', '/auth/logout'),
}

// ── board ─────────────────────────────────────────────────────────────────────

export const board = {
  get: () => request('GET', '/board'),
}

// ── tasks ─────────────────────────────────────────────────────────────────────

export const tasks = {
  create: (columnId, title, description, priority) =>
    request('POST', '/tasks', { column_id: columnId, title, description, priority }),

  update: (id, data) =>
    request('PUT', `/tasks/${id}`, data),

  move: (id, columnId, position) =>
    request('POST', `/tasks/${id}/move`, { column_id: columnId, position }),

  delete: (id) =>
    request('DELETE', `/tasks/${id}`),
}

// ── columns ───────────────────────────────────────────────────────────────────

export const columns = {
  create: (title, color) =>
    request('POST', '/columns', { title, color }),

  update: (id, data) =>
    request('PUT', `/columns/${id}`, data),

  delete: (id) =>
    request('DELETE', `/columns/${id}`),
}
