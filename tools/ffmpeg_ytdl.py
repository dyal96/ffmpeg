"""
FFmpeg YouTube Downloader Tool
Download videos using yt-dlp with FFmpeg integration
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import shutil
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_folder, get_theme, BINS_DIR
)

def get_ytdlp():
    """Get yt-dlp binary path."""
    if os.name == 'nt':
        local = BINS_DIR / "yt-dlp.exe"
    else:
        local = BINS_DIR / "yt-dlp"
    
    if local.exists():
        return str(local)
    
    found = shutil.which("yt-dlp")
    if found:
        return found
    return "yt-dlp"

class YouTubeTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("YouTube Downloader", 650, 550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # URL Section
        url_card = create_card(self.root, "🔗 Video URL")
        url_card.pack(fill="x", padx=10, pady=5)
        
        self.url_entry = ttk.Entry(url_card)
        self.url_entry.pack(fill="x", pady=5)
        
        # Format Section
        format_card = create_card(self.root, "📹 Format Options")
        format_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(format_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Quality:").pack(side="left")
        self.quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(row1, textvariable=self.quality_var,
                                      values=["best", "1080p", "720p", "480p", "360p", "audio only"],
                                      state="readonly", width=15)
        quality_combo.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Format:").pack(side="left", padx=(15, 0))
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(row1, textvariable=self.format_var,
                                     values=["mp4", "mkv", "webm", "mp3", "m4a"],
                                     state="readonly", width=10)
        format_combo.pack(side="left", padx=5)
        
        row2 = ttk.Frame(format_card)
        row2.pack(fill="x", pady=5)
        
        self.subs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="Download subtitles", variable=self.subs_var).pack(side="left")
        
        self.thumb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="Embed thumbnail", variable=self.thumb_var).pack(side="left", padx=10)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        ttk.Label(out_row, text="Save to:").pack(side="left")
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.out_entry.insert(0, str(Path.home() / "Downloads"))
        ttk.Button(out_row, text="Browse", command=lambda: browse_folder(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="⬇️ Download", command=self.run_download)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="📋 Get Info", command=self.get_info).pack(side="left", padx=5)
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def get_info(self):
        url = self.url_entry.get().strip()
        if not url:
            tk.messagebox.showerror("Error", "Please enter a URL.")
            return
        
        cmd = [get_ytdlp(), "--dump-json", url]
        
        self._on_log(f"Getting info...\n")
        
        def fetch():
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
                if result.returncode == 0:
                    import json
                    info = json.loads(result.stdout)
                    title = info.get("title", "Unknown")
                    duration = info.get("duration", 0)
                    uploader = info.get("uploader", "Unknown")
                    self.root.after(0, lambda: self._on_log(
                        f"\nTitle: {title}\nUploader: {uploader}\nDuration: {duration}s\n"
                    ))
                else:
                    self.root.after(0, lambda: self._on_log(f"Error: {result.stderr}\n"))
            except Exception as e:
                self.root.after(0, lambda: self._on_log(f"Error: {e}\n"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def run_download(self):
        url = self.url_entry.get().strip()
        if not url:
            tk.messagebox.showerror("Error", "Please enter a URL.")
            return
        
        output_folder = self.out_entry.get()
        quality = self.quality_var.get()
        fmt = self.format_var.get()
        
        cmd = [get_ytdlp()]
        
        # Format selection
        if quality == "audio only":
            cmd.extend(["-x", "--audio-format", fmt if fmt in ["mp3", "m4a"] else "mp3"])
        else:
            if quality == "best":
                cmd.extend(["-f", "bestvideo+bestaudio/best"])
            else:
                height = quality.replace("p", "")
                cmd.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
            
            cmd.extend(["--merge-output-format", fmt])
        
        # Subtitles
        if self.subs_var.get():
            cmd.extend(["--write-subs", "--sub-langs", "en"])
        
        # Thumbnail
        if self.thumb_var.get():
            cmd.append("--embed-thumbnail")
        
        # Output template
        cmd.extend(["-o", f"{output_folder}/%(title)s.%(ext)s"])
        cmd.append(url)
        
        self.set_preview(cmd)
        self._on_log(f"$ {' '.join(cmd)}\n\n")
        
        self.run_btn.config(state="disabled")
        
        def download():
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, creationflags=creationflags)
                for line in process.stdout:
                    self.root.after(0, lambda l=line: self._on_log(l))
                process.wait()
                
                self.root.after(0, lambda: self.run_btn.config(state="normal"))
                if process.returncode == 0:
                    self.root.after(0, lambda: tk.messagebox.showinfo("Complete", "Download finished!"))
                else:
                    self.root.after(0, lambda: tk.messagebox.showerror("Error", "Download failed."))
            except Exception as e:
                self.root.after(0, lambda: self._on_log(f"Error: {e}\n"))
                self.root.after(0, lambda: self.run_btn.config(state="normal"))
        
        threading.Thread(target=download, daemon=True).start()

if __name__ == "__main__":
    app = YouTubeTool()
    app.run()
