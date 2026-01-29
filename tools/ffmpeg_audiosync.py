"""
FFmpeg Audio Sync Tool
Synchronize audio and video tracks that are out of sync
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

class AudioSyncTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Audio Sync", 650, 500)
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
        
        # Sync Settings
        sync_card = create_card(self.root, "🔊 Audio Sync Adjustment")
        sync_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(sync_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Delay (seconds):").pack(side="left")
        self.delay_spin = ttk.Spinbox(row1, from_=-60, to=60, increment=0.1, width=10)
        self.delay_spin.set(0.0)
        self.delay_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="(+ = audio later, - = audio earlier)").pack(side="left", padx=5)
        
        # Quick adjust buttons
        quick_row = ttk.Frame(sync_card)
        quick_row.pack(fill="x", pady=5)
        
        ttk.Label(quick_row, text="Quick:").pack(side="left")
        for val in [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0]:
            sign = "+" if val > 0 else ""
            ttk.Button(quick_row, text=f"{sign}{val}s", width=6,
                      command=lambda v=val: self._adjust_delay(v)).pack(side="left", padx=2)
        
        # Mode
        mode_row = ttk.Frame(sync_card)
        mode_row.pack(fill="x", pady=5)
        
        ttk.Label(mode_row, text="Method:").pack(side="left")
        self.mode_var = tk.StringVar(value="delay")
        ttk.Radiobutton(mode_row, text="Delay Audio", variable=self.mode_var, value="delay").pack(side="left", padx=5)
        ttk.Radiobutton(mode_row, text="Delay Video", variable=self.mode_var, value="video").pack(side="left", padx=5)
        
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
        
        self.run_btn = ttk.Button(actions, text="▶ Apply Sync", command=self.run_sync)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def _adjust_delay(self, delta):
        current = float(self.delay_spin.get())
        self.delay_spin.set(round(current + delta, 2))
    
    def run_sync(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input video.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_synced")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        delay = float(self.delay_spin.get())
        mode = self.mode_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file]
        
        if delay == 0:
            # No change, just copy
            cmd.extend(["-c", "copy"])
        elif mode == "delay":
            # Delay audio (positive = audio comes later)
            if delay > 0:
                cmd.extend(["-itsoffset", str(delay), "-i", input_file])
                cmd.extend(["-map", "0:v", "-map", "1:a"])
            else:
                # Trim beginning of audio
                cmd.extend(["-af", f"adelay={int(abs(delay)*1000)}|{int(abs(delay)*1000)}"])
            cmd.extend(["-c:v", "copy", "-c:a", "aac"])
        else:
            # Delay video
            if delay > 0:
                cmd.extend(["-itsoffset", str(delay), "-i", input_file])
                cmd.extend(["-map", "1:v", "-map", "0:a"])
            else:
                cmd.extend(["-itsoffset", str(abs(delay)), "-i", input_file])
                cmd.extend(["-map", "1:v", "-map", "0:a"])
            cmd.extend(["-c:v", "libx264", "-crf", "18", "-c:a", "copy"])
        
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = AudioSyncTool()
    app.run()
