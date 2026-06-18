from pathlib import Path

from t_alpha.config import Settings


def test_settings_reads_required_environment(monkeypatch):
    monkeypatch.setenv("AD_USERNAME", "210400052339")
    monkeypatch.setenv("AD_PASSWORD", "secret")
    monkeypatch.setenv("AD_HOST", "140.206.44.234")
    monkeypatch.setenv("AD_PORT", "8600")
    monkeypatch.setenv("DB_HOST", "47.93.240.45")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USERNAME", "testroot")
    monkeypatch.setenv("DB_PASSWORD", "db-secret")
    monkeypatch.setenv("DB_NAME", "t_alpha")

    settings = Settings()

    assert settings.ad_username == "210400052339"
    assert settings.ad_port == 8600
    assert settings.db_name == "t_alpha"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8867
    assert settings.mysql_url.startswith("mysql+pymysql://testroot:")
    assert settings.smtp_host == "smtp.163.com"
    assert settings.commission_rate == 0.0001
    assert settings.min_trade_amount == 5000
    assert settings.max_trade_amount == 20000


def test_settings_masks_secrets(monkeypatch):
    monkeypatch.setenv("AD_PASSWORD", "Ttxs0727")
    monkeypatch.setenv("DB_PASSWORD", "zbmlhj8s")

    settings = Settings()

    assert "Ttxs0727" not in settings.safe_summary()
    assert "zbmlhj8s" not in settings.safe_summary()


def test_settings_reads_api_server_port(monkeypatch):
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_PORT", "9000")

    settings = Settings()

    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 9000


def test_settings_env_file_is_backend_local():
    expected_env_file = Path(__file__).resolve().parents[1] / ".env"

    assert Settings.model_config["env_file"] == expected_env_file
