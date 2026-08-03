from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Proxy in "http://user:pass@host:port" format. Optional — if unset, yt-dlp
    # connects directly to Instagram.
    proxy_url: str | None = None

    # Some MITM proxies re-sign TLS certs with their own CA, which breaks
    # verification. Only disable this if you know your proxy does that.
    proxy_verify_ssl: bool = True


settings = Settings()
