"""
FFmpeg Splitter Tool
Split video into multiple parts
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    browse_file, browse_folder, create_card, get_theme, parse_time_to_seconds
)

class SplitterApp(FFmpegToolApp):
    """Video splitting tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Video Splitter", width=600, height=560)
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
        
        # === Split Mode ===
        mode_card = create_card(main_frame, "✂️ Split Mode")
        mode_card.pack(fill="x", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="duration")
        ttk.Radiobutton(mode_card, text="By duration (each segment N seconds)",
                        variable=self.mode_var, value="duration",
                        command=self._on_mode_change).pack(anchor="w")
        ttk.Radiobutton(mode_card, text="By count (split into N parts)",
                        variable=self.mode_var, value="count",
                        command=self._on_mode_change).pack(anchor="w")
        
        # Duration input
        self.dur_frame = ttk.Frame(mode_card)
        self.dur_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.dur_frame, text="Segment duration:").pack(side="left")
        self.segment_dur = ttk.Entry(self.dur_frame, width=10)
        self.segment_dur.insert(0, "60")
        self.segment_dur.pack(side="left", padx=5)
        ttk.Label(self.dur_frame, text="seconds").pack(side="left")
        
        # Count input
        self.count_frame = ttk.Frame(mode_card)
        
        ttk.Label(self.count_frame, text="Number of parts:").pack(side="left")
        self.segment_count = ttk.Entry(self.count_frame, width=10)
        self.segment_count.insert(0, "4")
        self.segment_count.pack(side="left", padx=5)
        
        # Options
        self.reencode = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_card, text="Re-encode (accurate splits, slower)",
                        variable=self.reencode).pack(anchor="w", pady=5)
        
        # === Output Section ===
        output_card = create_card(main_frame, "📤 Output Folder")
        output_card.pack(fill="x", pady=(0, 10))
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        
        ttk.Label(output_row, text="Output Folder:").pack(side="left")
        self.output_entry = ttk.Entry(output_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(output_row, text="Browse", command=self._browse_output).pack(side="left")
        
        # Filename pattern
        pattern_row = ttk.Frame(output_card)
        pattern_row.pack(fill="x", pady=5)
        
        ttk.Label(pattern_row, text="Pattern:").pack(side="left")
        self.pattern_entry = ttk.Entry(pattern_row, width=30)
        self.pattern_entry.insert(0, "segment_%03d")
        self.pattern_entry.pack(side="left", padx=5)
        ttk.Label(pattern_row, text="(%03d = 001, 002, etc.)", foreground="gray").pack(side="left")
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="✂️ Split", command=self.run_split)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_mode_change(self):
        if self.mode_var.get() == "duration":
            self.dur_frame.pack(fill="x", pady=5)
            self.count_frame.pack_forget()
        else:
            self.count_frame.pack(fill="x", pady=5)
            self.dur_frame.pack_forget()
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            # Set output folder to same directory
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(Path(input_path).parent))
    
    def _browse_output(self):
        browse_folder(self.output_entry)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_folder = self.output_entry.get()
        
        if not input_path or not output_folder:
            return None
        
        # Get file extension
        ext = Path(input_path).suffix
        pattern = self.pattern_entry.get()
        output_pattern = str(Path(output_folder) / f"{pattern}{ext}")
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if self.mode_var.get() == "duration":
            segment_time = self.segment_dur.get()
            cmd.extend(["-f", "segment", "-segment_time", segment_time])
        else:
            # For count mode, calculate duration per segment
            duration = get_media_duration(input_path)
            if duration:
                count = int(self.segment_count.get())
                segment_time = duration / count
                cmd.extend(["-f", "segment", "-segment_time", str(int(segment_time))])
        
        if not self.reencode.get():
            cmd.extend(["-c", "copy"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        
        cmd.extend(["-reset_timestamps", "1"])
        cmd.append(output_pattern)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output.")
    
    def run_split(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = SplitterApp()
    app.run()
