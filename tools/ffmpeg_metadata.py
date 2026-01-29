"""
FFmpeg Metadata Tool
Edit video metadata/tags
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_info,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme
)

class MetadataApp(FFmpegToolApp):
    """Video metadata editor."""
    
    def __init__(self):
        super().__init__("FFmpeg Metadata Editor", width=600, height=600)
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
        
        ttk.Button(input_card, text="📋 Read Current Metadata", 
                   command=self._read_metadata).pack(anchor="w", pady=5)
        
        # === Metadata Fields ===
        meta_card = create_card(main_frame, "📝 Metadata")
        meta_card.pack(fill="x", pady=(0, 10))
        
        fields = [
            ("Title:", "title"),
            ("Artist:", "artist"),
            ("Album:", "album"),
            ("Year:", "year"),
            ("Genre:", "genre"),
            ("Comment:", "comment"),
            ("Description:", "description")
        ]
        
        self.meta_entries = {}
        for label, key in fields:
            row = ttk.Frame(meta_card)
            row.pack(fill="x", pady=2)
            
            ttk.Label(row, text=label, width=12).pack(side="left")
            entry = ttk.Entry(row, width=50)
            entry.pack(side="left", padx=5, fill="x", expand=True)
            self.meta_entries[key] = entry
        
        # Clear metadata option
        self.clear_existing = tk.BooleanVar(value=False)
        ttk.Checkbutton(meta_card, text="Clear all existing metadata first",
                        variable=self.clear_existing).pack(anchor="w", pady=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="📝 Apply Metadata", command=self.run_metadata)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _browse_input(self):
        filetypes = [("Media files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.m4a"), ("All files", "*.*")]
        browse_file(self.input_entry, filetypes)
        
        input_path = self.input_entry.get()
        if input_path:
            output_path = generate_output_path(input_path, "_tagged")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        input_path = self.input_entry.get()
        ext = Path(input_path).suffix if input_path else ".mp4"
        filetypes = [("Media files", f"*{ext}"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ext)
    
    def _read_metadata(self):
        input_path = self.input_entry.get()
        if not input_path:
            messagebox.showwarning("Warning", "Please select an input file first.")
            return
        
        info = get_media_info(input_path)
        if not info:
            messagebox.showerror("Error", "Could not read metadata.")
            return
        
        # Extract format tags
        tags = info.get("format", {}).get("tags", {})
        
        # Map common tag variations
        tag_map = {
            "title": ["title", "TITLE"],
            "artist": ["artist", "ARTIST", "album_artist"],
            "album": ["album", "ALBUM"],
            "year": ["year", "YEAR", "date", "DATE"],
            "genre": ["genre", "GENRE"],
            "comment": ["comment", "COMMENT"],
            "description": ["description", "DESCRIPTION"]
        }
        
        for key, entry in self.meta_entries.items():
            entry.delete(0, tk.END)
            for possible_tag in tag_map.get(key, [key]):
                if possible_tag in tags:
                    entry.insert(0, tags[possible_tag])
                    break
        
        self._on_log("Metadata loaded successfully.\n")
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        # Clear existing metadata if requested
        if self.clear_existing.get():
            cmd.extend(["-map_metadata", "-1"])
        
        # Add each metadata field
        for key, entry in self.meta_entries.items():
            value = entry.get().strip()
            if value:
                cmd.extend(["-metadata", f"{key}={value}"])
        
        # Copy streams
        cmd.extend(["-c", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_metadata(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())


if __name__ == "__main__":
    app = MetadataApp()
    app.run()
