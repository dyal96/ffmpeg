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
    ("Convert", "ffmpeg_convert.py", "🔄", "Convert video formats", "quick"),
    ("Compress", "ffmpeg_compress.py", "📉", "Reduce file size", "quick"),
    ("Trim/Cut", "ffmpeg_trim.py", "✂️", "Cut video segments", "quick"),
    ("Join Clips", "ffmpeg_concat.py", "🎞️", "Combine multiple videos", "quick"),
    ("Merge A+V", "ffmpeg_merge.py", "➕", "Combine audio & video", "quick"),
    ("Extract Audio", "ffmpeg_extract_audio.py", "🎵", "Get mp3/aac from video", "quick"),
    ("Resize", "ffmpeg_resize.py", "📏", "Change resolution", "quick"),
    ("Crop", "ffmpeg_crop.py", "🖼️", "Crop video area", "quick"),
    ("Rotate/Flip", "ffmpeg_rotate.py", "cw", "Rotate or flip video", "quick"),
    
    # Advanced
    ("Stabilize", "ffmpeg_stabilize.py", "⚖️", "Remove shake", "advanced"),
    ("Reverse", "ffmpeg_reverse.py", "⏪", "Play backwards", "advanced"),
    ("Speed/Slow", "ffmpeg_speed.py", "⏩", "Change playback speed", "advanced"),
    ("Watermark", "ffmpeg_watermark.py", "©️", "Add logo/text", "advanced"),
    ("Subtitles", "ffmpeg_subtitles.py", "📝", "Burn/Extract subs", "advanced"),
    ("Slideshow", "ffmpeg_slideshow.py", "🎞️", "Photos to video", "advanced"),
    ("Thumbnail", "ffmpeg_thumbnail.py", "📸", "Extract image", "advanced"),
    ("Video Info", "ffmpeg_info.py", "ℹ️", "Get metadata", "advanced"),
    ("Metadata", "ffmpeg_metadata.py", "🏷️", "Edit tags", "advanced"),
    ("Denoise", "ffmpeg_denoise.py", "🔇", "Remove noise", "advanced"),
    ("Sharpen", "ffmpeg_sharpen.py", "🔪", "Enhance details", "advanced"),
    ("Vibrance", "ffmpeg_color.py", "🎨", "Adjust colors", "advanced"),
    ("Fade In/Out", "ffmpeg_fade.py", "⬛", "Add fades", "advanced"),
    ("Normalize", "ffmpeg_normalize.py", "🔊", "Fix audio volume", "advanced"),
    ("Delogo", "ffmpeg_delogo.py", "🧼", "Remove logo", "advanced"),
    ("PIP", "ffmpeg_pip.py", "🖼️", "Picture in Picture", "advanced"),
    ("GIF", "ffmpeg_gif.py", "👾", "Video to GIF", "advanced"),
    ("Split", "ffmpeg_splitter.py", "➗", "Split into parts", "advanced"),
    ("Web Optimize", "ffmpeg_webopt.py", "🌐", "Web streaming", "advanced"),
    ("Interpolate", "ffmpeg_interpolate.py", "🔄", "Frame interpolation", "advanced"),
    ("Loop", "ffmpeg_loop.py", "🔁", "Loop video", "advanced"),
    ("Record Screen", "ffmpeg_recorder.py", "⏺️", "Screen capture", "advanced"),
    ("Grid Video", "ffmpeg_grid.py", "▦", "Video collage", "advanced"),
    ("Social Media", "ffmpeg_social.py", "📱", "Aspect ratio convert", "advanced"),
    ("Smart Cut", "ffmpeg_smartcut.py", "🔇", "Remove silence", "advanced"),
    ("Scene Detect", "ffmpeg_scenedetect.py", "🎬", "Detect scene changes", "advanced"),
    ("LUT Apply", "ffmpeg_lut.py", "🎨", "Apply 3D LUTs", "advanced"),
    ("Tonemap", "ffmpeg_tonemap.py", "☀️", "HDR to SDR", "advanced"),
    ("Visualizer", "ffmpeg_visualizer.py", "🎵", "Audio visualization", "advanced"),
    ("Mosaic", "ffmpeg_mosaic.py", "🔲", "Blur region", "advanced"),
    ("Img to Video", "ffmpeg_img2video.py", "🖼️", "Image to video", "advanced"),
    
    # Utilities
    ("Web File Browser", "webui.py", "🌐", "Browser file manager", "utility"),
    ("Bitrate Calc", "ffmpeg_bitratecalc.py", "🧮", "Calculate bitrate", "utility"),
    ("Stream Map", "ffmpeg_streammapper.py", "🗺️", "Map streams", "utility"),
    ("Video Scopes", "ffmpeg_scopes.py", "📊", "Video analysis", "utility"),
    
    # System
    ("Hardware Check", "ffmpeg_hwcheck.py", "🚀", "Configure GPU", "system"),
    ("Batch", "ffmpeg_batch.py", "📦", "Batch process", "system"),
    ("YouTube DL", "ffmpeg_ytdl.py", "⬇️", "Download videos", "system"),
    ("Audio Sync", "ffmpeg_audiosync.py", "🔊", "Sync audio/video", "system"),
    ("Proxy", "ffmpeg_proxy.py", "📹", "Generate proxies", "system"),
    ("Watch Folder", "ffmpeg_watchfolder.py", "👁️", "Auto-process folder", "system"),
    ("Temp Clean", "ffmpeg_tempcleaner.py", "🧹", "Clean temp files", "system"),
    ("Dependency Manager", "ffmpeg_dependency_manager.py", "🛠️", "Update FFmpeg/Tools", "system"),
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
        
        # Sort & Quick Access
        self.sort_var = tk.StringVar(value="Default")
        ttk.Button(search_frame, text="🛠️ Dependencies", command=lambda: self.launch_tool("ffmpeg_dependency_manager.py")).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Sort A-Z", command=self.toggle_sort).pack(side="left", padx=5)
        
        tk.Label(search_frame, text="🔍", bg=self.theme["bg"], fg=self.theme["fg"], font=("Segoe UI", 12)).pack(side="left", padx=(5, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left")
        
        # Categories
        cat_frame = tk.Frame(self.root, bg=self.theme["bg"])
        cat_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.cats = ["All", "Quick", "Advanced", "Utility", "System"]
        self.cat_var = tk.StringVar(value="All")
        
        for cat in self.cats:
            # Simple button style for categories
            btn = tk.Radiobutton(cat_frame, text=cat, variable=self.cat_var, value=cat,
                                indicatoron=0, command=self.refresh_tools,
                                bg=self.theme["card_bg"], fg=self.theme["fg"],
                                selectcolor=self.theme["accent"], font=("Segoe UI", 10),
                                padx=15, pady=5, borderwidth=0)
            btn.pack(side="left", padx=5)
        
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
        self.refresh_tools()
        
    def toggle_sort(self):
        if self.sort_var.get() == "Default":
            self.sort_var.set("A-Z")
            sorted_tools = sorted(TOOLS, key=lambda x: x[0])
            self.refresh_tools()
        else:
            self.sort_var.set("Default")
            self.refresh_tools()

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
            # Just trigger refresh, it handles sorting
            self.refresh_tools()
        else:
            self.refresh_tools()
    
    def refresh_tools(self):
        cat = self.cat_var.get()
        query = self.search_var.get().lower()
        
        filtered = TOOLS
        
        # Filter by Category
        if cat != "All":
            filtered = [t for t in filtered if t[4] == cat.lower()]
            
        # Filter by Search
        if query:
            filtered = [t for t in filtered if query in t[0].lower() or query in t[3].lower()]
            
        # Sort
        if self.sort_var.get() == "A-Z":
            filtered = sorted(filtered, key=lambda x: x[0])
            
        self.current_tools = filtered
        self.load_tools(filtered)

    def load_tools(self, tools_list):
        # Update count
        self.count_label.configure(text=f"Showing: {len(tools_list)} / {len(TOOLS)}")
        
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        # Grid layout
        columns = 5
        
        # If "All" is selected and no search, group by category
        if self.cat_var.get() == "All" and not self.search_var.get() and self.sort_var.get() == "Default":
            row = 0
            for cat_display in ["Quick", "Advanced", "Utility", "System"]:
                cat_tools = [t for t in tools_list if t[4] == cat_display.lower()]
                if not cat_tools: continue
                
                # Header
                tk.Label(self.scroll_frame, text=f"  {cat_display} Tools", 
                         bg=self.theme["bg"], fg=self.theme["accent"], 
                         font=("Segoe UI", 14, "bold"), anchor="w").grid(row=row, column=0, columnspan=columns, sticky="w", pady=(20, 10))
                row += 1
                
                # Grid for this category
                for i, tool in enumerate(cat_tools):
                    self.create_tool_card(tool, row + i//columns, i%columns)
                
                row += (len(cat_tools) - 1) // columns + 1
        else:
            # Flat grid
            for i, tool in enumerate(tools_list):
                self.create_tool_card(tool, i//columns, i%columns)
    
    def create_tool_card(self, tool, r, c):
        name, script, icon, desc, cat = tool
        
        # Card Frame
        card = tk.Frame(self.scroll_frame, bg=self.theme["card_bg"], 
                        highlightbackground=self.theme["card_border"], 
                        highlightthickness=1, padx=10, pady=10)
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(c, weight=1)
        
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
