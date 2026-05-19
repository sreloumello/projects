// src/components/AddTaskModal.jsx

import { useState } from 'react'
import './AddTaskModal.css'

export default function AddTaskModal({ onConfirm, onClose }) {
  const [title,       setTitle]       = useState('')
  const [description, setDescription] = useState('')
  const [priority,    setPriority]    = useState('medium')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    setError('')
    try {
      await onConfirm(title.trim(), description.trim() || null, priority)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>

        <div className="modal-header">
          <h2>new task</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="field">
            <label>title</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="what needs to be done?"
              required
              autoFocus
              maxLength={200}
            />
          </div>

          <div className="field">
            <label>description <span className="optional">(optional)</span></label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="add some details..."
              rows={3}
              maxLength={1000}
            />
          </div>

          <div className="field">
            <label>priority</label>
            <div className="priority-options">
              {['low', 'medium', 'high'].map(p => (
                <button
                  key={p}
                  type="button"
                  className={`priority-btn priority-btn--${p} ${priority === p ? 'active' : ''}`}
                  onClick={() => setPriority(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>
              cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading || !title.trim()}>
              {loading ? 'creating...' : 'create task'}
            </button>
          </div>
        </form>

      </div>
    </div>
  )
}
