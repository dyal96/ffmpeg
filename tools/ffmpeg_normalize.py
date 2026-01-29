"""
FFmpeg Normalize Tool
Audio normalization (loudness, peak normalize)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class NormalizeApp(FFmpegToolApp):
    """Audio normalization tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Normalize Audio", width=600, height=550)
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
        
        # === Normalization Options ===
        options_card = create_card(main_frame, "🔊 Normalization Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Mode selection
        mode_row = ttk.Frame(options_card)
        mode_row.pack(fill="x", pady=5)
        
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.mode_var = tk.StringVar(value="loudnorm")
        ttk.Radiobutton(mode_row, text="Loudness (EBU R128)", variable=self.mode_var,
                        value="loudnorm").pack(side="left", padx=10)
        ttk.Radiobutton(mode_row, text="Peak Normalize", variable=self.mode_var,
                        value="peak").pack(side="left", padx=10)
        ttk.Radiobutton(mode_row, text="Volume Adjust", variable=self.mode_var,
                        value="volume").pack(side="left", padx=10)
        
        # Target loudness (for loudnorm)
        loud_row = ttk.Frame(options_card)
        loud_row.pack(fill="x", pady=5)
        
        ttk.Label(loud_row, text="Target Loudness (LUFS):").pack(side="left")
        self.lufs_var = tk.DoubleVar(value=-16)
        lufs_spin = ttk.Spinbox(loud_row, from_=-30, to=-5, width=6, textvariable=self.lufs_var)
        lufs_spin.pack(side="left", padx=5)
        ttk.Label(loud_row, text="(-16 = YouTube, -14 = Spotify)", foreground="gray").pack(side="left")
        
        # True peak
        tp_row = ttk.Frame(options_card)
        tp_row.pack(fill="x", pady=5)
        
        ttk.Label(tp_row, text="True Peak (dB):").pack(side="left")
        self.tp_var = tk.DoubleVar(value=-1.5)
        tp_spin = ttk.Spinbox(tp_row, from_=-6, to=0, increment=0.5, width=6, textvariable=self.tp_var)
        tp_spin.pack(side="left", padx=5)
        
        # Volume adjustment
        vol_row = ttk.Frame(options_card)
        vol_row.pack(fill="x", pady=5)
        
        ttk.Label(vol_row, text="Volume (dB):").pack(side="left")
        self.volume_var = tk.DoubleVar(value=0)
        vol_scale = ttk.Scale(vol_row, from_=-20, to=20, variable=self.volume_var,
                              orient="horizontal", length=150)
        vol_scale.pack(side="left", padx=5)
        self.vol_label = ttk.Label(vol_row, text="0 dB")
        self.vol_label.pack(side="left")
        vol_scale.configure(command=lambda v: self.vol_label.configure(text=f"{float(v):.1f} dB"))
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔊 Normalize", command=self.run_normalize)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Media files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.flac *.aac"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "_normalized")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        input_path = self.input_entry.get()
        ext = Path(input_path).suffix if input_path else ".mp4"
        filetypes = [("Media files", f"*{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ext)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        mode = self.mode_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if mode == "loudnorm":
            lufs = self.lufs_var.get()
            tp = self.tp_var.get()
            af = f"loudnorm=I={lufs}:TP={tp}:LRA=11"
        elif mode == "peak":
            af = "acompressor"  # Simple peak limiting
        else:  # volume
            vol = self.volume_var.get()
            af = f"volume={vol}dB"
        
        cmd.extend(["-af", af])
        cmd.extend(["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_normalize(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = NormalizeApp()
    app.run()
