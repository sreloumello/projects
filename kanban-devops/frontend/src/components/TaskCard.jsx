// src/components/TaskCard.jsx

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useAuth } from '../context/AuthContext'
import './TaskCard.css'

const PRIORITY_COLORS = {
  high:   { bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.3)',   text: '#fca5a5' },
  medium: { bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.3)',  text: '#fcd34d' },
  low:    { bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.3)',  text: '#6ee7b7' },
}

export default function TaskCard({ task, onDelete }) {
  const { user } = useAuth()
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }

  const priority = PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.medium

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="task-card"
      {...attributes}
      {...listeners}
    >
      <p className="task-title">{task.title}</p>

      {task.description && (
        <p className="task-desc">{task.description}</p>
      )}

      <div className="task-footer">
        <span
          className="task-priority"
          style={{
            background: priority.bg,
            border: `1px solid ${priority.border}`,
            color: priority.text,
          }}
        >
          {task.priority}
        </span>

        {user && (
          <button
            className="task-delete"
            onClick={e => { e.stopPropagation(); onDelete(task.id) }}
            title="delete task"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  )
}
