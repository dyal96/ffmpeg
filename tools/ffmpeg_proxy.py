"""
FFmpeg Proxy Generator Tool
Generate low-res proxy files for editing
"""

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import threading
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_folder, get_binary, get_theme, ensure_dir
)

PROXY_PRESETS = {
    "1080p (Full HD Proxy)": {"scale": "1920:-2", "crf": "23"},
    "720p (Standard Proxy)": {"scale": "1280:-2", "crf": "25"},
    "540p (Light Proxy)": {"scale": "960:-2", "crf": "28"},
    "360p (Ultra Light)": {"scale": "640:-2", "crf": "30"},
}

class ProxyTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Proxy Generator", 650, 580)
        self.input_files = []
        self.processing = False
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Source Files")
        input_card.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ttk.Frame(input_card)
        btn_frame.pack(fill="x", pady=2)
        
        ttk.Button(btn_frame, text="➕ Add Files", command=self.add_files).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Clear", command=self.clear_files).pack(side="left", padx=2)
        
        self.file_list = tk.Listbox(input_card, height=5)
        self.file_list.pack(fill="x", pady=5)
        
        self.count_label = ttk.Label(input_card, text="0 files")
        self.count_label.pack(anchor="w")
        
        # Preset Section
        preset_card = create_card(self.root, "⚙️ Proxy Settings")
        preset_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(preset_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Preset:").pack(side="left")
        self.preset_var = tk.StringVar(value="720p (Standard Proxy)")
        preset_combo = ttk.Combobox(row1, textvariable=self.preset_var,
                                     values=list(PROXY_PRESETS.keys()), state="readonly", width=25)
        preset_combo.pack(side="left", padx=5)
        
        row2 = ttk.Frame(preset_card)
        row2.pack(fill="x", pady=5)
        
        self.fast_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="Fast encode (ultrafast preset)", variable=self.fast_var).pack(side="left")
        
        self.suffix_var = tk.StringVar(value="_proxy")
        ttk.Label(row2, text="Suffix:").pack(side="left", padx=(15, 0))
        ttk.Entry(row2, textvariable=self.suffix_var, width=10).pack(side="left", padx=5)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        ttk.Label(out_row, text="Proxy Folder:").pack(side="left")
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(out_row, text="Browse", command=lambda: browse_folder(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Generate Proxies", command=self.run_generate)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Video files", "*.mp4;*.mkv;*.mov;*.avi;*.mxf;*.r3d"), ("All", "*.*")]
        )
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
                self.file_list.insert(tk.END, os.path.basename(f))
        self.count_label.config(text=f"{len(self.input_files)} files")
    
    def clear_files(self):
        self.input_files.clear()
        self.file_list.delete(0, tk.END)
        self.count_label.config(text="0 files")
    
    def run_generate(self):
        if not self.input_files:
            tk.messagebox.showerror("Error", "No files selected.")
            return
        
        output_folder = self.out_entry.get()
        if not output_folder:
            tk.messagebox.showerror("Error", "Please select an output folder.")
            return
        
        ensure_dir(Path(output_folder))
        
        self.processing = True
        self.run_btn.config(state="disabled")
        
        threading.Thread(target=self._generate_proxies, args=(output_folder,), daemon=True).start()
    
    def _generate_proxies(self, output_folder):
        preset = PROXY_PRESETS.get(self.preset_var.get(), PROXY_PRESETS["720p (Standard Proxy)"])
        suffix = self.suffix_var.get()
        fast = self.fast_var.get()
        total = len(self.input_files)
        
        for i, input_file in enumerate(self.input_files):
            if not self.processing:
                break
            
            name = Path(input_file).stem
            out_file = str(Path(output_folder) / f"{name}{suffix}.mp4")
            
            cmd = [
                get_binary("ffmpeg"), "-y", "-i", input_file,
                "-vf", f"scale={preset['scale']}",
                "-c:v", "libx264", "-crf", preset["crf"],
                "-preset", "ultrafast" if fast else "medium",
                "-c:a", "aac", "-b:a", "128k",
                out_file
            ]
            
            self._on_log(f"\n[{i+1}/{total}] Generating proxy: {name}\n")
            
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(cmd, capture_output=True, creationflags=creationflags)
                self._on_log("✓ Done\n")
            except Exception as e:
                self._on_log(f"Failed: {e}\n")
            
            percent = int((i + 1) / total * 100)
            self.root.after(0, lambda p=percent: self.progress_bar.configure(value=p))
        
        self.root.after(0, self._complete)
    
    def _complete(self):
        self.processing = False
        self.run_btn.config(state="normal")
        tk.messagebox.showinfo("Complete", "Proxy generation finished!")

if __name__ == "__main__":
    app = ProxyTool()
    app.run()
