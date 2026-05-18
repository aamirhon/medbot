from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_TELEGRAM_IDS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://medbot:medbot@localhost:5432/medbot"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_PASSWORD: str = "medbot"
    DEV_MODE: bool = False

    ONE_C_URL: str = "http://localhost/Base"
    ONE_C_USER: str = "sync"
    ONE_C_PASSWORD: str = "secret"
    ONE_C_TIMEOUT: float = 30.0

    SYNC_PRODUCTS_INTERVAL: int = 900   # 15 минут
    SYNC_STOCK_INTERVAL: int = 300      # 5 минут
    SYNC_ORDERS_INTERVAL: int = 600     # 10 минут
    SYNC_PAYMENTS_INTERVAL: int = 600   # 10 минут

    @property
    def admin_ids(self) -> set[int]:
        return {int(x) for x in self.ADMIN_TELEGRAM_IDS.split(",") if x.strip()}

    class Config:
        env_file = ".env"


settings = Settings()
