import curl_cffi
import yt_dlp

# Note: yt-dlp doesn't support looking up an Instagram profile directly from just a
# username (the `instagram:user` extractor was disabled by yt-dlp because the old
# endpoint got blocked by Instagram). What still works is the extractor for a specific
# post/reel/tv, so this function takes a post URL and returns the uploader/user info
# from that post.

# Standard public App ID for Instagram's web client, used by many open-source scrapers
# to look up profiles by username without logging in.
_IG_APP_ID = "936619743392459"


def get_instagram_post_uploader_info(post_url: str, proxy_url: str | None = None, verify_ssl: bool = True) -> dict:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # Photo posts (as opposed to video/reel) have no video format, which yt-dlp
        # treats as an error by default. This option downgrades it to just a warning.
        "ignore_no_formats_error": True,
        "getcomments": True,
    }

    if proxy_url:
        ydl_opts["proxy"] = proxy_url
        # The network path to this proxy MITMs TLS (instagram.com's certificate is
        # replaced with one issued by a "Fortinet" CA), so certificate verification
        # has to be disabled for the proxy to work.
        ydl_opts["nocheckcertificate"] = not verify_ssl

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(post_url, download=False)

    # Carousel posts (multiple photos/videos) show up as info['entries'], each with its
    # own thumbnails/formats. Single posts have both directly on info.
    items = info.get("entries", [info])

    # "thumbnails" are ordered from lowest to highest resolution, so take the last element.
    thumbnail_urls = [item["thumbnails"][-1]["url"] for item in items if item.get("thumbnails")]

    # Photo items have no "formats" at all; video items have multiple qualities,
    # so take the one with the largest width.
    video_urls = [
        max(item["formats"], key=lambda f: f.get("width") or 0)["url"]
        for item in items
        if item.get("formats")
    ]

    return {
        "username": info.get("channel"),
        "uploader_name": info.get("uploader"),
        "uploader_id": info.get("uploader_id"),
        "description": info.get("description"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "upload_date": info.get("upload_date"),
        "thumbnail_urls": thumbnail_urls,
        "video_urls": video_urls,
        "comments": _collect_comments(info, items),
        "profile_photo_url": _get_profile_photo_url(info.get("channel"), proxy_url, verify_ssl),
    }


def _get_profile_photo_url(username: str | None, proxy_url: str | None, verify_ssl: bool) -> str | None:
    # yt-dlp doesn't expose profile_pic_url from the raw user data, so this
    # needs a separate request to Instagram's public endpoint. This is optional
    # enrichment: if it fails or gets rate-limited, degrade to None instead of
    # failing the main post request.
    if not username:
        return None
    try:
        resp = curl_cffi.requests.get(
            "https://www.instagram.com/api/v1/users/web_profile_info/",
            params={"username": username},
            headers={"X-IG-App-ID": _IG_APP_ID},
            impersonate="chrome",
            proxy=proxy_url,
            verify=verify_ssl,
            timeout=10,
        )
        resp.raise_for_status()
        user = resp.json()["data"]["user"]
        return user.get("profile_pic_url_hd") or user.get("profile_pic_url")
    except Exception:
        return None


def _collect_comments(info: dict, items: list[dict]) -> list[dict]:
    # Carousel posts: yt-dlp attaches the same POST comment list to every
    # entry, so merging them raw would duplicate each comment once per media item.
    # Dedupe by "id" (falling back to author_id+text+timestamp when empty).
    seen: set = set()
    result: list[dict] = []
    for source in (info.get("comments"), *(item.get("comments") for item in items)):
        for comment in source or []:
            key = comment.get("id") or (
                comment.get("author_id"),
                comment.get("text"),
                comment.get("timestamp"),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(
                {
                    "id": comment.get("id"),
                    "author": comment.get("author"),
                    "author_id": comment.get("author_id"),
                    "text": comment.get("text"),
                    "like_count": comment.get("like_count"),
                    "timestamp": comment.get("timestamp"),
                }
            )
    # Instagram doesn't send comments_connection.edges in a guaranteed order,
    # so sort by highest like_count first to approximate the "top comments"
    # shown by the Instagram app.
    result.sort(key=lambda c: c["like_count"] or 0, reverse=True)
    return result
