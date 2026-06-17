from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from t_alpha.constants import DEFAULT_TEST_CODE, PROJECT_DB_NAME


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ad_username: str = Field(default="", alias="AD_USERNAME")
    ad_password: str = Field(default="", alias="AD_PASSWORD")
    ad_host: str = Field(default="", alias="AD_HOST")
    ad_port: int = Field(default=8600, alias="AD_PORT")

    amazingdata_local_path: str = Field(default="D:/AmazingData_local_data/", alias="AMAZINGDATA_LOCAL_PATH")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_username: str = Field(default="root", alias="DB_USERNAME")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name: str = Field(default=PROJECT_DB_NAME, alias="DB_NAME")

    smtp_host: str = Field(default="smtp.163.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")
    alert_to: str = Field(default="", alias="ALERT_TO")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8867, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")
    admin_token_secret: str = Field(default="dev-admin-token-secret", alias="ADMIN_TOKEN_SECRET")
    admin_session_ttl_seconds: int = Field(default=8 * 60 * 60, alias="ADMIN_SESSION_TTL_SECONDS")
    default_test_code: str = DEFAULT_TEST_CODE
    min_trade_amount: int = Field(default=5000, alias="MIN_TRADE_AMOUNT")
    max_trade_amount: int = Field(default=20000, alias="MAX_TRADE_AMOUNT")
    commission_rate: float = Field(default=0.0001, alias="COMMISSION_RATE")
    t0_target_return: float = Field(default=0.03, alias="T0_TARGET_RETURN")
    t0_max_holding_trade_days: int = Field(default=10, alias="T0_MAX_HOLDING_TRADE_DAYS")
    t0_trade_cost_rate: float = Field(default=0.0001, alias="T0_TRADE_COST_RATE")
    t0_min_3y_trades: int = Field(default=60, alias="T0_MIN_3Y_TRADES")
    t0_observe_min_3y_trades: int = Field(default=30, alias="T0_OBSERVE_MIN_3Y_TRADES")
    t0_min_success_rate: float = Field(default=0.65, alias="T0_MIN_SUCCESS_RATE")

    @cached_property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    def validate_project_database(self) -> None:
        # 防止误连到非项目库，避免初始化或写入越界。
        if self.db_name != PROJECT_DB_NAME:
            raise ValueError(f"DB_NAME must be {PROJECT_DB_NAME!r}; got {self.db_name!r}")

    def safe_summary(self) -> str:
        return (
            f"AD_USERNAME={self.ad_username}, AD_HOST={self.ad_host}, AD_PORT={self.ad_port}, "
            f"DB_HOST={self.db_host}, DB_PORT={self.db_port}, DB_NAME={self.db_name}, "
            f"APP_ENV={self.app_env}, APP_HOST={self.app_host}, APP_PORT={self.app_port}, LOG_LEVEL={self.log_level}"
        )
