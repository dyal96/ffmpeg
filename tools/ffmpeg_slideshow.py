"""
FFmpeg Slideshow Tool
Create slideshow video from images
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary,
    browse_file, browse_save_file, create_card, get_theme, TEMP_DIR
)

class SlideshowApp(FFmpegToolApp):
    """Image slideshow creator."""
    
    def __init__(self):
        super().__init__("FFmpeg Slideshow", width=650, height=620)
        self.image_list = []
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Image List ===
        list_card = create_card(main_frame, "🖼️ Images (in order)")
        list_card.pack(fill="x", pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(list_card)
        list_frame.pack(fill="x", pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=5, selectmode=tk.SINGLE)
        self.listbox.pack(side="left", fill="x", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # List buttons
        btn_row = ttk.Frame(list_card)
        btn_row.pack(fill="x", pady=5)
        
        ttk.Button(btn_row, text="➕ Add", command=self._add_images).pack(side="left", padx=2)
        ttk.Button(btn_row, text="➖ Remove", command=self._remove_image).pack(side="left", padx=2)
        ttk.Button(btn_row, text="⬆️ Up", command=self._move_up).pack(side="left", padx=2)
        ttk.Button(btn_row, text="⬇️ Down", command=self._move_down).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🗑️ Clear", command=self._clear_list).pack(side="left", padx=2)
        
        self.count_label = ttk.Label(list_card, text="0 images")
        self.count_label.pack(anchor="w")
        
        # === Slideshow Settings ===
        settings_card = create_card(main_frame, "⚙️ Slideshow Settings")
        settings_card.pack(fill="x", pady=(0, 10))
        
        # Duration per image
        dur_row = ttk.Frame(settings_card)
        dur_row.pack(fill="x", pady=5)
        
        ttk.Label(dur_row, text="Duration per image:").pack(side="left")
        self.duration_var = tk.DoubleVar(value=3.0)
        dur_spin = ttk.Spinbox(dur_row, from_=0.5, to=30, increment=0.5, width=6,
                               textvariable=self.duration_var)
        dur_spin.pack(side="left", padx=5)
        ttk.Label(dur_row, text="seconds").pack(side="left")
        
        # Resolution
        res_row = ttk.Frame(settings_card)
        res_row.pack(fill="x", pady=5)
        
        ttk.Label(res_row, text="Resolution:").pack(side="left")
        self.resolution_var = tk.StringVar(value="1920x1080")
        res_combo = ttk.Combobox(res_row, textvariable=self.resolution_var, width=12,
                                 values=["1920x1080", "1280x720", "3840x2160", "1080x1920"])
        res_combo.pack(side="left", padx=5)
        
        # FPS
        fps_row = ttk.Frame(settings_card)
        fps_row.pack(fill="x", pady=5)
        
        ttk.Label(fps_row, text="FPS:").pack(side="left")
        self.fps_var = tk.IntVar(value=30)
        fps_combo = ttk.Combobox(fps_row, textvariable=self.fps_var, width=6,
                                 values=[24, 25, 30, 60])
        fps_combo.pack(side="left", padx=5)
        
        # Transition
        trans_row = ttk.Frame(settings_card)
        trans_row.pack(fill="x", pady=5)
        
        ttk.Label(trans_row, text="Transition:").pack(side="left")
        self.transition_var = tk.StringVar(value="none")
        trans_combo = ttk.Combobox(trans_row, textvariable=self.transition_var, width=12,
                                   values=["none", "fade", "dissolve"])
        trans_combo.pack(side="left", padx=5)
        
        # === Audio (optional) ===
        audio_card = create_card(main_frame, "🎵 Background Audio (optional)")
        audio_card.pack(fill="x", pady=(0, 10))
        
        audio_row = ttk.Frame(audio_card)
        audio_row.pack(fill="x")
        
        ttk.Label(audio_row, text="Audio:").pack(side="left")
        self.audio_entry = ttk.Entry(audio_row, width=50)
        self.audio_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(audio_row, text="Browse", command=self._browse_audio).pack(side="left")
        
        self.loop_audio = tk.BooleanVar(value=True)
        ttk.Checkbutton(audio_card, text="Loop audio to match video length",
                        variable=self.loop_audio).pack(anchor="w", pady=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="🎬 Create", command=self.run_slideshow)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _add_images(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(filetypes=filetypes)
        for f in files:
            self.image_list.append(f)
            self.listbox.insert(tk.END, Path(f).name)
        self.count_label.configure(text=f"{len(self.image_list)} images")
    
    def _remove_image(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.listbox.delete(idx)
            del self.image_list[idx]
            self.count_label.configure(text=f"{len(self.image_list)} images")
    
    def _move_up(self):
        sel = self.listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            self.image_list[idx], self.image_list[idx-1] = self.image_list[idx-1], self.image_list[idx]
            text = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx-1, text)
            self.listbox.selection_set(idx-1)
    
    def _move_down(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.image_list) - 1:
            idx = sel[0]
            self.image_list[idx], self.image_list[idx+1] = self.image_list[idx+1], self.image_list[idx]
            text = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx+1, text)
            self.listbox.selection_set(idx+1)
    
    def _clear_list(self):
        self.listbox.delete(0, tk.END)
        self.image_list.clear()
        self.count_label.configure(text="0 images")
    
    def _browse_audio(self):
        filetypes = [("Audio files", "*.mp3 *.aac *.wav *.flac"), ("All files", "*.*")]
        browse_file(self.audio_entry, filetypes)
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _create_image_list_file(self):
        """Create concat file for images."""
        list_file = TEMP_DIR / "slideshow_list.txt"
        duration = self.duration_var.get()
        with open(list_file, "w", encoding="utf-8") as f:
            for img in self.image_list:
                escaped = img.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
                f.write(f"duration {duration}\n")
            # Add last image again (for proper duration)
            if self.image_list:
                f.write(f"file '{self.image_list[-1]}'\n")
        return str(list_file)
    
    def build_command(self) -> list:
        if len(self.image_list) < 1:
            return None
        
        output_path = self.output_entry.get()
        if not output_path:
            return None
        
        resolution = self.resolution_var.get()
        fps = self.fps_var.get()
        
        # Create image list file
        list_file = self._create_image_list_file()
        
        cmd = [get_binary("ffmpeg"), "-y", "-f", "concat", "-safe", "0",
               "-i", list_file]
        
        # Add audio if specified
        audio_path = self.audio_entry.get()
        if audio_path:
            if self.loop_audio.get():
                cmd.extend(["-stream_loop", "-1"])
            cmd.extend(["-i", audio_path])
        
        # Video filter for scaling
        w, h = resolution.split("x")
        vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        cmd.extend(["-vf", vf])
        
        cmd.extend(["-c:v", "libx264", "-crf", "23", "-r", str(fps)])
        cmd.extend(["-pix_fmt", "yuv420p"])
        
        if audio_path:
            total_duration = len(self.image_list) * self.duration_var.get()
            cmd.extend(["-c:a", "aac", "-shortest", "-t", str(total_duration)])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please add images and set output.")
    
    def run_slideshow(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please add images and set output.")
            return
        
        self.set_preview(cmd)
        # Total duration based on image count
        duration = len(self.image_list) * self.duration_var.get()
        self.run_command(cmd, None, total_duration=duration)


if __name__ == "__main__":
    app = SlideshowApp()
    app.run()
