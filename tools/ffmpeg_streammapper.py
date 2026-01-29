"""
FFmpeg Stream Mapper Tool
View and selectively map streams from input files
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_file, browse_save_file,
    generate_output_path, get_binary, get_theme, get_media_info
)

class StreamMapperTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Stream Mapper", 700, 600)
        self.streams = []
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input File")
        input_card.pack(fill="x", padx=10, pady=5)
        
        input_row = ttk.Frame(input_card)
        input_row.pack(fill="x", pady=5)
        
        self.input_entry = ttk.Entry(input_row)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ttk.Button(input_row, text="Browse", 
                   command=self._browse_and_analyze).pack(side="left")
        
        ttk.Button(input_row, text="🔍 Analyze", 
                   command=self.analyze_streams).pack(side="left", padx=5)
        
        # Streams Display
        streams_card = create_card(self.root, "📊 Detected Streams")
        streams_card.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for streams
        columns = ("index", "type", "codec", "details", "selected")
        self.stream_tree = ttk.Treeview(streams_card, columns=columns, show="headings", height=8)
        
        self.stream_tree.heading("index", text="Index")
        self.stream_tree.heading("type", text="Type")
        self.stream_tree.heading("codec", text="Codec")
        self.stream_tree.heading("details", text="Details")
        self.stream_tree.heading("selected", text="Include")
        
        self.stream_tree.column("index", width=50)
        self.stream_tree.column("type", width=80)
        self.stream_tree.column("codec", width=100)
        self.stream_tree.column("details", width=250)
        self.stream_tree.column("selected", width=60)
        
        scrollbar = ttk.Scrollbar(streams_card, orient="vertical", command=self.stream_tree.yview)
        self.stream_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.stream_tree.pack(fill="both", expand=True, pady=5)
        
        # Toggle selection
        self.stream_tree.bind("<Double-1>", self._toggle_stream)
        
        btn_row = ttk.Frame(streams_card)
        btn_row.pack(fill="x", pady=5)
        
        ttk.Button(btn_row, text="✓ Select All", command=self._select_all).pack(side="left", padx=2)
        ttk.Button(btn_row, text="✗ Deselect All", command=self._deselect_all).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🎬 Video Only", command=self._select_video_only).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🔊 Audio Only", command=self._select_audio_only).pack(side="left", padx=2)
        
        # Output Section
        out_card = create_card(self.root, "💾 Output")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(out_row, text="Browse", command=lambda: browse_save_file(self.out_entry)).pack(side="left")
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Extract Selected Streams", command=self.run_extract)
        self.run_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        self.create_bottom_section(self.root)
    
    def _browse_and_analyze(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[("Media files", "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.ts"), ("All", "*.*")]
        )
        if filepath:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filepath)
            self.analyze_streams()
    
    def analyze_streams(self):
        input_file = self.input_entry.get()
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        info = get_media_info(input_file)
        if not info or "streams" not in info:
            tk.messagebox.showerror("Error", "Could not analyze file.")
            return
        
        # Clear existing
        for item in self.stream_tree.get_children():
            self.stream_tree.delete(item)
        
        self.streams = []
        
        for stream in info["streams"]:
            idx = stream.get("index", 0)
            codec_type = stream.get("codec_type", "unknown")
            codec_name = stream.get("codec_name", "unknown")
            
            details = ""
            if codec_type == "video":
                w = stream.get("width", "?")
                h = stream.get("height", "?")
                fps = stream.get("r_frame_rate", "?")
                details = f"{w}x{h} @ {fps}"
            elif codec_type == "audio":
                channels = stream.get("channels", "?")
                sample_rate = stream.get("sample_rate", "?")
                lang = stream.get("tags", {}).get("language", "")
                details = f"{channels}ch, {sample_rate}Hz {lang}"
            elif codec_type == "subtitle":
                lang = stream.get("tags", {}).get("language", "")
                details = f"Subtitle {lang}"
            
            self.streams.append({
                "index": idx,
                "type": codec_type,
                "codec": codec_name,
                "details": details,
                "selected": True
            })
            
            self.stream_tree.insert("", "end", values=(idx, codec_type, codec_name, details, "✓"))
    
    def _toggle_stream(self, event):
        item = self.stream_tree.selection()
        if item:
            idx = self.stream_tree.index(item[0])
            self.streams[idx]["selected"] = not self.streams[idx]["selected"]
            mark = "✓" if self.streams[idx]["selected"] else "✗"
            values = list(self.stream_tree.item(item[0], "values"))
            values[4] = mark
            self.stream_tree.item(item[0], values=values)
    
    def _select_all(self):
        for i, item in enumerate(self.stream_tree.get_children()):
            self.streams[i]["selected"] = True
            values = list(self.stream_tree.item(item, "values"))
            values[4] = "✓"
            self.stream_tree.item(item, values=values)
    
    def _deselect_all(self):
        for i, item in enumerate(self.stream_tree.get_children()):
            self.streams[i]["selected"] = False
            values = list(self.stream_tree.item(item, "values"))
            values[4] = "✗"
            self.stream_tree.item(item, values=values)
    
    def _select_video_only(self):
        for i, item in enumerate(self.stream_tree.get_children()):
            self.streams[i]["selected"] = self.streams[i]["type"] == "video"
            mark = "✓" if self.streams[i]["selected"] else "✗"
            values = list(self.stream_tree.item(item, "values"))
            values[4] = mark
            self.stream_tree.item(item, values=values)
    
    def _select_audio_only(self):
        for i, item in enumerate(self.stream_tree.get_children()):
            self.streams[i]["selected"] = self.streams[i]["type"] == "audio"
            mark = "✓" if self.streams[i]["selected"] else "✗"
            values = list(self.stream_tree.item(item, "values"))
            values[4] = mark
            self.stream_tree.item(item, values=values)
    
    def run_extract(self):
        input_file = self.input_entry.get()
        output_file = self.out_entry.get()
        
        if not input_file:
            tk.messagebox.showerror("Error", "Please select an input file.")
            return
        
        selected = [s for s in self.streams if s["selected"]]
        if not selected:
            tk.messagebox.showerror("Error", "Please select at least one stream.")
            return
        
        if not output_file:
            output_file = generate_output_path(input_file, "_mapped")
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, output_file)
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_file]
        
        for s in selected:
            cmd.extend(["-map", f"0:{s['index']}"])
        
        cmd.extend(["-c", "copy", output_file])
        
        self.set_preview(cmd)
        self.run_command(cmd, input_file)

if __name__ == "__main__":
    app = StreamMapperTool()
    app.run()
