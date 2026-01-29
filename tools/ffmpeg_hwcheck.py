"""
FFmpeg Hardware Checker
Detect and configure hardware acceleration (NVIDIA, Intel, AMD)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
from ffmpeg_common import (
    FFmpegToolApp, get_binary, create_card, get_theme, 
    save_config, load_config
)

class HWCheckApp(FFmpegToolApp):
    """Hardware acceleration detection and configuration tool."""
    
    def __init__(self):
        super().__init__("Hardware Acceleration Checker", width=600, height=500)
        self.build_ui()
        self.auto_detect()
    
    def build_ui(self):
        theme = get_theme()
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # === Introduction ===
        intro_card = create_card(main_frame, "🚀 Boost Performance")
        intro_card.pack(fill="x", pady=(0, 20))
        
        info_text = (
            "This tool detects your GPU capabilities and configures FFmpeg "
            "to use hardware acceleration. This can significantly speed up "
            "video processing for all tools in this suite."
        )
        ttk.Label(intro_card, text=info_text, wraplength=520, justify="left").pack(fill="x")
        
        # === Detection Results ===
        result_card = create_card(main_frame, "🔍 Detected Hardware")
        result_card.pack(fill="x", pady=(0, 20))
        
        self.results_frame = ttk.Frame(result_card)
        self.results_frame.pack(fill="x", pady=5)
        
        self.status_labels = {}
        for hw in ["NVIDIA (CUDA/NVENC)", "Intel (QSV)", "AMD (AMF)", "Direct3D 11"]:
            row = ttk.Frame(self.results_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=hw + ":", width=20).pack(side="left")
            lbl = ttk.Label(row, text="Scanning...", foreground="gray")
            lbl.pack(side="left")
            self.status_labels[hw] = lbl
        
        # === Configuration ===
        config_card = create_card(main_frame, "⚙️ Global Configuration")
        config_card.pack(fill="x", pady=(0, 20))
        
        ttk.Label(config_card, text="Preferred Encoder:").pack(anchor="w")
        
        self.encoder_var = tk.StringVar(value="libx264")
        self.encoder_combo = ttk.Combobox(config_card, textvariable=self.encoder_var, width=40, state="readonly")
        self.encoder_combo.pack(fill="x", pady=(5, 10))
        self.encoder_combo['values'] = ["libx264 (CPU - High Quality, Slow)"]
        
        # Save Button
        self.save_btn = ttk.Button(config_card, text="💾 Save Output & Apply to All Tools", command=self.save_settings)
        self.save_btn.pack(fill="x")
        self.save_lbl = ttk.Label(config_card, text="", foreground=theme["success"])
        self.save_lbl.pack(pady=(5, 0))
        
        # === Actions ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side="bottom", fill="x")
        
        ttk.Button(btn_frame, text="🔄 Re-scan Hardware", command=self.auto_detect).pack(side="right")
    
    def auto_detect(self):
        self.encoders = {}
        self.detected_methods = []
        
        # Reset UI
        for key in self.status_labels:
            self.status_labels[key].configure(text="Scanning...", foreground="gray")
        self.root.update()
        
        # 1. Check Hardware Acceleration Methods
        hw_accels = self.get_hw_accels()
        
        # 2. Check Encoders
        available_encoders = self.get_encoders()
        
        # Update UI based on findings
        
        # NVIDIA
        if "cuda" in hw_accels and "h264_nvenc" in available_encoders:
            self.status_labels["NVIDIA (CUDA/NVENC)"].configure(text="✅ Detected", foreground="green")
            self.encoders["h264_nvenc"] = "NVIDIA NVENC (Fastest)"
            self.detected_methods.append("cuda")
        else:
            self.status_labels["NVIDIA (CUDA/NVENC)"].configure(text="❌ Not Found", foreground="red")
            
        # Intel QSV
        if "qsv" in hw_accels and "h264_qsv" in available_encoders:
            self.status_labels["Intel (QSV)"].configure(text="✅ Detected", foreground="green")
            self.encoders["h264_qsv"] = "Intel QuickSync (Efficient)"
            self.detected_methods.append("qsv")
        else:
            self.status_labels["Intel (QSV)"].configure(text="❌ Not Found", foreground="red")
            
        # AMD AMF
        if "h264_amf" in available_encoders:
            self.status_labels["AMD (AMF)"].configure(text="✅ Detected", foreground="green")
            self.encoders["h264_amf"] = "AMD AMF"
        else:
            self.status_labels["AMD (AMF)"].configure(text="❌ Not Found", foreground="red")
            
        # D3D11
        if "d3d11va" in hw_accels:
            self.status_labels["Direct3D 11"].configure(text="✅ Detected (Decode only)", foreground="orange")
        else:
            self.status_labels["Direct3D 11"].configure(text="❌ Not Found", foreground="red")
            
        # Populate Combobox
        options = ["libx264 (CPU - High Quality, Slow)"]
        for enc, desc in self.encoders.items():
            options.append(f"{enc} - {desc}")
        
        self.encoder_combo['values'] = options
        
        # Load current config preference
        current_conf = load_config().get("preferred_encoder", "libx264")
        
        # Select current
        for opt in options:
            if opt.startswith(current_conf):
                self.encoder_combo.set(opt)
                break
        else:
            self.encoder_combo.current(0)
            
    def get_hw_accels(self) -> list:
        try:
            cmd = [get_binary("ffmpeg"), "-hwaccels"]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
            return result.stdout.lower()
        except:
            return ""

    def get_encoders(self) -> str:
        try:
            cmd = [get_binary("ffmpeg"), "-encoders"]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
            return result.stdout
        except:
            return ""
            
    def save_settings(self):
        selection = self.encoder_var.get()
        encoder = selection.split(" ")[0] # Get 'libx264' from 'libx264 (CPU...)'
        
        config_update = {
            "preferred_encoder": encoder
        }
        
        # Add hwaccel arg mapping
        # This helps common.py know which -hwaccel flag to use
        hw_arg = "none"
        if "nvenc" in encoder:
            hw_arg = "cuda"
        elif "qsv" in encoder:
            hw_arg = "qsv"
        # AMD usually handles auto
        
        config_update["hw_accel_method"] = hw_arg
        
        save_config(config_update)
        
        self.save_lbl.configure(text=f"Settings saved! Using {encoder}")
        self.root.after(3000, lambda: self.save_lbl.configure(text=""))

if __name__ == "__main__":
    app = HWCheckApp()
    app.run()
