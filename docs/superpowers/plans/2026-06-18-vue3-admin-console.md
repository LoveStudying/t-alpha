# Vue3 Admin Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local-use `t-alpha` Vue3 admin console with single-user login, protected FastAPI admin APIs, daily maintenance pages, a long-term planning page, and verification.

**Architecture:** Add protected auth/admin routes to the existing FastAPI app while keeping public market and strategy APIs compatible. Create an independent `web-admin/` Vue3/Vite/TypeScript app that calls the API through an Axios client and can optionally be served from `web-admin/dist` by FastAPI.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy, pytest, Vue 3, Vite, TypeScript, Vue Router, Pinia, Axios, Element Plus, ECharts.

---

## File Structure

Backend files:

- Create `src/t_alpha/api/auth.py`: signed token helpers and admin dependency.
- Create `src/t_alpha/api/routes_auth.py`: login, me, logout endpoints.
- Create `src/t_alpha/api/routes_admin.py`: overview, settings summary, watchlist CRUD, reports, positions, alerts.
- Modify `src/t_alpha/config.py`: add admin settings.
- Modify `src/t_alpha/api/deps.py`: add optional database session factory helpers and strategy service with session support.
- Modify `src/t_alpha/api/schemas.py`: add auth/admin schemas.
- Modify `src/t_alpha/main.py`: include new routers and optional static frontend mount.
- Modify `tests/conftest.py` only if shared test fixtures are needed.
- Create `tests/test_auth_api.py`.
- Create `tests/test_admin_api.py`.

Frontend files:

- Create `web-admin/package.json`, `index.html`, `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`.
- Create `web-admin/src/main.ts`, `App.vue`, `router/index.ts`.
- Create `web-admin/src/stores/auth.ts`.
- Create `web-admin/src/services/http.ts`, `services/auth.ts`, `services/admin.ts`, `services/market.ts`, `services/strategy.ts`.
- Create `web-admin/src/layouts/AdminLayout.vue`.
- Create reusable components in `web-admin/src/components/`.
- Create views in `web-admin/src/views/`.
- Create style tokens in `web-admin/src/styles/`.

---

### Task 1: Backend Auth Settings And Token API

**Files:**
- Modify: `src/t_alpha/config.py`
- Create: `src/t_alpha/api/auth.py`
- Create: `src/t_alpha/api/routes_auth.py`
- Modify: `src/t_alpha/api/schemas.py`
- Modify: `src/t_alpha/main.py`
- Test: `tests/test_auth_api.py`

- [ ] **Step 1: Write failing auth API tests**

Create `tests/test_auth_api.py`:

```python
from fastapi.testclient import TestClient

from t_alpha.api.deps import get_settings
from t_alpha.config import Settings
from t_alpha.main import app


def override_settings():
    return Settings(
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="secret",
        ADMIN_TOKEN_SECRET="unit-test-secret",
        ADMIN_SESSION_TTL_SECONDS=3600,
    )


def setup_function():
    app.dependency_overrides[get_settings] = override_settings


def teardown_function():
    app.dependency_overrides.clear()


def test_login_returns_bearer_token_for_valid_credentials():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "admin"


def test_login_rejects_invalid_credentials():
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid username or password"


def test_me_requires_valid_bearer_token():
    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})
    token = login.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_me_rejects_missing_token():
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
```

- [ ] **Step 2: Run auth tests and verify RED**

Run: `pytest tests/test_auth_api.py -q`

Expected: FAIL because `/api/v1/auth/login` and `/api/v1/auth/me` do not exist.

- [ ] **Step 3: Add admin settings**

Modify `src/t_alpha/config.py` inside `Settings`:

```python
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")
    admin_token_secret: str = Field(default="dev-admin-token-secret", alias="ADMIN_TOKEN_SECRET")
    admin_session_ttl_seconds: int = Field(default=8 * 60 * 60, alias="ADMIN_SESSION_TTL_SECONDS")
```

- [ ] **Step 4: Add auth schemas**

Modify `src/t_alpha/api/schemas.py`:

```python
class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AdminUser(BaseModel):
    username: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AdminUser
```

- [ ] **Step 5: Implement token helpers**

Create `src/t_alpha/api/auth.py`:

```python
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
    return _b64encode(hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest())


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
```

- [ ] **Step 6: Implement auth routes**

Create `src/t_alpha/api/routes_auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException

from t_alpha.api.auth import create_admin_token, get_current_admin_user
from t_alpha.api.deps import get_settings
from t_alpha.api.schemas import AdminUser, LoginRequest, LoginResponse
from t_alpha.config import Settings


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, settings: Settings = Depends(get_settings)):
    if request.username != settings.admin_username or request.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="invalid username or password")
    return LoginResponse(
        access_token=create_admin_token(request.username, settings),
        user=AdminUser(username=request.username),
    )


@router.get("/me", response_model=AdminUser)
def me(username: str = Depends(get_current_admin_user)):
    return AdminUser(username=username)


@router.post("/logout")
def logout(username: str = Depends(get_current_admin_user)):
    return {"status": "ok", "username": username}
```

- [ ] **Step 7: Include auth router**

Modify `src/t_alpha/main.py`:

```python
from t_alpha.api.routes_auth import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 8: Verify GREEN**

Run: `pytest tests/test_auth_api.py -q`

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
git add src/t_alpha/config.py src/t_alpha/api/auth.py src/t_alpha/api/routes_auth.py src/t_alpha/api/schemas.py src/t_alpha/main.py tests/test_auth_api.py
git commit -m "feat: add admin auth api"
```

---

### Task 2: Protected Admin Data API

**Files:**
- Modify: `src/t_alpha/api/deps.py`
- Create: `src/t_alpha/api/routes_admin.py`
- Modify: `src/t_alpha/api/schemas.py`
- Modify: `src/t_alpha/main.py`
- Test: `tests/test_admin_api.py`

- [ ] **Step 1: Write failing admin API tests**

Create `tests/test_admin_api.py`:

```python
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from t_alpha.api.deps import get_db_session, get_settings
from t_alpha.config import Settings
from t_alpha.main import app
from t_alpha.storage.models import AlertRecord, Base, T0Position, T0StrategyReportRow, Watchlist


def override_settings():
    return Settings(
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="secret",
        ADMIN_TOKEN_SECRET="unit-test-secret",
        ADMIN_SESSION_TTL_SECONDS=3600,
    )


def make_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def auth_headers(client: TestClient):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "secret"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def setup_function():
    session_factory = make_session_factory()

    def override_db_session():
        session = session_factory()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    with session_factory() as session:
        session.add(Watchlist(code="601318.SH", name="中国平安", strategy_name="mean_reversion_t0_v1", enabled=True))
        session.add(
            T0StrategyReportRow(
                code="601318.SH",
                strategy_name="mean_reversion_t0_v1",
                params_json='{"target_return": 0.03}',
                report_json='{"eligibility": {"eligible": true}}',
                eligible=True,
                eligibility_level="eligible",
            )
        )
        session.add(
            T0Position(
                code="601318.SH",
                strategy_name="mean_reversion_t0_v1",
                status="open",
                payload_json='{"target_sell_price": 42.0}',
            )
        )
        session.add(
            AlertRecord(
                code="601318.SH",
                signal_time=datetime(2026, 6, 18, 10, 0, 0),
                signal_type="buy",
                payload_json='{"current_price": 40.0}',
                sent=True,
            )
        )
        session.commit()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_db_session] = override_db_session


def teardown_function():
    app.dependency_overrides.clear()


def test_admin_overview_requires_auth():
    client = TestClient(app)

    response = client.get("/api/v1/admin/overview")

    assert response.status_code == 401


def test_admin_overview_returns_counts():
    client = TestClient(app)

    response = client.get("/api/v1/admin/overview", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["watchlist_count"] == 1
    assert body["enabled_watchlist_count"] == 1
    assert body["open_position_count"] == 1
    assert body["recent_alert_count"] == 1


def test_watchlist_crud_roundtrip():
    client = TestClient(app)
    headers = auth_headers(client)

    created = client.post(
        "/api/v1/admin/watchlist",
        headers=headers,
        json={"code": "000001.SZ", "name": "平安银行", "enabled": False, "strategy_name": "mean_reversion_t0_v1", "note": "test"},
    )
    assert created.status_code == 200
    row_id = created.json()["id"]

    patched = client.patch(f"/api/v1/admin/watchlist/{row_id}", headers=headers, json={"enabled": True, "note": "updated"})
    assert patched.status_code == 200
    assert patched.json()["enabled"] is True
    assert patched.json()["note"] == "updated"

    listed = client.get("/api/v1/admin/watchlist", headers=headers)
    assert any(row["code"] == "000001.SZ" for row in listed.json()["items"])


def test_admin_records_parse_json_payloads():
    client = TestClient(app)
    headers = auth_headers(client)

    reports = client.get("/api/v1/admin/t0/reports", headers=headers)
    positions = client.get("/api/v1/admin/t0/positions", headers=headers)
    alerts = client.get("/api/v1/admin/alerts", headers=headers)

    assert reports.json()["items"][0]["report"]["eligibility"]["eligible"] is True
    assert positions.json()["items"][0]["payload"]["target_sell_price"] == 42.0
    assert alerts.json()["items"][0]["payload"]["current_price"] == 40.0


def test_settings_summary_masks_sensitive_values():
    client = TestClient(app)

    response = client.get("/api/v1/admin/settings/summary", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert "admin_password" not in body
    assert body["admin_configured"] is True
```

- [ ] **Step 2: Run admin tests and verify RED**

Run: `pytest tests/test_admin_api.py -q`

Expected: FAIL because `get_db_session` and admin routes do not exist.

- [ ] **Step 3: Add admin schemas**

Modify `src/t_alpha/api/schemas.py` with models for `PagedResponse`, `WatchlistCreate`, `WatchlistUpdate`, `WatchlistOut`, `AdminOverview`, `SettingsSummary`, `T0ReportOut`, `T0PositionOut`, `AlertRecordOut`. Use `dict | str | None` fields for parsed JSON.

- [ ] **Step 4: Add database dependency**

Modify `src/t_alpha/api/deps.py`:

```python
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

from t_alpha.storage.database import build_session_factory, create_mysql_engine


@lru_cache
def get_session_factory():
    engine = create_mysql_engine(get_settings())
    return build_session_factory(engine)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Update `get_strategy_service` to accept `session: Session = Depends(get_db_session)` only in route-level usage if required, or create a separate dependency `get_persistent_strategy_service`.

- [ ] **Step 5: Implement admin routes**

Create `src/t_alpha/api/routes_admin.py` with:

- `GET /overview`
- `GET /settings/summary`
- `GET/POST/PATCH/DELETE /watchlist`
- `GET /t0/reports`, `GET /t0/reports/{id}`
- `GET /t0/positions`, `GET /t0/positions/{id}`
- `GET /alerts`, `GET /alerts/{id}`

Every route depends on `get_current_admin_user`.

- [ ] **Step 6: Include admin router**

Modify `src/t_alpha/main.py`:

```python
from t_alpha.api.routes_admin import router as admin_router

app.include_router(admin_router)
```

- [ ] **Step 7: Verify GREEN**

Run: `pytest tests/test_admin_api.py -q`

Expected: PASS.

- [ ] **Step 8: Run backend API regression tests**

Run: `pytest tests/test_auth_api.py tests/test_admin_api.py tests/test_strategy_api.py tests/test_market_api.py -q`

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
git add src/t_alpha/api/deps.py src/t_alpha/api/routes_admin.py src/t_alpha/api/schemas.py src/t_alpha/main.py tests/test_admin_api.py
git commit -m "feat: add protected admin data api"
```

---

### Task 3: Vue3 App Shell, Auth, Layout

**Files:**
- Create frontend project files under `web-admin/`
- Create auth store, HTTP client, router, layout, login and dashboard shell views

- [ ] **Step 1: Create Vite project files**

Create package scripts:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview --host 127.0.0.1"
  }
}
```

- [ ] **Step 2: Install frontend dependencies**

Run in `web-admin/`:

```bash
npm install vue@^3 @vitejs/plugin-vue vite typescript vue-tsc vue-router@^4 pinia axios element-plus @element-plus/icons-vue echarts
```

Expected: dependencies installed and `package-lock.json` created.

- [ ] **Step 3: Implement auth store and router guard**

Create `src/stores/auth.ts` with `login`, `loadMe`, `logout`, `isAuthenticated`.

Create `src/router/index.ts` with routes:

- `/login`
- `/`
- `/market`
- `/strategy/t0`
- `/watchlist`
- `/records`
- `/system`
- `/roadmap`

- [ ] **Step 4: Implement HTTP client**

Create `src/services/http.ts` with Axios instance, `VITE_API_BASE_URL` default, Bearer token injection, 401 logout handling.

- [ ] **Step 5: Implement app layout**

Create `AdminLayout.vue` with sidebar navigation, topbar, responsive collapse, and router outlet.

- [ ] **Step 6: Implement LoginView and placeholder route views**

Create functional login page and placeholder views for every route so navigation is complete before feature pages are filled in.

- [ ] **Step 7: Verify frontend build**

Run: `npm run build` in `web-admin/`

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```bash
git add web-admin
git commit -m "feat: scaffold vue admin shell"
```

---

### Task 4: Core Daily Operation Pages

**Files:**
- Create/modify `web-admin/src/views/DashboardView.vue`
- Create/modify `web-admin/src/views/MarketQueryView.vue`
- Create/modify `web-admin/src/views/T0StrategyView.vue`
- Create `web-admin/src/services/admin.ts`
- Create `web-admin/src/services/market.ts`
- Create `web-admin/src/services/strategy.ts`
- Create components `MetricTile.vue`, `RiskDisclaimer.vue`, `StatusBadge.vue`

- [ ] **Step 1: Implement API services**

Add typed service functions for overview, settings summary, market query, T0 build, and T0 monitor.

- [ ] **Step 2: Implement DashboardView**

Show admin overview metrics, health status, recent record tables, and quick action buttons.

- [ ] **Step 3: Implement MarketQueryView**

Build form controls for asset type, code, dates, period, adjust. Render ECharts line chart and Element Plus table. Show requested and normalized dates.

- [ ] **Step 4: Implement T0StrategyView**

Build code input, report generation action, metric sections, eligibility reasons, recent trades table, and monitor enable action when eligible.

- [ ] **Step 5: Verify frontend build**

Run: `npm run build` in `web-admin/`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add web-admin
git commit -m "feat: add admin daily operation pages"
```

---

### Task 5: Maintenance Records, System, Roadmap

**Files:**
- Create/modify `web-admin/src/views/WatchlistView.vue`
- Create/modify `web-admin/src/views/RecordsView.vue`
- Create/modify `web-admin/src/views/SystemView.vue`
- Create/modify `web-admin/src/views/RoadmapView.vue`
- Create components `JsonDrawer.vue`, `DataTableToolbar.vue`

- [ ] **Step 1: Implement watchlist maintenance**

List watchlist rows, add/edit dialog, enable toggle, delete confirmation, and direct generate-report action.

- [ ] **Step 2: Implement records tabs**

Add reports, positions, and alerts tabs with paged tables and JSON detail drawer.

- [ ] **Step 3: Implement system settings summary**

Show masked settings, admin configuration state, API docs link, and environment summary.

- [ ] **Step 4: Implement long-term roadmap page**

Static page covering future system direction: multi-strategy, realtime snapshots, risk filters, task orchestration, report center, read-only account validation, future permissions, deployment security.

- [ ] **Step 5: Verify frontend build**

Run: `npm run build` in `web-admin/`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add web-admin
git commit -m "feat: add admin maintenance and roadmap pages"
```

---

### Task 6: Static Frontend Hosting And Final Verification

**Files:**
- Modify `src/t_alpha/main.py`
- Modify `README.md` or create `docs/admin_console_usage.md`
- Verify all touched behavior

- [ ] **Step 1: Add optional static mount**

Modify `src/t_alpha/main.py` to mount `web-admin/dist` if it exists. Keep `/api`, `/docs`, `/openapi.json`, and `/health` unaffected.

- [ ] **Step 2: Add usage docs**

Document:

- backend startup
- frontend dev startup
- admin env vars
- build command
- local static serving behavior

- [ ] **Step 3: Run backend tests**

Run: `pytest -q`

Expected: PASS, except failures caused by pre-existing unrelated user changes must be isolated and reported.

- [ ] **Step 4: Run frontend build**

Run: `npm run build` in `web-admin/`

Expected: PASS.

- [ ] **Step 5: Smoke-test app startup**

Run backend:

```bash
$env:PYTHONPATH="src"
python -m uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867
```

Verify:

- `GET /health` returns `{"status":"ok"}`
- `GET /docs` returns Swagger UI
- frontend dev server can open login page

- [ ] **Step 6: Commit**

Run:

```bash
git add src/t_alpha/main.py docs/admin_console_usage.md README.md
git commit -m "feat: serve and document admin console"
```

---

## Self-Review

Spec coverage:

- Single-user login: Task 1.
- Protected management APIs: Task 2.
- Vue3/Vite independent frontend: Task 3.
- Daily operation pages: Task 4.
- Watchlist, reports, positions, alerts, system, roadmap: Task 5.
- Static serving and verification: Task 6.

Placeholder scan:

- The plan avoids unfinished marker words and undefined future steps.
- Backend tests are concrete and define expected API shape.
- Frontend tasks are page-level because generated Vue SFC source will be implemented directly during execution and verified by TypeScript/Vite.

Type consistency:

- Auth endpoints use `/api/v1/auth/**`.
- Admin endpoints use `/api/v1/admin/**`.
- Token header is `Authorization: Bearer <token>`.
- Existing public market and strategy endpoints remain unchanged.
