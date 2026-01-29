"""
FFmpeg Concat Tool
Concatenate multiple video files
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ffmpeg_common import (
    FFmpegToolApp, get_binary, get_media_duration, format_duration,
    browse_file, browse_save_file, create_card, get_theme, TEMP_DIR
)

class ConcatApp(FFmpegToolApp):
    """Video concatenation tool."""
    
    def __init__(self):
        super().__init__("FFmpeg Concat Videos", width=650, height=600)
        self.video_list = []
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # === Video List ===
        list_card = create_card(main_frame, "📁 Video Files (in order)")
        list_card.pack(fill="x", pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(list_card)
        list_frame.pack(fill="x", pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=6, selectmode=tk.SINGLE)
        self.listbox.pack(side="left", fill="x", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # List buttons
        btn_row = ttk.Frame(list_card)
        btn_row.pack(fill="x", pady=5)
        
        ttk.Button(btn_row, text="➕ Add", command=self._add_file).pack(side="left", padx=2)
        ttk.Button(btn_row, text="➖ Remove", command=self._remove_file).pack(side="left", padx=2)
        ttk.Button(btn_row, text="⬆️ Move Up", command=self._move_up).pack(side="left", padx=2)
        ttk.Button(btn_row, text="⬇️ Move Down", command=self._move_down).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🗑️ Clear", command=self._clear_list).pack(side="left", padx=2)
        
        # Total duration
        self.total_label = ttk.Label(list_card, text="Total: 0 files, 00:00:00")
        self.total_label.pack(anchor="w")
        
        # === Concat Options ===
        options_card = create_card(main_frame, "⚙️ Options")
        options_card.pack(fill="x", pady=(0, 10))
        
        # Method
        method_row = ttk.Frame(options_card)
        method_row.pack(fill="x", pady=5)
        
        ttk.Label(method_row, text="Method:").pack(side="left")
        self.method_var = tk.StringVar(value="demuxer")
        method_combo = ttk.Combobox(method_row, textvariable=self.method_var, width=15,
                                    values=["demuxer", "filter"])
        method_combo.pack(side="left", padx=5)
        
        ttk.Label(options_card, text="• demuxer: Fast, requires same codec (uses concat protocol)",
                  foreground="gray").pack(anchor="w")
        ttk.Label(options_card, text="• filter: Slower, works with different formats",
                  foreground="gray").pack(anchor="w")
        
        # Re-encode option
        self.reencode = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_card, text="Re-encode output (for filter method)",
                        variable=self.reencode).pack(anchor="w", pady=5)
        
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
        self.run_btn = ttk.Button(btn_frame, text="🔗 Concatenate", command=self.run_concat)
        self.run_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_command).pack(side="left", padx=5)
        
        # === Bottom Section ===
        bottom = self.create_bottom_section(main_frame)
        bottom.pack(fill="both", expand=True)
    
    def _add_file(self):
        from tkinter import filedialog
        filetypes = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(filetypes=filetypes)
        for f in files:
            self.video_list.append(f)
            self.listbox.insert(tk.END, Path(f).name)
        self._update_total()
    
    def _remove_file(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.listbox.delete(idx)
            del self.video_list[idx]
            self._update_total()
    
    def _move_up(self):
        sel = self.listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            # Swap in list
            self.video_list[idx], self.video_list[idx-1] = self.video_list[idx-1], self.video_list[idx]
            # Swap in listbox
            text = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx-1, text)
            self.listbox.selection_set(idx-1)
    
    def _move_down(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.video_list) - 1:
            idx = sel[0]
            # Swap in list
            self.video_list[idx], self.video_list[idx+1] = self.video_list[idx+1], self.video_list[idx]
            # Swap in listbox
            text = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx+1, text)
            self.listbox.selection_set(idx+1)
    
    def _clear_list(self):
        self.listbox.delete(0, tk.END)
        self.video_list.clear()
        self._update_total()
    
    def _update_total(self):
        total_dur = 0
        for f in self.video_list:
            dur = get_media_duration(f)
            if dur:
                total_dur += dur
        self.total_label.configure(text=f"Total: {len(self.video_list)} files, {format_duration(total_dur)}")
    
    def _browse_output(self):
        filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
        browse_save_file(self.output_entry, filetypes, ".mp4")
    
    def _create_concat_file(self):
        """Create concat demuxer file list."""
        concat_file = TEMP_DIR / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for video in self.video_list:
                # Escape single quotes
                escaped = video.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
        return str(concat_file)
    
    def build_command(self) -> list:
        if len(self.video_list) < 2:
            return None
        
        output_path = self.output_entry.get()
        if not output_path:
            return None
        
        method = self.method_var.get()
        
        if method == "demuxer":
            concat_file = self._create_concat_file()
            cmd = [get_binary("ffmpeg"), "-y", "-f", "concat", "-safe", "0",
                   "-i", concat_file]
            if not self.reencode.get():
                cmd.extend(["-c", "copy"])
            else:
                cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        else:
            # Filter concat
            cmd = [get_binary("ffmpeg"), "-y"]
            for video in self.video_list:
                cmd.extend(["-i", video])
            
            # Build filter complex
            n = len(self.video_list)
            inputs = "".join([f"[{i}:v][{i}:a]" for i in range(n)])
            filter_complex = f"{inputs}concat=n={n}:v=1:a=1[outv][outa]"
            cmd.extend(["-filter_complex", filter_complex])
            cmd.extend(["-map", "[outv]", "-map", "[outa]"])
            cmd.extend(["-c:v", "libx264", "-crf", "23", "-c:a", "aac"])
        
        cmd.append(output_path)
        return cmd
    
    def preview_command(self):
        cmd = self.build_command()
        if cmd:
            self.set_preview(cmd)
        else:
            messagebox.showwarning("Missing Input", "Please add at least 2 videos and set output.")
    
    def run_concat(self):
        cmd = self.build_command()
        if not cmd:
            messagebox.showwarning("Missing Input", "Please add at least 2 videos and set output.")
            return
        
        self.set_preview(cmd)
        self.run_command(cmd, self.video_list[0] if self.video_list else None)


if __name__ == "__main__":
    app = ConcatApp()
    app.run()
