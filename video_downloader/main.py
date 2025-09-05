# main.py
import os
import sys
import json
import argparse
from datetime import datetime
from video_utils import get_video_infos, get_playlist_entries
import yt_dlp


def estimate_size(duration_sec, bitrate_kbps, efficiency_factor=0.85):
    size_bytes = (bitrate_kbps * 1000 / 8) * duration_sec * efficiency_factor
    return round(size_bytes / (1024 ** 2), 2)


def get_default_save_path():
    if "ANDROID_STORAGE" in os.environ or "com.termux" in sys.prefix:
        return "/storage/emulated/0/Download/termux/"
    elif sys.platform.startswith("win"):
        return os.path.expanduser("~/Downloads/video_downloader/")
    else:
        return os.path.expanduser("~/Downloads/video_downloader/")


# ---------------- JSON HISTORY LOGGER ---------------- #

def log_session_result(log_path, session_id, entries):
    history = {}
    if os.path.isfile(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not read history file: {e}")
            history = {}

    history[session_id] = entries

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def build_cookie_opts(cookiefile, ydl_opts):
    if cookiefile:
        if not os.path.isfile(cookiefile):
            print(f"[WARNING] Cookie file not found: {cookiefile}")
        else:
            ydl_opts['cookiefile'] = cookiefile
            print(f"Using cookies from: {cookiefile}")
    return ydl_opts


def download_one(url_or_info, mode, quality, save_path, cookiefile, session_entries):
    """Download a single video and append its result to session_entries."""
    if not save_path:
        save_path = get_default_save_path()
    os.makedirs(save_path, exist_ok=True)

    if mode == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',  # no -id
            'quiet': False,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                {'key': 'EmbedThumbnail'}
            ],
            'writethumbnail': True,
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
        }
    else:
        format_map = {
            '1080p': 'bestvideo[height<=1080][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '720p':  'bestvideo[height<=720][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '480p':  'bestvideo[height<=480][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '360p':  'bestvideo[height<=360][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'best':  'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
        }
        ydl_opts = {
            'format': format_map.get(quality, 'best'),
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',  # no -id
            'merge_output_format': 'mp4',
            'quiet': False,
            'postprocessors': [{'key': 'EmbedThumbnail'}],
            'writethumbnail': True,
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
            'nocache': True,
            'no_mtime': False,
            'nooverwrites': True,
        }

    ydl_opts = build_cookie_opts(cookiefile, ydl_opts)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(
                url_or_info if isinstance(url_or_info, str) else url_or_info.get("webpage_url"),
                download=True
            )
            filename = ydl.prepare_filename(info)
            resolution = f"{info.get('height', 'N/A')}p" if info.get('height') else 'N/A'
            session_entries.append({
                "title": info.get("title", "Unknown Title"),
                "url": info.get("webpage_url", "N/A"),
                "filepath": filename,
                "status": "success" if os.path.isfile(filename) else "unknown",
                "resolution": resolution
            })
        except Exception as e:
            print(f"[ERROR] Failed to download {url_or_info}: {e}")
            session_entries.append({
                "title": "N/A",
                "url": url_or_info if isinstance(url_or_info, str) else url_or_info.get("webpage_url", "N/A"),
                "filepath": "N/A",
                "status": f"failed ({str(e)[:100]})",
                "resolution": "N/A"
            })


def main():
    parser = argparse.ArgumentParser(description="YouTube Downloader")
    parser.add_argument("url", nargs="?", help="Video or playlist URL")
    parser.add_argument("--playlist", action="store_true", help="Treat the given URL as a playlist (sequential)")
    parser.add_argument("--mode", choices=["video", "audio"], help="Download mode")
    parser.add_argument("--quality", help="Video quality or audio bitrate")
    parser.add_argument("--cookiefile", help="Path to cookies.txt file")
    parser.add_argument("--debug", action="store_true", help="Show yt-dlp version and exit")
    args = parser.parse_args()

    # Debug option
    if args.debug:
        print(f"yt-dlp version: {yt_dlp.version.__version__}")
        sys.exit(0)

    # URL handling
    if args.url:
        url = args.url
    else:
        url = input("Enter YouTube video or playlist URL: ").strip()

    # Session ID
    session_id = datetime.now().isoformat(timespec='seconds')
    save_path = get_default_save_path()
    log_file = os.path.join(save_path, 'download_history.json')
    session_entries = []

    # Playlist mode
    if args.playlist:
        print("\nFetching playlist entries...")
        playlist_urls = get_playlist_entries(url, cookiefile=args.cookiefile)
        if not playlist_urls:
            print("[ERROR] Could not fetch playlist or playlist is empty.")
            sys.exit(1)

        print(f"Found {len(playlist_urls)} videos in playlist.")
        # Ask mode + quality once
        mode = args.mode or input("Download mode - video or audio? (v/a): ").strip().lower()
        mode = 'audio' if mode.startswith('a') else 'video'

        if mode == 'video':
            bitrates = {
                '1': ('1080p', 5000),
                '2': ('720p', 2500),
                '3': ('480p', 1000),
                '4': ('360p', 700),
                '5': ('best', 4000)
            }
            print("\nChoose video quality:")
            for key, (label, _) in bitrates.items():
                print(f"{key}. {label}")
            choice = input("Enter choice (1-5): ").strip()
            selected_quality, _ = bitrates.get(choice, ('best', 4000 + 192))
            quality_param = selected_quality
        else:
            audio_bitrates = {
                '1': ('128', 128),
                '2': ('192', 192),
                '3': ('256', 256),
                '4': ('320', 320)
            }
            print("\nChoose MP3 bitrate:")
            for key, (label, _) in audio_bitrates.items():
                print(f"{key}. {label} kbps")
            choice = input("Enter choice (1-4): ").strip()
            selected_bitrate_label, _ = audio_bitrates.get(choice, ('192', 192))
            quality_param = selected_bitrate_label

        # Download sequentially with progress indicator
        total = len(playlist_urls)
        for idx, vid_url in enumerate(playlist_urls, 1):
            print(f"\n[{idx}/{total}] Downloading {vid_url}")
            download_one(vid_url, mode, quality_param, save_path, args.cookiefile, session_entries)

    else:
        # Single video
        print("\nFetching video information...")
        infos = get_video_infos(url, cookiefile=args.cookiefile)
        if not infos:
            print("[ERROR] Could not fetch video info. Exiting.")
            sys.exit(1)

        mode = args.mode or input("Download mode - video or audio? (v/a): ").strip().lower()
        mode = 'audio' if mode.startswith('a') else 'video'

        if mode == 'video':
            bitrates = {
                '1': ('1080p', 5000),
                '2': ('720p', 2500),
                '3': ('480p', 1000),
                '4': ('360p', 700),
                '5': ('best', 4000)
            }
            print("\nChoose video quality:")
            for key, (label, kbps) in bitrates.items():
                total_size = sum(estimate_size(d.get("duration", 0), kbps) for d in infos)
                print(f"{key}. {label} — approx. {total_size} MB")
            choice = input("Enter choice (1-5): ").strip()
            selected_quality, _ = bitrates.get(choice, ('best', 4000 + 192))
            quality_param = selected_quality
        else:
            audio_bitrates = {
                '1': ('128', 128),
                '2': ('192', 192),
                '3': ('256', 256),
                '4': ('320', 320)
            }
            print("\nChoose MP3 bitrate:")
            for key, (label, kbps) in audio_bitrates.items():
                total_size = sum(estimate_size(d.get("duration", 0), kbps) for d in infos)
                print(f"{key}. {label} kbps — approx. {total_size} MB")
            choice = input("Enter choice (1-4): ").strip()
            selected_bitrate_label, _ = audio_bitrates.get(choice, ('192', 192))
            quality_param = selected_bitrate_label

        download_one(url, mode, quality_param, save_path, args.cookiefile, session_entries)

    # Save session
    log_session_result(log_file, session_id, session_entries)


if __name__ == '__main__':
    main()
