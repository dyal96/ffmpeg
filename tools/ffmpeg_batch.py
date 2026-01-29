"""
FFmpeg Batch Processor Tool
Apply FFmpeg operations to multiple files at once
"""

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import threading
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, create_card, browse_folder, get_binary, get_theme, ensure_dir
)

# Preset operations
OPERATIONS = {
    "Convert to MP4 (H.264)": ["-c:v", "libx264", "-crf", "23", "-c:a", "aac"],
    "Convert to WebM (VP9)": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-c:a", "libopus"],
    "Compress (CRF 28)": ["-c:v", "libx264", "-crf", "28", "-preset", "medium", "-c:a", "copy"],
    "Extract Audio (MP3)": ["-vn", "-c:a", "libmp3lame", "-q:a", "2"],
    "Extract Audio (AAC)": ["-vn", "-c:a", "aac", "-b:a", "192k"],
    "Resize 720p": ["-vf", "scale=-2:720", "-c:v", "libx264", "-crf", "23", "-c:a", "copy"],
    "Resize 1080p": ["-vf", "scale=-2:1080", "-c:v", "libx264", "-crf", "23", "-c:a", "copy"],
    "Remove Audio": ["-an", "-c:v", "copy"],
    "Custom...": []
}

class BatchTool(FFmpegToolApp):
    def __init__(self):
        super().__init__("Batch Processor", 700, 650)
        self.input_files = []
        self.processing = False
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Input Section
        input_card = create_card(self.root, "📂 Input Files")
        input_card.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ttk.Frame(input_card)
        btn_frame.pack(fill="x", pady=2)
        
        ttk.Button(btn_frame, text="➕ Add Files", command=self.add_files).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📁 Add Folder", command=self.add_folder).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Clear", command=self.clear_files).pack(side="left", padx=2)
        
        self.file_list = tk.Listbox(input_card, height=6, selectmode="extended")
        scrollbar = ttk.Scrollbar(input_card, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.file_list.pack(fill="x", pady=5)
        
        self.count_label = ttk.Label(input_card, text="0 files selected")
        self.count_label.pack(anchor="w")
        
        # Operation Section
        op_card = create_card(self.root, "⚙️ Operation")
        op_card.pack(fill="x", padx=10, pady=5)
        
        op_row = ttk.Frame(op_card)
        op_row.pack(fill="x", pady=5)
        
        ttk.Label(op_row, text="Preset:").pack(side="left")
        self.op_var = tk.StringVar(value="Convert to MP4 (H.264)")
        op_combo = ttk.Combobox(op_row, textvariable=self.op_var, 
                                 values=list(OPERATIONS.keys()), state="readonly", width=30)
        op_combo.pack(side="left", padx=5)
        op_combo.bind("<<ComboboxSelected>>", self._on_op_change)
        
        # Custom command
        custom_row = ttk.Frame(op_card)
        custom_row.pack(fill="x", pady=5)
        
        ttk.Label(custom_row, text="Custom Args:").pack(side="left")
        self.custom_entry = ttk.Entry(custom_row, state="disabled")
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Output Settings
        out_card = create_card(self.root, "💾 Output Settings")
        out_card.pack(fill="x", padx=10, pady=5)
        
        out_row = ttk.Frame(out_card)
        out_row.pack(fill="x", pady=5)
        
        ttk.Label(out_row, text="Output Folder:").pack(side="left")
        self.out_entry = ttk.Entry(out_row)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(out_row, text="Browse", command=lambda: browse_folder(self.out_entry)).pack(side="left")
        
        ext_row = ttk.Frame(out_card)
        ext_row.pack(fill="x", pady=5)
        
        ttk.Label(ext_row, text="Output Extension:").pack(side="left")
        self.ext_var = tk.StringVar(value=".mp4")
        ext_combo = ttk.Combobox(ext_row, textvariable=self.ext_var, 
                                  values=[".mp4", ".mkv", ".webm", ".avi", ".mov", ".mp3", ".aac", ".wav"],
                                  width=10)
        ext_combo.pack(side="left", padx=5)
        
        self.suffix_var = tk.StringVar(value="_batch")
        ttk.Label(ext_row, text="Suffix:").pack(side="left", padx=(10, 0))
        ttk.Entry(ext_row, textvariable=self.suffix_var, width=10).pack(side="left", padx=5)
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        self.run_btn = ttk.Button(actions, text="▶ Process All", command=self.run_batch)
        self.run_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(actions, text="⏹ Stop", command=self.stop_batch, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Bottom section
        self.create_bottom_section(self.root)
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Media files", "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.mp3;*.wav;*.flac"), ("All", "*.*")]
        )
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
                self.file_list.insert(tk.END, os.path.basename(f))
        self._update_count()
    
    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            exts = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".flac")
            for f in Path(folder).iterdir():
                if f.is_file() and f.suffix.lower() in exts:
                    fp = str(f)
                    if fp not in self.input_files:
                        self.input_files.append(fp)
                        self.file_list.insert(tk.END, f.name)
        self._update_count()
    
    def clear_files(self):
        self.input_files.clear()
        self.file_list.delete(0, tk.END)
        self._update_count()
    
    def _update_count(self):
        self.count_label.config(text=f"{len(self.input_files)} files selected")
    
    def _on_op_change(self, event=None):
        if self.op_var.get() == "Custom...":
            self.custom_entry.config(state="normal")
        else:
            self.custom_entry.config(state="disabled")
    
    def run_batch(self):
        if not self.input_files:
            tk.messagebox.showerror("Error", "No files selected.")
            return
        
        output_folder = self.out_entry.get()
        if not output_folder:
            tk.messagebox.showerror("Error", "Please select an output folder.")
            return
        
        ensure_dir(Path(output_folder))
        
        self.processing = True
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        threading.Thread(target=self._process_batch, args=(output_folder,), daemon=True).start()
    
    def _process_batch(self, output_folder):
        op_name = self.op_var.get()
        if op_name == "Custom...":
            extra_args = self.custom_entry.get().split()
        else:
            extra_args = OPERATIONS.get(op_name, [])
        
        ext = self.ext_var.get()
        suffix = self.suffix_var.get()
        total = len(self.input_files)
        
        for i, input_file in enumerate(self.input_files):
            if not self.processing:
                break
            
            name = Path(input_file).stem
            out_file = str(Path(output_folder) / f"{name}{suffix}{ext}")
            
            cmd = [get_binary("ffmpeg"), "-y", "-i", input_file] + extra_args + [out_file]
            
            self._on_log(f"\n[{i+1}/{total}] Processing: {os.path.basename(input_file)}\n")
            self._on_log(f"$ {' '.join(cmd)}\n")
            
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
                if result.returncode != 0:
                    self._on_log(f"Error: {result.stderr[-500:]}\n")
                else:
                    self._on_log("✓ Done\n")
            except Exception as e:
                self._on_log(f"Failed: {e}\n")
            
            # Update progress
            percent = int((i + 1) / total * 100)
            self.root.after(0, lambda p=percent: self.progress_bar.configure(value=p))
        
        self.root.after(0, self._batch_complete)
    
    def _batch_complete(self):
        self.processing = False
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        tk.messagebox.showinfo("Complete", "Batch processing finished!")
    
    def stop_batch(self):
        self.processing = False
        self._on_log("\n⏹ Stopping...\n")

if __name__ == "__main__":
    app = BatchTool()
    app.run()
