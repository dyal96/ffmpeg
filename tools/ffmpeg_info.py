"""
FFmpeg Info Tool
Display detailed media file information
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_info, get_media_duration, format_duration,
    browse_file, create_card, get_theme
)

class InfoApp(FFmpegToolApp):
    """Media information tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Media Info", width=700, height=650)
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Input Section ===
        input_card = create_card(main_frame, "📁 Select Media File")
        input_card.pack(fill="x", pady=(0, 10))
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x")
        
        ttk.Label(input_row, text="File:").pack(side="left")
        self.input_entry = ttk.Entry(input_row, width=55)
        self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(input_row, text="Browse", command=self._browse_input).pack(side="left")
        ttk.Button(input_row, text="Analyze", command=self._analyze).pack(side="left", padx=5)
        
        # === Quick Info ===
        quick_card = create_card(main_frame, "📊 Quick Summary")
        quick_card.pack(fill="x", pady=(0, 10))
        
        self.summary_text = tk.Text(quick_card, height=6, wrap="word", state="disabled")
        self.summary_text.pack(fill="x", pady=5)
        
        # === Stream Details ===
        streams_card = create_card(main_frame, "🎬 Streams")
        streams_card.pack(fill="both", expand=True, pady=(0, 10))
        
        # Treeview for streams
        columns = ("Type", "Codec", "Details", "Bitrate")
        self.tree = ttk.Treeview(streams_card, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        tree_scroll = ttk.Scrollbar(streams_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # === Raw JSON ===
        raw_card = create_card(main_frame, "📋 Raw Metadata (JSON)")
        raw_card.pack(fill="both", expand=True)
        
        self.raw_text = tk.Text(raw_card, height=8, wrap="none", state="disabled")
        raw_scroll_y = ttk.Scrollbar(raw_card, orient="vertical", command=self.raw_text.yview)
        raw_scroll_x = ttk.Scrollbar(raw_card, orient="horizontal", command=self.raw_text.xview)
        self.raw_text.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)
        
        raw_scroll_y.pack(side="right", fill="y")
        raw_scroll_x.pack(side="bottom", fill="x")
        self.raw_text.pack(fill="both", expand=True)
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="📋 Copy Summary", command=self._copy_summary).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📋 Copy JSON", command=self._copy_json).pack(side="left", padx=5)
    
    def _browse_input(self):
        filetypes = [
            ("Media files", "*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.m4a"),
            ("All files", "*.*")
        ]
        browse_file(self.input_entry, filetypes)
        self._analyze()
    
    def _analyze(self):
        input_path = self.input_entry.get()
        if not input_path:
            messagebox.showinfo("Info", "Please select a file first.")
            return
        
        info = get_media_info(input_path)
        if not info:
            messagebox.showerror("Error", "Could not analyze file.")
            return
        
        # Clear previous
        self.tree.delete(*self.tree.get_children())
        
        # Quick summary
        summary_lines = []
        fmt = info.get("format", {})
        
        filename = Path(input_path).name
        file_size = int(fmt.get("size", 0))
        duration = float(fmt.get("duration", 0))
        bitrate = int(fmt.get("bit_rate", 0)) // 1000 if fmt.get("bit_rate") else 0
        
        summary_lines.append(f"📄 File: {filename}")
        summary_lines.append(f"📦 Size: {file_size / (1024*1024):.2f} MB")
        summary_lines.append(f"⏱️ Duration: {format_duration(duration)}")
        summary_lines.append(f"📊 Bitrate: {bitrate} kbps")
        summary_lines.append(f"📁 Format: {fmt.get('format_name', 'Unknown')}")
        
        # Stream count
        streams = info.get("streams", [])
        video_count = sum(1 for s in streams if s.get("codec_type") == "video")
        audio_count = sum(1 for s in streams if s.get("codec_type") == "audio")
        sub_count = sum(1 for s in streams if s.get("codec_type") == "subtitle")
        
        summary_lines.append(f"🎬 Streams: {video_count} video, {audio_count} audio, {sub_count} subtitle")
        
        # Update summary
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", "\n".join(summary_lines))
        self.summary_text.configure(state="disabled")
        
        # Populate streams tree
        for stream in streams:
            stream_type = stream.get("codec_type", "unknown").capitalize()
            codec = stream.get("codec_name", "unknown")
            
            # Build details based on type
            if stream_type == "Video":
                w = stream.get("width", "?")
                h = stream.get("height", "?")
                fps = stream.get("r_frame_rate", "?")
                try:
                    num, den = map(int, fps.split("/"))
                    fps = f"{num/den:.2f}" if den > 0 else fps
                except:
                    pass
                details = f"{w}x{h} @ {fps} fps"
            elif stream_type == "Audio":
                sr = stream.get("sample_rate", "?")
                ch = stream.get("channels", "?")
                details = f"{sr} Hz, {ch} ch"
            elif stream_type == "Subtitle":
                lang = stream.get("tags", {}).get("language", "?")
                details = f"Language: {lang}"
            else:
                details = ""
            
            bitrate = stream.get("bit_rate", "N/A")
            if bitrate != "N/A":
                bitrate = f"{int(bitrate) // 1000} kbps"
            
            self.tree.insert("", "end", values=(stream_type, codec, details, bitrate))
        
        # Raw JSON
        self.raw_text.configure(state="normal")
        self.raw_text.delete("1.0", tk.END)
        self.raw_text.insert("1.0", json.dumps(info, indent=2))
        self.raw_text.configure(state="disabled")
    
    def _copy_summary(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.summary_text.get("1.0", tk.END))
        messagebox.showinfo("Copied", "Summary copied to clipboard.")
    
    def _copy_json(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.raw_text.get("1.0", tk.END))
        messagebox.showinfo("Copied", "JSON copied to clipboard.")


if __name__ == "__main__":
    app = InfoApp()
    app.run()
