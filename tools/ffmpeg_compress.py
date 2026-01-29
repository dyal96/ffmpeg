"""
FFmpeg Compress Tool
Compress video files with quality control
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class CompressApp(FFmpegToolApp):
    """Video compression tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Compress", width=650, height=600)
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
        
        self.info_label = ttk.Label(input_card, text="Duration: --:--:-- | Size: --")
        self.info_label.pack(anchor="w", pady=(5, 0))
        
        # === Compression Options ===
        options_card = create_card(main_frame, "🗜️ Compression Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Mode selection
        mode_row = ttk.Frame(options_card)
        mode_row.pack(fill="x", pady=5)
        
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.mode_var = tk.StringVar(value="crf")
        ttk.Radiobutton(mode_row, text="Quality (CRF)", variable=self.mode_var, 
                        value="crf", command=self._on_mode_changed).pack(side="left", padx=10)
        ttk.Radiobutton(mode_row, text="Target Size", variable=self.mode_var, 
                        value="size", command=self._on_mode_changed).pack(side="left", padx=10)
        
        # CRF slider
        self.crf_frame = ttk.Frame(options_card)
        self.crf_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.crf_frame, text="Quality (CRF):").pack(side="left")
        self.crf_var = tk.IntVar(value=28)
        self.crf_scale = ttk.Scale(self.crf_frame, from_=18, to=40, variable=self.crf_var,
                                   orient="horizontal", length=200, command=self._update_crf_label)
        self.crf_scale.pack(side="left", padx=5)
        self.crf_label = ttk.Label(self.crf_frame, text="28 (Good)")
        self.crf_label.pack(side="left")
        
        # Target size
        self.size_frame = ttk.Frame(options_card)
        
        ttk.Label(self.size_frame, text="Target Size (MB):").pack(side="left")
        self.size_entry = ttk.Entry(self.size_frame, width=10)
        self.size_entry.insert(0, "50")
        self.size_entry.pack(side="left", padx=5)
        
        # Codec selection
        codec_row = ttk.Frame(options_card)
        codec_row.pack(fill="x", pady=5)
        
        ttk.Label(codec_row, text="Codec:").pack(side="left")
        self.codec_var = tk.StringVar(value="libx264")
        codec_combo = ttk.Combobox(codec_row, textvariable=self.codec_var, width=15,
                                   values=["libx264", "libx265", "h264_nvenc", "hevc_nvenc"])
        codec_combo.pack(side="left", padx=5)
        
        # Preset
        preset_row = ttk.Frame(options_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Preset:").pack(side="left")
        self.preset_var = tk.StringVar(value="medium")
        preset_combo = ttk.Combobox(preset_row, textvariable=self.preset_var, width=12,
                                    values=["ultrafast", "superfast", "veryfast", "faster",
                                            "fast", "medium", "slow", "slower", "veryslow"])
        preset_combo.pack(side="left", padx=5)
        ttk.Label(preset_row, text="(slower = better quality at same size)", 
                  foreground="gray").pack(side="left", padx=10)
        
        # Audio options
        audio_row = ttk.Frame(options_card)
        audio_row.pack(fill="x", pady=5)
        
        ttk.Label(audio_row, text="Audio:").pack(side="left")
        self.audio_var = tk.StringVar(value="128k")
        audio_combo = ttk.Combobox(audio_row, textvariable=self.audio_var, width=10,
                                   values=["copy", "64k", "96k", "128k", "192k", "256k"])
        audio_combo.pack(side="left", padx=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="🗜️ Compress", command=self.run_compress)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            # Get duration and file size
            duration = get_media_duration(input_path)
            try:
                size_mb = Path(input_path).stat().st_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            except:
                size_str = "--"
            
            dur_str = format_duration(duration) if duration else "--:--:--"
            self.info_label.configure(text=f"Duration: {dur_str} | Size: {size_str}")
            
            # Auto-generate output
            output_path = generate_output_path(input_path, "_compressed")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _on_mode_changed(self):
        if self.mode_var.get() == "crf":
            self.crf_frame.pack(fill="x", pady=5, after=self.crf_frame.master.winfo_children()[1])
            self.size_frame.pack_forget()
        else:
            self.size_frame.pack(fill="x", pady=5, after=self.crf_frame.master.winfo_children()[1])
            self.crf_frame.pack_forget()
    
    def _update_crf_label(self, value):
        crf = int(float(value))
        quality_map = {
            (18, 22): "Excellent",
            (23, 27): "Good",
            (28, 32): "Medium",
            (33, 40): "Low"
        }
        quality = "Medium"
        for (low, high), label in quality_map.items():
            if low <= crf <= high:
                quality = label
                break
        self.crf_label.configure(text=f"{crf} ({quality})")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        codec = self.codec_var.get()
        preset = self.preset_var.get()
        
        cmd.extend(["-c:v", codec])
        
        if self.mode_var.get() == "crf":
            cmd.extend(["-crf", str(self.crf_var.get())])
        else:
            # Target size mode - calculate bitrate
            try:
                target_mb = float(self.size_entry.get())
                duration = get_media_duration(input_path)
                if duration:
                    # Calculate video bitrate (kbps), reserve ~128k for audio
                    audio_kbps = 128
                    target_kbps = (target_mb * 8 * 1024) / duration
                    video_kbps = max(100, int(target_kbps - audio_kbps))
                    cmd.extend(["-b:v", f"{video_kbps}k"])
            except:
                cmd.extend(["-crf", "28"])  # Fallback
        
        # Only add preset for x264/x265
        if codec in ["libx264", "libx265"]:
            cmd.extend(["-preset", preset])
        
        # Audio
        audio = self.audio_var.get()
        if audio == "copy":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", audio])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_compress(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = CompressApp()
    app.run()
