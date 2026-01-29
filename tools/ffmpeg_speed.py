"""
FFmpeg Speed Tool
Change video playback speed with audio pitch correction
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class SpeedApp(FFmpegToolApp):
    """Video speed change tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Speed Changer", width=600, height=550)
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
        
        # === Speed Options ===
        options_card = create_card(main_frame, "⏩ Speed Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Speed multiplier
        speed_row = ttk.Frame(options_card)
        speed_row.pack(fill="x", pady=5)
        
        ttk.Label(speed_row, text="Speed:").pack(side="left")
        self.speed_var = tk.DoubleVar(value=2.0)
        speed_scale = ttk.Scale(speed_row, from_=0.25, to=4.0, variable=self.speed_var,
                                orient="horizontal", length=200, command=self._update_speed_label)
        speed_scale.pack(side="left", padx=5)
        self.speed_label = ttk.Label(speed_row, text="2.0x (faster)")
        self.speed_label.pack(side="left")
        
        # Preset buttons
        preset_row = ttk.Frame(options_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        for speed in [0.5, 0.75, 1.0, 1.5, 2.0, 4.0]:
            btn = ttk.Button(preset_row, text=f"{speed}x", width=5,
                           command=lambda s=speed: self._set_speed(s))
            btn.pack(side="left", padx=2)
        
        # Audio handling
        audio_row = ttk.Frame(options_card)
        audio_row.pack(fill="x", pady=5)
        
        self.keep_pitch = tk.BooleanVar(value=True)
        ttk.Checkbutton(audio_row, text="Keep audio pitch (prevent chipmunk effect)",
                        variable=self.keep_pitch).pack(anchor="w")
        
        self.include_audio = tk.BooleanVar(value=True)
        ttk.Checkbutton(audio_row, text="Include audio in output",
                        variable=self.include_audio).pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="⏩ Apply Speed", command=self.run_speed)
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
            
            output_path = generate_output_path(input_path, "_speed")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _set_speed(self, speed):
        self.speed_var.set(speed)
        self._update_speed_label(speed)
    
    def _update_speed_label(self, value):
        speed = float(value)
        if speed > 1:
            desc = "faster"
        elif speed < 1:
            desc = "slower"
        else:
            desc = "normal"
        self.speed_label.configure(text=f"{speed:.2f}x ({desc})")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        speed = self.speed_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        # Video filter: setpts for speed change
        video_filter = f"setpts={1/speed}*PTS"
        
        if self.include_audio.get():
            # Audio filter: atempo (only supports 0.5-2.0, chain for larger)
            if self.keep_pitch.get():
                atempo_filters = []
                remaining = speed
                while remaining > 2.0:
                    atempo_filters.append("atempo=2.0")
                    remaining /= 2.0
                while remaining < 0.5:
                    atempo_filters.append("atempo=0.5")
                    remaining /= 0.5
                atempo_filters.append(f"atempo={remaining}")
                audio_filter = ",".join(atempo_filters)
            else:
                audio_filter = f"asetrate=44100*{speed},aresample=44100"
            
            cmd.extend(["-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]"])
            cmd.extend(["-map", "[v]", "-map", "[a]"])
        else:
            cmd.extend(["-vf", video_filter, "-an"])
        
        cmd.extend(["-c:v", "libx264", "-crf", "23"])
        if self.include_audio.get():
            cmd.extend(["-c:a", "aac"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_speed(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = SpeedApp()
    app.run()
