"""
FFmpeg Bitrate Calculator Tool
Calculate optimal bitrate for target file size
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme, get_media_duration, get_media_info
)

class BitrateCalcTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Bitrate Calculator", 600, 550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input Video (optional)")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=self._browse_and_analyze).pack(side="left")
        
        self.info_label = ttk.Label(input_card, text="")
        self.info_label.pack(anchor="w", pady=2)
        
        # Calculator Section
        calc_card = create_card(self.root, "🧮 Calculator")
        calc_card.pack(fill="x", padx=10, pady=5)
        
        # Duration
        row1 = ttk.Frame(calc_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Duration (seconds):").pack(side="left")
        self.duration_spin = ttk.Spinbox(row1, from_=1, to=99999, width=10)
        self.duration_spin.set(60)
        self.duration_spin.pack(side="left", padx=5)
        
        # Target file size
        row2 = ttk.Frame(calc_card)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Target File Size:").pack(side="left")
        self.size_spin = ttk.Spinbox(row2, from_=1, to=99999, width=10)
        self.size_spin.set(100)
        self.size_spin.pack(side="left", padx=5)
        
        self.size_unit_var = tk.StringVar(value="MB")
        ttk.Combobox(row2, textvariable=self.size_unit_var, 
                     values=["KB", "MB", "GB"], width=5, state="readonly").pack(side="left", padx=5)
        
        # Audio bitrate
        row3 = ttk.Frame(calc_card)
        row3.pack(fill="x", pady=5)
        
        ttk.Label(row3, text="Audio Bitrate (kbps):").pack(side="left")
        self.audio_spin = ttk.Spinbox(row3, from_=0, to=512, width=8)
        self.audio_spin.set(128)
        self.audio_spin.pack(side="left", padx=5)
        
        # Calculate button
        ttk.Button(calc_card, text="📊 Calculate", command=self.calculate).pack(pady=10)
        
        # Results
        result_card = create_card(self.root, "📈 Results")
        result_card.pack(fill="x", padx=10, pady=5)
        
        self.result_text = tk.Text(result_card, height=8, state="disabled")
        self.result_text.pack(fill="x", pady=5)
        
        # Quick Encode
        encode_card = create_card(self.root, "🎬 Quick Encode")
        encode_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(encode_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(out_row, text="Browse", command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        self.run_btn = ttk.Button(encode_card, text="▶ Encode with Calculated Bitrate", command=self.run_encode)
        self.run_btn.pack(pady=5)
        
        self.calculated_video_bitrate = None
    
    def _browse_and_analyze(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.mkv;*.mov;*.avi"), ("All", "*.*")]
        )
        if filepath:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)
            
            # Get duration
            duration = get_media_duration(filepath)
            if duration:
                self.duration_spin.delete(0, tk.END)
                self.duration_spin.insert(0, int(duration))
                
                # Get current bitrate
                info = get_media_info(filepath)
                if info and "format" in info:
                    bitrate = int(info["format"].get("bit_rate", 0)) // 1000
                    size_mb = int(info["format"].get("size", 0)) / (1024 * 1024)
                    self.info_label.config(text=f"Current: {bitrate} kbps, {size_mb:.1f} MB, {duration:.1f}s")
    
    def calculate(self):
        duration = float(self.duration_spin.get())
        target_size = float(self.size_spin.get())
        size_unit = self.size_unit_var.get()
        audio_bitrate = float(self.audio_spin.get())
        
        # Convert to bits
        if size_unit == "KB":
            target_bits = target_size * 1024 * 8
        elif size_unit == "MB":
            target_bits = target_size * 1024 * 1024 * 8
        else:  # GB
            target_bits = target_size * 1024 * 1024 * 1024 * 8
        
        # Subtract audio
        audio_bits = audio_bitrate * 1000 * duration
        video_bits = target_bits - audio_bits
        
        if video_bits <= 0:
            self._show_result("Error: Target size too small for audio alone!")
            return
        
        video_bitrate_kbps = int(video_bits / duration / 1000)
        video_bitrate_mbps = video_bitrate_kbps / 1000
        
        self.calculated_video_bitrate = video_bitrate_kbps
        
        result = f"""Target: {target_size} {size_unit}
Duration: {duration:.1f} seconds
Audio Bitrate: {audio_bitrate:.0f} kbps

━━━ CALCULATED VIDEO BITRATE ━━━
{video_bitrate_kbps:,} kbps ({video_bitrate_mbps:.2f} Mbps)

FFmpeg command flags:
  -b:v {video_bitrate_kbps}k -b:a {int(audio_bitrate)}k

Two-pass encoding recommended for accuracy.
"""
        self._show_result(result)
    
    def _show_result(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")
    
    def run_encode(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        if not self.calculated_video_bitrate:
            tk.messagebox.showerror("Error", "Please calculate bitrate first.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_target")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        audio_bitrate = int(self.audio_spin.get())
        
        cmd = [
            get_binary("ffmpeg"), "-y", "-i", input_file,
            "-c:v", "libx264", "-b:v", f"{self.calculated_video_bitrate}k",
            "-c:a", "aac", "-b:a", f"{audio_bitrate}k",
            output_file
        ]
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)
    
    def create_bottom_section(self, parent):
        # Simplified - no log needed for calculator
        pass
    
    def set_preview(self, cmd):
        pass
    
    def run_command(self, cmd, input_file=None):
        import subprocess
        import os
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(cmd, creationflags=creationflags)
            tk.messagebox.showinfo("Complete", "Encoding finished!")
        except Exception as e:
            tk.messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = BitrateCalcTool()
    app.run()
