"""
FFmpeg Resize Tool
Resize/scale video files with preset resolutions
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, get_media_info, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

# Resolution presets
PRESETS = {
    "4K (3840x2160)": (3840, 2160),
    "1440p (2560x1440)": (2560, 1440),
    "1080p (1920x1080)": (1920, 1080),
    "720p (1280x720)": (1280, 720),
    "480p (854x480)": (854, 480),
    "360p (640x360)": (640, 360),
    "Custom": None
}

class ResizeApp(FFmpegToolApp):
    """Video resizing tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Resize", width=600, height=580)
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
        
        self.info_label = ttk.Label(input_card, text="Duration: --:--:-- | Resolution: --")
        self.info_label.pack(anchor="w", pady=(5, 0))
        
        # === Resize Options ===
        options_card = create_card(main_frame, "📐 Resize Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Preset selection
        preset_row = ttk.Frame(options_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Preset:").pack(side="left")
        self.preset_var = tk.StringVar(value="1080p (1920x1080)")
        preset_combo = ttk.Combobox(preset_row, textvariable=self.preset_var, width=20,
                                    values=list(PRESETS.keys()))
        preset_combo.pack(side="left", padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)
        
        # Custom dimensions
        self.custom_frame = ttk.Frame(options_card)
        self.custom_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.custom_frame, text="Width:").pack(side="left")
        self.width_entry = ttk.Entry(self.custom_frame, width=8)
        self.width_entry.insert(0, "1920")
        self.width_entry.pack(side="left", padx=5)
        
        ttk.Label(self.custom_frame, text="Height:").pack(side="left", padx=(20, 0))
        self.height_entry = ttk.Entry(self.custom_frame, width=8)
        self.height_entry.insert(0, "1080")
        self.height_entry.pack(side="left", padx=5)
        
        # Keep aspect ratio
        aspect_row = ttk.Frame(options_card)
        aspect_row.pack(fill="x", pady=5)
        
        self.keep_aspect = tk.BooleanVar(value=True)
        ttk.Checkbutton(aspect_row, text="Maintain aspect ratio (use -1 for auto height/width)",
                        variable=self.keep_aspect, command=self._toggle_aspect).pack(anchor="w")
        
        # Scaling algorithm
        algo_row = ttk.Frame(options_card)
        algo_row.pack(fill="x", pady=5)
        
        ttk.Label(algo_row, text="Algorithm:").pack(side="left")
        self.algo_var = tk.StringVar(value="lanczos")
        algo_combo = ttk.Combobox(algo_row, textvariable=self.algo_var, width=12,
                                  values=["lanczos", "bicubic", "bilinear", "neighbor", "spline"])
        algo_combo.pack(side="left", padx=5)
        ttk.Label(algo_row, text="(lanczos = best quality)", foreground="gray").pack(side="left")
        
        # Codec options
        codec_row = ttk.Frame(options_card)
        codec_row.pack(fill="x", pady=5)
        
        ttk.Label(codec_row, text="Codec:").pack(side="left")
        self.codec_var = tk.StringVar(value="libx264")
        codec_combo = ttk.Combobox(codec_row, textvariable=self.codec_var, width=12,
                                   values=["libx264", "libx265", "h264_nvenc", "copy"])
        codec_combo.pack(side="left", padx=5)
        
        # CRF
        crf_row = ttk.Frame(options_card)
        crf_row.pack(fill="x", pady=5)
        
        ttk.Label(crf_row, text="Quality (CRF):").pack(side="left")
        self.crf_var = tk.IntVar(value=23)
        crf_scale = ttk.Scale(crf_row, from_=15, to=35, variable=self.crf_var,
                              orient="horizontal", length=150, command=self._update_crf_label)
        crf_scale.pack(side="left", padx=5)
        self.crf_label = ttk.Label(crf_row, text="23")
        self.crf_label.pack(side="left")
        
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
        self.run_btn = ttk.Button(btn_frame, text="📐 Resize", command=self.run_resize)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            info = get_media_info(input_path)
            
            dur_str = format_duration(duration) if duration else "--:--:--"
            res_str = "--"
            
            if info and "streams" in info:
                for stream in info["streams"]:
                    if stream.get("codec_type") == "video":
                        w = stream.get("width", "?")
                        h = stream.get("height", "?")
                        res_str = f"{w}x{h}"
                        break
            
            self.info_label.configure(text=f"Duration: {dur_str} | Resolution: {res_str}")
            
            output_path = generate_output_path(input_path, "_resized")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _on_preset_changed(self, event=None):
        preset = self.preset_var.get()
        dims = PRESETS.get(preset)
        if dims:
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(dims[0]))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(dims[1]))
    
    def _toggle_aspect(self):
        if self.keep_aspect.get():
            # Set height to -1 for auto
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, "-1")
    
    def _update_crf_label(self, value):
        self.crf_label.configure(text=str(int(float(value))))
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        width = self.width_entry.get().strip()
        height = self.height_entry.get().strip()
        algo = self.algo_var.get()
        codec = self.codec_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        # Video filter for scaling
        if codec != "copy":
            scale_filter = f"scale={width}:{height}:flags={algo}"
            cmd.extend(["-vf", scale_filter])
        
        # Codec settings
        if codec == "copy":
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-c:v", codec])
            if codec in ["libx264", "libx265"]:
                cmd.extend(["-crf", str(self.crf_var.get())])
        
        cmd.extend(["-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_resize(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ResizeApp()
    app.run()
