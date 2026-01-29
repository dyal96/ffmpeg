"""
FFmpeg Audio Visualizer Tool
Generate audio visualization videos from audio or video files
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

# Visualization styles
VIZ_STYLES = {
    "Waveform (showwaves)": "showwaves=s={w}x{h}:mode=line:colors=cyan",
    "Spectrum (showspectrum)": "showspectrum=s={w}x{h}:slide=scroll:color=rainbow",
    "Frequency Bars (showfreqs)": "showfreqs=s={w}x{h}:mode=bar:colors=rainbow",
    "Volume Meter (showvolume)": "showvolume=w={w}:h=50",
    "Vector Scope (avectorscope)": "avectorscope=s={w}x{h}:mode=lissajous:draw=line",
    "Histogram (ahistogram)": "ahistogram=s={w}x{h}",
}

class VisualizerTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Audio Visualizer", 650, 580)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input Audio/Video")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=lambda: browse_file(self.input_entry, 
                   [("Media files", "*.mp3;*.mp4;*.wav;*.flac;*.mkv;*.aac"), ("All", "*.*")])).pack(side="left")
        
        # Visualization Settings
        viz_card = create_card(self.root, "🎵 Visualization Style")
        viz_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(viz_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Style:").pack(side="left")
        self.style_var = tk.StringVar(value="Waveform (showwaves)")
        style_combo = ttk.Combobox(row1, textvariable=self.style_var, 
                                    values=list(VIZ_STYLES.keys()), state="readonly", width=30)
        style_combo.pack(side="left", padx=5)
        
        # Resolution
        row2 = ttk.Frame(viz_card)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Width:").pack(side="left")
        self.width_spin = ttk.Spinbox(row2, from_=320, to=3840, increment=10, width=6)
        self.width_spin.set(1280)
        self.width_spin.pack(side="left", padx=5)
        
        ttk.Label(row2, text="Height:").pack(side="left", padx=(10, 0))
        self.height_spin = ttk.Spinbox(row2, from_=240, to=2160, increment=10, width=6)
        self.height_spin.set(720)
        self.height_spin.pack(side="left", padx=5)
        
        # Background
        row3 = ttk.Frame(viz_card)
        row3.pack(fill="x", pady=5)
        
        ttk.Label(row3, text="Background:").pack(side="left")
        self.bg_var = tk.StringVar(value="black")
        bg_combo = ttk.Combobox(row3, textvariable=self.bg_var, 
                                 values=["black", "white", "0x1a1a2e", "0x16213e"], 
                                 state="readonly", width=12)
        bg_combo.pack(side="left", padx=5)
        
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
        
        self.run_btn = ttk.Button(actions, text="▶ Generate", command=self.run_visualize)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def run_visualize(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_viz", ".mp4")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        style_name = self.style_var.get()
        w = int(self.width_spin.get())
        h = int(self.height_spin.get())
        bg = self.bg_var.get()
        
        # Get filter template and format with dimensions
        filter_template = VIZ_STYLES.get(style_name, VIZ_STYLES["Waveform (showwaves)"])
        audio_filter = filter_template.format(w=w, h=h)
        
        # Build filter complex
        filter_complex = (
            f"[0:a]{audio_filter}[viz];"
            f"color=c={bg}:s={w}x{h}[bg];"
            f"[bg][viz]overlay=shortest=1"
        )
        
        cmd = [
            get_binary("ffmpeg"), "-y", "-i", input_file,
            "-filter_complex", filter_complex,
            "-c:v", "libx264", "-crf", "23", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            output_file
        ]
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = VisualizerTool()
    app.run()
