"""
FFmpeg Crop Tool
Crop video to specific region
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, get_media_info, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class CropApp(FFmpegToolApp):
    """Video cropping tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Crop", width=600, height=580)
        self.input_width = 0
        self.input_height = 0
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
        
        self.info_label = ttk.Label(input_card, text="Resolution: -- | Duration: --:--:--")
        self.info_label.pack(anchor="w", pady=(5, 0))
        
        # === Crop Settings ===
        crop_card = create_card(main_frame, "✂️ Crop Region")
        crop_card.pack(fill="x", pady=(0, 10))
        
        # Output dimensions
        dim_row = ttk.Frame(crop_card)
        dim_row.pack(fill="x", pady=5)
        
        ttk.Label(dim_row, text="Output Width:").pack(side="left")
        self.width_entry = ttk.Entry(dim_row, width=8)
        self.width_entry.insert(0, "1280")
        self.width_entry.pack(side="left", padx=5)
        
        ttk.Label(dim_row, text="Height:").pack(side="left", padx=(20, 0))
        self.height_entry = ttk.Entry(dim_row, width=8)
        self.height_entry.insert(0, "720")
        self.height_entry.pack(side="left", padx=5)
        
        # Position
        pos_row = ttk.Frame(crop_card)
        pos_row.pack(fill="x", pady=5)
        
        ttk.Label(pos_row, text="X offset:").pack(side="left")
        self.x_entry = ttk.Entry(pos_row, width=8)
        self.x_entry.insert(0, "0")
        self.x_entry.pack(side="left", padx=5)
        
        ttk.Label(pos_row, text="Y offset:").pack(side="left", padx=(20, 0))
        self.y_entry = ttk.Entry(pos_row, width=8)
        self.y_entry.insert(0, "0")
        self.y_entry.pack(side="left", padx=5)
        
        # Preset buttons
        preset_row = ttk.Frame(crop_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        presets = [
            ("Center", "center"),
            ("16:9", "16:9"),
            ("4:3", "4:3"),
            ("1:1 (Square)", "1:1"),
            ("9:16 (Vertical)", "9:16")
        ]
        for name, value in presets:
            btn = ttk.Button(preset_row, text=name, width=10,
                           command=lambda v=value: self._apply_preset(v))
            btn.pack(side="left", padx=2)
        
        # Center crop option
        self.center_crop = tk.BooleanVar(value=True)
        ttk.Checkbutton(crop_card, text="Center crop (auto-calculate X/Y)",
                        variable=self.center_crop).pack(anchor="w", pady=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="✂️ Crop", command=self.run_crop)
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
            res_str = "--"
            
            if info and "streams" in info:
                for stream in info["streams"]:
                    if stream.get("codec_type") == "video":
                        self.input_width = stream.get("width", 0)
                        self.input_height = stream.get("height", 0)
                        res_str = f"{self.input_width}x{self.input_height}"
                        break
            
            self.info_label.configure(text=f"Resolution: {res_str} | Duration: {dur_str}")
            
            output_path = generate_output_path(input_path, "_cropped")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _apply_preset(self, preset):
        if not self.input_width or not self.input_height:
            messagebox.showinfo("Info", "Please load a video first.")
            return
        
        if preset == "center":
            # Keep current size, just center
            pass
        elif preset == "16:9":
            if self.input_width / self.input_height > 16/9:
                # Video is wider
                new_h = self.input_height
                new_w = int(new_h * 16 / 9)
            else:
                new_w = self.input_width
                new_h = int(new_w * 9 / 16)
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(new_w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(new_h))
        elif preset == "4:3":
            if self.input_width / self.input_height > 4/3:
                new_h = self.input_height
                new_w = int(new_h * 4 / 3)
            else:
                new_w = self.input_width
                new_h = int(new_w * 3 / 4)
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(new_w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(new_h))
        elif preset == "1:1":
            size = min(self.input_width, self.input_height)
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(size))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(size))
        elif preset == "9:16":
            if self.input_height / self.input_width > 16/9:
                new_w = self.input_width
                new_h = int(new_w * 16 / 9)
            else:
                new_h = self.input_height
                new_w = int(new_h * 9 / 16)
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(new_w))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(new_h))
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        w = self.width_entry.get().strip()
        h = self.height_entry.get().strip()
        
        if self.center_crop.get() and self.input_width and self.input_height:
            x = f"(in_w-{w})/2"
            y = f"(in_h-{h})/2"
        else:
            x = self.x_entry.get().strip()
            y = self.y_entry.get().strip()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        crop_filter = f"crop={w}:{h}:{x}:{y}"
        cmd.extend(["-vf", crop_filter])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_crop(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = CropApp()
    app.run()
