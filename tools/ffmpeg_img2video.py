"""
FFmpeg Image to Video Tool
Convert a single image or sequence of images to video
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_folder, browse_save_file,
    generate_output_path, get_binary, get_theme
)

class ImageToVideoTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Image to Video", 650, 550)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Mode Selection
        mode_card = create_card(self.root, "📷 Mode")
        mode_card.pack(fill="x", padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_card, text="Single Image → Video", 
                        variable=self.mode_var, value="single",
                        command=self._on_mode_change).pack(side="left", padx=10)
        ttk.Radiobutton(mode_card, text="Image Sequence → Video", 
                        variable=self.mode_var, value="sequence",
                        command=self._on_mode_change).pack(side="left", padx=10)
        
        # Single Image Input
        self.single_card = create_card(self.root, "🖼️ Input Image")
        self.single_card.pack(fill="x", padx=10, pady=5)
        
        single_row = ttk.Frame(self.single_card)
        single_row.pack(fill="x", pady=5)
        
        self.single_entry = ttk.Entry(single_row)
        self.single_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(single_row, text="Browse", 
                   command=lambda: browse_file(self.single_entry, 
                   [("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"), ("All", "*.*")])).pack(side="left")
        
        # Duration for single image
        dur_row = ttk.Frame(self.single_card)
        dur_row.pack(fill="x", pady=5)
        
        ttk.Label(dur_row, text="Duration (seconds):").pack(side="left")
        self.duration_spin = ttk.Spinbox(dur_row, from_=1, to=3600, width=8)
        self.duration_spin.set(10)
        self.duration_spin.pack(side="left", padx=5)
        
        # Sequence Input (hidden by default)
        self.seq_card = create_card(self.root, "📁 Image Sequence Folder")
        
        seq_row = ttk.Frame(self.seq_card)
        seq_row.pack(fill="x", pady=5)
        
        self.seq_entry = ttk.Entry(seq_row)
        self.seq_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(seq_row, text="Browse", command=lambda: browse_folder(self.seq_entry)).pack(side="left")
        
        seq_opt = ttk.Frame(self.seq_card)
        seq_opt.pack(fill="x", pady=5)
        
        ttk.Label(seq_opt, text="Pattern (e.g. img_%04d.png):").pack(side="left")
        self.pattern_entry = ttk.Entry(seq_opt, width=20)
        self.pattern_entry.insert(0, "img_%04d.png")
        self.pattern_entry.pack(side="left", padx=5)
        
        # Video Settings
        settings_card = create_card(self.root, "🎬 Video Settings")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(settings_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="FPS:").pack(side="left")
        self.fps_spin = ttk.Spinbox(row1, from_=1, to=120, width=5)
        self.fps_spin.set(30)
        self.fps_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Resolution (WxH):").pack(side="left", padx=(15, 0))
        self.width_spin = ttk.Spinbox(row1, from_=100, to=7680, width=6)
        self.width_spin.set(1920)
        self.width_spin.pack(side="left", padx=2)
        ttk.Label(row1, text="x").pack(side="left")
        self.height_spin = ttk.Spinbox(row1, from_=100, to=4320, width=6)
        self.height_spin.set(1080)
        self.height_spin.pack(side="left", padx=2)
        
        # Output
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(out_row, text="Browse", command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Create Video", command=self.run_create)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def _on_mode_change(self):
        if self.mode_var.get() == "single":
            self.seq_card.pack_forget()
            self.single_card.pack(fill="x", padx=10, pady=5, before=self.root.winfo_children()[2])
        else:
            self.single_card.pack_forget()
            self.seq_card.pack(fill="x", padx=10, pady=5, before=self.root.winfo_children()[2])
    
    def run_create(self):
        mode = self.mode_var.get()
        output_file = self.out_entry.get()
        fps = int(self.fps_spin.get())
        w = int(self.width_spin.get())
        h = int(self.height_spin.get())
        
        if mode == "single":
            input_file = self.single_entry.get()
            if not input_file:
                tk.messagebox.showerror("Error", "Please select an input image.")
                return
            
            if not output_file:
                output_file = generate_output_path(input_file, "_video", ".mp4")
                self.out_entry.delete(0, tk.END)
                self.out_entry.insert(0, output_file)
            
            duration = int(self.duration_spin.get())
            
            cmd = [
                get_binary("ffmpeg"), "-y",
                "-loop", "1", "-i", input_file,
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-t", str(duration), "-pix_fmt", "yuv420p",
                "-r", str(fps),
                output_file
            ]
        else:
            seq_folder = self.seq_entry.get()
            pattern = self.pattern_entry.get()
            
            if not seq_folder:
                tk.messagebox.showerror("Error", "Please select a sequence folder.")
                return
            
            if not output_file:
                output_file = str(Path(seq_folder).parent / "sequence_video.mp4")
                self.out_entry.delete(0, tk.END)
                self.out_entry.insert(0, output_file)
            
            input_pattern = str(Path(seq_folder) / pattern)
            
            cmd = [
                get_binary("ffmpeg"), "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                output_file
            ]
        
        self.set_preview(cmd)
        self.run_command(cmd)

if __name__ == "__main__":
    app = ImageToVideoTool()
    app.run()
