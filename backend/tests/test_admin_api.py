from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
        SMTP_USERNAME="sender@example.com",
        SMTP_PASSWORD="smtp-secret",
        ALERT_TO="receiver@example.com",
    )


def make_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
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
        json={
            "code": "000001.SZ",
            "name": "平安银行",
            "enabled": False,
            "strategy_name": "mean_reversion_t0_v1",
            "note": "test",
        },
    )
    assert created.status_code == 200
    row_id = created.json()["id"]

    patched = client.patch(f"/api/v1/admin/watchlist/{row_id}", headers=headers, json={"enabled": True, "note": "updated"})
    assert patched.status_code == 200
    assert patched.json()["enabled"] is True
    assert patched.json()["note"] == "updated"

    listed = client.get("/api/v1/admin/watchlist", headers=headers)
    assert any(row["code"] == "000001.SZ" for row in listed.json()["items"])

    deleted = client.delete(f"/api/v1/admin/watchlist/{row_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_admin_records_parse_json_payloads():
    client = TestClient(app)
    headers = auth_headers(client)

    reports = client.get("/api/v1/admin/t0/reports", headers=headers)
    positions = client.get("/api/v1/admin/t0/positions", headers=headers)
    alerts = client.get("/api/v1/admin/alerts", headers=headers)

    assert reports.status_code == 200
    assert positions.status_code == 200
    assert alerts.status_code == 200
    assert reports.json()["items"][0]["report"]["eligibility"]["eligible"] is True
    assert positions.json()["items"][0]["payload"]["target_sell_price"] == 42.0
    assert alerts.json()["items"][0]["payload"]["current_price"] == 40.0


def test_settings_summary_masks_sensitive_values():
    client = TestClient(app)

    response = client.get("/api/v1/admin/settings/summary", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert "admin_password" not in body
    assert "smtp_password" not in body
    assert body["admin_configured"] is True
    assert body["smtp_configured"] is True
