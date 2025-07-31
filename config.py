from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "HXQ ADE Proxy"
    MAIN_SYSTEM_URL: str = "http://main-service:8000"
    BACKUP_SYSTEM_URL: str = "http://backup-service:8000"
    TIMEOUT: int = 10

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # 管理员手机号
    ADMIN_MOBILE: str = "18888888888"

    # SMS
    IS_SEND_SMS: bool = True
    SMS_HOST: str = "https://sms.haoxinqing.cn"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
