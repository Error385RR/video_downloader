# video_utils.py
import yt_dlp


def _build_ydl_opts(cookiefile=None, quiet=True, extract_flat=False):
    """Helper to build yt-dlp options with optional cookiefile and flat extraction."""
    ydl_opts = {
        'quiet': quiet,
        'extract_flat': extract_flat,  # flat = only metadata, no full details
    }
    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile
        if not quiet:
            print(f"[yt-dlp] Using cookies from: {cookiefile}")
    return ydl_opts


def get_video_infos(url, cookiefile=None):
    """
    Fetch video information (single video or full playlist).
    :param url: str
    :param cookiefile: Path to cookies.txt
    :return: list of video info dicts
    """
    results = []
    ydl_opts = _build_ydl_opts(cookiefile)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:  # playlist
                results.extend(info["entries"])
            else:
                results.append(info)
        except Exception as e:
            print(f"[ERROR] Failed to fetch info for {url}: {e}")
    return results


def get_playlist_entries(url, cookiefile=None):
    """
    Fetch only the list of video URLs from a playlist (shallow).
    :param url: Playlist URL
    :param cookiefile: Path to cookies.txt
    :return: list of URLs (strings)
    """
    urls = []
    ydl_opts = _build_ydl_opts(cookiefile, extract_flat=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                urls = [entry['url'] for entry in info['entries'] if 'url' in entry]
        except Exception as e:
            print(f"[ERROR] Failed to fetch playlist entries: {e}")
    return urls
