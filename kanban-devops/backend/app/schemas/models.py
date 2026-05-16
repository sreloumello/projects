# app/schemas/models.py — pydantic request/response models

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum


class Priority(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


# ── auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str   = Field(..., min_length=8)
    name:     str   = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class ConfirmRequest(BaseModel):
    email: EmailStr
    code:  str


class UserOut(BaseModel):
    id:    str
    email: str
    name:  str


class AuthResponse(BaseModel):
    access_token: str
    id_token:     str
    expires_in:   int
    user:         UserOut


# ── board ─────────────────────────────────────────────────────────────────────

class TaskOut(BaseModel):
    id:          str
    column_id:   str
    title:       str
    description: Optional[str]
    priority:    str
    position:    int
    created_by:  Optional[str]
    created_at:  str
    updated_at:  str


class ColumnOut(BaseModel):
    id:       str
    title:    str
    color:    str
    position: int
    tasks:    List[TaskOut] = []


class BoardOut(BaseModel):
    columns: List[ColumnOut]


# ── tasks ─────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    column_id:   str
    title:       str            = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority:    Priority       = Priority.medium


class TaskUpdate(BaseModel):
    title:       Optional[str]      = Field(None, min_length=1, max_length=200)
    description: Optional[str]      = None
    priority:    Optional[Priority] = None


class TaskMove(BaseModel):
    column_id: str
    position:  int = Field(..., ge=0)


# ── columns ───────────────────────────────────────────────────────────────────

class ColumnCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    color: str = Field("#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


class ColumnUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
