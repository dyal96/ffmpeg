"""
FFmpeg Stabilize Tool
Video stabilization using vidstab filter (2-pass)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme,
    TEMP_DIR
)

class StabilizeApp(FFmpegToolApp):
    """Video stabilization tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Stabilizer", width=600, height=560)
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
        
        # === Stabilization Options ===
        options_card = create_card(main_frame, "🎯 Stabilization Settings")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Shakiness
        shake_row = ttk.Frame(options_card)
        shake_row.pack(fill="x", pady=5)
        
        ttk.Label(shake_row, text="Shakiness (1-10):").pack(side="left")
        self.shakiness_var = tk.IntVar(value=5)
        shake_scale = ttk.Scale(shake_row, from_=1, to=10, variable=self.shakiness_var,
                                orient="horizontal", length=150)
        shake_scale.pack(side="left", padx=5)
        self.shake_label = ttk.Label(shake_row, text="5")
        self.shake_label.pack(side="left")
        shake_scale.configure(command=lambda v: self.shake_label.configure(text=str(int(float(v)))))
        
        # Accuracy
        acc_row = ttk.Frame(options_card)
        acc_row.pack(fill="x", pady=5)
        
        ttk.Label(acc_row, text="Accuracy (1-15):").pack(side="left")
        self.accuracy_var = tk.IntVar(value=9)
        acc_scale = ttk.Scale(acc_row, from_=1, to=15, variable=self.accuracy_var,
                              orient="horizontal", length=150)
        acc_scale.pack(side="left", padx=5)
        self.acc_label = ttk.Label(acc_row, text="9")
        self.acc_label.pack(side="left")
        acc_scale.configure(command=lambda v: self.acc_label.configure(text=str(int(float(v)))))
        
        # Smoothing
        smooth_row = ttk.Frame(options_card)
        smooth_row.pack(fill="x", pady=5)
        
        ttk.Label(smooth_row, text="Smoothing:").pack(side="left")
        self.smoothing_var = tk.IntVar(value=10)
        smooth_scale = ttk.Scale(smooth_row, from_=0, to=30, variable=self.smoothing_var,
                                 orient="horizontal", length=150)
        smooth_scale.pack(side="left", padx=5)
        self.smooth_label = ttk.Label(smooth_row, text="10")
        self.smooth_label.pack(side="left")
        smooth_scale.configure(command=lambda v: self.smooth_label.configure(text=str(int(float(v)))))
        
        # Crop/zoom mode
        zoom_row = ttk.Frame(options_card)
        zoom_row.pack(fill="x", pady=5)
        
        ttk.Label(zoom_row, text="Edge handling:").pack(side="left")
        self.zoom_var = tk.StringVar(value="0")
        zoom_combo = ttk.Combobox(zoom_row, textvariable=self.zoom_var, width=20,
                                  values=[("0", "Keep (may show edges)"), 
                                          ("1", "Static zoom"),
                                          ("2", "Adaptive zoom")])
        zoom_combo.pack(side="left", padx=5)
        
        ttk.Label(options_card, text="⚠️ 2-pass process: First analyzes, then stabilizes",
                  foreground="orange").pack(anchor="w", pady=(10, 0))
        
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
        self.run_btn = ttk.Button(btn_frame, text="🎯 Stabilize", command=self.run_stabilize)
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
            
            output_path = generate_output_path(input_path, "_stabilized")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def build_command(self, pass_num=2) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        trf_path = str(TEMP_DIR / "transforms.trf")
        
        shakiness = self.shakiness_var.get()
        accuracy = self.accuracy_var.get()
        smoothing = self.smoothing_var.get()
        zoom = self.zoom_var.get().split(",")[0] if "," in self.zoom_var.get() else "0"
        
        if pass_num == 1:
            # Analysis pass
            cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
            cmd.extend(["-vf", f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:result={trf_path}"])
            cmd.extend(["-f", "null", "-"])
        else:
            # Stabilization pass
            cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
            cmd.extend(["-vf", f"vidstabtransform=input={trf_path}:smoothing={smoothing}:zoom={zoom}"])
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
            cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd1 = self.build_command(pass_num=1)
        cmd2 = self.build_command(pass_num=2)
        if cmd1 and cmd2:
            preview = f"Pass 1: {' '.join(cmd1)}\n\nPass 2: {' '.join(cmd2)}"
            if self.preview_text:
                self.preview_text.configure(state="normal")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert("1.0", preview)
                self.preview_text.configure(state="disabled")
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_stabilize(self):
        cmd1 = self.build_command(pass_num=1)
        cmd2 = self.build_command(pass_num=2)
        
        if not cmd1 or not cmd2:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        # Run pass 1, then pass 2
        self.preview_command()
        self._on_log("=== Pass 1: Analyzing motion ===\n")
        
        # Store pass 2 command for later
        self._pass2_cmd = cmd2
        self._original_callback = self.runner.on_finished
        self.runner.on_finished = self._on_pass1_finished
        
        self.run_command(cmd1, self.input_entry.get())
    
    def _on_pass1_finished(self, success, message):
        if success:
            self._on_log("\n=== Pass 2: Applying stabilization ===\n")
            self.runner.on_finished = self._original_callback
            self.runner.run(self._pass2_cmd, self.input_entry.get())
        else:
            self.runner.on_finished = self._original_callback
            self._on_finished(False, f"Pass 1 failed: {message}")


if __name__ == "__main__":
    app = StabilizeApp()
    app.run()
