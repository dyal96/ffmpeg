"""
FFmpeg Launcher
Central hub for all FFmpeg tools
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import get_theme, apply_theme, get_binary

# Tool Definitions: Name, Script, Icon, Description
TOOLS = [
    # Quick Tools
    ("Convert", "ffmpeg_convert.py", "🔄", "Convert video formats"),
    ("Compress", "ffmpeg_compress.py", "📉", "Reduce file size"),
    ("Trim/Cut", "ffmpeg_trim.py", "✂️", "Cut video segments"),
    ("Join Clips", "ffmpeg_concat.py", "🎞️", "Combine multiple videos"),
    ("Merge A+V", "ffmpeg_merge.py", "➕", "Combine audio & video"),
    ("Extract Audio", "ffmpeg_extract_audio.py", "🎵", "Get mp3/aac from video"),
    ("Resize", "ffmpeg_resize.py", "📏", "Change resolution"),
    ("Crop", "ffmpeg_crop.py", "🖼️", "Crop video area"),
    ("Rotate/Flip", "ffmpeg_rotate.py", "cw", "Rotate or flip video"),
    
    # Advanced
    ("Stabilize", "ffmpeg_stabilize.py", "⚖️", "Remove shake"),
    ("Reverse", "ffmpeg_reverse.py", "⏪", "Play backwards"),
    ("Speed/Slow", "ffmpeg_speed.py", "⏩", "Change playback speed"),
    ("Watermark", "ffmpeg_watermark.py", "©️", "Add logo/text"),
    ("Subtitles", "ffmpeg_subtitles.py", "📝", "Burn/Extract subs"),
    ("Slideshow", "ffmpeg_slideshow.py", "🎞️", "Photos to video"),
    ("Thumbnail", "ffmpeg_thumbnail.py", "📸", "Extract image"),
    ("Video Info", "ffmpeg_info.py", "ℹ️", "Get metadata"),
    ("Metadata", "ffmpeg_metadata.py", "🏷️", "Edit tags"),
    ("Denoise", "ffmpeg_denoise.py", "🔇", "Remove noise"),
    ("Sharpen", "ffmpeg_sharpen.py", "🔪", "Enhance details"),
    ("Vibrance", "ffmpeg_color.py", "🎨", "Adjust colors"),
    ("Fade In/Out", "ffmpeg_fade.py", "⬛", "Add fades"),
    ("Normalize", "ffmpeg_normalize.py", "🔊", "Fix audio volume"),
    ("Delogo", "ffmpeg_delogo.py", "🧼", "Remove logo"),
    ("PIP", "ffmpeg_pip.py", "🖼️", "Picture in Picture"),
    ("GIF", "ffmpeg_gif.py", "👾", "Video to GIF"),
    ("Split", "ffmpeg_splitter.py", "➗", "Split into parts"),
    ("Web Optimize", "ffmpeg_webopt.py", "🌐", "Web streaming"),
    ("Interpolate", "ffmpeg_interpolate.py", "🔄", "Frame interpolation"),
    ("Loop", "ffmpeg_loop.py", "🔁", "Loop video"),
    ("Record Screen", "ffmpeg_recorder.py", "⏺️", "Screen capture"),
    ("Grid Video", "ffmpeg_grid.py", "▦", "Video collage"),
    ("Social Media", "ffmpeg_social.py", "📱", "Aspect ratio convert"),
    ("Smart Cut", "ffmpeg_smartcut.py", "🔇", "Remove silence"),
    ("Scene Detect", "ffmpeg_scenedetect.py", "🎬", "Detect scene changes"),
    ("LUT Apply", "ffmpeg_lut.py", "🎨", "Apply 3D LUTs"),
    ("Tonemap", "ffmpeg_tonemap.py", "☀️", "HDR to SDR"),
    ("Visualizer", "ffmpeg_visualizer.py", "🎵", "Audio visualization"),
    ("Mosaic", "ffmpeg_mosaic.py", "🔲", "Blur region"),
    
    # Utilities
    ("Hardware Check", "ffmpeg_hwcheck.py", "🚀", "Configure GPU"),
    ("Batch", "ffmpeg_batch.py", "📦", "Batch process"),
    ("YouTube DL", "ffmpeg_ytdl.py", "⬇️", "Download videos"),
    ("Audio Sync", "ffmpeg_audiosync.py", "🔊", "Sync audio/video"),
    ("Proxy", "ffmpeg_proxy.py", "📹", "Generate proxies"),
    ("Watch Folder", "ffmpeg_watchfolder.py", "👁️", "Auto-process folder"),
    ("Temp Clean", "ffmpeg_tempcleaner.py", "🧹", "Clean temp files"),
    ("Img to Video", "ffmpeg_img2video.py", "🖼️", "Image to video"),
    
    # Analysis
    ("Bitrate Calc", "ffmpeg_bitratecalc.py", "🧮", "Calculate bitrate"),
    ("Stream Map", "ffmpeg_streammapper.py", "🗺️", "Map streams"),
    ("Video Scopes", "ffmpeg_scopes.py", "📊", "Video analysis"),
]

class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFmpeg Toolbox")
        self.root.geometry("1100x700")
        
        apply_theme(self.root)
        self.theme = get_theme()
        
        self.build_ui()
    
    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.theme["bg"])
        header.pack(fill="x", padx=20, pady=10)
        
        tk.Label(header, text="FFmpeg Toolbox", font=("Segoe UI", 24, "bold"),
                 bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left")
        
        # Search & Sort Frame
        search_frame = tk.Frame(header, bg=self.theme["bg"])
        search_frame.pack(side="right", fill="y")
        
        # Sort Button
        self.sort_var = tk.StringVar(value="Default")
        ttk.Button(search_frame, text="Sort A-Z", command=self.toggle_sort).pack(side="left", padx=5)
        
        tk.Label(search_frame, text="🔍", bg=self.theme["bg"], fg=self.theme["fg"], font=("Segoe UI", 12)).pack(side="left", padx=(5, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left")
        
        # Tool Count
        self.count_label = tk.Label(header, text=f"Total Tools: {len(TOOLS)}", 
                                  bg=self.theme["bg"], fg="gray", font=("Segoe UI", 10))
        self.count_label.pack(side="left", padx=20, pady=10)
        
        # Scrollable Grid Area
        self.canvas = tk.Canvas(self.root, bg=self.theme["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        
        self.scroll_frame = tk.Frame(self.canvas, bg=self.theme["bg"])
        self.scroll_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=20)
        self.scrollbar.pack(side="right", fill="y")
        
        # Maximize window
        self.root.state('zoomed')
        
        self.current_tools = TOOLS
        self.load_tools(TOOLS)
        
    def toggle_sort(self):
        if self.sort_var.get() == "Default":
            self.sort_var.set("A-Z")
            sorted_tools = sorted(TOOLS, key=lambda x: x[0])
            self.load_tools(sorted_tools)
        else:
            self.sort_var.set("Default")
            self.load_tools(TOOLS)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.scroll_window, width=self.canvas.winfo_width())
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _on_search(self, *args):
        query = self.search_var.get().lower()
        if not query:
            self.current_tools = TOOLS
        else:
            self.current_tools = [t for t in TOOLS if query in t[0].lower() or query in t[3].lower()]
        
        if self.sort_var.get() == "A-Z":
            self.load_tools(sorted(self.current_tools, key=lambda x: x[0]))
        else:
            self.load_tools(self.current_tools)
    
    def load_tools(self, tools_list):
        # Update count
        self.count_label.configure(text=f"Showing: {len(tools_list)} / {len(TOOLS)}")
        
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        # Grid layout
        columns = 5
        for i, tool in enumerate(tools_list):
            name, script, icon, desc = tool
            
            # Card Frame
            card = tk.Frame(self.scroll_frame, bg=self.theme["card_bg"], 
                            highlightbackground=self.theme["card_border"], 
                            highlightthickness=1, padx=10, pady=10)
            card.grid(row=i//columns, column=i%columns, padx=8, pady=8, sticky="nsew")
            self.scroll_frame.grid_columnconfigure(i%columns, weight=1)
            
            # Icon
            tk.Label(card, text=icon, font=("Segoe UI", 24), 
                     bg=self.theme["card_bg"], fg=self.theme["accent"]).pack(pady=(0, 5))
            
            # Name
            tk.Label(card, text=name, font=("Segoe UI", 11, "bold"),
                     bg=self.theme["card_bg"], fg=self.theme["fg"]).pack()
            
            # Description
            tk.Label(card, text=desc, font=("Segoe UI", 9),
                     bg=self.theme["card_bg"], fg="gray", wraplength=140).pack(pady=(2, 10))
            
            # Launch Button
            btn = ttk.Button(card, text="Open", command=lambda s=script: self.launch_tool(s))
            btn.pack(fill="x")
            
            # Hover effect
            card.bind("<Enter>", lambda e, c=card: c.config(bg=self.theme["bg"]))
            card.bind("<Leave>", lambda e, c=card: c.config(bg=self.theme["card_bg"]))

    def launch_tool(self, script_name):
        script_path = Path(__file__).parent / script_name
        if script_path.exists():
            subprocess.Popen([sys.executable, str(script_path)])
        else:
            print(f"File not found: {script_path}")

if __name__ == "__main__":
    app = LauncherApp()
    app.root.mainloop()
