from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="環境名")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://platinum:platinum@db:5432/platinum_axe",
        description="データベース接続URL",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis接続URL",
    )

    # J-Quants API
    JQUANTS_REFRESH_TOKEN: str = Field(
        default="",
        description="J-Quants API リフレッシュトークン",
    )
    JQUANTS_API_BASE_URL: str = Field(
        default="https://api.jquants.com/v1",
        description="J-Quants API ベースURL",
    )

    # ML Model
    ML_MODEL_DIR: str = Field(
        default="/workspace/ml/models",
        description="機械学習モデル保存ディレクトリ",
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="CORS許可オリジン（カンマ区切り）",
    )

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS許可オリジンのリスト"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @computed_field
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.ENVIRONMENT == "production"

    @computed_field
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.ENVIRONMENT == "development"


settings = Settings()
