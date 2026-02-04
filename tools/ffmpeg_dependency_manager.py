"""
FFmpeg & Dependency Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import shutil
import urllib.request
import urllib.error
import zipfile
import tarfile
from pathlib import Path
import threading
import json
import time

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, 
    get_theme, 
    create_card, 
    BINS_DIR, 
    ensure_dir
)

# Constants
FFMPEG_URL_WIN = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.01.31/yt-dlp.exe" # User specified tag
CAESIUM_RELEASES_API = "https://api.github.com/repos/Lymphatus/caesium-clt/releases/latest"

class DependencyManager(FFmpegToolApp):
    def __init__(self):
        super().__init__("Dependency Manager", width=800, height=600)
        
        self.portable_var = tk.BooleanVar(value=True)
        self.status_vars = {
            "ffmpeg": tk.StringVar(value="Checking..."),
            "yt-dlp": tk.StringVar(value="Checking..."),
            "caesium-clt": tk.StringVar(value="Checking...")
        }
        self.path_vars = {
            "ffmpeg": tk.StringVar(),
            "yt-dlp": tk.StringVar(),
            "caesium-clt": tk.StringVar()
        }
        
        self.build_ui()
        self.check_all_dependencies()
        
    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # --- Header Section ---
        header_frame = create_card(main_frame, "Configuration")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Checkbutton(header_frame, text="Portable Mode (Use ./bins folder)", 
                       variable=self.portable_var, command=self.check_all_dependencies).pack(anchor="w")
        
        ttk.Label(header_frame, text="When portable mode is ON, tools are downloaded to and run from the application's 'bins' folder.\nWhen OFF, the application looks for tools in your system PATH.", 
                 foreground="gray", font=("Segoe UI", 9)).pack(anchor="w", padx=20)

        # --- Dependencies List ---
        self.deps_frame = create_card(main_frame, "Dependencies")
        self.deps_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Tools
        self.create_tool_row(self.deps_frame, "FFmpeg", "ffmpeg", "Essential for all video operations.")
        self.create_tool_row(self.deps_frame, "yt-dlp", "yt-dlp", "YouTube video downloader.")
        self.create_tool_row(self.deps_frame, "Caesium CLT", "caesium-clt", "Image compression tool.")
        
        # --- Status/Log Section ---
        self.create_bottom_section(main_frame)
        
    def create_tool_row(self, parent, display_name, key, description):
        """Create a row for a tool."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)
        
        # Icon/Details
        details = ttk.Frame(frame)
        details.pack(side="left", fill="x", expand=True)
        
        header = ttk.Frame(details)
        header.pack(anchor="w")
        
        ttk.Label(header, text=display_name, font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(header, text=description, font=("Segoe UI", 9), foreground="gray").pack(side="left", padx=10)
        
        # Path & Status
        info_frame = ttk.Frame(details)
        info_frame.pack(anchor="w", fill="x", pady=2)
        
        ttk.Label(info_frame, text="Path: ", font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Label(info_frame, textvariable=self.path_vars[key], font=("Segoe UI", 9, "italic")).pack(side="left")
        
        status_lbl = ttk.Label(details, textvariable=self.status_vars[key], foreground=get_theme()["accent"])
        status_lbl.pack(anchor="w")
        
        # Actions
        actions = ttk.Frame(frame)
        actions.pack(side="right", padx=10)
        
        ttk.Button(actions, text="Update/Install", command=lambda k=key: self.start_update(k)).pack(side="right")

    def check_all_dependencies(self):
        """Check status of all tools."""
        for key in ["ffmpeg", "yt-dlp", "caesium-clt"]:
            self.check_dependency(key)

    def check_dependency(self, key):
        """Check a single dependency."""
        self.status_vars[key].set("Checking...")
        
        # Determine target name (windows)
        exe_name = key
        if key == "caesium-clt":
            exe_name = "caesiumclt" # binary name differs
        if not exe_name.endswith(".exe"):
            exe_name += ".exe"
            
        found_path = None
        
        # 1. Check Portable (bins)
        local_path = BINS_DIR / exe_name
        if local_path.exists():
            if self.portable_var.get():
                found_path = str(local_path)
            else:
                # Even if not portable, if it's in bins, we might acknowledge it,
                # but typically we look in PATH first if portable is off.
                pass
        
        # 2. Check System PATH (if not portable or not found locally yet)
        if not found_path:
            system_path = shutil.which(key) or shutil.which(exe_name.replace(".exe", ""))
            if system_path:
                if not self.portable_var.get():
                    found_path = system_path
                else:
                    # If portable is ON, but we found it in system, we still prefer local.
                    # If not found locally, we show "Not installed (Portable)"
                    pass

        if found_path:
            self.path_vars[key].set(found_path)
            
            # Try to get version
            try:
                # Getting version can be slow, maybe skip for now or do simplified check
                # For now just say "Detected"
                self.status_vars[key].set("Installed / Detected")
            except:
                 self.status_vars[key].set("Installed (Version unknown)")
        else:
            self.path_vars[key].set("Not found")
            self.status_vars[key].set("Not Installed")

    def start_update(self, key):
        """Start update thread."""
        if self.runner.is_running():
            messagebox.showwarning("Busy", "Wait for current task to finish.")
            return
            
        threading.Thread(target=self.perform_update, args=(key,), daemon=True).start()

    def perform_update(self, key):
        """Download and install the tool."""
        self.run_btn = None # Hack to disable button logic in base class if used
        
        def update_status_cb(percent, text=None):
            # Update main progress bar
            self._on_progress(percent)
            # Update row status text
            if text:
                 self.status_vars[key].set(text)
            else:
                 self.status_vars[key].set(f"Downloading... {percent}%")
        
        try:
            ensure_dir(BINS_DIR)
            
            self._on_log(f"Starting update for {key}...\n")
            update_status_cb(0, "Starting...")
            
            if key == "ffmpeg":
                self._install_ffmpeg(update_status_cb)
            elif key == "yt-dlp":
                self._install_ytdlp(update_status_cb)
            elif key == "caesium-clt":
                self._install_caesium(update_status_cb)
                
            update_status_cb(100, "Installed / Updated")
            self._on_log(f"\nSuccessfully updated {key}!\n")
            
            # Refresh UI on main thread
            self.root.after(0, self.check_all_dependencies)
            
        except Exception as e:
            self._on_log(f"\nError: {str(e)}\n")
            self.status_vars[key].set("Error")
            self._on_finished(False, str(e))

    def _download_file(self, url, target_path, progress_cb=None):
        """Download file with progress."""
        self._on_log(f"Downloading {url}...\n")
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            total_size = int(response.getheader('Content-Length', 0).strip())
            downloaded = 0
            block_size = 8192
            
            with open(target_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    # Update progress (0-100% relative to download)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        if progress_cb:
                            progress_cb(percent)

    def _install_ffmpeg(self, progress_cb):
        url = FFMPEG_URL_WIN
        zip_path = BINS_DIR / "ffmpeg.zip"
        
        # Wrapper to scale download progress (0-80%)
        def dl_progress(p):
            progress_cb(int(p * 0.8), f"Downloading FFmpeg... {p}%")
            
        self._download_file(url, zip_path, dl_progress)
        
        progress_cb(85, "Extracting...")
        self._on_log("Extracting FFmpeg...\n")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the bin folder inside zip
            bin_files = [f for f in zip_ref.namelist() if f.endswith('.exe') and 'bin/' in f]
            
            for file in bin_files:
                filename = os.path.basename(file)
                source = zip_ref.open(file)
                target = open(BINS_DIR / filename, "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
                self._on_log(f"Extracted {filename}\n")
        
        os.remove(zip_path)

    def _install_ytdlp(self, progress_cb):
        url = YTDLP_URL
        target_path = BINS_DIR / "yt-dlp.exe"
        
        def dl_progress(p):
            progress_cb(p, f"Downloading yt-dlp... {p}%")
            
        self._download_file(url, target_path, dl_progress)

    def _install_caesium(self, progress_cb):
        # 1. Get latest release URL
        progress_cb(5, "Fetching info...")
        self._on_log("Fetching latest release info...\n")
        req = urllib.request.Request(CAESIUM_RELEASES_API, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            
        # Find windows asset
        asset_url = None
        for asset in data.get("assets", []):
            name = asset["name"].lower()
            if "windows" in name and "x86_64" in name and name.endswith(".zip"):
                asset_url = asset["browser_download_url"]
                break
        
        if not asset_url:
            raise Exception("Could not find Windows asset for Caesium CLT")
            
        zip_path = BINS_DIR / "caesium.zip"
        
        def dl_progress(p):
            # Scale 10-90%
            scaled = 10 + int(p * 0.8)
            progress_cb(scaled, f"Downloading Caesium... {p}%")
            
        self._download_file(asset_url, zip_path, dl_progress)
        
        progress_cb(95, "Extracting...")
        self._on_log("Extracting Caesium...\n")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(".exe"):
                    filename = os.path.basename(file)
                    source = zip_ref.open(file)
                    target = open(BINS_DIR / filename, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    self._on_log(f"Extracted {filename}\n")
                    
        os.remove(zip_path)

if __name__ == "__main__":
    app = DependencyManager()
    app.run()
