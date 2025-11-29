# ffmpeg_toolbox_pyside6.py
import sys
import os
import shutil
import shlex
from pathlib import Path
from functools import partial

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QPushButton, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QTabWidget, QComboBox, QSpinBox, QCheckBox, QListWidget, QListWidgetItem,
    QProgressBar
)
from PySide6.QtCore import Qt, QProcess, Slot
from PySide6.QtGui import QTextCursor


# ---------------------------
# Helper utilities
# ---------------------------
def ffmpeg_exists():
    return shutil.which("ffmpeg") is not None

def ensure_dir(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)

def quote(p):
    # Use shlex.quote where available; on Windows it returns single-quoted strings which still works for QProcess when passed as list.
    return shlex.quote(str(p))

def default_output_path(input_path: str, out_folder: str, suffix: str, ext: str):
    p = Path(input_path)
    name = p.stem + suffix + ext
    return str(Path(out_folder) / name)

# ---------------------------
# Worker: Run ffmpeg via QProcess
# ---------------------------
class FFmpegRunner:
    def __init__(self, log_widget: QTextEdit, progress_bar: QProgressBar=None):
        self.log = log_widget
        self.process = None
        self.progress = progress_bar

    def run(self, args_list, on_finished=None):
        """
        args_list: list of arguments for ffmpeg (including 'ffmpeg' at index 0 OR relies on system)
        """
        if not ffmpeg_exists():
            QMessageBox.critical(None, "Error", "ffmpeg was not found in PATH. Install ffmpeg or add it to PATH.")
            return

        # If args_list is string, split safely
        if isinstance(args_list, str):
            args_list = shlex.split(args_list)

        # Build process
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._stdout)
        self.process.readyReadStandardError.connect(self._stdout)
        if on_finished:
            self.process.finished.connect(on_finished)
        # For Windows, pass program and args separately
        if os.name == "nt":
            program = args_list[0]
            args = args_list[1:]
        else:
            program = args_list[0]
            args = args_list[1:]

        self._log(f"Running: {program} {' '.join(map(quote, args))}\n\n")
        try:
            self.process.start(program, args)
        except Exception as e:
            self._log(f"Failed to start process: {e}\n")
            return

    def _stdout(self):
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        if data:
            self._log(data)
            # Try to parse progress info (primitive)
            if self.progress:
                # Try to grab "time=hh:mm:ss.xx" and set progress heuristically if file duration known (not implemented)
                pass

    def _log(self, text):
        self.log.moveCursor(QTextCursor.End)
        self.log.insertPlainText(text)
        self.log.ensureCursorVisible()

    def kill(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()

# ---------------------------
# Main Window
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg Toolbox - PySide6 (Full Pro)")
        self.resize(1000, 700)

        # Main widget and layout
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Shared widgets: log + command preview + progress
        bottom_h = QHBoxLayout()
        layout.addLayout(bottom_h)

        # Build tabs
        self.build_convert_tab()
        self.build_extract_tab()
        self.build_merge_tab()
        self.build_trim_tab()
        self.build_watermark_tab()
        self.build_subtitles_tab()
        self.build_batch_tab()

        # Log and preview
        right_v = QVBoxLayout()
        bottom_h.addLayout(right_v, 2)

        preview_label = QLabel("Command Preview")
        right_v.addWidget(preview_label)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        right_v.addWidget(self.preview, 2)

        log_label = QLabel("FFmpeg Log")
        right_v.addWidget(log_label)
        self.log = QTextEdit()
        self.log.setReadOnly(False)
        right_v.addWidget(self.log, 3)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        right_v.addWidget(self.progress)

        # Runner
        self.runner = FFmpegRunner(self.log, self.progress)

        # Menu: settings
        self.init_menu()

        # Quick check
        if not ffmpeg_exists():
            QMessageBox.warning(self, "ffmpeg not found", "ffmpeg executable was not found in PATH. Many features will fail. Install ffmpeg and add to PATH.")
        self.show()

    # ---------------------------
    # Tab builders
    # ---------------------------
    def build_convert_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Convert / Compress")

        # Input selector
        h1 = QHBoxLayout()
        v.addLayout(h1)
        self.conv_in = QLineEdit(); self.conv_in.setPlaceholderText("Select video file...")
        h1.addWidget(self.conv_in)
        btn_in = QPushButton("Browse")
        btn_in.clicked.connect(partial(self.browse_file, self.conv_in, "Video Files (*.mp4 *.mkv *.mov *.avi);;All Files (*)"))
        h1.addWidget(btn_in)

        # Output folder
        h2 = QHBoxLayout(); v.addLayout(h2)
        self.conv_outfolder = QLineEdit(); self.conv_outfolder.setPlaceholderText("Output folder (default: same folder)")
        h2.addWidget(self.conv_outfolder)
        btn_out = QPushButton("Choose Output Folder")
        btn_out.clicked.connect(partial(self.browse_folder, self.conv_outfolder))
        h2.addWidget(btn_out)

        # Codec selection & CRF
        h3 = QHBoxLayout(); v.addLayout(h3)
        h3.addWidget(QLabel("Video Codec:"))
        self.conv_vcodec = QComboBox()
        self.conv_vcodec.addItems(["copy", "libx264", "libx265", "libvpx-vp9", "libaom-av1"])
        h3.addWidget(self.conv_vcodec)
        h3.addWidget(QLabel("CRF (quality, lower=better):"))
        self.conv_crf = QSpinBox(); self.conv_crf.setRange(0,51); self.conv_crf.setValue(23)
        h3.addWidget(self.conv_crf)
        self.conv_two_pass = QCheckBox("2-pass (if encoding)")
        h3.addWidget(self.conv_two_pass)

        # Audio codec
        h4 = QHBoxLayout(); v.addLayout(h4)
        h4.addWidget(QLabel("Audio Codec:"))
        self.conv_acodec = QComboBox()
        self.conv_acodec.addItems(["copy", "aac", "libmp3lame", "opus"])
        h4.addWidget(self.conv_acodec)
        h4.addWidget(QLabel("Audio Bitrate (kbps):"))
        self.conv_abitrate = QSpinBox(); self.conv_abitrate.setRange(32,512); self.conv_abitrate.setValue(128)
        h4.addWidget(self.conv_abitrate)

        # Buttons
        h5 = QHBoxLayout(); v.addLayout(h5)
        self.conv_preview_btn = QPushButton("Preview Command"); self.conv_preview_btn.clicked.connect(self.conv_preview)
        h5.addWidget(self.conv_preview_btn)
        self.conv_run_btn = QPushButton("Run Convert/Compress"); self.conv_run_btn.clicked.connect(self.conv_run)
        h5.addWidget(self.conv_run_btn)

    def build_extract_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Extract Audio")

        h1 = QHBoxLayout(); v.addLayout(h1)
        self.ext_in = QLineEdit(); self.ext_in.setPlaceholderText("Select video file...")
        h1.addWidget(self.ext_in)
        btn = QPushButton("Browse"); btn.clicked.connect(partial(self.browse_file, self.ext_in, "Video Files (*.mp4 *.mkv *.mov *.avi);;All Files (*)"))
        h1.addWidget(btn)

        h2 = QHBoxLayout(); v.addLayout(h2)
        self.ext_outfolder = QLineEdit(); self.ext_outfolder.setPlaceholderText("Output folder (default: same folder/Extracted Audio)")
        h2.addWidget(self.ext_outfolder)
        btn2 = QPushButton("Choose Output Folder"); btn2.clicked.connect(partial(self.browse_folder, self.ext_outfolder))
        h2.addWidget(btn2)

        h3 = QHBoxLayout(); v.addLayout(h3)
        h3.addWidget(QLabel("Format:"))
        self.ext_format = QComboBox(); self.ext_format.addItems(["mp3", "m4a", "wav", "flac", "aac"])
        h3.addWidget(self.ext_format)
        h3.addStretch()

        h4 = QHBoxLayout(); v.addLayout(h4)
        self.ext_preview_btn = QPushButton("Preview Command"); self.ext_preview_btn.clicked.connect(self.ext_preview)
        h4.addWidget(self.ext_preview_btn)
        self.ext_run_btn = QPushButton("Extract Audio"); self.ext_run_btn.clicked.connect(self.ext_run)
        h4.addWidget(self.ext_run_btn)

    def build_merge_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Merge Video+Audio")

        h1 = QHBoxLayout(); v.addLayout(h1)
        self.mg_vid = QLineEdit(); h1.addWidget(self.mg_vid)
        b1 = QPushButton("Video"); b1.clicked.connect(partial(self.browse_file, self.mg_vid, "Video Files (*.mp4 *.mkv *.mov)"))
        h1.addWidget(b1)
        self.mg_aud = QLineEdit(); h1.addWidget(self.mg_aud)
        b2 = QPushButton("Audio"); b2.clicked.connect(partial(self.browse_file, self.mg_aud, "Audio Files (*.m4a *.mp3 *.wav)"))
        h1.addWidget(b2)

        h2 = QHBoxLayout(); v.addLayout(h2)
        self.mg_outfolder = QLineEdit(); h2.addWidget(self.mg_outfolder)
        b3 = QPushButton("Output Folder"); b3.clicked.connect(partial(self.browse_folder, self.mg_outfolder))
        h2.addWidget(b3)

        # Options
        h3 = QHBoxLayout(); v.addLayout(h3)
        self.mg_vcopy = QCheckBox("Copy Video Stream (no re-encode)"); self.mg_vcopy.setChecked(True)
        h3.addWidget(self.mg_vcopy)
        self.mg_acopy = QCheckBox("Copy Audio Stream"); self.mg_acopy.setChecked(True)
        h3.addWidget(self.mg_acopy)
        self.mg_overwrite = QCheckBox("Overwrite existing output"); self.mg_overwrite.setChecked(True)
        h3.addWidget(self.mg_overwrite)

        h4 = QHBoxLayout(); v.addLayout(h4)
        self.mg_preview_btn = QPushButton("Preview Command"); self.mg_preview_btn.clicked.connect(self.mg_preview)
        h4.addWidget(self.mg_preview_btn)
        self.mg_run_btn = QPushButton("Merge"); self.mg_run_btn.clicked.connect(self.mg_run)
        h4.addWidget(self.mg_run_btn)

    def build_trim_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Trim / Cut")

        h1 = QHBoxLayout(); v.addLayout(h1)
        self.trim_in = QLineEdit(); h1.addWidget(self.trim_in)
        btn = QPushButton("Browse"); btn.clicked.connect(partial(self.browse_file, self.trim_in, "Video Files (*.mp4 *.mkv *.mov *.avi)"))
        h1.addWidget(btn)

        h2 = QHBoxLayout(); v.addLayout(h2)
        h2.addWidget(QLabel("Start (hh:mm:ss):")); self.trim_start = QLineEdit("00:00:00"); h2.addWidget(self.trim_start)
        h2.addWidget(QLabel("End (hh:mm:ss):")); self.trim_end = QLineEdit("00:00:10"); h2.addWidget(self.trim_end)

        h3 = QHBoxLayout(); v.addLayout(h3)
        self.trim_preview_btn = QPushButton("Preview Command"); self.trim_preview_btn.clicked.connect(self.trim_preview)
        h3.addWidget(self.trim_preview_btn)
        self.trim_run_btn = QPushButton("Trim"); self.trim_run_btn.clicked.connect(self.trim_run)
        h3.addWidget(self.trim_run_btn)

    def build_watermark_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Watermark")

        h1 = QHBoxLayout(); v.addLayout(h1)
        self.wm_in = QLineEdit(); h1.addWidget(self.wm_in)
        b1 = QPushButton("Browse Video"); b1.clicked.connect(partial(self.browse_file, self.wm_in, "Video Files (*.mp4 *.mkv *.mov)"))
        h1.addWidget(b1)
        h1.addStretch()

        h2 = QHBoxLayout(); v.addLayout(h2)
        self.wm_logo = QLineEdit(); h2.addWidget(self.wm_logo)
        b2 = QPushButton("Choose Logo"); b2.clicked.connect(partial(self.browse_file, self.wm_logo, "Images (*.png *.jpg *.webp);;All Files (*)"))
        h2.addWidget(b2)

        h3 = QHBoxLayout(); v.addLayout(h3)
        h3.addWidget(QLabel("Position (x:y) or presets:"))
        self.wm_pos = QComboBox(); self.wm_pos.addItems(["10:10 (top-left)", "main_w-overlay_w-10:10 (top-right)", "10:main_h-overlay_h-10 (bottom-left)", "main_w-overlay_w-10:main_h-overlay_h-10 (bottom-right)"])
        h3.addWidget(self.wm_pos)

        h4 = QHBoxLayout(); v.addLayout(h4)
        self.wm_preview_btn = QPushButton("Preview Command"); self.wm_preview_btn.clicked.connect(self.wm_preview)
        h4.addWidget(self.wm_preview_btn)
        self.wm_run_btn = QPushButton("Add Watermark"); self.wm_run_btn.clicked.connect(self.wm_run)
        h4.addWidget(self.wm_run_btn)

    def build_subtitles_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Add Subtitles (burn)")

        h1 = QHBoxLayout(); v.addLayout(h1)
        self.sub_in = QLineEdit(); h1.addWidget(self.sub_in)
        b1 = QPushButton("Browse Video"); b1.clicked.connect(partial(self.browse_file, self.sub_in, "Video Files (*.mp4 *.mkv *.mov)"))
        h1.addWidget(b1)

        h2 = QHBoxLayout(); v.addLayout(h2)
        self.sub_file = QLineEdit(); h2.addWidget(self.sub_file)
        b2 = QPushButton("Browse Subtitles (.srt)"); b2.clicked.connect(partial(self.browse_file, self.sub_file, "Subtitles (*.srt *.ass);;All Files (*)"))
        h2.addWidget(b2)

        h3 = QHBoxLayout(); v.addLayout(h3)
        self.sub_preview_btn = QPushButton("Preview Command"); self.sub_preview_btn.clicked.connect(self.sub_preview)
        h3.addWidget(self.sub_preview_btn)
        self.sub_run_btn = QPushButton("Burn Subtitles"); self.sub_run_btn.clicked.connect(self.sub_run)
        h3.addWidget(self.sub_run_btn)

    def build_batch_tab(self):
        tab = QWidget(); v = QVBoxLayout(tab)
        self.tabs.addTab(tab, "Batch Processor")

        # Operation selector
        h1 = QHBoxLayout(); v.addLayout(h1)
        h1.addWidget(QLabel("Operation:"))
        self.batch_op = QComboBox()
        self.batch_op.addItems(["Extract Audio (mp3)", "Convert to mp4 h264", "Compress (CRF 28)", "Add watermark (requires logo)"])
        h1.addWidget(self.batch_op)

        # Input list
        h2 = QHBoxLayout(); v.addLayout(h2)
        self.batch_list = QListWidget(); v.addWidget(self.batch_list, 3)
        h2r = QVBoxLayout(); v.addLayout(h2r)
        btn_add = QPushButton("Add Files"); btn_add.clicked.connect(self.batch_add_files)
        h2r.addWidget(btn_add)
        btn_rem = QPushButton("Remove Selected"); btn_rem.clicked.connect(self.batch_remove)
        h2r.addWidget(btn_rem)
        btn_clear = QPushButton("Clear"); btn_clear.clicked.connect(self.batch_clear)
        h2r.addWidget(btn_clear)
        h2r.addStretch()

        # Run batch
        h3 = QHBoxLayout(); v.addLayout(h3)
        self.batch_outfolder = QLineEdit(); self.batch_outfolder.setPlaceholderText("Output folder for batch (defaults to each file folder/BatchOutput)")
        h3.addWidget(self.batch_outfolder)
        btn_bo = QPushButton("Choose Output Folder"); btn_bo.clicked.connect(partial(self.browse_folder, self.batch_outfolder))
        h3.addWidget(btn_bo)

        h4 = QHBoxLayout(); v.addLayout(h4)
        self.batch_preview_btn = QPushButton("Preview Batch"); self.batch_preview_btn.clicked.connect(self.batch_preview)
        h4.addWidget(self.batch_preview_btn)
        self.batch_run_btn = QPushButton("Run Batch"); self.batch_run_btn.clicked.connect(self.batch_run)
        h4.addWidget(self.batch_run_btn)

    # ---------------------------
    # Common UI helpers
    # ---------------------------
    def browse_file(self, lineedit: QLineEdit, filter_str="All Files (*)"):
        fp, _ = QFileDialog.getOpenFileName(self, "Select file", str(Path.home()), filter_str)
        if fp:
            lineedit.setText(fp)

    def browse_folder(self, lineedit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select folder", str(Path.home()))
        if folder:
            lineedit.setText(folder)

    # ---------------------------
    # Preview & run implementations
    # ---------------------------
    def conv_preview(self):
        inp = self.conv_in.text().strip()
        if not inp:
            QMessageBox.warning(self, "Missing input", "Select an input video file.")
            return
        outfolder = self.conv_outfolder.text().strip() or str(Path(inp).parent)
        ensure_dir(outfolder)
        ext = ".mp4"
        vcodec = self.conv_vcodec.currentText()
        acodec = self.conv_acodec.currentText()
        crf = self.conv_crf.value()
        ab = self.conv_abitrate.value()
        outp = default_output_path(inp, outfolder, "_converted", ext)
        cmd = ["ffmpeg", "-i", inp]
        if vcodec != "copy":
            cmd += ["-c:v", vcodec, "-crf", str(crf)]
        else:
            cmd += ["-c:v", "copy"]
        if acodec != "copy":
            cmd += ["-c:a", acodec, "-b:a", f"{ab}k"]
        else:
            cmd += ["-c:a", "copy"]
        cmd += [outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def conv_run(self):
        self.conv_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Convert", exitCode, status))

    def ext_preview(self):
        inp = self.ext_in.text().strip()
        if not inp:
            QMessageBox.warning(self, "Missing input", "Select a video file.")
            return
        outfolder = self.ext_outfolder.text().strip() or str(Path(inp).parent / "Extracted Audio")
        ensure_dir(outfolder)
        fmt = self.ext_format.currentText()
        outp = default_output_path(inp, outfolder, "_audio", f".{fmt}")
        cmd = ["ffmpeg", "-i", inp, "-vn", "-y", outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def ext_run(self):
        self.ext_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Extract Audio", exitCode, status))

    def mg_preview(self):
        video = self.mg_vid.text().strip()
        audio = self.mg_aud.text().strip()
        if not video or not audio:
            QMessageBox.warning(self, "Missing files", "Select both video and audio files.")
            return
        outfolder = self.mg_outfolder.text().strip() or str(Path(video).parent / "AV Videos")
        ensure_dir(outfolder)
        outp = default_output_path(video, outfolder, "_combined", ".mp4")
        cmd = ["ffmpeg"]
        if self.mg_overwrite.isChecked():
            cmd.append("-y")
        cmd += ["-i", video, "-i", audio]
        # Choose codecs
        if self.mg_vcopy.isChecked():
            cmd += ["-c:v", "copy"]
        if self.mg_acopy.isChecked():
            cmd += ["-c:a", "copy"]
        if not (self.mg_vcopy.isChecked() or self.mg_acopy.isChecked()):
            # default
            cmd += ["-c:v", "libx264", "-c:a", "aac"]
        cmd += [outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def mg_run(self):
        self.mg_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Merge", exitCode, status))

    def trim_preview(self):
        inp = self.trim_in.text().strip()
        if not inp:
            QMessageBox.warning(self, "Missing input", "Select a video file.")
            return
        s = self.trim_start.text().strip()
        e = self.trim_end.text().strip()
        outfolder = str(Path(inp).parent)
        outp = default_output_path(inp, outfolder, f"_trim_{s.replace(':','-')}_to_{e.replace(':','-')}", ".mp4")
        cmd = ["ffmpeg", "-i", inp, "-ss", s, "-to", e, "-c", "copy", outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def trim_run(self):
        self.trim_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Trim", exitCode, status))

    def wm_preview(self):
        inp = self.wm_in.text().strip()
        logo = self.wm_logo.text().strip()
        if not inp or not logo:
            QMessageBox.warning(self, "Missing files", "Select video and logo.")
            return
        outfolder = str(Path(inp).parent)
        outp = default_output_path(inp, outfolder, "_wm", ".mp4")
        pos = self.wm_pos.currentText().split(" ")[0]
        # filter_complex: overlay
        cmd = ["ffmpeg", "-i", inp, "-i", logo, "-filter_complex", f"overlay={pos}", "-c:a", "copy", outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def wm_run(self):
        self.wm_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Watermark", exitCode, status))

    def sub_preview(self):
        inp = self.sub_in.text().strip()
        sub = self.sub_file.text().strip()
        if not inp or not sub:
            QMessageBox.warning(self, "Missing files", "Select video and subtitle file.")
            return
        outfolder = str(Path(inp).parent)
        outp = default_output_path(inp, outfolder, "_subbed", ".mp4")
        # Using subtitles filter (requires libass support)
        cmd = ["ffmpeg", "-i", inp, "-vf", f"subtitles={quote(sub)}", outp]
        self.preview.setPlainText(" ".join(map(quote, cmd)))

    def sub_run(self):
        self.sub_preview()
        cmd = self.preview.toPlainText().strip()
        if not cmd:
            return
        self.runner.run(cmd, on_finished=lambda exitCode, status: self._on_finished("Subtitles", exitCode, status))

    # ---------------------------
    # Batch functions
    # ---------------------------
    def batch_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select files", str(Path.home()), "Video Files (*.mp4 *.mkv *.mov *.avi);;All Files (*)")
        for f in files:
            item = QListWidgetItem(f)
            self.batch_list.addItem(item)

    def batch_remove(self):
        for it in self.batch_list.selectedItems():
            self.batch_list.takeItem(self.batch_list.row(it))

    def batch_clear(self):
        self.batch_list.clear()

    def batch_preview(self):
        op = self.batch_op.currentText()
        items = [self.batch_list.item(i).text() for i in range(self.batch_list.count())]
        if not items:
            QMessageBox.warning(self, "No files", "Add files to the batch list.")
            return
        outfolder = self.batch_outfolder.text().strip()
        lines = []
        for f in items:
            if not outfolder:
                target = str(Path(f).parent / "BatchOutput")
            else:
                target = outfolder
            ensure_dir(target)
            if op.startswith("Extract Audio"):
                outp = default_output_path(f, target, "_audio", ".mp3")
                lines.append(f"ffmpeg -i {quote(f)} -vn -y {quote(outp)}")
            elif op.startswith("Convert to mp4"):
                outp = default_output_path(f, target, "_conv", ".mp4")
                lines.append(f"ffmpeg -i {quote(f)} -c:v libx264 -crf 23 -c:a aac -b:a 128k -y {quote(outp)}")
            elif op.startswith("Compress"):
                outp = default_output_path(f, target, "_compressed", ".mp4")
                lines.append(f"ffmpeg -i {quote(f)} -c:v libx264 -crf 28 -c:a aac -b:a 96k -y {quote(outp)}")
            elif op.startswith("Add watermark"):
                # NOTE: requires logo manually set in watermark tab.
                logo = self.wm_logo.text().strip()
                if not logo:
                    lines.append(f"REM Missing logo for {f}")
                else:
                    outp = default_output_path(f, target, "_wm", ".mp4")
                    pos = self.wm_pos.currentText().split(" ")[0]
                    lines.append(f"ffmpeg -i {quote(f)} -i {quote(logo)} -filter_complex \"overlay={pos}\" -c:a copy -y {quote(outp)}")
        self.preview.setPlainText("\n".join(lines))

    def batch_run(self):
        self.batch_preview()
        lines = self.preview.toPlainText().strip().splitlines()
        if not lines:
            return
        # For simplicity, run them sequentially
        def run_next(idx=0):
            if idx >= len(lines):
                self._on_finished("Batch", 0, 0)
                return
            cmdline = lines[idx].strip()
            if not cmdline or cmdline.startswith("REM"):
                self._log_in_ui(f"Skipping: {cmdline}\n")
                run_next(idx+1)
                return
            # run command
            self.runner.run(cmdline, on_finished=lambda exitCode, status, idx=idx: run_next(idx+1))
        run_next(0)

    # ---------------------------
    # End callbacks & helpers
    # ---------------------------
    def _on_finished(self, opname, exitCode, status):
        self._log_in_ui(f"\n---- {opname} finished (exitCode={exitCode}) ----\n")

    def _log_in_ui(self, text):
        self.log.moveCursor(QTextCursor.End)
        self.log.insertPlainText(text)
        self.log.ensureCursorVisible()

    # ---------------------------
    # Small menu
    # ---------------------------
    def init_menu(self):
        menubar = self.menuBar()
        filem = menubar.addMenu("File")
        exit_action = filem.addAction("Exit")
        exit_action.triggered.connect(self.close)
        tools = menubar.addMenu("Tools")
        check_ff = tools.addAction("Check ffmpeg")
        check_ff.triggered.connect(self.menu_check_ffmpeg)
        helpm = menubar.addMenu("Help")
        about = helpm.addAction("About")
        about.triggered.connect(self.menu_about)

    def menu_check_ffmpeg(self):
        ok = ffmpeg_exists()
        QMessageBox.information(self, "ffmpeg check", "ffmpeg found in PATH." if ok else "ffmpeg NOT found in PATH.")

    def menu_about(self):
        QMessageBox.information(self, "About", "FFmpeg Toolbox - PySide6\nFull Pro - example app\nMake sure ffmpeg is in PATH.")

# ---------------------------
# Run app
# ---------------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
