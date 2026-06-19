from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 설정. backend/.env 에서 로드."""

    bitbucket_base_url: str = "https://bitbucket.example.com"
    bitbucket_project_key: str = "PKG"

    # 인증: 둘 중 하나를 쓴다.
    #  - 최신 Bitbucket(5.5+): Personal Access Token → bitbucket_token (Bearer)
    #  - 구버전(PAT 메뉴 없음): 아이디/비밀번호 → bitbucket_username + bitbucket_password (Basic)
    # username/password 가 모두 채워져 있으면 Basic 을, 아니면 token(Bearer)을 쓴다.
    bitbucket_token: str = "changeme"
    bitbucket_username: str = ""
    bitbucket_password: str = ""

    @property
    def use_basic_auth(self) -> bool:
        return bool(self.bitbucket_username and self.bitbucket_password)

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
