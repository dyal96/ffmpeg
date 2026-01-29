"""
FFmpeg Watch Folder Tool
Monitor a folder and automatically process new video files
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_folder, get_binary, get_theme, ensure_dir
)

ACTIONS = {
    "Convert to MP4": ["-c:v", "libx264", "-crf", "23", "-c:a", "aac"],
    "Compress (CRF 28)": ["-c:v", "libx264", "-crf", "28", "-preset", "fast", "-c:a", "copy"],
    "Generate Proxy (720p)": ["-vf", "scale=1280:-2", "-c:v", "libx264", "-crf", "25", "-preset", "ultrafast", "-c:a", "aac"],
    "Extract Audio (MP3)": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
}

class WatchFolderTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Watch Folder", 650, 550)
        self.watching = False
        self.processed_files = set()
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Watch Folder Section
        watch_card = create_card(self.root, "👁️ Watch Folder")
        watch_card.pack(fill="x", padx=10, pady=5)
        
        watch_row = ttk.Frame(watch_card)
        watch_row.pack(fill="x", pady=5)
        
        ttk.Label(watch_row, text="Input:").pack(side="left")
        self.watch_entry = ttk.Entry(watch_row)
        self.watch_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(watch_row, text="Browse", command=lambda: browse_folder(self.watch_entry)).pack(side="left")
        
        # Output Folder
        out_row = ttk.Frame(watch_card)
        out_row.pack(fill="x", pady=5)
        
        ttk.Label(out_row, text="Output:").pack(side="left")
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(out_row, text="Browse", command=lambda: browse_folder(self.out_entry)).pack(side="left")
        
        # Action Settings
        action_card = create_card(self.root, "⚙️ Action")
        action_card.pack(fill="x", padx=10, pady=5)
        
        action_row = ttk.Frame(action_card)
        action_row.pack(fill="x", pady=5)
        
        ttk.Label(action_row, text="Action:").pack(side="left")
        self.action_var = tk.StringVar(value="Convert to MP4")
        action_combo = ttk.Combobox(action_row, textvariable=self.action_var,
                                     values=list(ACTIONS.keys()), state="readonly", width=25)
        action_combo.pack(side="left", padx=5)
        
        opts_row = ttk.Frame(action_card)
        opts_row.pack(fill="x", pady=5)
        
        ttk.Label(opts_row, text="Check interval (s):").pack(side="left")
        self.interval_spin = ttk.Spinbox(opts_row, from_=1, to=60, width=5)
        self.interval_spin.set(5)
        self.interval_spin.pack(side="left", padx=5)
        
        self.ext_var = tk.StringVar(value=".mp4")
        ttk.Label(opts_row, text="Output ext:").pack(side="left", padx=(10, 0))
        ttk.Entry(opts_row, textvariable=self.ext_var, width=8).pack(side="left", padx=5)
        
        # Status
        status_card = create_card(self.root, "📊 Status")
        status_card.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(status_card, text="Not watching")
        self.status_label.pack(anchor="w", pady=5)
        
        self.processed_label = ttk.Label(status_card, text="Processed: 0 files")
        self.processed_label.pack(anchor="w")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.start_btn = ttk.Button(actions, text="▶ Start Watching", command=self.start_watching)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(actions, text="⏹ Stop", command=self.stop_watching, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def start_watching(self):
        watch_folder = self.watch_entry.get()
        output_folder = self.out_entry.get()
        
        if not watch_folder or not Path(watch_folder).exists():
            tk.messagebox.showerror("Error", "Please select a valid watch folder.")
            return
        
        if not output_folder:
            tk.messagebox.showerror("Error", "Please select an output folder.")
            return
        
        ensure_dir(Path(output_folder))
        
        self.watching = True
        self.processed_files = set()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text=f"Watching: {watch_folder}")
        
        threading.Thread(target=self._watch_loop, args=(watch_folder, output_folder), daemon=True).start()
    
    def stop_watching(self):
        self.watching = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Stopped")
    
    def _watch_loop(self, watch_folder, output_folder):
        interval = int(self.interval_spin.get())
        action_args = ACTIONS.get(self.action_var.get(), [])
        out_ext = self.ext_var.get()
        
        video_exts = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".mxf")
        
        while self.watching:
            try:
                for f in Path(watch_folder).iterdir():
                    if not self.watching:
                        break
                    
                    if f.is_file() and f.suffix.lower() in video_exts:
                        fp = str(f)
                        if fp not in self.processed_files:
                            self._process_file(fp, output_folder, action_args, out_ext)
                            self.processed_files.add(fp)
                            self.root.after(0, lambda: self.processed_label.config(
                                text=f"Processed: {len(self.processed_files)} files"
                            ))
            except Exception as e:
                self._on_log(f"Error scanning folder: {e}\n")
            
            time.sleep(interval)
    
    def _process_file(self, input_file, output_folder, action_args, out_ext):
        name = Path(input_file).stem
        out_file = str(Path(output_folder) / f"{name}_processed{out_ext}")
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file] + action_args + [out_file]
        
        self._on_log(f"\nProcessing: {os.path.basename(input_file)}\n")
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
            if result.returncode == 0:
                self._on_log("✓ Done\n")
            else:
                self._on_log(f"Error: {result.stderr[-300:]}\n")
        except Exception as e:
            self._on_log(f"Failed: {e}\n")

if __name__ == "__main__":
    app = WatchFolderTool()
    app.run()
