"""
FFmpeg GIF Tool
Convert video to animated GIF with palette optimization
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme,
    TEMP_DIR
)

class GifApp(FFmpegToolApp):
    """Video to GIF conversion tool."""
    
    def __init__(self):
        super().__init__("FFmpeg GIF Maker", width=600, height=580)
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
        
        # === GIF Options ===
        options_card = create_card(main_frame, "🎞️ GIF Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Time range
        time_row = ttk.Frame(options_card)
        time_row.pack(fill="x", pady=2)
        
        ttk.Label(time_row, text="Start:").pack(side="left")
        self.start_entry = ttk.Entry(time_row, width=10)
        self.start_entry.insert(0, "00:00:00")
        self.start_entry.pack(side="left", padx=5)
        
        ttk.Label(time_row, text="Duration (sec):").pack(side="left", padx=(20, 0))
        self.duration_entry = ttk.Entry(time_row, width=8)
        self.duration_entry.insert(0, "5")
        self.duration_entry.pack(side="left", padx=5)
        
        # FPS
        fps_row = ttk.Frame(options_card)
        fps_row.pack(fill="x", pady=5)
        
        ttk.Label(fps_row, text="FPS:").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        fps_scale = ttk.Scale(fps_row, from_=5, to=30, variable=self.fps_var,
                              orient="horizontal", length=150, command=self._update_fps_label)
        fps_scale.pack(side="left", padx=5)
        self.fps_label = ttk.Label(fps_row, text="15 fps")
        self.fps_label.pack(side="left")
        
        # Scale
        scale_row = ttk.Frame(options_card)
        scale_row.pack(fill="x", pady=5)
        
        ttk.Label(scale_row, text="Width:").pack(side="left")
        self.width_var = tk.IntVar(value=480)
        width_combo = ttk.Combobox(scale_row, textvariable=self.width_var, width=8,
                                   values=[320, 480, 640, 720, 1280])
        width_combo.pack(side="left", padx=5)
        ttk.Label(scale_row, text="px (height auto)").pack(side="left")
        
        # Palette optimization
        palette_row = ttk.Frame(options_card)
        palette_row.pack(fill="x", pady=5)
        
        self.use_palette = tk.BooleanVar(value=True)
        ttk.Checkbutton(palette_row, text="Use palette optimization (better colors, slower)",
                        variable=self.use_palette).pack(anchor="w")
        
        # Dither mode
        dither_row = ttk.Frame(options_card)
        dither_row.pack(fill="x", pady=2)
        
        ttk.Label(dither_row, text="Dither:").pack(side="left")
        self.dither_var = tk.StringVar(value="sierra2_4a")
        dither_combo = ttk.Combobox(dither_row, textvariable=self.dither_var, width=15,
                                    values=["none", "bayer", "floyd_steinberg", "sierra2", "sierra2_4a"])
        dither_combo.pack(side="left", padx=5)
        
        # === Output Section ===
        output_card = create_card(main_frame, "📤 Output")
        output_card.pack(fill="x", pady=(0, 10))
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        
        ttk.Label(output_row, text="Output GIF:").pack(side="left")
        self.output_entry = ttk.Entry(output_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(output_row, text="Browse", command=self._browse_output).pack(side="left")
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="🎞️ Create GIF", command=self.run_gif)
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
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "", ".gif")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("GIF files", "*.gif"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".gif")
    
    def _update_fps_label(self, value):
        self.fps_label.configure(text=f"{int(float(value))} fps")
    
    def build_command(self) -> list:
        """Build the FFmpeg command for GIF creation."""
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        fps = self.fps_var.get()
        width = self.width_var.get()
        start = self.start_entry.get().strip()
        duration = self.duration_entry.get().strip()
        
        # Build filter string
        filters = f"fps={fps},scale={width}:-1:flags=lanczos"
        
        if self.use_palette.get():
            # Two-pass with palette (returns palette generation command first)
            # For preview, we'll show the final command
            dither = self.dither_var.get()
            filters += f",split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither={dither}"
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        if start and start != "00:00:00":
            cmd.extend(["-ss", start])
        
        cmd.extend(["-i", input_path])
        
        if duration:
            cmd.extend(["-t", duration])
        
        cmd.extend(["-vf", filters])
        cmd.extend(["-loop", "0"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_gif(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = GifApp()
    app.run()
