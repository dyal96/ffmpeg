"""
FFmpeg Fade Tool
Apply fade in/out effects to video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class FadeApp(FFmpegToolApp):
    """Video fade effects tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Fade Effects", width=600, height=550)
        self.total_duration = 0
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
        
        # === Fade Settings ===
        fade_card = create_card(main_frame, "🌅 Fade Settings")
        fade_card.pack(fill="x", pady=(0, 10))
        
        # Fade In
        fadein_row = ttk.Frame(fade_card)
        fadein_row.pack(fill="x", pady=5)
        
        self.fadein_enable = tk.BooleanVar(value=True)
        ttk.Checkbutton(fadein_row, text="Fade In", variable=self.fadein_enable).pack(side="left")
        
        ttk.Label(fadein_row, text="Duration:").pack(side="left", padx=(20, 0))
        self.fadein_dur = tk.DoubleVar(value=1.0)
        fadein_spin = ttk.Spinbox(fadein_row, from_=0.5, to=10, increment=0.5, width=6,
                                  textvariable=self.fadein_dur)
        fadein_spin.pack(side="left", padx=5)
        ttk.Label(fadein_row, text="sec").pack(side="left")
        
        # Fade Out
        fadeout_row = ttk.Frame(fade_card)
        fadeout_row.pack(fill="x", pady=5)
        
        self.fadeout_enable = tk.BooleanVar(value=True)
        ttk.Checkbutton(fadeout_row, text="Fade Out", variable=self.fadeout_enable).pack(side="left")
        
        ttk.Label(fadeout_row, text="Duration:").pack(side="left", padx=(20, 0))
        self.fadeout_dur = tk.DoubleVar(value=1.0)
        fadeout_spin = ttk.Spinbox(fadeout_row, from_=0.5, to=10, increment=0.5, width=6,
                                   textvariable=self.fadeout_dur)
        fadeout_spin.pack(side="left", padx=5)
        ttk.Label(fadeout_row, text="sec").pack(side="left")
        
        # Fade color
        color_row = ttk.Frame(fade_card)
        color_row.pack(fill="x", pady=5)
        
        ttk.Label(color_row, text="Fade to/from:").pack(side="left")
        self.fade_color = tk.StringVar(value="black")
        color_combo = ttk.Combobox(color_row, textvariable=self.fade_color, width=10,
                                   values=["black", "white"])
        color_combo.pack(side="left", padx=5)
        
        # Audio fade
        audio_row = ttk.Frame(fade_card)
        audio_row.pack(fill="x", pady=5)
        
        self.audio_fade = tk.BooleanVar(value=True)
        ttk.Checkbutton(audio_row, text="Apply fade to audio as well",
                        variable=self.audio_fade).pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="🌅 Apply Fade", command=self.run_fade)
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
            self.total_duration = get_media_duration(input_path) or 0
            if self.total_duration:
                self.duration_label.configure(text=f"Duration: {format_duration(self.total_duration)}")
            
            output_path = generate_output_path(input_path, "_faded")
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
        
        if not self.fadein_enable.get() and not self.fadeout_enable.get():
            messagebox.showinfo("Info", "Please enable at least one fade effect.")
            return None
        
        video_filters = []
        audio_filters = []
        
        color = self.fade_color.get()
        
        # Fade in
        if self.fadein_enable.get():
            dur = self.fadein_dur.get()
            video_filters.append(f"fade=in:st=0:d={dur}:c={color}")
            if self.audio_fade.get():
                audio_filters.append(f"afade=in:st=0:d={dur}")
        
        # Fade out
        if self.fadeout_enable.get() and self.total_duration > 0:
            dur = self.fadeout_dur.get()
            start_time = self.total_duration - dur
            video_filters.append(f"fade=out:st={start_time}:d={dur}:c={color}")
            if self.audio_fade.get():
                audio_filters.append(f"afade=out:st={start_time}:d={dur}")
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])
        
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_fade(self):
        cmd = self.build_command()
        if not cmd:
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = FadeApp()
    app.run()
