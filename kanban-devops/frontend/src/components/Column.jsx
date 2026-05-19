// src/components/Column.jsx

import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import TaskCard from './TaskCard'
import { useAuth } from '../context/AuthContext'
import './Column.css'

export default function Column({ column, onAddTask, onDeleteTask }) {
  const { user } = useAuth()

  const { setNodeRef, isOver } = useDroppable({ id: column.id })

  return (
    <div className={`column ${isOver ? 'column--over' : ''}`}>
      <div className="column-header">
        <div className="column-title-row">
          <span
            className="column-dot"
            style={{ background: column.color }}
          />
          <h3 className="column-title">{column.title}</h3>
          <span className="column-count">{column.tasks.length}</span>
        </div>
      </div>

      <SortableContext
        items={column.tasks.map(t => t.id)}
        strategy={verticalListSortingStrategy}
      >
        <div ref={setNodeRef} className="column-tasks">
          {column.tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onDelete={id => onDeleteTask(id, column.id)}
            />
          ))}

          {column.tasks.length === 0 && (
            <div className="column-empty">drop tasks here</div>
          )}
        </div>
      </SortableContext>

      {user && (
        <button
          className="column-add-btn"
          onClick={() => onAddTask(column.id)}
        >
          + add task
        </button>
      )}
    </div>
  )
}
