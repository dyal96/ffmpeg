"""
FFmpeg Video Scopes Tool
Generate video analysis scopes (waveform, vectorscope, histogram)
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme
)

SCOPE_TYPES = {
    "Waveform (Luma)": "waveform=mode=column:filter=lowpass",
    "Waveform (RGB Parade)": "waveform=mode=column:components=7:filter=lowpass",
    "Vectorscope": "vectorscope=mode=color4",
    "Histogram": "histogram=display_mode=stack",
    "RGB Histogram": "histogram=components=7:display_mode=parade",
    "All Scopes (Stack)": "split=4[a][b][c][d];[a]waveform[wa];[b]vectorscope=mode=color4[vs];[c]histogram[hi];[d]scale=iw/2:ih/2[sc];[wa][vs]hstack[top];[hi][sc]hstack[bot];[top][bot]vstack"
}

class VideoScopesTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Video Scopes", 650, 550)
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
        
        # Scope Settings
        scope_card = create_card(self.root, "📊 Scope Type")
        scope_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(scope_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Scope:").pack(side="left")
        self.scope_var = tk.StringVar(value="Waveform (Luma)")
        scope_combo = ttk.Combobox(row1, textvariable=self.scope_var,
                                    values=list(SCOPE_TYPES.keys()), state="readonly", width=30)
        scope_combo.pack(side="left", padx=5)
        
        # Output mode
        mode_card = create_card(self.root, "🎬 Output Mode")
        mode_card.pack(fill="x", padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="overlay")
        modes_row = ttk.Frame(mode_card)
        modes_row.pack(fill="x", pady=5)
        
        ttk.Radiobutton(modes_row, text="Overlay on Video", 
                        variable=self.mode_var, value="overlay").pack(side="left", padx=5)
        ttk.Radiobutton(modes_row, text="Scope Only", 
                        variable=self.mode_var, value="scope_only").pack(side="left", padx=5)
        ttk.Radiobutton(modes_row, text="Side by Side", 
                        variable=self.mode_var, value="side").pack(side="left", padx=5)
        
        # Frame extraction
        frame_row = ttk.Frame(mode_card)
        frame_row.pack(fill="x", pady=5)
        
        self.single_frame_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_row, text="Single frame only (at timestamp):", 
                        variable=self.single_frame_var).pack(side="left")
        self.timestamp_entry = ttk.Entry(frame_row, width=10)
        self.timestamp_entry.insert(0, "00:00:05")
        self.timestamp_entry.pack(side="left", padx=5)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(out_row, text="Browse", command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Generate Scope", command=self.run_scope)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        self.create_bottom_section(self.root)
    
    def run_scope(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        scope_name = self.scope_var.get()
        scope_filter = SCOPE_TYPES.get(scope_name, SCOPE_TYPES["Waveform (Luma)"])
        mode = self.mode_var.get()
        single_frame = self.single_frame_var.get()
        
        if not output_file:
            ext = ".png" if single_frame else ".mp4"
            output_file = generate_output_path(input_file, "_scope", ext)
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        if single_frame:
            timestamp = self.timestamp_entry.get()
            cmd.extend(["-ss", timestamp])
        
        cmd.extend(["-i", input_file])
        
        # Build filter based on mode
        if mode == "overlay":
            filter_str = f"split[main][scope];[scope]{scope_filter},scale=iw/3:-1[sc];[main][sc]overlay=W-w-10:H-h-10"
        elif mode == "scope_only":
            filter_str = scope_filter
        else:  # side by side
            filter_str = f"split[main][scope];[scope]{scope_filter}[sc];[main][sc]hstack"
        
        cmd.extend(["-vf", filter_str])
        
        if single_frame:
            cmd.extend(["-frames:v", "1"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "18", "-an"])
        
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = VideoScopesTool()
    app.run()
