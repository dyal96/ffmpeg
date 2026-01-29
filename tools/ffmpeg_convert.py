"""
FFmpeg Convert Tool
Convert video files between formats with codec control
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Import shared utilities
from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class ConvertApp(FFmpegToolApp):
    """Video format conversion tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Convert", width=650, height=600)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Input")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="Input File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=50)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", 
                   command=lambda: self._browse_input()).pack(side="left")
        
        # Duration display
        self.duration_label = ttk.Label(input_card, text="Duration: --:--:--")
        self.duration_label.pack(anchor="w", pady=(5, 0))
        
        # === Output Section ===
        output_card = create_card(main_frame, "📤 Output")
        output_card.pack(fill="x", pady=(0, 10))
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        
        ttk.Label(output_row, text="Output File:").pack(side="left")
        self.output_entry = ttk.Entry(output_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(output_row, text="Browse", 
                   command=lambda: self._browse_output()).pack(side="left")
        
        # === Format Options ===
        options_card = create_card(main_frame, "⚙️ Format Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Container format
        format_row = ttk.Frame(options_card)
        format_row.pack(fill="x", pady=2)
        
        ttk.Label(format_row, text="Container:").pack(side="left")
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(format_row, textvariable=self.format_var, width=10,
                                    values=["mp4", "mkv", "avi", "mov", "webm", "flv", "ts"])
        format_combo.pack(side="left", padx=5)
        format_combo.bind("<<ComboboxSelected>>", self._on_format_changed)
        
        # Video codec
        vcodec_row = ttk.Frame(options_card)
        vcodec_row.pack(fill="x", pady=2)
        
        ttk.Label(vcodec_row, text="Video Codec:").pack(side="left")
        self.vcodec_var = tk.StringVar(value="libx264")
        vcodec_combo = ttk.Combobox(vcodec_row, textvariable=self.vcodec_var, width=15,
                                    values=["copy", "libx264", "libx265", "libvpx-vp9", 
                                            "h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv"])
        vcodec_combo.pack(side="left", padx=5)
        
        # Audio codec
        acodec_row = ttk.Frame(options_card)
        acodec_row.pack(fill="x", pady=2)
        
        ttk.Label(acodec_row, text="Audio Codec:").pack(side="left")
        self.acodec_var = tk.StringVar(value="aac")
        acodec_combo = ttk.Combobox(acodec_row, textvariable=self.acodec_var, width=15,
                                    values=["copy", "aac", "mp3", "opus", "flac", "ac3"])
        acodec_combo.pack(side="left", padx=5)
        
        # CRF (quality)
        crf_row = ttk.Frame(options_card)
        crf_row.pack(fill="x", pady=2)
        
        ttk.Label(crf_row, text="Quality (CRF):").pack(side="left")
        self.crf_var = tk.IntVar(value=23)
        crf_scale = ttk.Scale(crf_row, from_=0, to=51, variable=self.crf_var, 
                              orient="horizontal", length=150)
        crf_scale.pack(side="left", padx=5)
        self.crf_label = ttk.Label(crf_row, text="23")
        self.crf_label.pack(side="left")
        crf_scale.configure(command=lambda v: self.crf_label.configure(text=str(int(float(v)))))
        
        ttk.Label(crf_row, text="(0=lossless, 51=worst)", foreground="gray").pack(side="left", padx=10)
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview Command", 
                   command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="▶️ Convert", command=self.run_convert)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section (Preview, Log, Progress) ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.m4v *.wmv"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        
        # Update duration and auto-generate output
        input_path = self.input_entry.get()
        if input_path:
            duration = get_media_duration(input_path)
            if duration:
                self.duration_label.configure(text=f"Duration: {format_duration(duration)}")
            
            # Auto-generate output path
            ext = "." + self.format_var.get()
            output_path = generate_output_path(input_path, "_converted", ext)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        ext = self.format_var.get()
        filetypes = [(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, f".{ext}")
    
    def _on_format_changed(self, event=None):
        """Update output extension when format changes."""
        input_path = self.input_entry.get()
        if input_path:
            ext = "." + self.format_var.get()
            output_path = generate_output_path(input_path, "_converted", ext)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def build_command(self) -> list:
        """Build FFmpeg command."""
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        # Video codec
        vcodec = self.vcodec_var.get()
        if vcodec == "copy":
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-c:v", vcodec])
            # Add CRF for x264/x265
            if vcodec in ["libx264", "libx265"]:
                cmd.extend(["-crf", str(self.crf_var.get())])
        
        # Audio codec
        acodec = self.acodec_var.get()
        if acodec == "copy":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", acodec])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        """Show command preview."""
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_convert(self):
        """Run the conversion."""
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = ConvertApp()
    app.run()
