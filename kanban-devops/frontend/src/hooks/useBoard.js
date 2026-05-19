// src/hooks/useBoard.js — board state and api operations

import { useState, useEffect, useCallback } from 'react'
import { board, tasks } from '../services/api'

export function useBoard() {
  const [columns, setColumns]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  const fetchBoard = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await board.get()
      setColumns(data.columns)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchBoard() }, [fetchBoard])

  const createTask = useCallback(async (columnId, title, description, priority) => {
    const task = await tasks.create(columnId, title, description, priority)
    setColumns(prev => prev.map(col =>
      col.id === columnId
        ? { ...col, tasks: [...col.tasks, task] }
        : col
    ))
    return task
  }, [])

  const moveTask = useCallback(async (taskId, fromColumnId, toColumnId, newPosition) => {
    // optimistic update
    setColumns(prev => {
      const next = prev.map(col => ({ ...col, tasks: [...col.tasks] }))
      const fromCol = next.find(c => c.id === fromColumnId)
      const toCol   = next.find(c => c.id === toColumnId)
      const taskIdx = fromCol.tasks.findIndex(t => t.id === taskId)
      const [task]  = fromCol.tasks.splice(taskIdx, 1)
      task.column_id = toColumnId
      toCol.tasks.splice(newPosition, 0, task)
      return next
    })
    try {
      await tasks.move(taskId, toColumnId, newPosition)
    } catch {
      fetchBoard() // rollback on error
    }
  }, [fetchBoard])

  const deleteTask = useCallback(async (taskId, columnId) => {
    setColumns(prev => prev.map(col =>
      col.id === columnId
        ? { ...col, tasks: col.tasks.filter(t => t.id !== taskId) }
        : col
    ))
    await tasks.delete(taskId)
  }, [])

  return { columns, loading, error, fetchBoard, createTask, moveTask, deleteTask }
}
