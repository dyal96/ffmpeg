"""
FFmpeg Smart Cut Tool
Remove silent sections from videos (silence removal / jump cut)
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme, TEMP_DIR, ensure_dir
)

class SmartCutTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Smart Cut (Silence Removal)", 650, 600)
        self.segments = []
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
        
        # Detection Settings
        settings_card = create_card(self.root, "🔇 Silence Detection Settings")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        row1 = ttk.Frame(settings_card)
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="Silence Threshold (dB):").pack(side="left")
        self.threshold_spin = ttk.Spinbox(row1, from_=-80, to=-10, width=6)
        self.threshold_spin.set(-30)
        self.threshold_spin.pack(side="left", padx=5)
        
        ttk.Label(row1, text="Min Silence Duration (s):").pack(side="left", padx=(15, 0))
        self.duration_spin = ttk.Spinbox(row1, from_=0.1, to=10, increment=0.1, width=6)
        self.duration_spin.set(0.5)
        self.duration_spin.pack(side="left", padx=5)
        
        row2 = ttk.Frame(settings_card)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Padding Before/After (s):").pack(side="left")
        self.padding_spin = ttk.Spinbox(row2, from_=0, to=2, increment=0.05, width=6)
        self.padding_spin.set(0.1)
        self.padding_spin.pack(side="left", padx=5)
        
        # Analyze Button
        analyze_btn = ttk.Button(settings_card, text="🔍 Analyze Silence", command=self.analyze_silence)
        analyze_btn.pack(pady=10)
        
        # Detected Segments Display
        seg_card = create_card(self.root, "✂️ Detected Non-Silent Segments")
        seg_card.pack(fill="x", padx=10, pady=5)
        
        self.seg_list = tk.Listbox(seg_card, height=5)
        self.seg_list.pack(fill="x", pady=5)
        
        self.seg_info_label = ttk.Label(seg_card, text="No segments detected yet.")
        self.seg_info_label.pack(anchor="w")
        
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
        
        self.run_btn = ttk.Button(actions, text="▶ Remove Silence", command=self.run_cut)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def analyze_silence(self):
        input_file = self.input_entry.get()
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        threshold = self.threshold_spin.get()
        duration = self.duration_spin.get()
        
        # Use silencedetect filter
        cmd = [
            get_binary("ffmpeg"), "-i", input_file,
            "-af", f"silencedetect=noise={threshold}dB:d={duration}",
            "-f", "null", "-"
        ]
        
        self._on_log(f"Analyzing: {' '.join(cmd)}\n")
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
            output = result.stderr
            
            # Parse silence_start and silence_end
            silence_starts = [float(m.group(1)) for m in re.finditer(r'silence_start: ([\d.]+)', output)]
            silence_ends = [float(m.group(1)) for m in re.finditer(r'silence_end: ([\d.]+)', output)]
            
            # Get video duration
            dur_match = re.search(r'Duration: (\d+):(\d+):([\d.]+)', output)
            if dur_match:
                h, m, s = dur_match.groups()
                total_duration = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                total_duration = 9999  # Fallback
            
            # Build non-silent segments
            self.segments = []
            padding = float(self.padding_spin.get())
            
            # Handle beginning
            if silence_starts and silence_starts[0] > 0:
                self.segments.append((0, max(0, silence_starts[0] - padding)))
            elif not silence_starts:
                # No silence detected at all
                self.segments.append((0, total_duration))
            
            # Middle segments
            for i, end in enumerate(silence_ends):
                start = end + padding
                if i + 1 < len(silence_starts):
                    seg_end = silence_starts[i + 1] - padding
                else:
                    seg_end = total_duration
                
                if seg_end > start:
                    self.segments.append((max(0, start), seg_end))
            
            # Display segments
            self.seg_list.delete(0, tk.END)
            total_kept = 0
            for i, (s, e) in enumerate(self.segments):
                self.seg_list.insert(tk.END, f"Segment {i+1}: {s:.2f}s - {e:.2f}s ({e-s:.2f}s)")
                total_kept += (e - s)
            
            removed = total_duration - total_kept
            self.seg_info_label.config(
                text=f"Found {len(self.segments)} segments. Keeping {total_kept:.1f}s, removing {removed:.1f}s of silence."
            )
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Analysis failed: {e}")
    
    def run_cut(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        if not self.segments:
            tk.messagebox.showerror("Error", "Please analyze silence first.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_smartcut")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        ensure_dir(TEMP_DIR)
        
        # Create concat file
        concat_file = TEMP_DIR / "smartcut_segments.txt"
        temp_files = []
        
        # Export each segment
        for i, (start, end) in enumerate(self.segments):
            temp_file = TEMP_DIR / f"smartcut_seg_{i}.mp4"
            temp_files.append(temp_file)
            
            # Re-encode for clean cuts
            cmd = [
                get_binary("ffmpeg"), "-y",
                "-ss", str(start), "-to", str(end),
                "-i", input_file,
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                str(temp_file)
            ]
            self._on_log(f"Exporting segment {i+1}: {' '.join(cmd)}\n")
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(cmd, creationflags=creationflags)
        
        # Write concat file
        with open(concat_file, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf}'\n")
        
        # Concatenate
        cmd = [
            get_binary("ffmpeg"), "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            output_file
        ]
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = SmartCutTool()
    app.run()
