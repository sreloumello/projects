# app/routers/auth.py — register, login, refresh, logout via cognito

import base64
import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Response, Cookie

from app.config import get_settings
from app.database import get_connection
from app.schemas.models import (
    RegisterRequest, LoginRequest, ConfirmRequest,
    AuthResponse, UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _cognito_client():
    s = get_settings()
    import os
    return boto3.client(
        "cognito-idp",
        region_name=s.COGNITO_REGION,
        endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    )


def _set_refresh_cookie(response: Response, refresh_token: str):
    s = get_settings()
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=s.COOKIE_SECURE,
        samesite=s.COOKIE_SAMESITE,
        max_age=30 * 24 * 60 * 60,
        path="/auth",
    )


def _decode_id_token_claims(id_token: str) -> dict:
    """decode id_token payload without validating — token just came from cognito"""
    payload_b64 = id_token.split(".")[1]
    padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _upsert_user(cognito_sub: str, email: str, name: str) -> dict:
    """insert or update user in local database after successful cognito auth"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (cognito_sub, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (cognito_sub) DO UPDATE
              SET email = EXCLUDED.email,
                  name  = EXCLUDED.name
            RETURNING id, email, name
        """, (cognito_sub, email, name))
        user = dict(cur.fetchone())
        user["id"] = str(user["id"])
    conn.commit()
    conn.close()
    return user


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(payload: RegisterRequest):
    s = get_settings()
    client = _cognito_client()
    try:
        client.sign_up(
            ClientId=s.COGNITO_CLIENT_ID,
            Username=payload.email,
            Password=payload.password,
            UserAttributes=[
                {"Name": "email", "Value": payload.email},
                {"Name": "name",  "Value": payload.name},
            ],
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "UsernameExistsException":
            raise HTTPException(409, "email already registered")
        if code == "InvalidPasswordException":
            raise HTTPException(422, "password does not meet requirements")
        raise HTTPException(400, e.response["Error"]["Message"])

    return {"message": "registration successful — check your email to confirm"}


# ── POST /auth/confirm ────────────────────────────────────────────────────────

@router.post("/confirm")
def confirm_email(payload: ConfirmRequest):
    s = get_settings()
    client = _cognito_client()
    try:
        client.confirm_sign_up(
            ClientId=s.COGNITO_CLIENT_ID,
            Username=payload.email,
            ConfirmationCode=payload.code,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "CodeMismatchException":
            raise HTTPException(400, "invalid confirmation code")
        if code == "ExpiredCodeException":
            raise HTTPException(400, "code expired — request a new one")
        raise HTTPException(400, e.response["Error"]["Message"])

    return {"message": "email confirmed — you can now log in"}


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response):
    s = get_settings()
    client = _cognito_client()
    try:
        result = client.initiate_auth(
            ClientId=s.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": payload.email,
                "PASSWORD": payload.password,
            },
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("NotAuthorizedException", "UserNotFoundException"):
            raise HTTPException(401, "invalid email or password")
        if code == "UserNotConfirmedException":
            raise HTTPException(403, "please confirm your email before logging in")
        raise HTTPException(400, e.response["Error"]["Message"])

    auth = result["AuthenticationResult"]
    claims = _decode_id_token_claims(auth["IdToken"])

    user = _upsert_user(
        cognito_sub=claims["sub"],
        email=claims["email"],
        name=claims.get("name", claims["email"].split("@")[0]),
    )

    _set_refresh_cookie(response, auth["RefreshToken"])

    return AuthResponse(
        access_token=auth["AccessToken"],
        id_token=auth["IdToken"],
        expires_in=auth["ExpiresIn"],
        user=UserOut(**user),
    )


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post("/refresh", response_model=AuthResponse)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(401, "session expired — please log in again")

    s = get_settings()
    client = _cognito_client()
    try:
        result = client.initiate_auth(
            ClientId=s.COGNITO_CLIENT_ID,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )
    except ClientError:
        raise HTTPException(401, "invalid session — please log in again")

    auth = result["AuthenticationResult"]
    claims = _decode_id_token_claims(auth["IdToken"])

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, name FROM users WHERE cognito_sub = %s",
            (claims["sub"],),
        )
        row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(401, "user not found")

    user = dict(row)
    user["id"] = str(user["id"])

    if new_rt := auth.get("RefreshToken"):
        _set_refresh_cookie(response, new_rt)

    return AuthResponse(
        access_token=auth["AccessToken"],
        id_token=auth["IdToken"],
        expires_in=auth["ExpiresIn"],
        user=UserOut(**user),
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post("/logout")
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
):
    if refresh_token:
        try:
            s = get_settings()
            _cognito_client().revoke_token(
                Token=refresh_token,
                ClientId=s.COGNITO_CLIENT_ID,
            )
        except Exception:
            pass

    response.delete_cookie("refresh_token", path="/auth")
    return {"message": "logged out"}
