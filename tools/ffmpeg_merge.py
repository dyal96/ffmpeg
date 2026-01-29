"""
FFmpeg Merge Tool
Merge/combine audio and video streams
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class MergeApp(FFmpegToolApp):
    """Audio/Video merging tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Merge Audio+Video", width=600, height=550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Video Input ===
        video_card = create_card(main_frame, "🎬 Video Input")
        video_card.pack(fill="x", pady=(0, 10))
        
        video_row = ttk.Frame(video_card)
        video_row.pack(fill="x")
        
        ttk.Label(video_row, text="Video File:").pack(side="left")
        self.video_entry = ttk.Entry(video_row, width=50)
        self.video_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(video_row, text="Browse", command=self._browse_video).pack(side="left")
        
        self.video_info = ttk.Label(video_card, text="Duration: --:--:--")
        self.video_info.pack(anchor="w", pady=(5, 0))
        
        # === Audio Input ===
        audio_card = create_card(main_frame, "🎵 Audio Input")
        audio_card.pack(fill="x", pady=(0, 10))
        
        audio_row = ttk.Frame(audio_card)
        audio_row.pack(fill="x")
        
        ttk.Label(audio_row, text="Audio File:").pack(side="left")
        self.audio_entry = ttk.Entry(audio_row, width=50)
        self.audio_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(audio_row, text="Browse", command=self._browse_audio).pack(side="left")
        
        self.audio_info = ttk.Label(audio_card, text="Duration: --:--:--")
        self.audio_info.pack(anchor="w", pady=(5, 0))
        
        # === Merge Options ===
        options_card = create_card(main_frame, "⚙️ Merge Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Copy mode
        copy_row = ttk.Frame(options_card)
        copy_row.pack(fill="x", pady=5)
        
        self.copy_streams = tk.BooleanVar(value=True)
        ttk.Checkbutton(copy_row, text="Copy streams (fast, no re-encoding)",
                        variable=self.copy_streams).pack(anchor="w")
        
        # Shortest option
        shortest_row = ttk.Frame(options_card)
        shortest_row.pack(fill="x", pady=5)
        
        self.use_shortest = tk.BooleanVar(value=True)
        ttk.Checkbutton(shortest_row, text="End output at shortest stream",
                        variable=self.use_shortest).pack(anchor="w")
        
        # Volume adjustment
        vol_row = ttk.Frame(options_card)
        vol_row.pack(fill="x", pady=5)
        
        ttk.Label(vol_row, text="Audio Volume:").pack(side="left")
        self.volume_var = tk.DoubleVar(value=1.0)
        vol_scale = ttk.Scale(vol_row, from_=0.0, to=2.0, variable=self.volume_var,
                              orient="horizontal", length=150, command=self._update_vol_label)
        vol_scale.pack(side="left", padx=5)
        self.vol_label = ttk.Label(vol_row, text="100%")
        self.vol_label.pack(side="left")
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔗 Merge", command=self.run_merge)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_video(self):
        filetypes = [
            ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            ("All files", "*.*")
        ]
        browse_file(self.video_entry, filetypes)
        
        video_path = self.video_entry.get()
        if video_path:
            duration = get_media_duration(video_path)
            if duration:
                self.video_info.configure(text=f"Duration: {format_duration(duration)}")
            
            # Auto-generate output
            output_path = generate_output_path(video_path, "_merged")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_audio(self):
        filetypes = [
            ("Audio files", "*.mp3 *.aac *.wav *.flac *.ogg *.m4a"),
            ("All files", "*.*")
        ]
        browse_file(self.audio_entry, filetypes)
        
        audio_path = self.audio_entry.get()
        if audio_path:
            duration = get_media_duration(audio_path)
            if duration:
                self.audio_info.configure(text=f"Duration: {format_duration(duration)}")
    
    def _browse_output(self):
        video_path = self.video_entry.get()
        ext = Path(video_path).suffix if video_path else ".mp4"
        filetypes = [("Video files", f"*{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ext)
    
    def _update_vol_label(self, value):
        vol = float(value)
        self.vol_label.configure(text=f"{int(vol * 100)}%")
    
    def build_command(self) -> list:
        video_path = self.video_entry.get()
        audio_path = self.audio_entry.get()
        output_path = self.output_entry.get()
        
        if not video_path or not audio_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y"]
        cmd.extend(["-i", video_path])
        cmd.extend(["-i", audio_path])
        
        # Map streams: video from first input, audio from second
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0"])
        
        # Copy or re-encode
        if self.copy_streams.get():
            cmd.extend(["-c:v", "copy"])
            # Volume adjustment requires re-encoding audio
            vol = self.volume_var.get()
            if abs(vol - 1.0) > 0.01:
                cmd.extend(["-c:a", "aac", "-af", f"volume={vol}"])
            else:
                cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23"])
            vol = self.volume_var.get()
            cmd.extend(["-c:a", "aac", "-af", f"volume={vol}"])
        
        if self.use_shortest.get():
            cmd.append("-shortest")
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select video, audio, and output files.")
    
    def run_merge(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select video, audio, and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.video_entry.get())


if __name__ == "__main__":
    app = MergeApp()
    app.run()
