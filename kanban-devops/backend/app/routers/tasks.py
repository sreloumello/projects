# app/routers/tasks.py — protected task crud

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.middleware.auth import require_auth
from app.schemas.models import TaskCreate, TaskUpdate, TaskMove, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize(row) -> TaskOut:
    d = dict(row)
    d["id"]         = str(d["id"])
    d["column_id"]  = str(d["column_id"])
    d["created_by"] = str(d["created_by"]) if d["created_by"] else None
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return TaskOut(**d)


def _get_user_id(cognito_sub: str, db) -> str:
    """resolve cognito sub to local user id"""
    with db.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE cognito_sub = %s", (cognito_sub,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(401, "user not found")
    return str(row["id"])


# ── POST /tasks ───────────────────────────────────────────────────────────────

@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    user_id = _get_user_id(token["sub"], db)

    with db.cursor() as cur:
        # get max position in column to append at the end
        cur.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM tasks WHERE column_id = %s",
            (payload.column_id,),
        )
        next_pos = cur.fetchone()["next_pos"]

        cur.execute("""
            INSERT INTO tasks (column_id, title, description, priority, position, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            payload.column_id,
            payload.title,
            payload.description,
            payload.priority.value,
            next_pos,
            user_id,
        ))
        row = cur.fetchone()
    db.commit()
    return _serialize(row)


# ── PUT /tasks/{task_id} ──────────────────────────────────────────────────────

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(400, "no fields to update")

    # convert enums to string
    for k, v in updates.items():
        if hasattr(v, "value"):
            updates[k] = v.value

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values     = list(updates.values()) + [task_id]

    with db.cursor() as cur:
        cur.execute(
            f"UPDATE tasks SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
            values,
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "task not found")

    db.commit()
    return _serialize(row)


# ── POST /tasks/{task_id}/move ────────────────────────────────────────────────

@router.post("/{task_id}/move", response_model=TaskOut)
def move_task(
    task_id: str,
    payload: TaskMove,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    with db.cursor() as cur:
        # get current task
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()

        if not task:
            raise HTTPException(404, "task not found")

        old_column_id = str(task["column_id"])
        old_position  = task["position"]
        new_column_id = payload.column_id
        new_position  = payload.position

        # shift tasks in old column up to fill the gap
        cur.execute("""
            UPDATE tasks
            SET position = position - 1
            WHERE column_id = %s AND position > %s AND id != %s
        """, (old_column_id, old_position, task_id))

        # shift tasks in new column down to make room
        cur.execute("""
            UPDATE tasks
            SET position = position + 1
            WHERE column_id = %s AND position >= %s AND id != %s
        """, (new_column_id, new_position, task_id))

        # move the task
        cur.execute("""
            UPDATE tasks
            SET column_id = %s, position = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, (new_column_id, new_position, task_id))
        row = cur.fetchone()

    db.commit()
    return _serialize(row)


# ── DELETE /tasks/{task_id} ───────────────────────────────────────────────────

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    with db.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "task not found")

    db.commit()
