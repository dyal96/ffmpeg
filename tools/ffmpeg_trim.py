"""
FFmpeg Trim Tool
Cut/trim video files with start and end time
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme,
    parse_time_to_seconds
)

class TrimApp(FFmpegToolApp):
    """Video trimming tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Trim", width=600, height=550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Input")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="Input File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=50)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", command=self._browse_input).pack(side="left")
        
        self.duration_label = ttk.Label(input_card, text="Duration: --:--:--")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        # === Trim Options ===
        trim_card = create_card(main_frame, "✂️ Trim Settings")
        trim_card.pack(fill="x", pady=(0, 10))
        
        # Start time
        start_row = ttk.Frame(trim_card)
        start_row.pack(fill="x", pady=2)
        
        ttk.Label(start_row, text="Start Time:").pack(side="left")
        self.start_entry = ttk.Entry(start_row, width=15)
        self.start_entry.insert(0, "00:00:00")
        self.start_entry.pack(side="left", padx=5)
        ttk.Label(start_row, text="(HH:MM:SS)", foreground="gray").pack(side="left")
        
        # End time
        end_row = ttk.Frame(trim_card)
        end_row.pack(fill="x", pady=2)
        
        ttk.Label(end_row, text="End Time:").pack(side="left")
        self.end_entry = ttk.Entry(end_row, width=15)
        self.end_entry.insert(0, "00:00:10")
        self.end_entry.pack(side="left", padx=5)
        ttk.Label(end_row, text="(HH:MM:SS or leave empty for end)").pack(side="left")
        
        # Copy mode (fast) vs re-encode
        mode_row = ttk.Frame(trim_card)
        mode_row.pack(fill="x", pady=5)
        
        self.copy_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode_row, text="Fast copy mode (no re-encode, may be inaccurate)", 
                        variable=self.copy_mode).pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="✂️ Trim", command=self.run_trim)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
                # Set end time to full duration
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, format_duration(duration))
            
            # Auto-generate output
            output_path = generate_output_path(input_path, "_trimmed")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        input_path = self.input_entry.get()
        ext = Path(input_path).suffix if input_path else ".mp4"
        filetypes = [("Video files", f"*{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ext)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        start_str = self.start_entry.get().strip()
        end_str = self.end_entry.get().strip()
        
        if not input_path or not output_path:
            return None
            
        # Calculate duration
        start_sec = parse_time_to_seconds(start_str) if start_str else 0
        end_sec = parse_time_to_seconds(end_str) if end_str else 0
        
        duration = 0
        if end_sec > start_sec:
            duration = end_sec - start_sec
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        # Add start time (before input for faster seeking)
        if start_sec > 0:
            cmd.extend(["-ss", str(start_sec)])
        
        cmd.extend(["-i", input_path])
        
        # Add duration
        if duration > 0:
            cmd.extend(["-t", str(duration)])
        
        # Copy mode or re-encode
        if self.copy_mode.get():
            cmd.extend(["-c", "copy"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_trim(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = TrimApp()
    app.run()
