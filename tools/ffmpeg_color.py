"""
FFmpeg Color Tool
Adjust video color (brightness, contrast, saturation, etc.)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class ColorApp(FFmpegToolApp):
    """Video color adjustment tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Color Adjust", width=600, height=600)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Input Video")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="Input File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=50)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", command=self._browse_input).pack(side="left")
        
        # === Color Adjustments ===
        color_card = create_card(main_frame, "🎨 Color Adjustments")
        color_card.pack(fill="x", pady=(0, 10))
        
        # Brightness
        bright_row = ttk.Frame(color_card)
        bright_row.pack(fill="x", pady=3)
        ttk.Label(bright_row, text="Brightness:", width=12).pack(side="left")
        self.brightness_var = tk.DoubleVar(value=0)
        bright_scale = ttk.Scale(bright_row, from_=-1, to=1, variable=self.brightness_var,
                                 orient="horizontal", length=200)
        bright_scale.pack(side="left", padx=5)
        self.bright_label = ttk.Label(bright_row, text="0.00")
        self.bright_label.pack(side="left")
        bright_scale.configure(command=lambda v: self.bright_label.configure(text=f"{float(v):.2f}"))
        
        # Contrast
        contrast_row = ttk.Frame(color_card)
        contrast_row.pack(fill="x", pady=3)
        ttk.Label(contrast_row, text="Contrast:", width=12).pack(side="left")
        self.contrast_var = tk.DoubleVar(value=1)
        contrast_scale = ttk.Scale(contrast_row, from_=0, to=2, variable=self.contrast_var,
                                   orient="horizontal", length=200)
        contrast_scale.pack(side="left", padx=5)
        self.contrast_label = ttk.Label(contrast_row, text="1.00")
        self.contrast_label.pack(side="left")
        contrast_scale.configure(command=lambda v: self.contrast_label.configure(text=f"{float(v):.2f}"))
        
        # Saturation
        sat_row = ttk.Frame(color_card)
        sat_row.pack(fill="x", pady=3)
        ttk.Label(sat_row, text="Saturation:", width=12).pack(side="left")
        self.saturation_var = tk.DoubleVar(value=1)
        sat_scale = ttk.Scale(sat_row, from_=0, to=3, variable=self.saturation_var,
                              orient="horizontal", length=200)
        sat_scale.pack(side="left", padx=5)
        self.sat_label = ttk.Label(sat_row, text="1.00")
        self.sat_label.pack(side="left")
        sat_scale.configure(command=lambda v: self.sat_label.configure(text=f"{float(v):.2f}"))
        
        # Gamma
        gamma_row = ttk.Frame(color_card)
        gamma_row.pack(fill="x", pady=3)
        ttk.Label(gamma_row, text="Gamma:", width=12).pack(side="left")
        self.gamma_var = tk.DoubleVar(value=1)
        gamma_scale = ttk.Scale(gamma_row, from_=0.1, to=3, variable=self.gamma_var,
                                orient="horizontal", length=200)
        gamma_scale.pack(side="left", padx=5)
        self.gamma_label = ttk.Label(gamma_row, text="1.00")
        self.gamma_label.pack(side="left")
        gamma_scale.configure(command=lambda v: self.gamma_label.configure(text=f"{float(v):.2f}"))
        
        # Reset button
        ttk.Button(color_card, text="Reset All", command=self._reset_values).pack(anchor="w", pady=5)
        
        # === Presets ===
        preset_card = create_card(main_frame, "📋 Presets")
        preset_card.pack(fill="x", pady=(0, 10))
        
        preset_row = ttk.Frame(preset_card)
        preset_row.pack(fill="x")
        
        presets = [
            ("Vivid", 0, 1.2, 1.5, 1),
            ("Cinematic", -0.05, 1.1, 0.9, 1.1),
            ("B&W", 0, 1, 0, 1),
            ("Warm", 0.05, 1, 1.1, 1),
            ("Cool", -0.05, 1, 0.9, 1)
        ]
        for name, b, c, s, g in presets:
            btn = ttk.Button(preset_row, text=name, width=10,
                           command=lambda b=b, c=c, s=s, g=g: self._apply_preset(b, c, s, g))
            btn.pack(side="left", padx=2)
        
        # === Output Section ===
        output_card = create_card(main_frame, "📤 Output")
        output_card.pack(fill="x", pady=(0, 10))
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        
        ttk.Label(output_row, text="Output File:").pack(side="left")
        self.output_entry = ttk.Entry(output_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(output_row, text="Browse", command=self._browse_output).pack(side="left")
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="🎨 Apply", command=self.run_color)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            output_path = generate_output_path(input_path, "_color")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _reset_values(self):
        self.brightness_var.set(0)
        self.contrast_var.set(1)
        self.saturation_var.set(1)
        self.gamma_var.set(1)
        self.bright_label.configure(text="0.00")
        self.contrast_label.configure(text="1.00")
        self.sat_label.configure(text="1.00")
        self.gamma_label.configure(text="1.00")
    
    def _apply_preset(self, b, c, s, g):
        self.brightness_var.set(b)
        self.contrast_var.set(c)
        self.saturation_var.set(s)
        self.gamma_var.set(g)
        self.bright_label.configure(text=f"{b:.2f}")
        self.contrast_label.configure(text=f"{c:.2f}")
        self.sat_label.configure(text=f"{s:.2f}")
        self.gamma_label.configure(text=f"{g:.2f}")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        b = self.brightness_var.get()
        c = self.contrast_var.get()
        s = self.saturation_var.get()
        g = self.gamma_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        # Build eq filter
        eq_filter = f"eq=brightness={b}:contrast={c}:saturation={s}:gamma={g}"
        cmd.extend(["-vf", eq_filter])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_color(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ColorApp()
    app.run()
