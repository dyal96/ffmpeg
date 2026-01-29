"""
FFmpeg Loop Tool
Loop video/audio a specified number of times
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class LoopApp(FFmpegToolApp):
    """Video/audio loop tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Loop", width=600, height=500)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Input Media")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="Input File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=50)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", command=self._browse_input).pack(side="left")
        
        self.duration_label = ttk.Label(input_card, text="Duration: --:--:--")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        # === Loop Settings ===
        loop_card = create_card(main_frame, "🔁 Loop Settings")
        loop_card.pack(fill="x", pady=(0, 10))
        
        # Loop count
        count_row = ttk.Frame(loop_card)
        count_row.pack(fill="x", pady=5)
        
        ttk.Label(count_row, text="Loop count:").pack(side="left")
        self.loop_count = tk.IntVar(value=3)
        count_spin = ttk.Spinbox(count_row, from_=2, to=100, width=6, textvariable=self.loop_count)
        count_spin.pack(side="left", padx=5)
        ttk.Label(count_row, text="times").pack(side="left")
        
        # Estimated output duration
        self.est_label = ttk.Label(loop_card, text="Estimated output: --:--:--")
        self.est_label.pack(anchor="w", pady=5)
        
        # Update button
        ttk.Button(loop_card, text="Calculate", command=self._update_estimate).pack(anchor="w")
        
        # Method
        method_row = ttk.Frame(loop_card)
        method_row.pack(fill="x", pady=5)
        
        ttk.Label(method_row, text="Method:").pack(side="left")
        self.method_var = tk.StringVar(value="concat")
        method_combo = ttk.Combobox(method_row, textvariable=self.method_var, width=12,
                                    values=["concat", "stream_loop"])
        method_combo.pack(side="left", padx=5)
        
        ttk.Label(loop_card, text="• concat: Create file list and concatenate\n"
                                   "• stream_loop: Use FFmpeg stream loop (simpler)",
                  foreground="gray").pack(anchor="w")
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔁 Create Loop", command=self.run_loop)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Media files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.gif"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
                self._update_estimate()
            
            output_path = generate_output_path(input_path, "_looped")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        input_path = self.input_entry.get()
        ext = Path(input_path).suffix if input_path else ".mp4"
        filetypes = [("Media files", f"*{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ext)
    
    def _update_estimate(self):
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                loops = self.loop_count.get()
                total = duration * loops
                self.est_label.configure(text=f"Estimated output: {format_duration(total)}")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        loops = self.loop_count.get()
        method = self.method_var.get()
        
        cmd = [get_binary("ffmpeg"), "-y"]
        
        if method == "stream_loop":
            cmd.extend(["-stream_loop", str(loops - 1)])
            cmd.extend(["-i", input_path])
            cmd.extend(["-c", "copy"])
        else:  # concat
            # For preview, show the command concept
            cmd.extend(["-f", "concat", "-safe", "0"])
            cmd.extend(["-i", f"<loop_list_{loops}x>"])
            cmd.extend(["-c", "copy"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_loop(self):
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        loops = self.loop_count.get()
        
        # Use stream_loop for simplicity
        cmd = [get_binary("ffmpeg"), "-y"]
        cmd.extend(["-stream_loop", str(loops - 1)])
        cmd.extend(["-i", input_path])
        cmd.extend(["-c", "copy"])
        cmd.append(output_path)
        
        self.set_preview(cmd)
        self.run_command(cmd, input_path)


if __name__ == "__main__":
    app = LoopApp()
    app.run()
