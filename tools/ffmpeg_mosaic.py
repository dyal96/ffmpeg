"""
FFmpeg Mosaic/Blur Region Tool
Apply blur or pixelate to specific regions of video
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme
)

class MosaicTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Blur/Mosaic Region", 650, 600)
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
        
        # Region Settings
        region_card = create_card(self.root, "📐 Region (pixels from top-left)")
        region_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(region_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="X:").pack(side="left")
        self.x_spin = ttk.Spinbox(row1, from_=0, to=9999, width=6)
        self.x_spin.set(100)
        self.x_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Y:").pack(side="left", padx=(10, 0))
        self.y_spin = ttk.Spinbox(row1, from_=0, to=9999, width=6)
        self.y_spin.set(100)
        self.y_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Width:").pack(side="left", padx=(10, 0))
        self.w_spin = ttk.Spinbox(row1, from_=10, to=9999, width=6)
        self.w_spin.set(200)
        self.w_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Height:").pack(side="left", padx=(10, 0))
        self.h_spin = ttk.Spinbox(row1, from_=10, to=9999, width=6)
        self.h_spin.set(200)
        self.h_spin.pack(side="left", padx=5)
        
        # Effect Settings
        effect_card = create_card(self.root, "🎨 Effect Type")
        effect_card.pack(fill="x", padx=10, pady=5)
        
        effects_row = ttk.Frame(effect_card)
        effects_row.pack(fill="x", pady=5)
        
        self.effect_var = tk.StringVar(value="blur")
        ttk.Radiobutton(effects_row, text="Blur (boxblur)", 
                        variable=self.effect_var, value="blur").pack(side="left", padx=5)
        ttk.Radiobutton(effects_row, text="Pixelate (mosaic)", 
                        variable=self.effect_var, value="pixelate").pack(side="left", padx=5)
        ttk.Radiobutton(effects_row, text="Black Box", 
                        variable=self.effect_var, value="black").pack(side="left", padx=5)
        
        strength_row = ttk.Frame(effect_card)
        strength_row.pack(fill="x", pady=5)
        
        ttk.Label(strength_row, text="Strength:").pack(side="left")
        self.strength_spin = ttk.Spinbox(strength_row, from_=1, to=50, width=6)
        self.strength_spin.set(10)
        self.strength_spin.pack(side="left", padx=5)
        
        ttk.Label(strength_row, text="(blur radius or pixel size)").pack(side="left", padx=5)
        
        # Time Range (optional)
        time_card = create_card(self.root, "⏱️ Time Range (optional)")
        time_card.pack(fill="x", padx=10, pady=5)
        
        time_row = ttk.Frame(time_card)
        time_row.pack(fill="x", pady=5)
        
        ttk.Label(time_row, text="Start (s):").pack(side="left")
        self.start_spin = ttk.Spinbox(time_row, from_=0, to=99999, width=8)
        self.start_spin.set(0)
        self.start_spin.pack(side="left", padx=5)
        
        ttk.Label(time_row, text="End (s):").pack(side="left", padx=(10, 0))
        self.end_spin = ttk.Spinbox(time_row, from_=0, to=99999, width=8)
        self.end_spin.set(0)
        self.end_spin.pack(side="left", padx=5)
        
        ttk.Label(time_row, text="(0 = entire video)").pack(side="left", padx=5)
        
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
        
        self.run_btn = ttk.Button(actions, text="▶ Apply Effect", command=self.run_mosaic)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def run_mosaic(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_mosaic")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        x = int(self.x_spin.get())
        y = int(self.y_spin.get())
        w = int(self.w_spin.get())
        h = int(self.h_spin.get())
        effect = self.effect_var.get()
        strength = int(self.strength_spin.get())
        start = float(self.start_spin.get())
        end = float(self.end_spin.get())
        
        # Build filter based on effect type
        if effect == "blur":
            # Crop region, blur it, overlay back
            filter_str = (
                f"[0:v]split[base][blur];"
                f"[blur]crop={w}:{h}:{x}:{y},boxblur={strength}:{strength}[blurred];"
                f"[base][blurred]overlay={x}:{y}"
            )
        elif effect == "pixelate":
            # Scale down then up for pixelate effect
            scale_down = max(1, w // strength)
            filter_str = (
                f"[0:v]split[base][pix];"
                f"[pix]crop={w}:{h}:{x}:{y},scale={scale_down}:-1,scale={w}:{h}:flags=neighbor[pixelated];"
                f"[base][pixelated]overlay={x}:{y}"
            )
        else:  # black box
            filter_str = f"drawbox=x={x}:y={y}:w={w}:h={h}:color=black:t=fill"
        
        # Add time enable if specified
        if start > 0 or end > 0:
            if end > start:
                filter_str = filter_str.replace("[0:v]", f"[0:v]").rstrip("]") + f":enable='between(t,{start},{end})'"
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file]
        
        if "[base]" in filter_str:
            cmd.extend(["-filter_complex", filter_str])
        else:
            cmd.extend(["-vf", filter_str])
        
        cmd.extend(["-c:v", "libx264", "-crf", "18", "-preset", "medium"])
        cmd.extend(["-c:a", "copy"])
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = MosaicTool()
    app.run()
