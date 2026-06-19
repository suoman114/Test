from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 설정. backend/.env 에서 로드."""

    bitbucket_base_url: str = "https://bitbucket.example.com"
    bitbucket_project_key: str = "PKG"
    bitbucket_token: str = "changeme"

    # repo 루트 기준 tar 경로. 버전은 git tag 로 식별한다.
    package_tar_path: str = "package.tar"

    # 노출할 repo slug 정규식 필터 (빈 문자열이면 전체)
    repo_slug_filter: str = ""

    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
