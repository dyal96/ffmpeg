"""
FFmpeg PiP Tool
Picture-in-Picture overlay
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class PipApp(FFmpegToolApp):
    """Picture-in-picture tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Picture-in-Picture", width=650, height=600)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Main Video ===
        main_card = create_card(main_frame, "🎬 Main Video (Background)")
        main_card.pack(fill="x", pady=(0, 10))
        
        main_row = ttk.Frame(main_card)
        main_row.pack(fill="x")
        
        ttk.Label(main_row, text="Main Video:").pack(side="left")
        self.main_entry = ttk.Entry(main_row, width=50)
        self.main_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(main_row, text="Browse", command=self._browse_main).pack(side="left")
        
        # === Overlay Video ===
        overlay_card = create_card(main_frame, "📺 Overlay Video (PiP)")
        overlay_card.pack(fill="x", pady=(0, 10))
        
        overlay_row = ttk.Frame(overlay_card)
        overlay_row.pack(fill="x")
        
        ttk.Label(overlay_row, text="Overlay Video:").pack(side="left")
        self.overlay_entry = ttk.Entry(overlay_row, width=50)
        self.overlay_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(overlay_row, text="Browse", command=self._browse_overlay).pack(side="left")
        
        # === PiP Settings ===
        pip_card = create_card(main_frame, "⚙️ PiP Settings")
        pip_card.pack(fill="x", pady=(0, 10))
        
        # Position presets
        pos_row = ttk.Frame(pip_card)
        pos_row.pack(fill="x", pady=5)
        
        ttk.Label(pos_row, text="Position:").pack(side="left")
        self.position_var = tk.StringVar(value="bottom-right")
        positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center", "custom"]
        pos_combo = ttk.Combobox(pos_row, textvariable=self.position_var, width=15, values=positions)
        pos_combo.pack(side="left", padx=5)
        pos_combo.bind("<<ComboboxSelected>>", self._on_position_change)
        
        # Custom position
        self.custom_frame = ttk.Frame(pip_card)
        
        custom_row = ttk.Frame(self.custom_frame)
        custom_row.pack(fill="x")
        
        ttk.Label(custom_row, text="X:").pack(side="left")
        self.x_entry = ttk.Entry(custom_row, width=8)
        self.x_entry.insert(0, "10")
        self.x_entry.pack(side="left", padx=5)
        
        ttk.Label(custom_row, text="Y:").pack(side="left", padx=(20, 0))
        self.y_entry = ttk.Entry(custom_row, width=8)
        self.y_entry.insert(0, "10")
        self.y_entry.pack(side="left", padx=5)
        
        # Scale
        scale_row = ttk.Frame(pip_card)
        scale_row.pack(fill="x", pady=5)
        
        ttk.Label(scale_row, text="PiP Scale:").pack(side="left")
        self.scale_var = tk.DoubleVar(value=0.25)
        scale_scale = ttk.Scale(scale_row, from_=0.1, to=0.5, variable=self.scale_var,
                                orient="horizontal", length=150)
        scale_scale.pack(side="left", padx=5)
        self.scale_label = ttk.Label(scale_row, text="25%")
        self.scale_label.pack(side="left")
        scale_scale.configure(command=lambda v: self.scale_label.configure(text=f"{int(float(v)*100)}%"))
        
        # Margin
        margin_row = ttk.Frame(pip_card)
        margin_row.pack(fill="x", pady=5)
        
        ttk.Label(margin_row, text="Margin:").pack(side="left")
        self.margin_var = tk.IntVar(value=20)
        margin_spin = ttk.Spinbox(margin_row, from_=0, to=100, width=6, textvariable=self.margin_var)
        margin_spin.pack(side="left", padx=5)
        ttk.Label(margin_row, text="px").pack(side="left")
        
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
        self.run_btn = ttk.Button(btn_frame, text="📺 Create PiP", command=self.run_pip)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_main(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.main_entry, filetypes)
        
        main_path = self.main_entry.get()
        if main_path:
            output_path = generate_output_path(main_path, "_pip")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_overlay(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.overlay_entry, filetypes)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _on_position_change(self, event=None):
        if self.position_var.get() == "custom":
            self.custom_frame.pack(fill="x", pady=5)
        else:
            self.custom_frame.pack_forget()
    
    def _get_overlay_position(self):
        pos = self.position_var.get()
        margin = self.margin_var.get()
        
        positions = {
            "top-left": (f"{margin}", f"{margin}"),
            "top-right": (f"main_w-overlay_w-{margin}", f"{margin}"),
            "bottom-left": (f"{margin}", f"main_h-overlay_h-{margin}"),
            "bottom-right": (f"main_w-overlay_w-{margin}", f"main_h-overlay_h-{margin}"),
            "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
            "custom": (self.x_entry.get(), self.y_entry.get())
        }
        return positions.get(pos, positions["bottom-right"])
    
    def build_command(self) -> list:
        main_path = self.main_entry.get()
        overlay_path = self.overlay_entry.get()
        output_path = self.output_entry.get()
        
        if not main_path or not overlay_path or not output_path:
            return None
        
        scale = self.scale_var.get()
        x, y = self._get_overlay_position()
        
        cmd = [get_binary("ffmpeg"), "-y"]
        cmd.extend(["-i", main_path])
        cmd.extend(["-i", overlay_path])
        
        # Scale overlay and position
        filter_complex = f"[1:v]scale=iw*{scale}:ih*{scale}[pip];[0:v][pip]overlay={x}:{y}"
        cmd.extend(["-filter_complex", filter_complex])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select all video files.")
    
    def run_pip(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select all video files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.main_entry.get())


if __name__ == "__main__":
    app = PipApp()
    app.run()
