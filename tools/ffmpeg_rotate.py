"""
FFmpeg Rotate Tool
Rotate/flip video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class RotateApp(FFmpegToolApp):
    """Video rotate/flip tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Rotate/Flip", width=600, height=520)
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
        
        # === Rotation Options ===
        rotate_card = create_card(main_frame, "🔄 Rotation")
        rotate_card.pack(fill="x", pady=(0, 10))
        
        self.rotate_var = tk.StringVar(value="none")
        
        rotations = [
            ("None", "none"),
            ("90° Clockwise", "cw"),
            ("90° Counter-clockwise", "ccw"),
            ("180°", "180"),
            ("Custom angle", "custom")
        ]
        
        for text, value in rotations:
            ttk.Radiobutton(rotate_card, text=text, variable=self.rotate_var,
                           value=value, command=self._on_rotate_change).pack(anchor="w")
        
        # Custom angle
        self.custom_frame = ttk.Frame(rotate_card)
        
        ttk.Label(self.custom_frame, text="Angle (degrees):").pack(side="left")
        self.angle_entry = ttk.Entry(self.custom_frame, width=8)
        self.angle_entry.insert(0, "45")
        self.angle_entry.pack(side="left", padx=5)
        
        # === Flip Options ===
        flip_card = create_card(main_frame, "↔️ Flip")
        flip_card.pack(fill="x", pady=(0, 10))
        
        self.flip_h = tk.BooleanVar(value=False)
        ttk.Checkbutton(flip_card, text="Flip Horizontal (mirror)",
                        variable=self.flip_h).pack(anchor="w")
        
        self.flip_v = tk.BooleanVar(value=False)
        ttk.Checkbutton(flip_card, text="Flip Vertical",
                        variable=self.flip_v).pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔄 Apply", command=self.run_rotate)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_rotate_change(self):
        if self.rotate_var.get() == "custom":
            self.custom_frame.pack(fill="x", pady=5)
        else:
            self.custom_frame.pack_forget()
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "_rotated")
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
        
        filters = []
        
        # Rotation
        rotate = self.rotate_var.get()
        if rotate == "cw":
            filters.append("transpose=1")
        elif rotate == "ccw":
            filters.append("transpose=2")
        elif rotate == "180":
            filters.append("transpose=1,transpose=1")
        elif rotate == "custom":
            angle = self.angle_entry.get()
            # Convert degrees to radians
            import math
            radians = float(angle) * math.pi / 180
            filters.append(f"rotate={radians}")
        
        # Flips
        if self.flip_h.get():
            filters.append("hflip")
        if self.flip_v.get():
            filters.append("vflip")
        
        if not filters:
            messagebox.showinfo("Info", "No transformation selected.")
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        cmd.extend(["-vf", ",".join(filters)])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_rotate(self):
        cmd = self.build_command()
        if not cmd:
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = RotateApp()
    app.run()
