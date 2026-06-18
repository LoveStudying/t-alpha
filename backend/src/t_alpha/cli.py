import uvicorn

from t_alpha.config import Settings


def run_api() -> None:
    settings = Settings()
    uvicorn.run(
        "t_alpha.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "dev",
    )
