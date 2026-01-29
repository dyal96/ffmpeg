"""
FFmpeg Social Media Tool
Convert videos to social media aspect ratios with crop/blur/pad options
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_media_info, get_theme
)

# Preset aspect ratios for social platforms
PRESETS = {
    "TikTok / Reels (9:16)": (9, 16),
    "Instagram Square (1:1)": (1, 1),
    "Instagram Portrait (4:5)": (4, 5),
    "YouTube / Landscape (16:9)": (16, 9),
    "Twitter Video (16:9)": (16, 9),
    "Custom": None,
}

class SocialTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Social Media Crop", 650, 580)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input Video")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=lambda: browse_file(self.input_entry, 
                   [("Video files", "*.mp4;*.mkv;*.mov;*.avi"), ("All", "*.*")])).pack(side="left")
        
        # Aspect Ratio Section
        ar_card = create_card(self.root, "📐 Target Aspect Ratio")
        ar_card.pack(fill="x", padx=10, pady=5)
        
        preset_row = ttk.Frame(ar_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Platform:").pack(side="left")
        self.preset_var = tk.StringVar(value="TikTok / Reels (9:16)")
        self.preset_combo = ttk.Combobox(preset_row, textvariable=self.preset_var, 
                                         values=list(PRESETS.keys()), state="readonly", width=25)
        self.preset_combo.pack(side="left", padx=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)
        
        # Custom AR inputs
        custom_row = ttk.Frame(ar_card)
        custom_row.pack(fill="x", pady=5)
        
        ttk.Label(custom_row, text="Width Ratio:").pack(side="left")
        self.ar_w_spin = ttk.Spinbox(custom_row, from_=1, to=100, width=5)
        self.ar_w_spin.set(9)
        self.ar_w_spin.pack(side="left", padx=5)
        
        ttk.Label(custom_row, text="Height Ratio:").pack(side="left", padx=(10, 0))
        self.ar_h_spin = ttk.Spinbox(custom_row, from_=1, to=100, width=5)
        self.ar_h_spin.set(16)
        self.ar_h_spin.pack(side="left", padx=5)
        
        # Mode Section
        mode_card = create_card(self.root, "🎨 Fill Mode")
        mode_card.pack(fill="x", padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="blur")
        
        modes_frame = ttk.Frame(mode_card)
        modes_frame.pack(fill="x", pady=5)
        
        ttk.Radiobutton(modes_frame, text="Blur Background", 
                        variable=self.mode_var, value="blur").pack(side="left", padx=5)
        ttk.Radiobutton(modes_frame, text="Black Bars", 
                        variable=self.mode_var, value="black").pack(side="left", padx=5)
        ttk.Radiobutton(modes_frame, text="White Bars", 
                        variable=self.mode_var, value="white").pack(side="left", padx=5)
        ttk.Radiobutton(modes_frame, text="Crop to Fill", 
                        variable=self.mode_var, value="crop").pack(side="left", padx=5)
        
        # Output Resolution
        res_frame = ttk.Frame(mode_card)
        res_frame.pack(fill="x", pady=5)
        
        ttk.Label(res_frame, text="Output Width:").pack(side="left")
        self.out_w_spin = ttk.Spinbox(res_frame, from_=100, to=3840, increment=10, width=6)
        self.out_w_spin.set(1080)
        self.out_w_spin.pack(side="left", padx=5)
        
        ttk.Label(res_frame, text="(Height auto-calculated from AR)").pack(side="left", padx=5)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(out_row, text="Browse", 
                   command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Convert", command=self.run_convert)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section (log/progress)
        self.create_bottom_section(self.root)
    
    def _on_preset_change(self, event=None):
        preset = self.preset_var.get()
        ar = PRESETS.get(preset)
        if ar:
            self.ar_w_spin.set(ar[0])
            self.ar_h_spin.set(ar[1])
    
    def run_convert(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_social")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        ar_w = int(self.ar_w_spin.get())
        ar_h = int(self.ar_h_spin.get())
        out_w = int(self.out_w_spin.get())
        out_h = int(out_w * ar_h / ar_w)
        
        # Ensure even dimensions
        out_w = out_w if out_w % 2 == 0 else out_w + 1
        out_h = out_h if out_h % 2 == 0 else out_h + 1
        
        mode = self.mode_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file]
        
        if mode == "crop":
            # Crop to fill - center crop
            # Scale to cover, then crop
            filter_str = f"scale=w='if(gt(iw/ih,{ar_w}/{ar_h}),{out_h}*iw/ih,{out_w})':h='if(gt(iw/ih,{ar_w}/{ar_h}),{out_h},{out_w}*ih/iw)',crop={out_w}:{out_h}"
            cmd.extend(["-vf", filter_str])
        
        elif mode == "blur":
            # Split -> blur for bg -> overlay scaled video
            filter_complex = (
                f"[0:v]split[bg][fg];"
                f"[bg]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h},boxblur=20:5[blurred];"
                f"[fg]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[scaled];"
                f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2"
            )
            cmd.extend(["-filter_complex", filter_complex])
        
        elif mode in ("black", "white"):
            color = "black" if mode == "black" else "white"
            filter_str = f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color={color}"
            cmd.extend(["-vf", filter_str])
        
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "medium"])
        cmd.extend(["-c:a", "copy"])
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = SocialTool()
    app.run()
