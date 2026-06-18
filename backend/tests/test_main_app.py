import importlib
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

import t_alpha.main as main_module


def test_app_does_not_serve_web_admin_dist():
    web_admin_dist = Path(main_module.__file__).resolve().parents[2] / "web-admin" / "dist"
    created_dist = not web_admin_dist.exists()

    if created_dist:
        (web_admin_dist / "assets").mkdir(parents=True)
        (web_admin_dist / "index.html").write_text("<html>admin</html>", encoding="utf-8")
        (web_admin_dist / "assets" / "app.js").write_text("console.log('admin')", encoding="utf-8")

    try:
        reloaded_main = importlib.reload(main_module)
        client = TestClient(reloaded_main.app)

        response = client.get("/")

        assert response.status_code == 404
        assert all(route.name != "web-admin-assets" for route in reloaded_main.app.routes)
    finally:
        if created_dist:
            shutil.rmtree(web_admin_dist)
        importlib.reload(main_module)
