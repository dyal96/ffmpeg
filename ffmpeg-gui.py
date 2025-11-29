import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ----------------------------
# FFmpeg GUI App
# ----------------------------
class FFmpegGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Toolbox GUI")
        self.root.geometry("650x500")

        self.ffmpeg_path = "ffmpeg"   # assume ffmpeg is in PATH

        # Main notebook (tabs)
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        # Tabs
        self.extract_audio_tab()
        self.merge_tab()
        self.compress_tab()
        self.trim_tab()
        self.convert_tab()

    # ----------------------------
    # Helper: run ffmpeg
    # ----------------------------
    def run_ffmpeg(self, command):
        try:
            print("Running:", command)
            process = subprocess.run(command, shell=True)
            if process.returncode == 0:
                messagebox.showinfo("Success", "Task Completed!")
            else:
                messagebox.showerror("FFmpeg Error", "FFmpeg reported an error.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------------------
    # TAB 1: Extract Audio
    # ----------------------------
    def extract_audio_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Extract Audio")

        self.ea_file = tk.StringVar()

        ttk.Label(tab, text="Select Video:").pack(pady=5)
        ttk.Entry(tab, textvariable=self.ea_file, width=50).pack()
        ttk.Button(tab, text="Browse", command=lambda: self.select_file(self.ea_file)).pack(pady=5)

        ttk.Button(tab, text="Extract Audio (MP3)", command=self.extract_audio).pack(pady=20)

    def extract_audio(self):
        inp = self.ea_file.get()
        if not inp:
            return
        out = os.path.splitext(inp)[0] + ".mp3"
        command = f'{self.ffmpeg_path} -i "{inp}" -vn "{out}"'
        self.run_ffmpeg(command)

    # ----------------------------
    # TAB 2: Merge Video + Audio
    # ----------------------------
    def merge_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Merge Video + Audio")

        self.mv_video = tk.StringVar()
        self.mv_audio = tk.StringVar()

        ttk.Label(tab, text="Video File:").pack()
        ttk.Entry(tab, textvariable=self.mv_video, width=50).pack()
        ttk.Button(tab, text="Browse Video", command=lambda: self.select_file(self.mv_video)).pack()

        ttk.Label(tab, text="Audio File:").pack(pady=5)
        ttk.Entry(tab, textvariable=self.mv_audio, width=50).pack()
        ttk.Button(tab, text="Browse Audio", command=lambda: self.select_file(self.mv_audio)).pack()

        ttk.Button(tab, text="Merge", command=self.merge_video_audio).pack(pady=20)

    def merge_video_audio(self):
        video = self.mv_video.get()
        audio = self.mv_audio.get()
        if not video or not audio:
            return
        out = os.path.splitext(video)[0] + "_combined.mp4"
        command = f'{self.ffmpeg_path} -i "{video}" -i "{audio}" -c:v copy -c:a copy "{out}"'
        self.run_ffmpeg(command)

    # ----------------------------
    # TAB 3: Compress Video
    # ----------------------------
    def compress_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Compress Video")

        self.cmp_in = tk.StringVar()

        ttk.Label(tab, text="Select Video:").pack()
        ttk.Entry(tab, textvariable=self.cmp_in, width=50).pack()
        ttk.Button(tab, text="Browse", command=lambda: self.select_file(self.cmp_in)).pack()

        ttk.Button(tab, text="Compress (H.264 CRF 23)", command=self.compress_video).pack(pady=20)

    def compress_video(self):
        inp = self.cmp_in.get()
        if not inp:
            return
        out = os.path.splitext(inp)[0] + "_compressed.mp4"
        command = f'{self.ffmpeg_path} -i "{inp}" -vcodec libx264 -crf 23 "{out}"'
        self.run_ffmpeg(command)

    # ----------------------------
    # TAB 4: Trim Video
    # ----------------------------
    def trim_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Trim Video")

        self.trim_in = tk.StringVar()
        self.trim_start = tk.StringVar(value="00:00:00")
        self.trim_end = tk.StringVar(value="00:00:05")

        ttk.Label(tab, text="Select Video:").pack()
        ttk.Entry(tab, textvariable=self.trim_in, width=50).pack()
        ttk.Button(tab, text="Browse", command=lambda: self.select_file(self.trim_in)).pack()

        ttk.Label(tab, text="Start Time (hh:mm:ss):").pack(pady=5)
        ttk.Entry(tab, textvariable=self.trim_start).pack()

        ttk.Label(tab, text="End Time (hh:mm:ss):").pack(pady=5)
        ttk.Entry(tab, textvariable=self.trim_end).pack()

        ttk.Button(tab, text="Trim", command=self.trim_video).pack(pady=20)

    def trim_video(self):
        inp = self.trim_in.get()
        start = self.trim_start.get()
        end = self.trim_end.get()
        if not inp:
            return
        out = os.path.splitext(inp)[0] + "_trimmed.mp4"
        command = f'{self.ffmpeg_path} -ss {start} -to {end} -i "{inp}" -c copy "{out}"'
        self.run_ffmpeg(command)

    # ----------------------------
    # TAB 5: Convert Format
    # ----------------------------
    def convert_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Convert Format")

        self.cv_in = tk.StringVar()

        ttk.Label(tab, text="Select Video:").pack()
        ttk.Entry(tab, textvariable=self.cv_in, width=50).pack()
        ttk.Button(tab, text="Browse", command=lambda: self.select_file(self.cv_in)).pack()

        ttk.Label(tab, text="Convert To:").pack(pady=10)

        self.format_var = tk.StringVar()
        formats = ["mp4", "mkv", "mov", "avi", "flv", "webm"]
        self.format_dropdown = ttk.Combobox(tab, textvariable=self.format_var, values=formats, state="readonly")
        self.format_dropdown.pack()

        ttk.Button(tab, text="Convert", command=self.convert_video).pack(pady=20)

    def convert_video(self):
        inp = self.cv_in.get()
        fmt = self.format_var.get()
        if not inp or not fmt:
            return
        out = os.path.splitext(inp)[0] + "." + fmt
        command = f'{self.ffmpeg_path} -i "{inp}" "{out}"'
        self.run_ffmpeg(command)

    # ----------------------------
    # File Selector
    # ----------------------------
    def select_file(self, var):
        file = filedialog.askopenfilename()
        if file:
            var.set(file)


# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    FFmpegGUI(root)
    root.mainloop()
