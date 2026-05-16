# app/routers/columns.py — protected column crud

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.middleware.auth import require_auth
from app.schemas.models import ColumnCreate, ColumnUpdate, ColumnOut

router = APIRouter(prefix="/columns", tags=["columns"])


def _serialize(row, tasks=None) -> ColumnOut:
    d = dict(row)
    d["id"]         = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    return ColumnOut(
        id=d["id"],
        title=d["title"],
        color=d["color"],
        position=d["position"],
        tasks=tasks or [],
    )


# ── POST /columns ─────────────────────────────────────────────────────────────

@router.post("", response_model=ColumnOut, status_code=201)
def create_column(
    payload: ColumnCreate,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM columns"
        )
        next_pos = cur.fetchone()["next_pos"]

        cur.execute("""
            INSERT INTO columns (title, color, position)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (payload.title, payload.color, next_pos))
        row = cur.fetchone()
    db.commit()
    return _serialize(row)


# ── PUT /columns/{column_id} ──────────────────────────────────────────────────

@router.put("/{column_id}", response_model=ColumnOut)
def update_column(
    column_id: str,
    payload: ColumnUpdate,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(400, "no fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values     = list(updates.values()) + [column_id]

    with db.cursor() as cur:
        cur.execute(
            f"UPDATE columns SET {set_clause} WHERE id = %s RETURNING *",
            values,
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "column not found")

    db.commit()
    return _serialize(row)


# ── DELETE /columns/{column_id} ───────────────────────────────────────────────

@router.delete("/{column_id}", status_code=204)
def delete_column(
    column_id: str,
    db=Depends(get_db),
    token: dict = Depends(require_auth),
):
    with db.cursor() as cur:
        # tasks are deleted automatically via ON DELETE CASCADE
        cur.execute("DELETE FROM columns WHERE id = %s RETURNING id", (column_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(404, "column not found")

    db.commit()
