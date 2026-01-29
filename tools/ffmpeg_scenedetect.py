"""
FFmpeg Scene Detection Tool
Detect scene changes and optionally split video at scene boundaries
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_folder,
    get_binary, get_theme, TEMP_DIR, ensure_dir
)

class SceneDetectTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Scene Detection", 650, 600)
        self.scenes = []
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input Video")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=lambda: browse_file(self.input_entry, 
                   [("Video files", "*.mp4;*.mkv;*.mov;*.avi"), ("All", "*.*")])).pack(side="left")
        
        # Detection Settings
        settings_card = create_card(self.root, "🎬 Detection Settings")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(settings_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Scene Threshold (0.0-1.0):").pack(side="left")
        self.threshold_spin = ttk.Spinbox(row1, from_=0.1, to=0.9, increment=0.05, width=6)
        self.threshold_spin.set(0.4)
        self.threshold_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="(Lower = more sensitive)").pack(side="left", padx=5)
        
        # Analyze Button
        ttk.Button(settings_card, text="🔍 Detect Scenes", command=self.detect_scenes).pack(pady=10)
        
        # Detected Scenes Display
        scenes_card = create_card(self.root, "📍 Detected Scenes")
        scenes_card.pack(fill="x", padx=10, pady=5)
        
        self.scene_list = tk.Listbox(scenes_card, height=8)
        scrollbar = ttk.Scrollbar(scenes_card, orient="vertical", command=self.scene_list.yview)
        self.scene_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.scene_list.pack(fill="x", pady=5)
        
        self.scene_info_label = ttk.Label(scenes_card, text="No scenes detected yet.")
        self.scene_info_label.pack(anchor="w")
        
        # Output Section
        out_card = create_card(self.root, "💾 Split Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        ttk.Label(out_row, text="Output Folder:").pack(side="left")
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(out_row, text="Browse", 
                   command=lambda: browse_folder(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="✂️ Split at Scenes", command=self.run_split)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="📋 Export Timestamps", command=self.export_timestamps).pack(side="left", padx=5)
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def detect_scenes(self):
        input_file = self.input_entry.get()
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        threshold = self.threshold_spin.get()
        
        # Use select filter with scene detection
        cmd = [
            get_binary("ffmpeg"), "-i", input_file,
            "-vf", f"select='gt(scene,{threshold})',showinfo",
            "-f", "null", "-"
        ]
        
        self._on_log(f"Detecting: {' '.join(cmd)}\n")
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
            output = result.stderr
            
            # Parse pts_time from showinfo output
            self.scenes = [0.0]  # Always start at 0
            for match in re.finditer(r'pts_time:([\d.]+)', output):
                ts = float(match.group(1))
                if ts > 0:
                    self.scenes.append(ts)
            
            # Remove duplicates and sort
            self.scenes = sorted(set(self.scenes))
            
            # Display scenes
            self.scene_list.delete(0, tk.END)
            for i, ts in enumerate(self.scenes):
                mins = int(ts // 60)
                secs = ts % 60
                self.scene_list.insert(tk.END, f"Scene {i+1}: {mins:02d}:{secs:05.2f}")
            
            self.scene_info_label.config(text=f"Found {len(self.scenes)} scene boundaries.")
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Detection failed: {e}")
    
    def run_split(self):
        input_file = self.input_entry.get()
        output_folder = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        if not self.scenes or len(self.scenes) < 2:
            tk.messagebox.showerror("Error", "Please detect scenes first (need at least 2 boundaries).")
            return
        
        if not output_folder:
            output_folder = str(Path(input_file).parent / "scenes")
        
        ensure_dir(Path(output_folder))
        
        input_name = Path(input_file).stem
        ext = Path(input_file).suffix
        
        # Split at each scene boundary
        for i in range(len(self.scenes)):
            start = self.scenes[i]
            end = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
            
            out_file = str(Path(output_folder) / f"{input_name}_scene{i+1:03d}{ext}")
            
            cmd = [get_binary("ffmpeg"), "-y", "-ss", str(start)]
            if end:
                cmd.extend(["-to", str(end)])
            cmd.extend(["-i", input_file, "-c", "copy", out_file])
            
            self._on_log(f"Extracting scene {i+1}: {' '.join(cmd)}\n")
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(cmd, creationflags=creationflags)
        
        tk.messagebox.showinfo("Complete", f"Split into {len(self.scenes)} scenes in {output_folder}")
    
    def export_timestamps(self):
        if not self.scenes:
            tk.messagebox.showerror("Error", "No scenes detected.")
            return
        
        input_file = self.input_entry.get()
        out_file = str(Path(input_file).with_suffix(".scenes.txt")) if input_file else "scenes.txt"
        
        with open(out_file, "w") as f:
            for i, ts in enumerate(self.scenes):
                mins = int(ts // 60)
                secs = ts % 60
                f.write(f"Scene {i+1}: {mins:02d}:{secs:05.2f}\n")
        
        tk.messagebox.showinfo("Exported", f"Timestamps saved to {out_file}")

if __name__ == "__main__":
    app = SceneDetectTool()
    app.run()
