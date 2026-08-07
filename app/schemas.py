from pydantic import BaseModel


class Comment(BaseModel):
    id: str | None
    author: str | None
    author_id: str | None
    text: str | None
    like_count: int | None
    timestamp: int | None


class InstagramPostInfo(BaseModel):
    username: str | None
    uploader_name: str | None
    profile_photo_url: str | None
    uploader_id: str | None
    description: str | None
    like_count: int | None
    comment_count: int | None
    upload_date: str | None
    thumbnail_urls: list[str]
    video_urls: list[str]
    comments: list[Comment]
