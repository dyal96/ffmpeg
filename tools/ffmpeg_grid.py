import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os
from pathlib import Path

# Add parent directory to path to import ffmpeg_common
sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_save_file, 
    generate_output_path, get_binary, get_media_info
)

class GridTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Grid Video / Collage", 700, 600)
        self.input_files = []
        self.build_ui()
    
    def build_ui(self):
        # Input Section
        input_card = create_card(self.root, "Video Sources")
        input_card.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ttk.Frame(input_card)
        btn_frame.pack(fill="x", pady=2)
        
        ttk.Button(btn_frame, text="➕ Add Video", command=self.add_video).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="➖ Remove", command=self.remove_video).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self.clear_videos).pack(side="left", padx=2)
        
        self.file_list = tk.Listbox(input_card, height=6, selectmode="extended")
        self.file_list.pack(fill="x", pady=5)
        
        # Grid Configuration
        settings_card = create_card(self.root, "Grid Layout")
        settings_card.pack(fill="x", padx=10, pady=5)
        
        # Rows/Cols
        grid_opts = ttk.Frame(settings_card)
        grid_opts.pack(fill="x", pady=5)
        
        ttk.Label(grid_opts, text="Rows:").pack(side="left")
        self.rows_spin = ttk.Spinbox(grid_opts, from_=1, to=10, width=5)
        self.rows_spin.set(2)
        self.rows_spin.pack(side="left", padx=5)
        
        ttk.Label(grid_opts, text="Cols:").pack(side="left", padx=(10, 0))
        self.cols_spin = ttk.Spinbox(grid_opts, from_=1, to=10, width=5)
        self.cols_spin.set(2)
        self.cols_spin.pack(side="left", padx=5)
        
        # Resolution per cell
        ttk.Label(grid_opts, text="Cell Width:").pack(side="left", padx=(10, 0))
        self.width_spin = ttk.Spinbox(grid_opts, from_=100, to=3840, increment=10, width=6)
        self.width_spin.set(640)
        self.width_spin.pack(side="left", padx=5)
        
        ttk.Label(grid_opts, text="Height:").pack(side="left")
        self.height_spin = ttk.Spinbox(grid_opts, from_=100, to=2160, increment=10, width=6)
        self.height_spin.set(360)
        self.height_spin.pack(side="left", padx=5)
        
        # Audio Options
        audio_frame = ttk.Frame(settings_card)
        audio_frame.pack(fill="x", pady=5)
        
        ttk.Label(audio_frame, text="Audio:").pack(side="left")
        self.audio_mode = tk.StringVar(value="mix")
        ttk.Radiobutton(audio_frame, text="Mix All", variable=self.audio_mode, value="mix").pack(side="left", padx=5)
        ttk.Radiobutton(audio_frame, text="First Video Only", variable=self.audio_mode, value="first").pack(side="left", padx=5)
        ttk.Radiobutton(audio_frame, text="None", variable=self.audio_mode, value="none").pack(side="left", padx=5)

        # Output Section
        out_card = create_card(self.root, "Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        ui_out_row = ttk.Frame(out_card)
        ui_out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(ui_out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(ui_out_row, text="Browse", 
                 command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        controls = ttk.Frame(self.root)
        controls.pack(pady=10)
        
        self.run_btn = ttk.Button(controls, text="▶ Run Grid", command=self.run_grid)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(controls, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Standard Bottom Section (Log/Progress)
        self.create_bottom_section(self.root)

    def add_video(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4;*.mkv;*.mov;*.avi"), ("All files", "*.*")])
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
                self.file_list.insert(tk.END, os.path.basename(f))
        self._update_output_suggestion()

    def remove_video(self):
        sel = self.file_list.curselection()
        for index in reversed(sel):
            self.file_list.delete(index)
            self.input_files.pop(index)
        self._update_output_suggestion()

    def clear_videos(self):
        self.file_list.delete(0, tk.END)
        self.input_files.clear()

    def _update_output_suggestion(self):
        if self.input_files and not self.out_entry.get():
            first = self.input_files[0]
            out = generate_output_path(first, "_grid")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, out)

    def run_grid(self):
        input_files = self.input_files
        output_file = self.out_entry.get()
        
        if not input_files:
            tk.messagebox.showerror("Error", "No input files selected!")
            return
        if not output_file:
            tk.messagebox.showerror("Error", "Output file not specified!")
            return
            
        rows = int(self.rows_spin.get())
        cols = int(self.cols_spin.get())
        w = self.width_spin.get()
        h = self.height_spin.get()
        
        # Basic validation
        if len(input_files) > rows * cols:
            tk.messagebox.showwarning("Warning", f"More videos ({len(input_files)}) than grid slots ({rows*cols}). Extra videos will be ignored.")
            input_files = input_files[:rows*cols]
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        # Inputs
        for f in input_files:
            cmd.extend(["-i", f])
            
        # Filter Complex
        filter_parts = []
        
        # 1. Scale all inputs to uniform size
        for i in range(len(input_files)):
            filter_parts.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2[v{i}]")
            
        # 2. xstack Layout
        # xstack layout: 0_0|w0_0|w0_0+w1_0...
        # Simple grid logic:
        # Col 0: 0
        # Col 1: w0
        # Col 2: w0+w1 (normalized, assume all same width W)
        # So x = (index % cols) * W
        # y = (index // cols) * H
        
        layout_str = ""
        input_refs = ""
        
        # Need to handle case where we have fewer videos than grid slots
        # For xstack, we need exactly N inputs if we define layout for N
        # Actually xstack documentation says inputs must match layout
        
        used_count = len(input_files)
        
        for i in range(used_count):
            input_refs += f"[v{i}]"
            
            c = i % cols
            r = i // cols
            
            x_pos = "0" if c == 0 else "+".join([f"w0"] * c)
            y_pos = "0" if r == 0 else "+".join([f"h0"] * r)
            
            if i > 0:
                layout_str += "|"
            layout_str += f"{x_pos}_{y_pos}"
            
        filter_parts.append(f"{input_refs}xstack=inputs={used_count}:layout={layout_str}[vout]")
        
        # Audio handling
        audio_map = ""
        if self.audio_mode.get() == "mix":
            # amix
            filter_parts.append(f"amix=inputs={used_count}:duration=shortest[aout]")
            audio_map = "[aout]"
        elif self.audio_mode.get() == "first":
            audio_map = "0:a"
            
        full_filter = ";".join(filter_parts)
        
        cmd.extend(["-filter_complex", full_filter])
        cmd.extend(["-map", "[vout]"])
        if self.audio_mode.get() != "none" and audio_map:
            cmd.extend(["-map", audio_map])
            
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "medium"])
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        cmd.append(output_file)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_files[0]) # Use first file for duration est

if __name__ == "__main__":
    app = GridTool()
    app.run()
