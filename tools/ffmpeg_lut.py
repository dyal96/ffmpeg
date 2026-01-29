"""
FFmpeg LUT Applicator Tool
Apply 3D LUT files (.cube, .3dl) for color grading
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

class LutTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("LUT Applicator", 650, 550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Video Section
        input_card = create_card(self.root, "📂 Input Video")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=lambda: browse_file(self.input_entry, 
                   [("Video files", "*.mp4;*.mkv;*.mov;*.avi"), ("All", "*.*")])).pack(side="left")
        
        # LUT File Section
        lut_card = create_card(self.root, "🎨 LUT File")
        lut_card.pack(fill="x", padx=10, pady=5)
        
        lut_row = ttk.Frame(lut_card)
        lut_row.pack(fill="x", pady=5)
        
        self.lut_entry = ttk.Entry(lut_row)
        self.lut_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(lut_row, text="Browse", 
                   command=lambda: browse_file(self.lut_entry, 
                   [("LUT files", "*.cube;*.3dl;*.lut"), ("All", "*.*")])).pack(side="left")
        
        # Settings
        settings_card = create_card(self.root, "⚙️ Settings")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(settings_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Intensity (0-1):").pack(side="left")
        self.intensity_spin = ttk.Spinbox(row1, from_=0.0, to=1.0, increment=0.1, width=6)
        self.intensity_spin.set(1.0)
        self.intensity_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="(1.0 = full LUT effect)").pack(side="left", padx=5)
        
        # Interpolation mode
        row2 = ttk.Frame(settings_card)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Interpolation:").pack(side="left")
        self.interp_var = tk.StringVar(value="tetrahedral")
        interp_combo = ttk.Combobox(row2, textvariable=self.interp_var, 
                                     values=["nearest", "trilinear", "tetrahedral"], 
                                     state="readonly", width=12)
        interp_combo.pack(side="left", padx=5)
        
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
        
        self.run_btn = ttk.Button(actions, text="▶ Apply LUT", command=self.run_lut)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def run_lut(self):
        input_file = self.input_entry.get()
        lut_file = self.lut_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        if not lut_file:
            tk.messagebox.showerror("Error", "Please select a LUT file.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_lut")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        intensity = float(self.intensity_spin.get())
        interp = self.interp_var.get()
        
        # Escape LUT path for filter (Windows paths need escaping)
        lut_escaped = lut_file.replace("\\", "/").replace(":", "\\:")
        
        if intensity >= 1.0:
            # Full LUT
            filter_str = f"lut3d='{lut_escaped}':interp={interp}"
        else:
            # Blend with original using split and mix
            filter_str = (
                f"split[a][b];"
                f"[a]lut3d='{lut_escaped}':interp={interp}[lut];"
                f"[b][lut]blend=all_expr='A*(1-{intensity})+B*{intensity}'"
            )
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file]
        
        if intensity >= 1.0:
            cmd.extend(["-vf", filter_str])
        else:
            cmd.extend(["-filter_complex", filter_str])
        
        cmd.extend(["-c:v", "libx264", "-crf", "18", "-preset", "medium"])
        cmd.extend(["-c:a", "copy"])
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = LutTool()
    app.run()
