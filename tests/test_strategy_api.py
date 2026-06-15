from fastapi.testclient import TestClient

from t_alpha.api.deps import get_strategy_service
from t_alpha.main import app


class FakeStrategyService:
    def build_report(self, code):
        return {
            "code": code,
            "strategy_name": "mean_reversion_t0_v1",
            "params": {"target_return": 0.03},
            "full_metrics": {"trade_count": 60},
            "train_metrics": {"trade_count": 40},
            "validation_metrics": {"trade_count": 20},
            "recent_metrics": {"trade_count": 3},
            "recent_trades": [],
            "eligibility": {"eligible": True, "level": "eligible", "reasons": []},
            "generated_at": "2024-01-02 10:00:00",
            "disclaimer": "research only",
        }

    def enable_monitor(self, code, enabled):
        return {"code": code, "enabled": enabled, "strategy_name": "mean_reversion_t0_v1"}


def setup_module():
    app.dependency_overrides[get_strategy_service] = lambda: FakeStrategyService()


def teardown_module():
    app.dependency_overrides.clear()


def test_t0_build_endpoint_returns_report():
    client = TestClient(app)
    response = client.post("/api/v1/strategy/t0/build", json={"code": "601318.SH"})

    assert response.status_code == 200
    assert response.json()["code"] == "601318.SH"
    assert response.json()["eligibility"]["eligible"] is True


def test_t0_monitor_endpoint_toggles_enabled():
    client = TestClient(app)
    response = client.post("/api/v1/strategy/t0/monitor", json={"code": "601318.SH", "enabled": True})

    assert response.status_code == 200
    assert response.json()["enabled"] is True
