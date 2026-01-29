"""
FFmpeg Temp Cleaner Tool
Clean temporary files created by FFmpeg tools
"""

import tkinter as tk
from tkinter import ttk
import shutil
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import create_card, get_theme, TEMP_DIR, BINS_DIR

class TempCleanerTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧹 Temp Cleaner")
        self.root.geometry("500x400")
        
        theme = get_theme()
        self.root.configure(bg=theme["bg"])
        
        self.build_ui()
    
    def build_ui(self):
        theme = get_theme()
        
        # Info Card
        info_card = create_card(self.root, "📁 Temp Folder Info")
        info_card.pack(fill="x", padx=10, pady=10)
        
        self.path_label = ttk.Label(info_card, text=f"Path: {TEMP_DIR}")
        self.path_label.pack(anchor="w", pady=2)
        
        self.size_label = ttk.Label(info_card, text="Size: Calculating...")
        self.size_label.pack(anchor="w", pady=2)
        
        self.files_label = ttk.Label(info_card, text="Files: Calculating...")
        self.files_label.pack(anchor="w", pady=2)
        
        ttk.Button(info_card, text="🔄 Refresh", command=self.scan_temp).pack(anchor="w", pady=5)
        
        # Files List
        files_card = create_card(self.root, "📄 Temp Files")
        files_card.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.file_list = tk.Listbox(files_card, height=8)
        scrollbar = ttk.Scrollbar(files_card, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.file_list.pack(fill="both", expand=True, pady=5)
        
        # Actions
        actions = ttk.Frame(self.root)
        actions.pack(pady=10)
        
        ttk.Button(actions, text="🗑️ Clean All Temp Files", command=self.clean_temp).pack(side="left", padx=5)
        ttk.Button(actions, text="📂 Open Folder", command=self.open_folder).pack(side="left", padx=5)
        ttk.Button(actions, text="Quit", command=self.root.quit).pack(side="left", padx=5)
        
        # Initial scan
        self.scan_temp()
    
    def scan_temp(self):
        self.file_list.delete(0, tk.END)
        
        if not TEMP_DIR.exists():
            self.size_label.config(text="Size: 0 B (folder doesn't exist)")
            self.files_label.config(text="Files: 0")
            return
        
        total_size = 0
        file_count = 0
        
        for f in TEMP_DIR.iterdir():
            if f.is_file():
                size = f.stat().st_size
                total_size += size
                file_count += 1
                size_str = self._format_size(size)
                self.file_list.insert(tk.END, f"{f.name} ({size_str})")
        
        self.size_label.config(text=f"Size: {self._format_size(total_size)}")
        self.files_label.config(text=f"Files: {file_count}")
    
    def _format_size(self, size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def clean_temp(self):
        if not TEMP_DIR.exists():
            tk.messagebox.showinfo("Info", "Temp folder is already empty.")
            return
        
        confirm = tk.messagebox.askyesno("Confirm", "Delete all files in temp folder?")
        if not confirm:
            return
        
        try:
            count = 0
            for f in TEMP_DIR.iterdir():
                if f.is_file():
                    f.unlink()
                    count += 1
                elif f.is_dir():
                    shutil.rmtree(f)
                    count += 1
            
            tk.messagebox.showinfo("Complete", f"Deleted {count} items.")
            self.scan_temp()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to clean: {e}")
    
    def open_folder(self):
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            os.startfile(TEMP_DIR)
        else:
            os.system(f"open '{TEMP_DIR}'")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TempCleanerTool()
    app.run()
