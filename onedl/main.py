# main.py
import os
import sys
from video_utils import get_video_infos, get_video_duration
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
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
            'best': 'bestvideo+bestaudio/best'
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
            'nocache': True,   
        }

    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        urls_to_download = [video['webpage_url'] for video in urls] if isinstance(urls, list) else [urls]
        ydl.download(urls_to_download)

def main():
    url = input("Enter YouTube video or playlist URL: ").strip()
    is_playlist = input("Is this a playlist? (y/n): ").strip().lower() == 'y'
    print("\nFetching video information...")
    video_infos = get_video_infos(url, is_playlist)

    # Cache durations once
    #durations = [get_video_duration(video['webpage_url']) for video in video_infos]

    durations = [video.get('duration', 0) for video in video_infos]


    user_path = input("Enter save directory (or leave blank for default): ").strip()
    save_path = os.path.expanduser(user_path) if user_path else get_default_save_path()


    """
    save_path = input("Enter save directory (default: downloads): ").strip()
    if not save_path:
        save_path = '/storage/emulated/0/Download/termux/'
    """
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

    cookiefile = input("Enter path to cookies file (leave blank if none): ").strip()
    if cookiefile == '':
        cookiefile = None


    download_media(
        video_infos if is_playlist else url,
        mode,
        quality_param,
        save_path,
        cookiefile=cookiefile
    )

if __name__ == '__main__':
    main()
