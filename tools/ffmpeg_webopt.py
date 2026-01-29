"""
FFmpeg WebOpt Tool
Optimize video for web streaming (faststart, web-compatible codec)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class WebOptApp(FFmpegToolApp):
    """Web optimization tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Web Optimizer", width=600, height=520)
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
        
        # === Web Optimization Options ===
        options_card = create_card(main_frame, "🌐 Web Optimization")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Faststart
        self.faststart = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_card, text="Enable faststart (move moov atom to start)",
                        variable=self.faststart).pack(anchor="w", pady=2)
        
        # Profile
        profile_row = ttk.Frame(options_card)
        profile_row.pack(fill="x", pady=5)
        
        ttk.Label(profile_row, text="H.264 Profile:").pack(side="left")
        self.profile_var = tk.StringVar(value="main")
        profile_combo = ttk.Combobox(profile_row, textvariable=self.profile_var, width=12,
                                     values=["baseline", "main", "high"])
        profile_combo.pack(side="left", padx=5)
        ttk.Label(profile_row, text="(baseline = max compatibility)", foreground="gray").pack(side="left")
        
        # Pixel format
        pix_row = ttk.Frame(options_card)
        pix_row.pack(fill="x", pady=5)
        
        ttk.Label(pix_row, text="Pixel Format:").pack(side="left")
        self.pix_var = tk.StringVar(value="yuv420p")
        pix_combo = ttk.Combobox(pix_row, textvariable=self.pix_var, width=12,
                                 values=["yuv420p", "yuv422p", "yuv444p"])
        pix_combo.pack(side="left", padx=5)
        ttk.Label(pix_row, text="(yuv420p = required for most browsers)", foreground="gray").pack(side="left")
        
        # Quality
        crf_row = ttk.Frame(options_card)
        crf_row.pack(fill="x", pady=5)
        
        ttk.Label(crf_row, text="Quality (CRF):").pack(side="left")
        self.crf_var = tk.IntVar(value=23)
        crf_scale = ttk.Scale(crf_row, from_=18, to=35, variable=self.crf_var,
                              orient="horizontal", length=150)
        crf_scale.pack(side="left", padx=5)
        self.crf_label = ttk.Label(crf_row, text="23")
        self.crf_label.pack(side="left")
        crf_scale.configure(command=lambda v: self.crf_label.configure(text=str(int(float(v)))))
        
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
        self.run_btn = ttk.Button(btn_frame, text="🌐 Optimize", command=self.run_webopt)
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
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "_web", ".mp4")
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
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        cmd.extend(["-c:v", "libx264"])
        cmd.extend(["-profile:v", self.profile_var.get()])
        cmd.extend(["-pix_fmt", self.pix_var.get()])
        cmd.extend(["-crf", str(self.crf_var.get())])
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        
        if self.faststart.get():
            cmd.extend(["-movflags", "+faststart"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_webopt(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = WebOptApp()
    app.run()
