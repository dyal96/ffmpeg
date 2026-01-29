"""
FFmpeg Sharpen Tool
Apply video sharpening
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class SharpenApp(FFmpegToolApp):
    """Video sharpening tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Sharpen", width=600, height=520)
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
        
        # === Sharpen Settings ===
        sharpen_card = create_card(main_frame, "✨ Sharpen Settings")
        sharpen_card.pack(fill="x", pady=(0, 10))
        
        # Filter type
        filter_row = ttk.Frame(sharpen_card)
        filter_row.pack(fill="x", pady=5)
        
        ttk.Label(filter_row, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value="unsharp")
        filter_combo = ttk.Combobox(filter_row, textvariable=self.filter_var, width=15,
                                    values=["unsharp", "cas"])
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # Unsharp settings
        self.unsharp_frame = ttk.Frame(sharpen_card)
        self.unsharp_frame.pack(fill="x", pady=5)
        
        luma_row = ttk.Frame(self.unsharp_frame)
        luma_row.pack(fill="x", pady=2)
        
        ttk.Label(luma_row, text="Luma Amount:").pack(side="left")
        self.luma_amount = tk.DoubleVar(value=1.0)
        luma_scale = ttk.Scale(luma_row, from_=0, to=5, variable=self.luma_amount,
                               orient="horizontal", length=150)
        luma_scale.pack(side="left", padx=5)
        self.luma_label = ttk.Label(luma_row, text="1.0")
        self.luma_label.pack(side="left")
        luma_scale.configure(command=lambda v: self.luma_label.configure(text=f"{float(v):.1f}"))
        
        size_row = ttk.Frame(self.unsharp_frame)
        size_row.pack(fill="x", pady=2)
        
        ttk.Label(size_row, text="Matrix Size:").pack(side="left")
        self.matrix_size = tk.IntVar(value=5)
        size_combo = ttk.Combobox(size_row, textvariable=self.matrix_size, width=5,
                                  values=[3, 5, 7, 9, 11, 13])
        size_combo.pack(side="left", padx=5)
        ttk.Label(size_row, text="(odd values only)", foreground="gray").pack(side="left")
        
        # CAS (Contrast Adaptive Sharpening) settings
        self.cas_frame = ttk.Frame(sharpen_card)
        
        cas_row = ttk.Frame(self.cas_frame)
        cas_row.pack(fill="x")
        
        ttk.Label(cas_row, text="Sharpness:").pack(side="left")
        self.cas_strength = tk.DoubleVar(value=0.5)
        cas_scale = ttk.Scale(cas_row, from_=0, to=1, variable=self.cas_strength,
                              orient="horizontal", length=150)
        cas_scale.pack(side="left", padx=5)
        self.cas_label = ttk.Label(cas_row, text="0.5")
        self.cas_label.pack(side="left")
        cas_scale.configure(command=lambda v: self.cas_label.configure(text=f"{float(v):.2f}"))
        
        # Presets
        preset_row = ttk.Frame(sharpen_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        presets = [("Subtle", 0.5), ("Medium", 1.0), ("Strong", 2.0)]
        for name, value in presets:
            btn = ttk.Button(preset_row, text=name, width=8,
                           command=lambda v=value: self._apply_preset(v))
            btn.pack(side="left", padx=2)
        
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
        self.run_btn = ttk.Button(btn_frame, text="✨ Sharpen", command=self.run_sharpen)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_filter_change(self, event=None):
        if self.filter_var.get() == "unsharp":
            self.unsharp_frame.pack(fill="x", pady=5)
            self.cas_frame.pack_forget()
        else:
            self.cas_frame.pack(fill="x", pady=5)
            self.unsharp_frame.pack_forget()
    
    def _apply_preset(self, value):
        self.luma_amount.set(value)
        self.cas_strength.set(min(value / 2, 1.0))
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            output_path = generate_output_path(input_path, "_sharpened")
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
        
        if self.filter_var.get() == "unsharp":
            size = self.matrix_size.get()
            amount = self.luma_amount.get()
            vf = f"unsharp={size}:{size}:{amount}:{size}:{size}:{amount}"
        else:  # cas
            strength = self.cas_strength.get()
            vf = f"cas={strength}"
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
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
    
    def run_sharpen(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = SharpenApp()
    app.run()
