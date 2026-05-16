# app/routers/board.py — public read of the full kanban board

from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas.models import BoardOut, ColumnOut, TaskOut

router = APIRouter(prefix="/board", tags=["board"])


def _serialize_task(row) -> TaskOut:
    d = dict(row)
    d["id"]         = str(d["id"])
    d["column_id"]  = str(d["column_id"])
    d["created_by"] = str(d["created_by"]) if d["created_by"] else None
    d["created_at"] = d["created_at"].isoformat()
    d["updated_at"] = d["updated_at"].isoformat()
    return TaskOut(**d)


def _serialize_column(row, tasks: list) -> ColumnOut:
    d = dict(row)
    d["id"]         = str(d["id"])
    d["created_at"] = d["created_at"].isoformat()
    return ColumnOut(
        id=d["id"],
        title=d["title"],
        color=d["color"],
        position=d["position"],
        tasks=tasks,
    )


# ── GET /board ────────────────────────────────────────────────────────────────

@router.get("", response_model=BoardOut)
def get_board(db=Depends(get_db)):
    """public endpoint — returns all columns and tasks"""
    with db.cursor() as cur:
        # fetch columns ordered by position
        cur.execute("SELECT * FROM columns ORDER BY position ASC")
        columns = cur.fetchall()

        # fetch all tasks ordered by position within each column
        cur.execute("""
            SELECT t.*, u.name as creator_name
            FROM tasks t
            LEFT JOIN users u ON u.id = t.created_by
            ORDER BY t.column_id, t.position ASC
        """)
        tasks = cur.fetchall()

    # group tasks by column_id
    tasks_by_column: dict = {}
    for task in tasks:
        col_id = str(task["column_id"])
        if col_id not in tasks_by_column:
            tasks_by_column[col_id] = []
        tasks_by_column[col_id].append(_serialize_task(task))

    return BoardOut(
        columns=[
            _serialize_column(col, tasks_by_column.get(str(col["id"]), []))
            for col in columns
        ]
    )
