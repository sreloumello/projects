// src/components/Board.jsx

import { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import Column from './Column'
import TaskCard from './TaskCard'
import AddTaskModal from './AddTaskModal'
import { useBoard } from '../hooks/useBoard'
import './Board.css'

export default function Board() {
  const { columns, loading, error, createTask, moveTask, deleteTask } = useBoard()
  const [activeTask,      setActiveTask]      = useState(null)
  const [addingToColumn,  setAddingToColumn]  = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  )

  function findColumn(taskId) {
    return columns.find(col => col.tasks.some(t => t.id === taskId))
  }

  function handleDragStart({ active }) {
    const col  = findColumn(active.id)
    const task = col?.tasks.find(t => t.id === active.id)
    setActiveTask(task || null)
  }

  async function handleDragEnd({ active, over }) {
    setActiveTask(null)
    if (!over) return

    const fromCol = findColumn(active.id)
    if (!fromCol) return

    // dropped over a column id directly
    const toColById = columns.find(c => c.id === over.id)
    const toColByTask = findColumn(over.id)
    const toCol = toColById || toColByTask
    if (!toCol) return

    const fromTasks = fromCol.tasks
    const toTasks   = toCol.tasks

    if (fromCol.id === toCol.id) {
      // reorder within same column
      const oldIdx = fromTasks.findIndex(t => t.id === active.id)
      const newIdx = toTasks.findIndex(t => t.id === over.id)
      if (oldIdx !== newIdx && newIdx !== -1) {
        await moveTask(active.id, fromCol.id, toCol.id, newIdx)
      }
    } else {
      // move to different column
      const newIdx = toTasks.findIndex(t => t.id === over.id)
      const position = newIdx === -1 ? toTasks.length : newIdx
      await moveTask(active.id, fromCol.id, toCol.id, position)
    }
  }

  if (loading) return <div className="board-loading">loading board...</div>
  if (error)   return <div className="board-error">error: {error}</div>

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="board">
          {columns.map(col => (
            <Column
              key={col.id}
              column={col}
              onAddTask={colId => setAddingToColumn(colId)}
              onDeleteTask={deleteTask}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask && (
            <TaskCard task={activeTask} onDelete={() => {}} />
          )}
        </DragOverlay>
      </DndContext>

      {addingToColumn && (
        <AddTaskModal
          onConfirm={(title, description, priority) =>
            createTask(addingToColumn, title, description, priority)
          }
          onClose={() => setAddingToColumn(null)}
        />
      )}
    </>
  )
}
