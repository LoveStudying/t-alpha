from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from t_alpha.api.deps import get_settings
from t_alpha.config import Settings


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_admin_token(username: str, settings: Settings, now: int | None = None) -> str:
    issued_at = int(now if now is not None else time.time())
    payload = {
        "sub": username,
        "iat": issued_at,
        "exp": issued_at + settings.admin_session_ttl_seconds,
    }
    payload_part = _b64encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signature = _sign(payload_part, settings.admin_token_secret)
    return f"{payload_part}.{signature}"


def verify_admin_token(token: str, settings: Settings, now: int | None = None) -> str:
    try:
        payload_part, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc

    expected = _sign(payload_part, settings.admin_token_secret)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="invalid token")

    try:
        payload = json.loads(_b64decode(payload_part).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc

    current_time = int(now if now is not None else time.time())
    if int(payload.get("exp", 0)) < current_time:
        raise HTTPException(status_code=401, detail="token expired")

    username = str(payload.get("sub", ""))
    if username != settings.admin_username:
        raise HTTPException(status_code=401, detail="invalid token")
    return username


def get_current_admin_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return verify_admin_token(authorization.removeprefix("Bearer ").strip(), settings)
