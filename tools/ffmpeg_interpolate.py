"""
FFmpeg Interpolate Tool
Frame interpolation for slow motion or smooth playback
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, get_media_info, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class InterpolateApp(FFmpegToolApp):
    """Frame interpolation tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Frame Interpolation", width=600, height=550)
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
        
        self.info_label = ttk.Label(input_card, text="FPS: -- | Duration: --:--:--")
        self.info_label.pack(anchor="w", pady=(5, 0))
        
        # === Interpolation Settings ===
        interp_card = create_card(main_frame, "🎞️ Interpolation Settings")
        interp_card.pack(fill="x", pady=(0, 10))
        
        # Target FPS
        fps_row = ttk.Frame(interp_card)
        fps_row.pack(fill="x", pady=5)
        
        ttk.Label(fps_row, text="Target FPS:").pack(side="left")
        self.target_fps = tk.IntVar(value=60)
        fps_combo = ttk.Combobox(fps_row, textvariable=self.target_fps, width=8,
                                 values=[30, 48, 60, 120, 144, 240])
        fps_combo.pack(side="left", padx=5)
        
        # Mode
        mode_row = ttk.Frame(interp_card)
        mode_row.pack(fill="x", pady=5)
        
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.mode_var = tk.StringVar(value="mci")
        mode_combo = ttk.Combobox(mode_row, textvariable=self.mode_var, width=10,
                                  values=["blend", "mci", "dup"])
        mode_combo.pack(side="left", padx=5)
        
        ttk.Label(interp_card, text="• blend: Mix adjacent frames\n"
                                     "• mci: Motion compensated (best quality, slowest)\n"
                                     "• dup: Duplicate frames (fastest)",
                  foreground="gray").pack(anchor="w")
        
        # MCI settings
        mci_row = ttk.Frame(interp_card)
        mci_row.pack(fill="x", pady=5)
        
        ttk.Label(mci_row, text="Motion estimation:").pack(side="left")
        self.me_var = tk.StringVar(value="hexbs")
        me_combo = ttk.Combobox(mci_row, textvariable=self.me_var, width=10,
                                values=["bidir", "bilat", "hexbs"])
        me_combo.pack(side="left", padx=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="🎞️ Interpolate", command=self.run_interpolate)
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
            info = get_media_info(input_path)
            
            dur_str = format_duration(duration) if duration else "--:--:--"
            fps_str = "--"
            
            if info and "streams" in info:
                for stream in info["streams"]:
                    if stream.get("codec_type") == "video":
                        r_fps = stream.get("r_frame_rate", "0/1")
                        try:
                            num, den = map(int, r_fps.split("/"))
                            if den > 0:
                                fps_str = f"{num/den:.2f}"
                        except:
                            pass
                        break
            
            self.info_label.configure(text=f"FPS: {fps_str} | Duration: {dur_str}")
            
            output_path = generate_output_path(input_path, "_interpolated")
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
        
        target_fps = self.target_fps.get()
        mode = self.mode_var.get()
        me = self.me_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if mode == "mci":
            vf = f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode={me}"
        else:
            vf = f"minterpolate=fps={target_fps}:mi_mode={mode}"
        
        cmd.extend(["-vf", vf])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_interpolate(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = InterpolateApp()
    app.run()
