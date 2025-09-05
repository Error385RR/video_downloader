# gui_main.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from video_utils import get_video_infos
from main import download_one, get_default_save_path
import yt_dlp


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader (GUI)")
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        # URL input
        tk.Label(root, text="YouTube URL:").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = tk.Entry(root, width=70)
        self.url_entry.pack(padx=10, pady=5)

        # Mode dropdown
        tk.Label(root, text="Mode:").pack(anchor="w", padx=10, pady=(10, 0))
        self.mode_var = tk.StringVar(value="video")
        self.mode_menu = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            values=["video", "audio"],  # lowercase for consistency
            state="readonly",
            width=20,
        )
        self.mode_menu.pack(padx=10, pady=5)

        # Quality dropdown
        tk.Label(root, text="Quality:").pack(anchor="w", padx=10, pady=(10, 0))
        self.quality_var = tk.StringVar(value="best")
        self.quality_menu = ttk.Combobox(root, textvariable=self.quality_var, state="readonly", width=20)
        self.update_quality_options()
        self.mode_var.trace("w", lambda *args: self.update_quality_options())
        self.quality_menu.pack(padx=10, pady=5)

        # Save folder selection
        tk.Label(root, text="Save Folder:").pack(anchor="w", padx=10, pady=(10, 0))
        frame = tk.Frame(root)
        frame.pack(fill="x", padx=10, pady=5)
        self.save_path_var = tk.StringVar(value=get_default_save_path())
        self.save_entry = tk.Entry(frame, textvariable=self.save_path_var, width=50)
        self.save_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(frame, text="Browse", command=self.browse_folder).pack(side="right")

        # Progress bar
        self.progress = ttk.Progressbar(root, length=500, mode="determinate")
        self.progress.pack(pady=15)

        # Status label
        self.status_label = tk.Label(root, text="Idle", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        # Download button
        self.download_btn = ttk.Button(root, text="Start Download", command=self.start_download)
        self.download_btn.pack(pady=10)

        # Log field
        tk.Label(root, text="Logs:").pack(anchor="w", padx=10, pady=(10, 0))
        self.log_text = tk.Text(root, height=10, width=70, state="disabled", wrap="word")
        self.log_text.pack(padx=10, pady=(0, 10))

    def update_quality_options(self):
        if self.mode_var.get() == "video":
            options = ["1080p", "720p", "480p", "360p", "best"]
            self.quality_var.set("best")
        else:
            options = ["128", "192", "256", "320"]
            self.quality_var.set("192")
        self.quality_menu["values"] = options

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder:
            self.save_path_var.set(folder)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL.")
            return

        save_path = self.save_path_var.get()
        mode = self.mode_var.get()
        quality = self.quality_var.get()

        self.download_btn.config(state="disabled")
        self.log("Starting download...")

        threading.Thread(
            target=self.download_thread, args=(url, mode, quality, save_path), daemon=True
        ).start()

    def download_thread(self, url, mode, quality, save_path):
        try:
            self.set_status("Fetching video info...")
            infos = get_video_infos(url, False)  # fixed positional arg
            if not infos:
                self.set_status("Failed to fetch video info.")
                self.log("No video info found.")
                self.download_btn.config(state="normal")
                return

            self.set_status("Downloading...")
            self.log(f"Downloading {infos[0].get('title', 'Unknown Title')}...")

            # yt_dlp options with progress hook
            ydl_opts = {
                "progress_hooks": [self.progress_hook],
                "quiet": True,
                "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
            }
            if mode == "audio":
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": quality,
                    }],
                })
            else:
                format_map = {
                    "1080p": "bestvideo[height<=1080][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                    "720p": "bestvideo[height<=720][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                    "480p": "bestvideo[height<=480][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                    "360p": "bestvideo[height<=360][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                    "best": "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                }
                ydl_opts["format"] = format_map.get(quality, "best")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.set_status("Download completed!")
            self.log("Download finished successfully!")
            messagebox.showinfo("Success", "Download finished successfully!")

        except Exception as e:
            self.set_status("Error occurred.")
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.download_btn.config(state="normal")
            self.progress["value"] = 0  # reset progress bar

    def progress_hook(self, d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%").strip()
            try:
                percent_value = float(percent.replace("%", ""))
            except ValueError:
                percent_value = 0
            speed = d.get("_speed_str", "")
            eta = d.get("eta", "")
            self.root.after(0, lambda: self.update_progress(percent_value, speed, eta))
        elif d["status"] == "finished":
            self.root.after(0, lambda: self.set_status("Processing..."))

    def update_progress(self, percent, speed, eta):
        self.progress["value"] = percent
        self.set_status(f"Downloading... {percent:.1f}% | {speed} | ETA: {eta}s")

    def set_status(self, msg):
        self.status_label.config(text=msg)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()
