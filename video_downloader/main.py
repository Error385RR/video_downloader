# main.py
import os
import sys
import time
import argparse
from datetime import datetime
from .video_utils import get_video_infos, get_video_duration
import yt_dlp


def estimate_size(duration_sec, bitrate_kbps, efficiency_factor=0.85):
    """
    Estimate file size in MB given duration in seconds and bitrate in kbps.
    Applies an efficiency factor to correct for real-world compression.
    """
    size_bytes = (bitrate_kbps * 1000 / 8) * duration_sec * efficiency_factor
    return round(size_bytes / (1024 ** 2), 2)


def get_default_save_path():
    if "ANDROID_STORAGE" in os.environ or "com.termux" in sys.prefix:
        # Likely Termux
        return "/storage/emulated/0/Download/termux/"
    elif sys.platform.startswith("win"):
        return os.path.expanduser("~/Downloads/video_downloader/")
    else:
        return os.path.expanduser("~/Downloads/video_downloader/")

def log_download_result(log_path, title, url, filepath, status, resolution='N/A'):
    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {status.upper()} | {title} | {url} -> {filepath} | Resolution: {resolution}\n")



def download_media(urls, mode='video', quality='best', save_path=None,cookiefile=None):

    if not save_path:
        save_path = get_default_save_path()
    
    os.makedirs(save_path, exist_ok=True)



    if mode == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{save_path}/%(title)s.%(ext)s',
            'quiet': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
        }
    else:
        # Updated fallback formats for video quality
        format_map = {
            '1080p': 'bestvideo[height<=1080][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '720p':  'bestvideo[height<=720][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '480p':  'bestvideo[height<=480][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '360p':  'bestvideo[height<=360][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'best':  'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
            }
        
        ydl_opts = { 'format': format_map.get(quality, 'best'), 
            'outtmpl': f'{save_path}/%(title)s.%(ext)s', 
            'merge_output_format': 'mp4',
            'quiet': False, 
            'nocheckcertificate': True,
            'prefer_ffmpeg': True, 
            'nocache': True,     
            'no_mtime': True,
            'nooverwrites': True,   
        }

    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile
        print(f"Using cookies from: {cookiefile}")


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        urls_to_download = [video['webpage_url'] for video in urls] if isinstance(urls, list) else [urls]
        ydl.download(urls_to_download)
        
        log_file = os.path.join(save_path, 'download_history.txt')
        for url in urls_to_download:
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')
                filename = ydl.prepare_filename(info)
                
                # ✅ Force mtime to current time
                if os.path.isfile(filename):
                    now = time.time()
                    os.utime(filename, (now, now))

                # Try to get resolution (height x width or formatted)
                resolution = f"{info.get('height', 'N/A')}p" if info.get('height') else 'N/A'
                
                log_download_result(log_file, title, url, filename, 'success', resolution)
            except Exception as e:
                log_download_result(log_file, 'N/A', url, 'N/A', f'failed ({str(e)[:100]})')
                print(f"Download failed for {url}: {e}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Downloader")
    parser.add_argument('--file', type=str, help='Path to text file with list of YouTube URLs')
    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            print(f"File not found: {args.file}")
            sys.exit(1)
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(urls)} URLs from {args.file}")
        is_playlist = False  # Assume list of video URLs for simplicity
        url = None  # We're using `urls` instead of `url`
    else:
        url = input("Enter YouTube video or playlist URL: ").strip()
        is_playlist = input("Is this a playlist? (y/n): ").strip().lower() == 'y'
        urls = [url]

    cookiefile = input("Enter path to cookies file (leave blank if none): ").strip() or None
    user_path = input("Enter save directory (or leave blank for default): ").strip()
    save_path = os.path.expanduser(user_path) if user_path else get_default_save_path()

    print(f"Using cookies from: {cookiefile}")
    print("\nFetching video information...")

    all_video_infos = []
    for single_url in urls:
        infos = get_video_infos(single_url, is_playlist, cookiefile=cookiefile)
        all_video_infos.extend(infos)

    durations = [video.get('duration', 0) for video in all_video_infos]

    mode = input("Download mode - video or audio? (v/a): ").strip().lower()
    mode = 'audio' if mode == 'a' else 'video'

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
            total_size = sum(estimate_size(d, kbps) for d in durations)
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
            total_size = sum(estimate_size(d, kbps) for d in durations)
            print(f"{key}. {label} kbps — approx. {total_size} MB")
        choice = input("Enter choice (1-4): ").strip()
        selected_bitrate_label, _ = audio_bitrates.get(choice, ('192', 192))
        quality_param = selected_bitrate_label

    # Pass in either a single URL or video infos
    if args.file or is_playlist:
        download_media(
            all_video_infos,
            mode,
            quality_param,
            save_path,
            cookiefile=cookiefile
        )
    else:
        download_media(
            url,
            mode,
            quality_param,
            save_path,
            cookiefile=cookiefile
        )

if __name__ == '__main__':
    main()
