"""
FFmpeg Denoise Tool
Apply video noise reduction
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class DenoiseApp(FFmpegToolApp):
    """Video denoising tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Denoise", width=600, height=550)
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
        
        self.duration_label = ttk.Label(input_card, text="Duration: --:--:--")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        # === Denoise Settings ===
        denoise_card = create_card(main_frame, "🧹 Denoise Settings")
        denoise_card.pack(fill="x", pady=(0, 10))
        
        # Filter type
        filter_row = ttk.Frame(denoise_card)
        filter_row.pack(fill="x", pady=5)
        
        ttk.Label(filter_row, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value="hqdn3d")
        filter_combo = ttk.Combobox(filter_row, textvariable=self.filter_var, width=15,
                                    values=["hqdn3d", "nlmeans", "atadenoise"])
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # HQDN3D settings
        self.hq_frame = ttk.Frame(denoise_card)
        self.hq_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.hq_frame, text="Luma Spatial:").pack(side="left")
        self.luma_spatial = tk.DoubleVar(value=4.0)
        luma_s = ttk.Scale(self.hq_frame, from_=0, to=10, variable=self.luma_spatial,
                           orient="horizontal", length=100)
        luma_s.pack(side="left", padx=5)
        
        ttk.Label(self.hq_frame, text="Chroma:").pack(side="left", padx=(10, 0))
        self.chroma = tk.DoubleVar(value=3.0)
        chroma_s = ttk.Scale(self.hq_frame, from_=0, to=10, variable=self.chroma,
                             orient="horizontal", length=100)
        chroma_s.pack(side="left", padx=5)
        
        # NLMeans settings
        self.nlm_frame = ttk.Frame(denoise_card)
        
        nlm_row = ttk.Frame(self.nlm_frame)
        nlm_row.pack(fill="x")
        
        ttk.Label(nlm_row, text="Strength:").pack(side="left")
        self.nlm_strength = tk.DoubleVar(value=1.0)
        nlm_s = ttk.Scale(nlm_row, from_=0.5, to=10, variable=self.nlm_strength,
                          orient="horizontal", length=150)
        nlm_s.pack(side="left", padx=5)
        self.nlm_label = ttk.Label(nlm_row, text="1.0")
        self.nlm_label.pack(side="left")
        nlm_s.configure(command=lambda v: self.nlm_label.configure(text=f"{float(v):.1f}"))
        
        ttk.Label(self.nlm_frame, text="⚠️ NLMeans is slow but high quality", 
                  foreground="orange").pack(anchor="w")
        
        # Preset
        preset_row = ttk.Frame(denoise_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        presets = [("Light", 2.0), ("Medium", 4.0), ("Heavy", 7.0)]
        for name, value in presets:
            btn = ttk.Button(preset_row, text=name, width=8,
                           command=lambda v=value: self._apply_preset(v))
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
        self.run_btn = ttk.Button(btn_frame, text="🧹 Denoise", command=self.run_denoise)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_filter_change(self, event=None):
        filter_type = self.filter_var.get()
        self.hq_frame.pack_forget()
        self.nlm_frame.pack_forget()
        
        if filter_type == "hqdn3d":
            self.hq_frame.pack(fill="x", pady=5)
        elif filter_type == "nlmeans":
            self.nlm_frame.pack(fill="x", pady=5)
    
    def _apply_preset(self, value):
        self.luma_spatial.set(value)
        self.chroma.set(value * 0.75)
        self.nlm_strength.set(value / 4)
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "_denoised")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        filter_type = self.filter_var.get()
        
        if filter_type == "hqdn3d":
            ls = self.luma_spatial.get()
            c = self.chroma.get()
            vf = f"hqdn3d={ls}:{c}:{ls}:{c}"
        elif filter_type == "nlmeans":
            s = self.nlm_strength.get()
            vf = f"nlmeans=s={s}"
        else:  # atadenoise
            vf = "atadenoise"
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        cmd.extend(["-vf", vf])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_denoise(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = DenoiseApp()
    app.run()
