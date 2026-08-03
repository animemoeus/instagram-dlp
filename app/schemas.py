from pydantic import BaseModel


class InstagramPostInfo(BaseModel):
    username: str | None
    uploader_name: str | None
    uploader_id: str | None
    description: str | None
    like_count: int | None
    comment_count: int | None
    upload_date: str | None
    thumbnail_urls: list[str]
    video_urls: list[str]
