"""
FFmpeg Delogo Tool
Remove logos/watermarks from video
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import os
import subprocess

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    generate_output_path, browse_file, browse_save_file, create_card, get_theme, TEMP_DIR
)

class DelogoApp(FFmpegToolApp):
    """Logo/watermark removal tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Delogo", width=600, height=560)
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
        
        # === Delogo Region ===
        region_card = create_card(main_frame, "🎯 Logo Region (pixels)")
        region_card.pack(fill="x", pady=(0, 10))
        
        # Tools Row
        tools_row = ttk.Frame(region_card)
        tools_row.pack(fill="x", pady=(0, 5))
        ttk.Button(tools_row, text="Select Area via Visual Selector", command=self._open_selector).pack(side="left")
        
        # Position
        pos_row = ttk.Frame(region_card)
        pos_row.pack(fill="x", pady=5)
        
        ttk.Label(pos_row, text="X:").pack(side="left")
        self.x_entry = ttk.Entry(pos_row, width=8)
        self.x_entry.insert(0, "10")
        self.x_entry.pack(side="left", padx=5)
        
        ttk.Label(pos_row, text="Y:").pack(side="left", padx=(20, 0))
        self.y_entry = ttk.Entry(pos_row, width=8)
        self.y_entry.insert(0, "10")
        self.y_entry.pack(side="left", padx=5)
        
        # Size
        size_row = ttk.Frame(region_card)
        size_row.pack(fill="x", pady=5)
        
        ttk.Label(size_row, text="Width:").pack(side="left")
        self.w_entry = ttk.Entry(size_row, width=8)
        self.w_entry.insert(0, "100")
        self.w_entry.pack(side="left", padx=5)
        
        ttk.Label(size_row, text="Height:").pack(side="left", padx=(20, 0))
        self.h_entry = ttk.Entry(size_row, width=8)
        self.h_entry.insert(0, "50")
        self.h_entry.pack(side="left", padx=5)
        
        # Presets for common positions
        preset_row = ttk.Frame(region_card)
        preset_row.pack(fill="x", pady=5)
        
        ttk.Label(preset_row, text="Presets:").pack(side="left")
        presets = [
            ("Top-Left", 10, 10),
            ("Top-Right", -110, 10),
            ("Bottom-Left", 10, -60),
            ("Bottom-Right", -110, -60)
        ]
        for name, x, y in presets:
            btn = ttk.Button(preset_row, text=name, width=10,
                           command=lambda px=x, py=y: self._set_preset(px, py))
            btn.pack(side="left", padx=2)
        
        ttk.Label(region_card, text="💡 Tip: Use ffplay to find exact coordinates",
                  foreground="gray").pack(anchor="w", pady=(10, 0))
        
        # === Options ===
        options_card = create_card(main_frame, "⚙️ Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        self.show_region = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="Show region outline (for testing)",
                        variable=self.show_region).pack(anchor="w")
        
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
        
        ttk.Button(btn_frame, text="📋 Command Preview", command=self.preview_command).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="▶️ Live Preview (ffplay)", command=self.run_live_preview).pack(side="left", padx=5)
        self.run_btn = ttk.Button(btn_frame, text="🎯 Remove Logo", command=self.run_delogo)
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
            
            output_path = generate_output_path(input_path, "_delogo")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _open_selector(self):
        input_path = self.input_entry.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input video first.")
            return
            
        # Dialog to pick coords
        dialog = FrameSelectorDialog(self.root, input_path)
        self.root.wait_window(dialog)
        
        if dialog.result:
            x, y, w, h = dialog.result
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))
            self.w_entry.delete(0, tk.END)
            self.w_entry.insert(0, str(w))
            self.h_entry.delete(0, tk.END)
            self.h_entry.insert(0, str(h))

    def _set_preset(self, x, y):
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(x) if x >= 0 else f"iw{x}")
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(y) if y >= 0 else f"ih{y}")

    def run_live_preview(self):
        """Run ffplay with current settings."""
        input_path = self.input_entry.get()
        if not input_path:
            return
            
        x = self.x_entry.get().strip()
        y = self.y_entry.get().strip()
        w = self.w_entry.get().strip()
        h = self.h_entry.get().strip()
        
        if self.show_region.get():
             vf = f"drawbox=x={x}:y={y}:w={w}:h={h}:c=red:t=2"
        else:
             vf = f"delogo=x={x}:y={y}:w={w}:h={h}"
             
        # ffplay command
        cmd = [get_binary("ffplay"), "-window_title", "Delogo Preview", 
               "-vf", vf, "-t", "10", "-autoexit", input_path]
               
        self.run_command(cmd)
    
    def build_command(self) -> list:
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        
        if not input_path or not output_path:
            return None
        
        x = self.x_entry.get().strip()
        y = self.y_entry.get().strip()
        w = self.w_entry.get().strip()
        h = self.h_entry.get().strip()
        
        cmd = [get_binary("ffmpeg"), "-y", "-i", input_path]
        
        if self.show_region.get():
            # Draw rectangle instead of delogo (for testing)
            vf = f"drawbox=x={x}:y={y}:w={w}:h={h}:c=red:t=2"
        else:
            vf = f"delogo=x={x}:y={y}:w={w}:h={h}"
        
        cmd.extend(["-vf", vf])
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "copy"])
        cmd.append(output_path)
        
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
    
    def run_delogo(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please select input and output files.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.input_entry.get())




try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class FrameSelectorDialog(tk.Toplevel):
    def __init__(self, parent, video_path):
        super().__init__(parent)
        self.title("Select Area")
        self.geometry("1000x700")
        self.result = None
        
        self.video_path = video_path
        self.temp_image_path = TEMP_DIR / "delogo_preview.png"
        
        # State
        self.pil_image = None  # Original PIL image
        self.tk_image = None   # Current displayed ImageTk
        self.scale = 1.0       # Current zoom level
        self.rect_coords = None # (x1, y1, x2, y2) in ORIGINAL image coordinates
        
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow (PIL) library is required for this feature.")
            self.destroy()
            return

        self.extract_frame()
        self.build_ui()
        
        # After UI is built and window is shown, fit to screen
        self.after(100, self.fit_to_window)
        
    def extract_frame(self, time="5"):
        # Extract frame
        if self.temp_image_path.exists():
            try: os.remove(self.temp_image_path)
            except: pass
            
        cmd = [get_binary("ffmpeg"), "-y", "-ss", str(time), "-i", self.video_path, 
               "-vframes", "1", str(self.temp_image_path)]
        subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
        if self.temp_image_path.exists():
            try:
                self.pil_image = Image.open(self.temp_image_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                self.pil_image = None
        else:
             messagebox.showerror("Error", "Could not extract frame.")

    def build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill="x", side="top")
        
        ttk.Label(toolbar, text="Draw Rectangle (Left Click) | Pan (Right Click) | Zoom (Wheel)").pack(side="left")
        
        # Controls
        ctrl = ttk.Frame(toolbar)
        ctrl.pack(side="right")
        
        ttk.Button(ctrl, text="Fit Screen", command=self.fit_to_window).pack(side="left", padx=2)
        ttk.Button(ctrl, text="-", width=3, command=lambda: self.zoom(0.8)).pack(side="left", padx=2)
        ttk.Button(ctrl, text="+", width=3, command=lambda: self.zoom(1.2)).pack(side="left", padx=2)
        ttk.Button(ctrl, text="Reset Selection", command=self.reset_selection).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Confirm", style="Accent.TButton", command=self.confirm).pack(side="left", padx=5)
        
        # Canvas
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient="horizontal")
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient="vertical")
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#222",
                                xscrollcommand=self.h_scroll.set, 
                                yscrollcommand=self.v_scroll.set,
                                highlightthickness=0)
        
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)
        
        self.h_scroll.pack(side="bottom", fill="x")
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Events
        self.canvas.bind("<ButtonPress-1>", self.on_draw_start)
        self.canvas.bind("<B1-Motion>", self.on_draw_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_draw_end)
        
        # Pan
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start)
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        # Mousewheel
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        # Windows/Linux difference support for wheel? usually <MouseWheel> works on windows.
        
        self.draw_rect_id = None
    
    def fit_to_window(self):
        if not self.pil_image: return
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw, ih = self.pil_image.size
        
        if cw > 10 and ch > 10:
            scale_w = cw / iw
            scale_h = ch / ih
            self.scale = min(scale_w, scale_h) * 0.95 # Slight padding
            self.redraw()
            # Center it
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)

    def zoom(self, factor):
        self.scale *= factor
        self.redraw()
        
    def on_wheel(self, event):
        if event.delta > 0:
            self.zoom(1.1)
        else:
            self.zoom(0.9)

    def redraw(self):
        if not self.pil_image: return
        
        # Calculate new size
        nw = int(self.pil_image.width * self.scale)
        nh = int(self.pil_image.height * self.scale)
        
        if nw < 1 or nh < 1: return
        
        # Resample
        resized = self.pil_image.resize((nw, nh), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        # Provide plenty of scrollregion
        self.canvas.delete("img") # remove old
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw", tags="img")
        self.canvas.config(scrollregion=(0, 0, nw, nh))
        
        # Re-draw rectangle if exists
        self.draw_existing_rect()

    def draw_existing_rect(self):
        if self.draw_rect_id:
            self.canvas.delete(self.draw_rect_id)
        
        if self.rect_coords:
            x1, y1, x2, y2 = self.rect_coords
            # Convert to current scale
            sx1 = x1 * self.scale
            sy1 = y1 * self.scale
            sx2 = x2 * self.scale
            sy2 = y2 * self.scale
            
            self.draw_rect_id = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="red", width=2, tags="rect")

    # --- Drawing Logic ---
    def on_draw_start(self, event):
        self.start_draw_x = self.canvas.canvasx(event.x)
        self.start_draw_y = self.canvas.canvasy(event.y)
        
        if self.draw_rect_id:
            self.canvas.delete(self.draw_rect_id)
            self.draw_rect_id = None
            
        self.draw_rect_id = self.canvas.create_rectangle(
            self.start_draw_x, self.start_draw_y, self.start_draw_x, self.start_draw_y, 
            outline="red", width=2, tags="rect"
        )

    def on_draw_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.draw_rect_id, self.start_draw_x, self.start_draw_y, cur_x, cur_y)

    def on_draw_end(self, event):
        # Save coordinates in ORIGINAL image scale
        coords = self.canvas.coords(self.draw_rect_id)
        if coords:
            x1, y1, x2, y2 = coords
            # Sort
            rx1, rx2 = min(x1, x2), max(x1, x2)
            ry1, ry2 = min(y1, y2), max(y1, y2)
            
            # Convert back to original
            ox1 = int(rx1 / self.scale)
            oy1 = int(ry1 / self.scale)
            ox2 = int(rx2 / self.scale)
            oy2 = int(ry2 / self.scale)
            
            self.rect_coords = (ox1, oy1, ox2, oy2)
    
    def reset_selection(self):
        self.rect_coords = None
        if self.draw_rect_id:
            self.canvas.delete(self.draw_rect_id)
            self.draw_rect_id = None

    # --- Pan Logic ---
    def on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
    
    def on_pan_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def confirm(self):
        if not self.rect_coords:
            self.destroy()
            return
            
        x1, y1, x2, y2 = self.rect_coords
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        # Clamp to image size
        if self.pil_image:
            iw, ih = self.pil_image.size
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            if x1 + w > iw: w = iw - x1
            if y1 + h > ih: h = ih - y1
            
        self.result = (x1, y1, w, h)
        self.destroy()

if __name__ == "__main__":
    app = DelogoApp()
    app.run()
