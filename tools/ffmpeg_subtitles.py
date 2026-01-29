"""
FFmpeg Subtitles Tool
Burn-in or extract subtitles from video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class SubtitlesApp(FFmpegToolApp):
    """Subtitles burn-in and extraction tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Subtitles", width=650, height=600)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Mode selection
        mode_card = create_card(main_frame, "🎯 Mode")
        mode_card.pack(fill="x", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="burn")
        ttk.Radiobutton(mode_card, text="Burn-in subtitles (hardcode into video)",
                        variable=self.mode_var, value="burn",
                        command=self._on_mode_change).pack(anchor="w")
        ttk.Radiobutton(mode_card, text="Extract subtitles from video",
                        variable=self.mode_var, value="extract",
                        command=self._on_mode_change).pack(anchor="w")
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Input Video")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="Video File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=50)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", command=self._browse_input).pack(side="left")
        
        # === Subtitle File (for burn-in) ===
        self.sub_card = create_card(main_frame, "📝 Subtitle File")
        self.sub_card.pack(fill="x", pady=(0, 10))
        
        sub_row = ttk.Frame(self.sub_card)
        sub_row.pack(fill="x")
        
        ttk.Label(sub_row, text="Subtitle:").pack(side="left")
        self.sub_entry = ttk.Entry(sub_row, width=50)
        self.sub_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(sub_row, text="Browse", command=self._browse_sub).pack(side="left")
        
        # Subtitle style options
        style_row = ttk.Frame(self.sub_card)
        style_row.pack(fill="x", pady=5)
        
        ttk.Label(style_row, text="Font Size:").pack(side="left")
        self.fontsize_var = tk.IntVar(value=24)
        fontsize_spin = ttk.Spinbox(style_row, from_=12, to=48, width=5,
                                    textvariable=self.fontsize_var)
        fontsize_spin.pack(side="left", padx=5)
        
        ttk.Label(style_row, text="Force Style:").pack(side="left", padx=(20, 0))
        self.force_style = tk.BooleanVar(value=False)
        ttk.Checkbutton(style_row, variable=self.force_style).pack(side="left")
        
        # === Extract Options ===
        self.extract_card = create_card(main_frame, "📤 Extract Options")
        
        format_row = ttk.Frame(self.extract_card)
        format_row.pack(fill="x", pady=5)
        
        ttk.Label(format_row, text="Output Format:").pack(side="left")
        self.extract_format = tk.StringVar(value="srt")
        format_combo = ttk.Combobox(format_row, textvariable=self.extract_format, width=10,
                                    values=["srt", "ass", "vtt"])
        format_combo.pack(side="left", padx=5)
        
        stream_row = ttk.Frame(self.extract_card)
        stream_row.pack(fill="x", pady=5)
        
        ttk.Label(stream_row, text="Stream Index:").pack(side="left")
        self.stream_idx = tk.IntVar(value=0)
        stream_spin = ttk.Spinbox(stream_row, from_=0, to=10, width=5, textvariable=self.stream_idx)
        stream_spin.pack(side="left", padx=5)
        ttk.Label(stream_row, text="(usually 0 for first subtitle track)", foreground="gray").pack(side="left")
        
        # === Output Section ===
        output_card = create_card(main_frame, "📤 Output")
        output_card.pack(fill="x", pady=(0, 10))
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        
        ttk.Label(output_row, text="Output:").pack(side="left")
        self.output_entry = ttk.Entry(output_row, width=50)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(output_row, text="Browse", command=self._browse_output).pack(side="left")
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Preview", command=self.preview_command).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="▶️ Run", command=self.run_subtitles)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _on_mode_change(self):
        if self.mode_var.get() == "burn":
            self.sub_card.pack(fill="x", pady=(0, 10), after=self.sub_card.master.winfo_children()[1])
            self.extract_card.pack_forget()
        else:
            self.extract_card.pack(fill="x", pady=(0, 10), after=self.sub_card.master.winfo_children()[1])
            self.sub_card.pack_forget()
    
    def _browse_input(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            if self.mode_var.get() == "burn":
                output_path = generate_output_path(input_path, "_subbed")
            else:
                output_path = generate_output_path(input_path, "", f".{self.extract_format.get()}")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_sub(self):
        filetypes = [("Subtitle files", "*.srt *.ass *.ssa *.vtt"), ("All files", "*.*")]
        browse_file(self.sub_entry, filetypes)
    
    def _browse_output(self):
        if self.mode_var.get() == "burn":
            filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
            browse_save_file(self.output_entry, filetypes, ".mp4")
        else:
            ext = self.extract_format.get()
            filetypes = [(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")]
            browse_save_file(self.output_entry, filetypes, f".{ext}")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if self.mode_var.get() == "burn":
            sub_path = self.sub_entry.get()
            if not sub_path:
                return None
            
            # Escape path for subtitles filter
            escaped_sub = sub_path.replace("\\", "/").replace(":", "\\:")
            
            if self.force_style.get():
                style = f"FontSize={self.fontsize_var.get()}"
                vf = f"subtitles='{escaped_sub}':force_style='{style}'"
            else:
                vf = f"subtitles='{escaped_sub}'"
            
            cmd.extend(["-vf", vf])
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        else:
            # Extract subtitles
            idx = self.stream_idx.get()
            cmd.extend(["-map", f"0:s:{idx}"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please fill all required fields.")
    
    def run_subtitles(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please fill all required fields.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = SubtitlesApp()
    app.run()
