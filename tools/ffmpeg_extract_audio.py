"""
FFmpeg Extract Audio Tool
Extract audio track from video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class ExtractAudioApp(FFmpegToolApp):
    """Audio extraction tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Extract Audio", width=600, height=520)
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
        
        # === Audio Options ===
        options_card = create_card(main_frame, "🎵 Audio Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Format
        format_row = ttk.Frame(options_card)
        format_row.pack(fill="x", pady=5)
        
        ttk.Label(format_row, text="Format:").pack(side="left")
        self.format_var = tk.StringVar(value="mp3")
        format_combo = ttk.Combobox(format_row, textvariable=self.format_var, width=10,
                                    values=["mp3", "aac", "wav", "flac", "ogg", "m4a"])
        format_combo.pack(side="left", padx=5)
        format_combo.bind("<<ComboboxSelected>>", self._on_format_change)
        
        # Bitrate
        bitrate_row = ttk.Frame(options_card)
        bitrate_row.pack(fill="x", pady=5)
        
        ttk.Label(bitrate_row, text="Bitrate:").pack(side="left")
        self.bitrate_var = tk.StringVar(value="192k")
        bitrate_combo = ttk.Combobox(bitrate_row, textvariable=self.bitrate_var, width=10,
                                     values=["64k", "96k", "128k", "192k", "256k", "320k"])
        bitrate_combo.pack(side="left", padx=5)
        
        # Sample rate
        sample_row = ttk.Frame(options_card)
        sample_row.pack(fill="x", pady=5)
        
        ttk.Label(sample_row, text="Sample Rate:").pack(side="left")
        self.sample_var = tk.StringVar(value="original")
        sample_combo = ttk.Combobox(sample_row, textvariable=self.sample_var, width=10,
                                    values=["original", "44100", "48000", "96000"])
        sample_combo.pack(side="left", padx=5)
        
        # Channels
        channel_row = ttk.Frame(options_card)
        channel_row.pack(fill="x", pady=5)
        
        ttk.Label(channel_row, text="Channels:").pack(side="left")
        self.channel_var = tk.StringVar(value="original")
        channel_combo = ttk.Combobox(channel_row, textvariable=self.channel_var, width=10,
                                     values=["original", "mono", "stereo"])
        channel_combo.pack(side="left", padx=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="🎵 Extract", command=self.run_extract)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            ext = "." + self.format_var.get()
            output_path = generate_output_path(input_path, "", ext)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        ext = self.format_var.get()
        filetypes = [(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, f".{ext}")
    
    def _on_format_change(self, event=None):
        input_path = self.input_entry.get()
        if input_path:
            ext = "." + self.format_var.get()
            output_path = generate_output_path(input_path, "", ext)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        fmt = self.format_var.get()
        bitrate = self.bitrate_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        cmd.extend(["-vn"])  # No video
        
        # Codec based on format
        codecs = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "m4a": "aac",
            "ogg": "libvorbis",
            "flac": "flac",
            "wav": "pcm_s16le"
        }
        codec = codecs.get(fmt, "copy")
        cmd.extend(["-c:a", codec])
        
        # Bitrate (not for lossless)
        if fmt not in ["wav", "flac"]:
            cmd.extend(["-b:a", bitrate])
        
        # Sample rate
        if self.sample_var.get() != "original":
            cmd.extend(["-ar", self.sample_var.get()])
        
        # Channels
        if self.channel_var.get() == "mono":
            cmd.extend(["-ac", "1"])
        elif self.channel_var.get() == "stereo":
            cmd.extend(["-ac", "2"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_extract(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ExtractAudioApp()
    app.run()
