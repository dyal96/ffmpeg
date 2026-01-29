"""
FFmpeg Thumbnail Tool
Extract thumbnails/frames from video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    browse_file, browse_folder, create_card, get_theme
)

class ThumbnailApp(FFmpegToolApp):
    """Thumbnail/frame extraction tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Thumbnails", width=600, height=560)
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
        
        # === Extraction Mode ===
        mode_card = create_card(main_frame, "🎯 Extraction Mode")
        mode_card.pack(fill="x", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="interval")
        ttk.Radiobutton(mode_card, text="Extract at interval",
                        variable=self.mode_var, value="interval",
                        command=self._on_mode_change).pack(anchor="w")
        ttk.Radiobutton(mode_card, text="Extract specific time",
                        variable=self.mode_var, value="single",
                        command=self._on_mode_change).pack(anchor="w")
        ttk.Radiobutton(mode_card, text="Extract N frames total",
                        variable=self.mode_var, value="count",
                        command=self._on_mode_change).pack(anchor="w")
        
        # Interval settings
        self.interval_frame = ttk.Frame(mode_card)
        self.interval_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.interval_frame, text="Extract every:").pack(side="left")
        self.interval_var = tk.DoubleVar(value=1.0)
        interval_spin = ttk.Spinbox(self.interval_frame, from_=0.1, to=60, increment=0.5,
                                    width=6, textvariable=self.interval_var)
        interval_spin.pack(side="left", padx=5)
        ttk.Label(self.interval_frame, text="seconds").pack(side="left")
        
        # Single time
        self.single_frame = ttk.Frame(mode_card)
        
        ttk.Label(self.single_frame, text="Time (HH:MM:SS):").pack(side="left")
        self.time_entry = ttk.Entry(self.single_frame, width=12)
        self.time_entry.insert(0, "00:00:05")
        self.time_entry.pack(side="left", padx=5)
        
        # Count settings
        self.count_frame = ttk.Frame(mode_card)
        
        ttk.Label(self.count_frame, text="Number of frames:").pack(side="left")
        self.count_var = tk.IntVar(value=10)
        count_spin = ttk.Spinbox(self.count_frame, from_=1, to=100, width=6,
                                 textvariable=self.count_var)
        count_spin.pack(side="left", padx=5)
        
        # === Output Settings ===
        output_card = create_card(main_frame, "📤 Output")
        output_card.pack(fill="x", pady=(0, 10))
        
        folder_row = ttk.Frame(output_card)
        folder_row.pack(fill="x")
        
        ttk.Label(folder_row, text="Output Folder:").pack(side="left")
        self.output_entry = ttk.Entry(folder_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(folder_row, text="Browse", command=self._browse_output).pack(side="left")
        
        # Format
        format_row = ttk.Frame(output_card)
        format_row.pack(fill="x", pady=5)
        
        ttk.Label(format_row, text="Format:").pack(side="left")
        self.format_var = tk.StringVar(value="jpg")
        format_combo = ttk.Combobox(format_row, textvariable=self.format_var, width=8,
                                    values=["jpg", "png", "bmp"])
        format_combo.pack(side="left", padx=5)
        
        ttk.Label(format_row, text="Quality (1-31):").pack(side="left", padx=(20, 0))
        self.quality_var = tk.IntVar(value=2)
        quality_spin = ttk.Spinbox(format_row, from_=1, to=31, width=4,
                                   textvariable=self.quality_var)
        quality_spin.pack(side="left", padx=5)
        
        # Filename pattern
        pattern_row = ttk.Frame(output_card)
        pattern_row.pack(fill="x", pady=5)
        
        ttk.Label(pattern_row, text="Filename:").pack(side="left")
        self.pattern_entry = ttk.Entry(pattern_row, width=20)
        self.pattern_entry.insert(0, "thumb_%04d")
        self.pattern_entry.pack(side="left", padx=5)
        ttk.Label(pattern_row, text="(%04d = 0001, 0002...)", foreground="gray").pack(side="left")
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="🖼️ Extract", command=self.run_extract)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_mode_change(self):
        mode = self.mode_var.get()
        # Hide all
        self.interval_frame.pack_forget()
        self.single_frame.pack_forget()
        self.count_frame.pack_forget()
        # Show selected
        if mode == "interval":
            self.interval_frame.pack(fill="x", pady=5)
        elif mode == "single":
            self.single_frame.pack(fill="x", pady=5)
        else:
            self.count_frame.pack(fill="x", pady=5)
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(Path(input_path).parent))
    
    def _browse_output(self):
        browse_folder(self.output_entry)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_folder = self.output_entry.get()
        
        if not input_path or not output_folder:
            return None
        
        mode = self.mode_var.get()
        fmt = self.format_var.get()
        pattern = self.pattern_entry.get()
        output_pattern = str(Path(output_folder) / f"{pattern}.{fmt}")
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if mode == "interval":
            interval = self.interval_var.get()
            fps = 1 / interval
            cmd.extend(["-vf", f"fps={fps}"])
        elif mode == "single":
            time = self.time_entry.get()
            cmd.extend(["-ss", time, "-vframes", "1"])
            # Override output pattern for single frame
            output_pattern = str(Path(output_folder) / f"frame.{fmt}")
        else:  # count
            count = self.count_var.get()
            duration = get_media_duration(input_path)
            if duration:
                interval = duration / count
                cmd.extend(["-vf", f"fps=1/{interval}"])
        
        cmd.extend(["-q:v", str(self.quality_var.get())])
        cmd.append(output_pattern)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output.")
    
    def run_extract(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ThumbnailApp()
    app.run()
