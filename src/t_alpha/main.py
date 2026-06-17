from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


WEB_ADMIN_DIST = Path(__file__).resolve().parents[2] / "web-admin" / "dist"

if WEB_ADMIN_DIST.exists():
    assets_dir = WEB_ADMIN_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="web-admin-assets")

    @app.get("/")
    def web_admin_index():
        return FileResponse(WEB_ADMIN_DIST / "index.html")

    @app.get("/{full_path:path}")
    def web_admin_spa(full_path: str):
        reserved_prefixes = ("api/", "docs", "openapi.json", "health")
        if full_path.startswith(reserved_prefixes):
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(WEB_ADMIN_DIST / "index.html")
