import curl_cffi
import yt_dlp

# Catatan: yt-dlp tidak mendukung lookup profil Instagram langsung dari username saja
# (extractor `instagram:user` sudah dinonaktifkan oleh yt-dlp karena endpoint lama diblokir
# Instagram). Yang masih berfungsi adalah extractor untuk post/reel/tv spesifik, jadi fungsi
# ini menerima URL post dan mengembalikan info uploader/user dari post tersebut.

# App ID publik standar web client Instagram, dipakai banyak scraper open-source
# untuk lookup profil by username tanpa login.
_IG_APP_ID = "936619743392459"


def get_instagram_post_uploader_info(post_url: str, proxy_url: str | None = None, verify_ssl: bool = True) -> dict:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # Post foto (bukan video/reel) tidak punya format video, yang oleh yt-dlp
        # dianggap error secara default. Opsi ini mengubahnya jadi warning saja.
        "ignore_no_formats_error": True,
        "getcomments": True,
    }

    if proxy_url:
        ydl_opts["proxy"] = proxy_url
        # Jaringan di path menuju proxy ini mem-MITM TLS (sertifikat instagram.com
        # diganti dengan sertifikat terbitan CA "Fortinet"), jadi verifikasi sertifikat
        # harus dimatikan supaya proxy bisa dipakai.
        ydl_opts["nocheckcertificate"] = not verify_ssl

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(post_url, download=False)

    # Post carousel (banyak foto/video) muncul sebagai info['entries'], masing-masing
    # dengan thumbnails/formats-nya sendiri. Post tunggal punya keduanya langsung di info.
    items = info.get("entries", [info])

    # "thumbnails" berurutan dari resolusi terendah ke tertinggi, jadi ambil elemen terakhir.
    thumbnail_urls = [item["thumbnails"][-1]["url"] for item in items if item.get("thumbnails")]

    # Item foto tidak punya "formats" sama sekali; item video punya beberapa kualitas,
    # ambil yang width-nya terbesar.
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
    # yt-dlp tidak mengekspos profile_pic_url dari data user mentah, jadi ini
    # butuh request terpisah ke endpoint publik Instagram. Enrichment opsional:
    # kalau gagal/di-rate-limit, degrade ke None, jangan sampai bikin request
    # post utama gagal.
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
    # Post carousel: yt-dlp menempelkan list komentar POST yang sama ke setiap
    # entry, jadi digabung mentah-mentah akan terduplikasi sebanyak jumlah media.
    # Dedupe berdasarkan "id" (fallback ke author_id+text+timestamp kalau kosong).
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
    # Instagram tidak mengirim comments_connection.edges dalam urutan yang
    # dijamin, jadi urutkan sendiri berdasarkan like_count terbanyak dulu
    # untuk mendekati "top comments" yang ditampilkan aplikasi Instagram.
    result.sort(key=lambda c: c["like_count"] or 0, reverse=True)
    return result
