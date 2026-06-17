from fastapi import FastAPI

from t_alpha.api.routes_admin import router as admin_router
from t_alpha.api.routes_auth import router as auth_router
from t_alpha.api.routes_market import router as market_router
from t_alpha.api.routes_strategy import router as strategy_router


app = FastAPI(title="t-alpha", version="0.1.0")
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(market_router)
app.include_router(strategy_router)


@app.get("/health")
def health():
    return {"status": "ok"}
