"""
FFmpeg Common Utilities
Shared module for all FFmpeg Tkinter GUI tools
"""

import os
import sys
import json
import subprocess
import threading
import shutil
import re
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

# ============================================================================
# Path Resolution
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
BINS_DIR = SCRIPT_DIR.parent / "bins"
TEMP_DIR = SCRIPT_DIR.parent / "temp"
CONFIG_PATH = Path.home() / ".ffmpeg_toolbox_config.json"

def get_binary(name: str) -> str:
    """Get path to binary, preferring local bins folder."""
    if os.name == 'nt' and not name.endswith(".exe"):
        name += ".exe"
    
    local_bin = BINS_DIR / name
    if local_bin.exists():
        return str(local_bin)
    
    # Fall back to system PATH
    found = shutil.which(name.replace(".exe", ""))
    if found:
        return found
    return name  # Let subprocess handle the error

def ensure_dir(folder: Path):
    """Ensure directory exists."""
    folder.mkdir(parents=True, exist_ok=True)

# Ensure temp directory exists
ensure_dir(TEMP_DIR)

# ============================================================================
# Configuration
# ============================================================================

def load_config() -> dict:
    """Load configuration from file."""
    config = {"theme": "light", "last_dir": str(Path.home())}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                saved = json.load(f)
                config.update(saved)
        except:
            pass
    return config

def save_config(new_data: dict):
    """Save configuration to file (merging with existing)."""
    current = load_config()
    current.update(new_data)
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(current, f)
    except:
        pass

# ============================================================================
# Media Info (FFprobe)
# ============================================================================

def get_media_duration(filepath: str) -> float | None:
    """Get media duration in seconds using ffprobe."""
    try:
        cmd = [get_binary("ffprobe"), "-v", "quiet", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return None

def get_media_info(filepath: str) -> dict | None:
    """Get detailed media info using ffprobe as JSON."""
    try:
        cmd = [get_binary("ffprobe"), "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None

def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds is None:
        return "00:00:00"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_time_to_seconds(time_str: str) -> float:
    """Parse HH:MM:SS or SS format to seconds."""
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except:
        return 0.0

# ============================================================================
# FFmpeg Runner (Threaded with Progress)
# ============================================================================

class FFmpegRunner:
    """Runs FFmpeg in a background thread with progress updates."""
    
    def __init__(self, on_progress=None, on_log=None, on_finished=None):
        self.on_progress = on_progress  # callback(percent: int)
        self.on_log = on_log            # callback(text: str)
        self.on_finished = on_finished  # callback(success: bool, message: str)
        self.process = None
        self.thread = None
        self.total_duration = None
        self._stop_flag = False
    
    def run(self, cmd: list, input_file: str = None):
        """Start FFmpeg command in background thread."""
        if self.is_running():
            if self.on_log:
                self.on_log("⚠ Already running, please wait...\n")
            return False
        
        # Get duration for progress calculation
        if input_file:
            self.total_duration = get_media_duration(input_file)
        else:
            self.total_duration = None
        
        self._stop_flag = False
        self.thread = threading.Thread(target=self._run_thread, args=(cmd,), daemon=True)
        self.thread.start()
        return True
    
    def _run_thread(self, cmd: list):
        """Internal thread function."""
        try:
            if self.on_log:
                self.on_log(f"$ {' '.join(cmd)}\n")
            
            # Start process
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )
            
            # Read output line by line
            for line in self.process.stdout:
                if self._stop_flag:
                    self.process.terminate()
                    break
                
                if self.on_log:
                    self.on_log(line)
                
                # Parse progress
                self._parse_progress(line)
            
            self.process.wait()
            
            if self._stop_flag:
                if self.on_finished:
                    self.on_finished(False, "Cancelled by user")
            elif self.process.returncode == 0:
                if self.on_progress:
                    self.on_progress(100)
                if self.on_finished:
                    self.on_finished(True, "Success!")
            else:
                if self.on_finished:
                    self.on_finished(False, f"FFmpeg exited with code {self.process.returncode}")
        
        except Exception as e:
            if self.on_finished:
                self.on_finished(False, str(e))
        finally:
            self.process = None
    
    def _parse_progress(self, text: str):
        """Parse FFmpeg output to extract progress percentage."""
        if not self.total_duration or not self.on_progress:
            return
        
        # Look for "time=HH:MM:SS.ms" pattern
        match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', text)
        if match:
            h, m, s, ms = map(int, match.groups())
            current = h * 3600 + m * 60 + s + ms / 100.0
            percent = int((current / self.total_duration) * 100)
            self.on_progress(min(percent, 99))
    
    def is_running(self) -> bool:
        """Check if FFmpeg is currently running."""
        return self.thread is not None and self.thread.is_alive()
    
    def stop(self):
        """Stop the running FFmpeg process."""
        self._stop_flag = True
        if self.process:
            try:
                self.process.terminate()
            except:
                pass

    def send_input(self, text: str):
        """Send input to stdin."""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(text)
                self.process.stdin.flush()
            except:
                pass

# ============================================================================
# Tkinter Styling & Helpers
# ============================================================================

# Color Schemes
THEMES = {
    "light": {
        "bg": "#f5f7fa",
        "fg": "#2d3748",
        "card_bg": "#ffffff",
        "card_border": "#e2e8f0",
        "accent": "#667eea",
        "accent_hover": "#5a67d8",
        "input_bg": "#ffffff",
        "input_border": "#cbd5e0",
        "button_fg": "#ffffff",
        "success": "#48bb78",
        "error": "#f56565",
    },
    "dark": {
        "bg": "#1a1a2e",
        "fg": "#eaeaea",
        "card_bg": "#16213e",
        "card_border": "#3a3a5c",
        "accent": "#e94560",
        "accent_hover": "#ff6b8a",
        "input_bg": "#0f3460",
        "input_border": "#3a3a5c",
        "button_fg": "#ffffff",
        "success": "#48bb78",
        "error": "#f56565",
    }
}

def get_theme() -> dict:
    """Get current theme colors."""
    config = load_config()
    theme_name = config.get("theme", "light")
    return THEMES.get(theme_name, THEMES["light"])

def apply_theme(root: tk.Tk):
    """Apply theme to Tkinter window."""
    theme = get_theme()
    
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure ttk styles
    style.configure("TFrame", background=theme["bg"])
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
    style.configure("TButton", background=theme["accent"], foreground=theme["button_fg"])
    style.map("TButton", background=[("active", theme["accent_hover"])])
    style.configure("TEntry", fieldbackground=theme["input_bg"], foreground=theme["fg"])
    style.configure("TCombobox", fieldbackground=theme["input_bg"], foreground=theme["fg"])
    style.configure("Horizontal.TProgressbar", troughcolor=theme["card_bg"], background=theme["accent"])
    
    # Card frame style
    style.configure("Card.TFrame", background=theme["card_bg"], bordercolor=theme["card_border"])
    
    # Title label style
    style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), foreground=theme["accent"])
    
    # Root window
    root.configure(bg=theme["bg"])

def create_card(parent, title: str = None) -> ttk.Frame:
    """Create a styled card frame with optional title."""
    theme = get_theme()
    
    outer = ttk.Frame(parent, style="Card.TFrame", padding=10)
    outer.configure(relief="solid", borderwidth=1)
    
    if title:
        title_lbl = ttk.Label(outer, text=title, style="Title.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 5))
    
    return outer

def browse_file(entry: ttk.Entry, filetypes=None):
    """Open file dialog and set entry value."""
    if filetypes is None:
        filetypes = [("All files", "*.*")]
    
    config = load_config()
    initial_dir = config.get("last_dir", str(Path.home()))
    
    filepath = filedialog.askopenfilename(initialdir=initial_dir, filetypes=filetypes)
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)
        save_config({"last_dir": str(Path(filepath).parent)})

def browse_folder(entry: ttk.Entry):
    """Open folder dialog and set entry value."""
    config = load_config()
    initial_dir = config.get("last_dir", str(Path.home()))
    
    folderpath = filedialog.askdirectory(initialdir=initial_dir)
    if folderpath:
        entry.delete(0, tk.END)
        entry.insert(0, folderpath)
        save_config({"last_dir": folderpath})

def browse_save_file(entry: ttk.Entry, filetypes=None, defaultext=".mp4"):
    """Open save file dialog and set entry value."""
    if filetypes is None:
        filetypes = [("Video files", "*.mp4"), ("All files", "*.*")]
    
    config = load_config()
    initial_dir = config.get("last_dir", str(Path.home()))
    
    filepath = filedialog.asksaveasfilename(
        initialdir=initial_dir, 
        filetypes=filetypes,
        defaultextension=defaultext
    )
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)
        save_config({"last_dir": str(Path(filepath).parent)})

def generate_output_path(input_path: str, suffix: str, new_ext: str = None) -> str:
    """Generate output path based on input with suffix and optional new extension."""
    p = Path(input_path)
    ext = new_ext if new_ext else p.suffix
    return str(p.parent / f"{p.stem}{suffix}{ext}")

# ============================================================================
# Drag & Drop Support (Windows)
# ============================================================================

def enable_dnd(widget, entry: ttk.Entry):
    """Enable drag and drop for a widget (basic implementation)."""
    # Note: Full DnD requires windnd or tkinterdnd2 package
    # This is a placeholder - users can install these packages for full support
    pass

# ============================================================================
# Base Application Class
# ============================================================================

class FFmpegToolApp:
    """Base class for FFmpeg tool applications."""
    
    def __init__(self, title: str, width: int = 600, height: int = 500):
        self.root = tk.Tk()
        self.root.title(f"🎬 {title}")
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(500, 400)
        
        # Apply theme
        apply_theme(self.root)
        
        # Runner
        self.runner = FFmpegRunner(
            on_progress=self._on_progress,
            on_log=self._on_log,
            on_finished=self._on_finished
        )
        
        # UI references (to be set by subclass)
        self.progress_bar = None
        self.log_text = None
        self.preview_text = None
        self.run_btn = None
        self.status_label = None
    
    def _on_progress(self, percent: int):
        """Handle progress updates (thread-safe)."""
        if self.progress_bar:
            self.root.after(0, lambda: self.progress_bar.configure(value=percent))
    
    def _on_log(self, text: str):
        """Handle log messages (thread-safe)."""
        if self.log_text:
            def update():
                self.log_text.configure(state="normal")
                self.log_text.insert(tk.END, text)
                self.log_text.see(tk.END)
                self.log_text.configure(state="disabled")
            self.root.after(0, update)
    
    def _on_finished(self, success: bool, message: str):
        """Handle completion (thread-safe)."""
        def update():
            if self.run_btn:
                self.run_btn.configure(state="normal")
            if self.status_label:
                theme = get_theme()
                color = theme["success"] if success else theme["error"]
                self.status_label.configure(text=message, foreground=color)
            if self.progress_bar:
                self.progress_bar.configure(value=100 if success else 0)
            
            if success:
                messagebox.showinfo("Complete", message)
            else:
                messagebox.showerror("Error", message)
        
        self.root.after(0, update)
    
    def set_preview(self, cmd: list):
        """Set command preview text."""
        if self.preview_text:
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", " ".join(cmd))
            self.preview_text.configure(state="disabled")
    
    def clear_log(self):
        """Clear log text."""
        if self.log_text:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", tk.END)
            self.log_text.configure(state="disabled")
    
    def run_command(self, cmd: list, input_file: str = None):
        """Run FFmpeg command."""
        if self.runner.is_running():
            messagebox.showwarning("Busy", "Please wait for current operation to complete.")
            return
        
        self.clear_log()
        if self.run_btn:
            self.run_btn.configure(state="disabled")
        if self.status_label:
            self.status_label.configure(text="Processing...", foreground=get_theme()["fg"])
        if self.progress_bar:
            self.progress_bar.configure(value=0)
        
        self.runner.run(cmd, input_file)
    
    def stop_command(self):
        """Stop running command."""
        self.runner.stop()
    
    def send_command_input(self, text: str):
        """Send input to running command."""
        self.runner.send_input(text)
    
    def create_bottom_section(self, parent) -> ttk.Frame:
        """Create standard bottom section with preview, log, progress."""
        theme = get_theme()
        
        bottom = ttk.Frame(parent)
        
        # Preview
        preview_frame = create_card(bottom, "📋 Command Preview")
        preview_frame.pack(fill="x", pady=(0, 5))
        
        self.preview_text = tk.Text(preview_frame, height=2, wrap="word", state="disabled",
                                    bg=theme["input_bg"], fg=theme["fg"])
        self.preview_text.pack(fill="x")
        
        # Log
        log_frame = create_card(bottom, "📃 Log")
        log_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled",
                                bg=theme["input_bg"], fg=theme["fg"])
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)
        
        # Progress & Status
        status_frame = ttk.Frame(bottom)
        status_frame.pack(fill="x")
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side="left")
        
        self.progress_bar = ttk.Progressbar(status_frame, mode="determinate", length=300)
        self.progress_bar.pack(side="right", padx=(10, 0))
        
        return bottom
    
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()
