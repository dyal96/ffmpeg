"""
FFmpeg Reverse Tool
Reverse video playback
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class ReverseApp(FFmpegToolApp):
    """Video reverse tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Reverse", width=600, height=500)
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
        
        # === Reverse Options ===
        options_card = create_card(main_frame, "🔄 Reverse Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        self.reverse_video = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_card, text="Reverse video", 
                        variable=self.reverse_video).pack(anchor="w", pady=2)
        
        self.reverse_audio = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_card, text="Reverse audio",
                        variable=self.reverse_audio).pack(anchor="w", pady=2)
        
        ttk.Label(options_card, text="⚠️ Note: This requires loading the entire video into memory",
                  foreground="orange").pack(anchor="w", pady=(10, 0))
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔄 Reverse", command=self.run_reverse)
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
            
            output_path = generate_output_path(input_path, "_reversed")
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
        
        filters = []
        if self.reverse_video.get():
            filters.append("reverse")
        if self.reverse_audio.get():
            filters.append("areverse")
        
        if filters:
            if len(filters) == 2:
                cmd.extend(["-vf", "reverse", "-af", "areverse"])
            elif "reverse" in filters:
                cmd.extend(["-vf", "reverse", "-an"])
            else:
                cmd.extend(["-af", "areverse", "-c:v", "copy"])
        
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_reverse(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ReverseApp()
    app.run()
