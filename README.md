# instagram-dlp

Welcome to the world's most niche API: a web service with exactly one job. Hand it an Instagram post/reel URL, and it hands back the uploader info, caption, like count, comments, and video/thumbnail links. It's not magic, it's just `yt-dlp` wearing a FastAPI costume to look professional.

## What's in the box

- `GET /health` checks whether the server is alive or just quietly rotting. Always answers `{"status": "ok"}`, because let's be honest, if the server were actually dead this endpoint wouldn't answer at all.
- `GET /instagram/post?url=...` is the whole point of this project. Feed it a post/reel/tv URL and get back JSON with username, uploader name, profile photo, caption, like count, comment count, upload date, video/thumbnail URLs, and the full comment list.

If the URL is garbage or Instagram is having a mood, you get a `400` straight from yt-dlp with the error message attached. Don't blame me, blame Instagram for making their API deliberately annoying.

## Example

```
https://instagram-dlp.animemoe.us/instagram/post?url=https://www.instagram.com/p/Clb-h2Uy_Xr/
```

```json
{
    "username": "udon05310531",
    "uploader_name": "山本崇一朗",
    "uploader_id": "32917698626",
    "description": null,
    "like_count": 4879,
    "comment_count": 32,
    "upload_date": "20221126",
    "thumbnail_urls": [
        "https://scontent-sin2-1.cdninstagram.com/v/t51.82787-15/626671446_..._n.jpg?...signed URL"
    ],
    "video_urls": []
}
```

Yes, `profile_photo_url` and `comments` are missing here, this example is just older than those fields. Hit the endpoint yourself and you'll get the full schema.

## Running it

Use [uv](https://docs.astral.sh/uv/), because installing packages one by one with plain `pip` is a crime against your own time:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or if you can't be bothered installing anything and already have Docker lying around:

```bash
docker compose up --build
```

## Configuration

Everything lives in `.env` (copy `.env.example` to get started):

| Variable | What it does |
| --- | --- |
| `PROXY_URL` | Proxy for yt-dlp to reach Instagram through, format `http://user:pass@host:port`. Leave it empty if Instagram still trusts your IP. |
| `PROXY_VERIFY_SSL` | Set to `false` only if your proxy MITMs and re-signs TLS certs. Otherwise leave it alone. |

If Instagram starts blocking your IP, that's not a bug, that's a consequence. Get a proxy, or stop scraping like it's a competitive sport.

## Quick disclaimer

This thing pulls public data from Instagram posts. It is not a license to mass scrape, stalk people's accounts, or do anything that gets your lawyer's phone ringing. Use it responsibly, or at least quietly.
