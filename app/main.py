from fastapi import FastAPI, HTTPException, Query
from yt_dlp.utils import DownloadError

from app.config import settings
from app.instagram import get_instagram_post_uploader_info
from app.schemas import InstagramPostInfo

app = FastAPI(title="instagram-dlp", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/instagram/post", response_model=InstagramPostInfo)
def instagram_info(url: str = Query(..., description="Instagram post/reel/tv URL")) -> dict:
    try:
        return get_instagram_post_uploader_info(
            url,
            proxy_url=settings.proxy_url,
            verify_ssl=settings.proxy_verify_ssl,
        )
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
