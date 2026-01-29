"""
FFmpeg Screen Recorder Tool
Record screen using FFmpeg
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys

from ffmpeg_common import (
    FFmpegToolApp, get_binary,
    browse_save_file, create_card, get_theme
)

class RecorderApp(FFmpegToolApp):
    """Screen recording tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Screen Recorder", width=600, height=520)
        self.is_recording = False
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Capture Settings ===
        capture_card = create_card(main_frame, "🖥️ Capture Settings")
        capture_card.pack(fill="x", pady=(0, 10))
        
        # Source
        source_row = ttk.Frame(capture_card)
        source_row.pack(fill="x", pady=5)
        
        ttk.Label(source_row, text="Source:").pack(side="left")
        self.source_var = tk.StringVar(value="desktop")
        source_combo = ttk.Combobox(source_row, textvariable=self.source_var, width=15,
                                    values=["desktop", "window"])
        source_combo.pack(side="left", padx=5)
        
        # Resolution
        res_row = ttk.Frame(capture_card)
        res_row.pack(fill="x", pady=5)
        
        ttk.Label(res_row, text="Resolution:").pack(side="left")
        self.resolution_var = tk.StringVar(value="1920x1080")
        res_combo = ttk.Combobox(res_row, textvariable=self.resolution_var, width=12,
                                 values=["1920x1080", "1280x720", "2560x1440", "3840x2160"])
        res_combo.pack(side="left", padx=5)
        
        # FPS
        fps_row = ttk.Frame(capture_card)
        fps_row.pack(fill="x", pady=5)
        
        ttk.Label(fps_row, text="FPS:").pack(side="left")
        self.fps_var = tk.IntVar(value=30)
        fps_combo = ttk.Combobox(fps_row, textvariable=self.fps_var, width=6,
                                 values=[15, 24, 30, 60])
        fps_combo.pack(side="left", padx=5)
        
        # Audio
        audio_row = ttk.Frame(capture_card)
        audio_row.pack(fill="x", pady=5)
        
        self.record_audio = tk.BooleanVar(value=False)
        ttk.Checkbutton(audio_row, text="Record audio (system + mic)",
                        variable=self.record_audio).pack(anchor="w")
        
        # === Encoding Settings ===
        encode_card = create_card(main_frame, "⚙️ Encoding")
        encode_card.pack(fill="x", pady=(0, 10))
        
        # Codec
        codec_row = ttk.Frame(encode_card)
        codec_row.pack(fill="x", pady=5)
        
        ttk.Label(codec_row, text="Codec:").pack(side="left")
        self.codec_var = tk.StringVar(value="libx264")
        codec_combo = ttk.Combobox(codec_row, textvariable=self.codec_var, width=12,
                                   values=["libx264", "h264_nvenc", "h264_qsv"])
        codec_combo.pack(side="left", padx=5)
        
        # Quality
        crf_row = ttk.Frame(encode_card)
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
        
        # === Recording Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.start_btn = ttk.Button(btn_frame, text="⏺️ Start Recording", command=self.start_recording)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="Ready", foreground="gray")
        self.status_label.pack(side="left", padx=20)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("MKV files", "*.mkv"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def build_command(self) -> list:
        output_path = self.output_entry.get()
        if not output_path:
            return None
        
        resolution = self.resolution_var.get()
        fps = self.fps_var.get()
        codec = self.codec_var.get()
        crf = self.crf_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        # Windows screen capture using gdigrab
        if sys.platform == "win32":
            cmd.extend(["-f", "gdigrab"])
            cmd.extend(["-framerate", str(fps)])
            cmd.extend(["-video_size", resolution])
            cmd.extend(["-i", self.source_var.get()])
            
            if self.record_audio.get():
                # Add audio capture (requires dshow device)
                cmd.extend(["-f", "dshow"])
                cmd.extend(["-i", "audio=virtual-audio-capturer"])
        else:
            # Linux/Mac (x11grab)
            cmd.extend(["-f", "x11grab"])
            cmd.extend(["-framerate", str(fps)])
            cmd.extend(["-video_size", resolution])
            cmd.extend(["-i", ":0.0"])
        
        cmd.extend(["-c:v", codec])
        if codec == "libx264":
            cmd.extend(["-crf", str(crf)])
            cmd.extend(["-preset", "ultrafast"])
        
        if self.record_audio.get():
            cmd.extend(["-c:a", "aac"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Output", "Please specify output file.")
    

    
    def start_recording(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Output", "Please specify output file.")
            return
        
        self.is_recording = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="🔴 Recording...", foreground="red")
        
        self.set_preview(cmd)
        self.run_command(cmd, None)
    
    def stop_recording(self):
        self.is_recording = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Stopping...", foreground="orange")
        
        # Send 'q' to stop gracefully (needs newline sometimes)
        self.send_command_input("q\n")
        
        # Monitor and force stop if needed
        self.check_stop_status(0)
    
    def check_stop_status(self, attempt):
        if not self.runner.is_running():
            self.status_label.configure(text="Stopped", foreground="gray")
            return

        if attempt < 30:  # Wait up to 3 seconds (30 * 100ms)
            self.root.after(100, lambda: self.check_stop_status(attempt + 1))
        else:
            # Force kill if still running
            self.status_label.configure(text="Force Stopping...", foreground="red")
            self.stop_command()
            self.root.after(1000, lambda: self.status_label.configure(text="Stopped (Forced)", foreground="gray"))



if __name__ == "__main__":
    app = RecorderApp()
    app.run()
