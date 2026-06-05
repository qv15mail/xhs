from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDSCOPE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./redscope.db"
    # 采集模式：mock（默认，安全演示）/ real（Playwright 真实采集，需自有登录态）
    collect_mode: str = "mock"
    cors_origins: str = "http://localhost:5173"

    # 默认 LLM 配置（也可在前端「设置」里覆盖并落库）
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.8

    # Playwright 持久化登录态目录
    user_data_dir: str = "./.xhs-user-data"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
