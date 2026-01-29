"""
FFmpeg Tonemap Tool
Convert HDR video to SDR (tone mapping)
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme
)

# Tonemap algorithms
TONEMAP_ALGOS = [
    "hable",
    "reinhard",
    "mobius",
    "linear",
    "clip",
    "gamma",
    "none"
]

class TonemapTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("HDR to SDR Tonemap", 650, 550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input HDR Video")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=lambda: browse_file(self.input_entry, 
                   [("Video files", "*.mp4;*.mkv;*.mov;*.webm"), ("All", "*.*")])).pack(side="left")
        
        # Tonemap Settings
        settings_card = create_card(self.root, "🎨 Tonemap Settings")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(settings_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Algorithm:").pack(side="left")
        self.algo_var = tk.StringVar(value="hable")
        algo_combo = ttk.Combobox(row1, textvariable=self.algo_var, 
                                   values=TONEMAP_ALGOS, state="readonly", width=12)
        algo_combo.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Peak (nits):").pack(side="left", padx=(15, 0))
        self.peak_spin = ttk.Spinbox(row1, from_=100, to=10000, increment=100, width=6)
        self.peak_spin.set(1000)
        self.peak_spin.pack(side="left", padx=5)
        
        row2 = ttk.Frame(settings_card)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Desat Strength:").pack(side="left")
        self.desat_spin = ttk.Spinbox(row2, from_=0.0, to=1.0, increment=0.1, width=6)
        self.desat_spin.set(0.0)
        self.desat_spin.pack(side="left", padx=5)
        
        # Color Space Options
        row3 = ttk.Frame(settings_card)
        row3.pack(fill="x", pady=5)
        
        ttk.Label(row3, text="Target Color Space:").pack(side="left")
        self.colorspace_var = tk.StringVar(value="bt709")
        cs_combo = ttk.Combobox(row3, textvariable=self.colorspace_var, 
                                 values=["bt709", "bt601", "smpte170m"], state="readonly", width=12)
        cs_combo.pack(side="left", padx=5)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(out_row, text="Browse", 
                   command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Tonemap", command=self.run_tonemap)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def run_tonemap(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_sdr")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        algo = self.algo_var.get()
        peak = float(self.peak_spin.get()) / 10000.0  # Convert to 0-1 range
        desat = float(self.desat_spin.get())
        colorspace = self.colorspace_var.get()
        
        # Build tonemap filter chain
        filter_str = (
            f"zscale=t=linear:npl={int(float(self.peak_spin.get()))},"
            f"tonemap={algo}:desat={desat}:peak={peak},"
            f"zscale=t={colorspace}:m={colorspace}:r=tv,"
            f"format=yuv420p"
        )
        
        cmd = [
            get_binary("ffmpeg"), "-y", "-i", input_file,
            "-vf", filter_str,
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-c:a", "copy",
            output_file
        ]
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = TonemapTool()
    app.run()
