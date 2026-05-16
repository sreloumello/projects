// src/main.jsx — application entry point

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './context/AuthContext'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>
)
