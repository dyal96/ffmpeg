"""
FFmpeg Watermark Tool
Add image/text watermark to video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class WatermarkApp(FFmpegToolApp):
    """Video watermarking tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Watermark", width=650, height=620)
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
        
        # === Watermark Type ===
        type_card = create_card(main_frame, "🎯 Watermark Type")
        type_card.pack(fill="x", pady=(0, 10))
        
        self.wm_type = tk.StringVar(value="image")
        ttk.Radiobutton(type_card, text="Image watermark", variable=self.wm_type,
                        value="image", command=self._on_type_change).pack(anchor="w")
        ttk.Radiobutton(type_card, text="Text watermark", variable=self.wm_type,
                        value="text", command=self._on_type_change).pack(anchor="w")
        
        # === Image Watermark ===
        self.img_card = create_card(main_frame, "🖼️ Image Watermark")
        self.img_card.pack(fill="x", pady=(0, 10))
        
        img_row = ttk.Frame(self.img_card)
        img_row.pack(fill="x")
        
        ttk.Label(img_row, text="Image:").pack(side="left")
        self.img_entry = ttk.Entry(img_row, width=50)
        self.img_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(img_row, text="Browse", command=self._browse_image).pack(side="left")
        
        # Scale
        scale_row = ttk.Frame(self.img_card)
        scale_row.pack(fill="x", pady=5)
        
        ttk.Label(scale_row, text="Scale:").pack(side="left")
        self.img_scale_var = tk.DoubleVar(value=0.15)
        scale_scale = ttk.Scale(scale_row, from_=0.05, to=0.5, variable=self.img_scale_var,
                                orient="horizontal", length=150)
        scale_scale.pack(side="left", padx=5)
        self.img_scale_label = ttk.Label(scale_row, text="15%")
        self.img_scale_label.pack(side="left")
        scale_scale.configure(command=lambda v: self.img_scale_label.configure(text=f"{int(float(v)*100)}%"))
        
        # === Text Watermark ===
        self.txt_card = create_card(main_frame, "📝 Text Watermark")
        
        text_row = ttk.Frame(self.txt_card)
        text_row.pack(fill="x", pady=5)
        
        ttk.Label(text_row, text="Text:").pack(side="left")
        self.text_entry = ttk.Entry(text_row, width=40)
        self.text_entry.insert(0, "© My Video")
        self.text_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        font_row = ttk.Frame(self.txt_card)
        font_row.pack(fill="x", pady=5)
        
        ttk.Label(font_row, text="Font Size:").pack(side="left")
        self.fontsize_var = tk.IntVar(value=24)
        fontsize_spin = ttk.Spinbox(font_row, from_=12, to=72, width=5, textvariable=self.fontsize_var)
        fontsize_spin.pack(side="left", padx=5)
        
        ttk.Label(font_row, text="Color:").pack(side="left", padx=(20, 0))
        self.fontcolor_var = tk.StringVar(value="white")
        color_combo = ttk.Combobox(font_row, textvariable=self.fontcolor_var, width=10,
                                   values=["white", "black", "red", "yellow", "blue"])
        color_combo.pack(side="left", padx=5)
        
        # === Position ===
        pos_card = create_card(main_frame, "📍 Position")
        pos_card.pack(fill="x", pady=(0, 10))
        
        pos_row = ttk.Frame(pos_card)
        pos_row.pack(fill="x")
        
        ttk.Label(pos_row, text="Position:").pack(side="left")
        self.position_var = tk.StringVar(value="bottom-right")
        positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
        pos_combo = ttk.Combobox(pos_row, textvariable=self.position_var, width=15, values=positions)
        pos_combo.pack(side="left", padx=5)
        
        margin_row = ttk.Frame(pos_card)
        margin_row.pack(fill="x", pady=5)
        
        ttk.Label(margin_row, text="Margin:").pack(side="left")
        self.margin_var = tk.IntVar(value=20)
        margin_spin = ttk.Spinbox(margin_row, from_=0, to=100, width=6, textvariable=self.margin_var)
        margin_spin.pack(side="left", padx=5)
        ttk.Label(margin_row, text="px").pack(side="left")
        
        # Opacity
        opacity_row = ttk.Frame(pos_card)
        opacity_row.pack(fill="x", pady=5)
        
        ttk.Label(opacity_row, text="Opacity:").pack(side="left")
        self.opacity_var = tk.DoubleVar(value=0.8)
        opacity_scale = ttk.Scale(opacity_row, from_=0.1, to=1.0, variable=self.opacity_var,
                                  orient="horizontal", length=150)
        opacity_scale.pack(side="left", padx=5)
        self.opacity_label = ttk.Label(opacity_row, text="80%")
        self.opacity_label.pack(side="left")
        opacity_scale.configure(command=lambda v: self.opacity_label.configure(text=f"{int(float(v)*100)}%"))
        
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
        self.run_btn = ttk.Button(btn_frame, text="💧 Add Watermark", command=self.run_watermark)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_type_change(self):
        if self.wm_type.get() == "image":
            self.img_card.pack(fill="x", pady=(0, 10), after=self.img_card.master.winfo_children()[1])
            self.txt_card.pack_forget()
        else:
            self.txt_card.pack(fill="x", pady=(0, 10), after=self.img_card.master.winfo_children()[1])
            self.img_card.pack_forget()
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            output_path = generate_output_path(input_path, "_watermarked")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")]
        browse_file(self.img_entry, filetypes)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _get_position(self, is_text=False):
        pos = self.position_var.get()
        margin = self.margin_var.get()
        
        if is_text:
            positions = {
                "top-left": (f"{margin}", f"{margin}"),
                "top-right": (f"w-tw-{margin}", f"{margin}"),
                "bottom-left": (f"{margin}", f"h-th-{margin}"),
                "bottom-right": (f"w-tw-{margin}", f"h-th-{margin}"),
                "center": ("(w-tw)/2", "(h-th)/2")
            }
        else:
            positions = {
                "top-left": (f"{margin}", f"{margin}"),
                "top-right": (f"main_w-overlay_w-{margin}", f"{margin}"),
                "bottom-left": (f"{margin}", f"main_h-overlay_h-{margin}"),
                "bottom-right": (f"main_w-overlay_w-{margin}", f"main_h-overlay_h-{margin}"),
                "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2")
            }
        return positions.get(pos, positions["bottom-right"])
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if self.wm_type.get() == "image":
            img_path = self.img_entry.get()
            if not img_path:
                return None
            
            cmd.extend(["-i", img_path])
            
            scale = self.img_scale_var.get()
            opacity = self.opacity_var.get()
            x, y = self._get_position(is_text=False)
            
            # Scale watermark and set opacity, then overlay
            filter_complex = (
                f"[1:v]scale=iw*{scale}:ih*{scale},"
                f"format=rgba,colorchannelmixer=aa={opacity}[wm];"
                f"[0:v][wm]overlay={x}:{y}"
            )
            cmd.extend(["-filter_complex", filter_complex])
        else:
            text = self.text_entry.get()
            fontsize = self.fontsize_var.get()
            fontcolor = self.fontcolor_var.get()
            x, y = self._get_position(is_text=True)
            
            # Use drawtext filter
            vf = f"drawtext=text='{text}':fontsize={fontsize}:fontcolor={fontcolor}:x={x}:y={y}"
            cmd.extend(["-vf", vf])
        
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please fill all required fields.")
    
    def run_watermark(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please fill all required fields.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = WatermarkApp()
    app.run()
