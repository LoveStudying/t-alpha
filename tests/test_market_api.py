from fastapi.testclient import TestClient

from t_alpha.api.deps import get_market_service
from t_alpha.main import app


class FakeMarketService:
    def get_prices(self, asset_type, code, start_date, end_date, period, adjust):
        return {
            "code": code,
            "asset_type": asset_type,
            "period": period,
            "adjust": adjust,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "normalized_dates": {"start_date": "20240102", "end_date": "20240110"},
            "rows": [{"date": "20240102", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 100.0, "amount": 100.0}],
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }

    def get_fund_nav(self, code, start_date, end_date):
        return {
            "code": code,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "rows": [{"price_date": "20240102", "unit_nav": 1.0, "accum_nav": 1.1, "adj_unit_nav": 1.2, "inner_code": "", "outer_code": "000001"}],
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }


def setup_module():
    app.dependency_overrides[get_market_service] = lambda: FakeMarketService()


def teardown_module():
    app.dependency_overrides.clear()


def test_stock_price_endpoint_shape():
    client = TestClient(app)
    response = client.get("/api/v1/market/stock/prices?code=601318.SH")
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "601318.SH"
    assert payload["asset_type"] == "stock"
    assert payload["rows"][0]["date"] == "20240102"
    assert "不构成投资建议" in payload["disclaimer"]


def test_invalid_adjust_rejected():
    client = TestClient(app)
    response = client.get("/api/v1/market/stock/prices?code=601318.SH&adjust=bad")
    assert response.status_code == 422


def test_fund_nav_endpoint_shape():
    client = TestClient(app)
    response = client.get("/api/v1/market/fund/nav?code=000001.OF")
    assert response.status_code == 200
    assert response.json()["rows"][0]["unit_nav"] == 1.0


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_default_watchlist_endpoint_shape():
    client = TestClient(app)
    response = client.get("/api/v1/strategy/default-watchlist")
    assert response.status_code == 200
    assert response.json()["code"] == "601318.SH"
