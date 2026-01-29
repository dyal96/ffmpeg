"""
FFmpeg Delogo Tool
Remove logos/watermarks from video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class DelogoApp(FFmpegToolApp):
    """Logo/watermark removal tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Delogo", width=600, height=560)
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
        
        # === Delogo Region ===
        region_card = create_card(main_frame, "🎯 Logo Region (pixels)")
        region_card.pack(fill="x", pady=(0, 10))
        
        # Position
        pos_row = ttk.Frame(region_card)
        pos_row.pack(fill="x", pady=5)
        
        ttk.Label(pos_row, text="X:").pack(side="left")
        self.x_entry = ttk.Entry(pos_row, width=8)
        self.x_entry.insert(0, "10")
        self.x_entry.pack(side="left", padx=5)
        
        ttk.Label(pos_row, text="Y:").pack(side="left", padx=(20, 0))
        self.y_entry = ttk.Entry(pos_row, width=8)
        self.y_entry.insert(0, "10")
        self.y_entry.pack(side="left", padx=5)
        
        # Size
        size_row = ttk.Frame(region_card)
        size_row.pack(fill="x", pady=5)
        
        ttk.Label(size_row, text="Width:").pack(side="left")
        self.w_entry = ttk.Entry(size_row, width=8)
        self.w_entry.insert(0, "100")
        self.w_entry.pack(side="left", padx=5)
        
        ttk.Label(size_row, text="Height:").pack(side="left", padx=(20, 0))
        self.h_entry = ttk.Entry(size_row, width=8)
        self.h_entry.insert(0, "50")
        self.h_entry.pack(side="left", padx=5)
        
        # Presets for common positions
        preset_row = ttk.Frame(region_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        presets = [
            ("Top-Left", 10, 10),
            ("Top-Right", -110, 10),
            ("Bottom-Left", 10, -60),
            ("Bottom-Right", -110, -60)
        ]
        for name, x, y in presets:
            btn = ttk.Button(preset_row, text=name, width=10,
                           command=lambda px=x, py=y: self._set_preset(px, py))
            btn.pack(side="left", padx=2)
        
        ttk.Label(region_card, text="💡 Tip: Use ffplay to find exact coordinates",
                  foreground="gray").pack(anchor="w", pady=(10, 0))
        
        # === Options ===
        options_card = create_card(main_frame, "⚙️ Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        self.show_region = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="Show region outline (for testing)",
                        variable=self.show_region).pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="🎯 Remove Logo", command=self.run_delogo)
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
            
            output_path = generate_output_path(input_path, "_delogo")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _set_preset(self, x, y):
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(x) if x >= 0 else f"iw{x}")
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(y) if y >= 0 else f"ih{y}")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        x = self.x_entry.get().strip()
        y = self.y_entry.get().strip()
        w = self.w_entry.get().strip()
        h = self.h_entry.get().strip()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if self.show_region.get():
            # Draw rectangle instead of delogo (for testing)
            vf = f"drawbox=x={x}:y={y}:w={w}:h={h}:c=red:t=2"
        else:
            vf = f"delogo=x={x}:y={y}:w={w}:h={h}"
        
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
    
    def run_delogo(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = DelogoApp()
    app.run()
