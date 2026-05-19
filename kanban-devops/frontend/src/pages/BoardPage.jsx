// src/pages/BoardPage.jsx

import { useAuth } from '../context/AuthContext'
import Board from '../components/Board'
import './BoardPage.css'

export default function BoardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="board-page">
      <header className="header">
        <h1 className="header-logo">Luan's Kanban</h1>
        <div className="header-right">
          {user && (
            <>
              <span className="header-user">{user.name}</span>
              <button className="header-logout" onClick={logout}>
                logout
              </button>
            </>
          )}
        </div>
      </header>

      <main>
        <Board />
      </main>
    </div>
  )
}
