# video_utils.py
import yt_dlp

def get_video_infos(urls, is_playlist):
    """
    Fetches video information using yt-dlp for the given URL(s).
    :param urls: URL or list of URLs to fetch information from
    :param is_playlist: Boolean indicating whether the URL is a playlist
    :return: A list of video information dictionaries
    """
    ydl_opts = {'quiet': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if isinstance(urls, list):
            return [ydl.extract_info(u, download=False) for u in urls]
        else:
            info = ydl.extract_info(urls, download=False)
            return [info]

def get_video_duration(url):
    """
    Fetches the duration of a single video using yt-dlp.
    :param url: Video URL
    :return: Duration in seconds
    """
    ydl_opts = {'quiet': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('duration', 0)
