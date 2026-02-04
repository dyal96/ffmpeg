"""
FFmpeg Tools Web UI - Complete Rebuild
Modern web interface for all FFmpeg tools
"""
import os
import sys
import json
import secrets
import subprocess
import threading
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, abort, Response
from werkzeug.utils import secure_filename

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
try:
    from ffmpeg_common import get_binary, get_media_duration, get_media_info
except ImportError:
    def get_binary(name): return name
    def get_media_duration(f): return 0
    def get_media_info(f): return {}

# Initialize Flask
app = Flask(__name__, 
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static"))
app.secret_key = secrets.token_hex(16)

# Configuration
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = TEMP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Job tracking
jobs = {}  # {job_id: {status, progress, output, cmd, process, ...}}
jobs_lock = threading.Lock()

# =============================================================================
# Tool Definitions - All 46 tools with input schemas
# =============================================================================
TOOLS = [
    # Quick Tools
    {"id": "browser", "name": "File Browser", "icon": "📁", "desc": "Browse & Manage Files", "cat": "quick", "inputs": []},
    {"id": "convert", "name": "Convert", "icon": "🔄", "desc": "Convert video formats", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"},
         {"name": "format", "type": "select", "label": "Output Format", "options": ["mp4", "mkv", "webm", "avi", "mov", "mp3", "aac"], "default": "mp4"},
         {"name": "vcodec", "type": "select", "label": "Video Codec", "options": ["libx264", "libx265", "copy", "auto"], "default": "auto"},
         {"name": "acodec", "type": "select", "label": "Audio Codec", "options": ["aac", "mp3", "copy", "auto"], "default": "auto"}
     ]},
    {"id": "compress", "name": "Compress", "icon": "📉", "desc": "Reduce file size", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "crf", "type": "range", "label": "Quality (CRF)", "min": 18, "max": 35, "default": 23},
         {"name": "preset", "type": "select", "label": "Preset", "options": ["ultrafast", "fast", "medium", "slow", "veryslow"], "default": "medium"}
     ]},
    {"id": "trim", "name": "Trim/Cut", "icon": "✂️", "desc": "Cut video segments", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"},
         {"name": "start", "type": "text", "label": "Start Time (HH:MM:SS)", "default": "00:00:00"},
         {"name": "end", "type": "text", "label": "End Time (HH:MM:SS)", "default": "00:00:30"}
     ]},
    {"id": "concat", "name": "Join Clips", "icon": "🎞️", "desc": "Combine multiple videos", "cat": "quick",
     "inputs": [
         {"name": "inputs", "type": "filelist", "label": "Input Files (select multiple)", "accept": "video/*"},
         {"name": "method", "type": "select", "label": "Method", "options": ["concat_demuxer", "filter_complex"], "default": "concat_demuxer"}
     ]},
    {"id": "merge", "name": "Merge A+V", "icon": "➕", "desc": "Combine audio & video", "cat": "quick",
     "inputs": [
         {"name": "video", "type": "file", "label": "Video File", "accept": "video/*"},
         {"name": "audio", "type": "file", "label": "Audio File", "accept": "audio/*"},
         {"name": "replace", "type": "checkbox", "label": "Replace existing audio", "default": True}
     ]},
    {"id": "extract_audio", "name": "Extract Audio", "icon": "🎵", "desc": "Get audio from video", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "format", "type": "select", "label": "Output Format", "options": ["mp3", "aac", "wav", "flac", "ogg"], "default": "mp3"},
         {"name": "bitrate", "type": "select", "label": "Bitrate", "options": ["128k", "192k", "256k", "320k"], "default": "192k"}
     ]},
    {"id": "resize", "name": "Resize", "icon": "📏", "desc": "Change resolution", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "width", "type": "number", "label": "Width", "default": 1280},
         {"name": "height", "type": "number", "label": "Height (-1 for auto)", "default": -1}
     ]},
    {"id": "crop", "name": "Crop", "icon": "🖼️", "desc": "Crop video area", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "w", "type": "number", "label": "Width", "default": 640},
         {"name": "h", "type": "number", "label": "Height", "default": 480},
         {"name": "x", "type": "number", "label": "X Position", "default": 0},
         {"name": "y", "type": "number", "label": "Y Position", "default": 0}
     ]},
    {"id": "rotate", "name": "Rotate/Flip", "icon": "🔃", "desc": "Rotate or flip video", "cat": "quick",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "action", "type": "select", "label": "Action", "options": ["90cw", "90ccw", "180", "hflip", "vflip"], "default": "90cw"}
     ]},
    # Advanced Tools
    {"id": "stabilize", "name": "Stabilize", "icon": "⚖️", "desc": "Remove camera shake", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "shakiness", "type": "range", "label": "Shakiness", "min": 1, "max": 10, "default": 5},
         {"name": "smoothing", "type": "range", "label": "Smoothing", "min": 1, "max": 30, "default": 10}
     ]},
    {"id": "reverse", "name": "Reverse", "icon": "⏪", "desc": "Play backwards", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "audio", "type": "checkbox", "label": "Reverse audio too", "default": True}
     ]},
    {"id": "speed", "name": "Speed/Slow", "icon": "⏩", "desc": "Change playback speed", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "factor", "type": "number", "label": "Speed Factor (0.5=slow, 2=fast)", "default": 2, "step": 0.1}
     ]},
    {"id": "watermark", "name": "Watermark", "icon": "©️", "desc": "Add logo/text", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input Video", "accept": "video/*"},
         {"name": "logo", "type": "file", "label": "Watermark Image", "accept": "image/*"},
         {"name": "position", "type": "select", "label": "Position", "options": ["topleft", "topright", "bottomleft", "bottomright", "center"], "default": "bottomright"},
         {"name": "opacity", "type": "range", "label": "Opacity", "min": 0, "max": 1, "step": 0.1, "default": 0.7}
     ]},
    {"id": "subtitles", "name": "Subtitles", "icon": "📝", "desc": "Burn/Extract subs", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input Video", "accept": "video/*"},
         {"name": "mode", "type": "select", "label": "Mode", "options": ["burn", "extract"], "default": "burn"},
         {"name": "subfile", "type": "file", "label": "Subtitle File (.srt)", "accept": ".srt,.ass,.vtt"}
     ]},
    {"id": "slideshow", "name": "Slideshow", "icon": "🎞️", "desc": "Photos to video", "cat": "advanced",
     "inputs": [
         {"name": "folder", "type": "folder", "label": "Image Folder"},
         {"name": "duration", "type": "number", "label": "Seconds per image", "default": 3},
         {"name": "transition", "type": "select", "label": "Transition", "options": ["none", "fade", "dissolve"], "default": "fade"}
     ]},
    {"id": "thumbnail", "name": "Thumbnail", "icon": "📸", "desc": "Extract frame", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input Video", "accept": "video/*"},
         {"name": "time", "type": "text", "label": "Time (HH:MM:SS)", "default": "00:00:05"},
         {"name": "format", "type": "select", "label": "Format", "options": ["jpg", "png", "webp"], "default": "jpg"}
     ]},
    {"id": "info", "name": "Video Info", "icon": "ℹ️", "desc": "Get metadata", "cat": "advanced",
     "inputs": [{"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"}]},
    {"id": "metadata", "name": "Metadata", "icon": "🏷️", "desc": "Edit tags", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"},
         {"name": "title", "type": "text", "label": "Title"},
         {"name": "artist", "type": "text", "label": "Artist"},
         {"name": "album", "type": "text", "label": "Album"}
     ]},
    {"id": "denoise", "name": "Denoise", "icon": "🔇", "desc": "Remove noise", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "type", "type": "select", "label": "Type", "options": ["video", "audio", "both"], "default": "video"},
         {"name": "strength", "type": "range", "label": "Strength", "min": 1, "max": 10, "default": 5}
     ]},
    {"id": "sharpen", "name": "Sharpen", "icon": "🔪", "desc": "Enhance details", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "amount", "type": "range", "label": "Amount", "min": 0.5, "max": 2, "step": 0.1, "default": 1}
     ]},
    {"id": "color", "name": "Vibrance", "icon": "🎨", "desc": "Adjust colors", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "brightness", "type": "range", "label": "Brightness", "min": -1, "max": 1, "step": 0.1, "default": 0},
         {"name": "contrast", "type": "range", "label": "Contrast", "min": -1, "max": 1, "step": 0.1, "default": 0},
         {"name": "saturation", "type": "range", "label": "Saturation", "min": 0, "max": 3, "step": 0.1, "default": 1}
     ]},
    {"id": "fade", "name": "Fade In/Out", "icon": "⬛", "desc": "Add fades", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "fade_in", "type": "number", "label": "Fade In (seconds)", "default": 1},
         {"name": "fade_out", "type": "number", "label": "Fade Out (seconds)", "default": 1}
     ]},
    {"id": "normalize", "name": "Normalize", "icon": "🔊", "desc": "Fix audio levels", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"},
         {"name": "loudness", "type": "number", "label": "Target Loudness (LUFS)", "default": -16}
     ]},
    {"id": "delogo", "name": "Delogo", "icon": "🧼", "desc": "Remove logo", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "x", "type": "number", "label": "X Position", "default": 10},
         {"name": "y", "type": "number", "label": "Y Position", "default": 10},
         {"name": "w", "type": "number", "label": "Width", "default": 100},
         {"name": "h", "type": "number", "label": "Height", "default": 50}
     ]},
    {"id": "pip", "name": "PIP", "icon": "🖼️", "desc": "Picture in Picture", "cat": "advanced",
     "inputs": [
         {"name": "main", "type": "file", "label": "Main Video", "accept": "video/*"},
         {"name": "overlay", "type": "file", "label": "Overlay Video", "accept": "video/*"},
         {"name": "position", "type": "select", "label": "Position", "options": ["topleft", "topright", "bottomleft", "bottomright"], "default": "bottomright"},
         {"name": "scale", "type": "range", "label": "Scale", "min": 0.1, "max": 0.5, "step": 0.05, "default": 0.25}
     ]},
    {"id": "gif", "name": "GIF", "icon": "👾", "desc": "Video to GIF", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input Video", "accept": "video/*"},
         {"name": "start", "type": "text", "label": "Start Time", "default": "00:00:00"},
         {"name": "duration", "type": "number", "label": "Duration (seconds)", "default": 5},
         {"name": "width", "type": "number", "label": "Width", "default": 480},
         {"name": "fps", "type": "number", "label": "FPS", "default": 15}
     ]},
    {"id": "split", "name": "Split", "icon": "➗", "desc": "Split into parts", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "method", "type": "select", "label": "Split By", "options": ["duration", "count"], "default": "duration"},
         {"name": "value", "type": "number", "label": "Duration (sec) or Count", "default": 60}
     ]},
    {"id": "webopt", "name": "Web Optimize", "icon": "🌐", "desc": "Web streaming", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "faststart", "type": "checkbox", "label": "Fast Start (moov atom)", "default": True}
     ]},
    {"id": "interpolate", "name": "Interpolate", "icon": "🔄", "desc": "Frame interpolation", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "fps", "type": "number", "label": "Target FPS", "default": 60}
     ]},
    {"id": "loop", "name": "Loop", "icon": "🔁", "desc": "Loop video", "cat": "advanced",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "count", "type": "number", "label": "Loop Count", "default": 3}
     ]},
    {"id": "grid", "name": "Grid Video", "icon": "▦", "desc": "Video collage", "cat": "advanced",
     "inputs": [
         {"name": "inputs", "type": "filelist", "label": "Input Videos (2-9)", "accept": "video/*"},
         {"name": "cols", "type": "number", "label": "Columns", "default": 2}
     ]},
    # Utilities
    {"id": "social", "name": "Social Media", "icon": "📱", "desc": "Aspect ratio presets", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "platform", "type": "select", "label": "Platform", "options": ["instagram_square", "instagram_story", "youtube", "tiktok", "twitter"], "default": "instagram_square"}
     ]},
    {"id": "smartcut", "name": "Smart Cut", "icon": "🔇", "desc": "Remove silence", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*,audio/*"},
         {"name": "threshold", "type": "number", "label": "Silence Threshold (dB)", "default": -30},
         {"name": "duration", "type": "number", "label": "Min Silence (seconds)", "default": 0.5}
     ]},
    {"id": "scenedetect", "name": "Scene Detect", "icon": "🎬", "desc": "Detect scene changes", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "threshold", "type": "range", "label": "Threshold", "min": 0.1, "max": 0.9, "step": 0.1, "default": 0.4}
     ]},
    {"id": "lut", "name": "LUT Apply", "icon": "🎨", "desc": "Apply 3D LUTs", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input Video", "accept": "video/*"},
         {"name": "lut", "type": "file", "label": "LUT File", "accept": ".cube,.3dl"}
     ]},
    {"id": "tonemap", "name": "Tonemap", "icon": "☀️", "desc": "HDR to SDR", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "algorithm", "type": "select", "label": "Algorithm", "options": ["hable", "reinhard", "mobius"], "default": "hable"}
     ]},
    {"id": "visualizer", "name": "Visualizer", "icon": "🎵", "desc": "Audio visualization", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Audio File", "accept": "audio/*"},
         {"name": "style", "type": "select", "label": "Style", "options": ["waves", "bars", "cline"], "default": "waves"},
         {"name": "color", "type": "text", "label": "Color (hex)", "default": "#3b82f6"}
     ]},
    {"id": "mosaic", "name": "Mosaic/Blur", "icon": "🔲", "desc": "Blur region", "cat": "utility",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "x", "type": "number", "label": "X", "default": 100},
         {"name": "y", "type": "number", "label": "Y", "default": 100},
         {"name": "w", "type": "number", "label": "Width", "default": 200},
         {"name": "h", "type": "number", "label": "Height", "default": 200},
         {"name": "type", "type": "select", "label": "Type", "options": ["blur", "pixelize"], "default": "blur"}
     ]},
    # System Tools
    {"id": "recorder", "name": "Screen Record", "icon": "⏺️", "desc": "Record screen", "cat": "system",
     "inputs": [
         {"name": "duration", "type": "number", "label": "Duration (0=manual stop)", "default": 0},
         {"name": "fps", "type": "number", "label": "FPS", "default": 30},
         {"name": "audio", "type": "checkbox", "label": "Record Audio", "default": True}
     ]},
    {"id": "hwcheck", "name": "Hardware Check", "icon": "🚀", "desc": "GPU acceleration", "cat": "system",
     "inputs": []},
    {"id": "batch", "name": "Batch Process", "icon": "📦", "desc": "Process folder", "cat": "system",
     "inputs": [
         {"name": "folder", "type": "folder", "label": "Input Folder"},
         {"name": "operation", "type": "select", "label": "Operation", "options": ["compress", "convert", "resize"], "default": "compress"},
         {"name": "format", "type": "select", "label": "Output Format", "options": ["mp4", "mkv", "webm"], "default": "mp4"}
     ]},
    {"id": "ytdl", "name": "YouTube DL", "icon": "⬇️", "desc": "Download videos", "cat": "system",
     "inputs": [
         {"name": "url", "type": "text", "label": "Video URL"},
         {"name": "quality", "type": "select", "label": "Quality", "options": ["best", "1080p", "720p", "480p", "audio_only"], "default": "best"},
         {"name": "format", "type": "select", "label": "Format", "options": ["mp4", "mkv", "webm", "mp3", "m4a"], "default": "mp4"},
         {"name": "subs", "type": "checkbox", "label": "Download Subtitles", "default": False},
         {"name": "thumbnail", "type": "checkbox", "label": "Embed Thumbnail", "default": False}
     ]},
    {"id": "audiosync", "name": "Audio Sync", "icon": "🔊", "desc": "Sync audio/video", "cat": "system",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "offset", "type": "number", "label": "Offset (ms, +/-)", "default": 0}
     ]},
    {"id": "proxy", "name": "Proxy", "icon": "📹", "desc": "Generate proxies", "cat": "system",
     "inputs": [
         {"name": "input", "type": "file", "label": "Input File", "accept": "video/*"},
         {"name": "scale", "type": "select", "label": "Scale", "options": ["1/2", "1/4", "1/8"], "default": "1/4"}
     ]},
    {"id": "watchfolder", "name": "Watch Folder", "icon": "👁️", "desc": "Auto-process", "cat": "system",
     "inputs": [
         {"name": "folder", "type": "folder", "label": "Folder to Watch"},
         {"name": "operation", "type": "select", "label": "Operation", "options": ["compress", "convert"], "default": "compress"}
     ]},
    {"id": "tempclean", "name": "Temp Clean", "icon": "🧹", "desc": "Clean temp files", "cat": "system",
     "inputs": []},
]

# Create tools lookup
TOOLS_BY_ID = {t["id"]: t for t in TOOLS}

# =============================================================================
# Routes
# =============================================================================

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS)

@app.route("/browse/", defaults={"req_path": ""})
@app.route("/browse/<path:req_path>")
def browse(req_path):
    """File browser page - redirect to main with file browser modal"""
    return render_template("index.html", tools=TOOLS, open_browser=True, browse_path=req_path)

@app.route("/api/tools")
def api_tools():
    return jsonify(TOOLS)

@app.route("/api/tools/<tool_id>")
def api_tool_detail(tool_id):
    tool = TOOLS_BY_ID.get(tool_id)
    if not tool:
        return jsonify({"error": "Tool not found"}), 404
    return jsonify(tool)

@app.route("/api/tools/<tool_id>/run", methods=["POST"])
def api_run_tool(tool_id):
    """Execute a tool with provided parameters"""
    tool = TOOLS_BY_ID.get(tool_id)
    if not tool:
        return jsonify({"error": "Tool not found"}), 404
    
    data = request.json or {}
    job_id = str(uuid.uuid4())[:8]
    
    # Build FFmpeg command based on tool
    try:
        cmd, output_path = build_ffmpeg_command(tool_id, data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    # Create job
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "tool": tool_id,
            "status": "running",
            "progress": 0,
            "output": output_path,
            "logs": [],
            "started": datetime.now().isoformat(),
            "process": None
        }
    
    # Run in background
    thread = threading.Thread(target=run_ffmpeg_job, args=(job_id, cmd, data.get("input", "")))
    thread.start()
    
    return jsonify({"job_id": job_id, "status": "started"})

@app.route("/api/jobs")
def api_jobs():
    """List all jobs"""
    with jobs_lock:
        return jsonify([{k: v for k, v in j.items() if k != "process"} for j in jobs.values()])

@app.route("/api/jobs/<job_id>")
def api_job_status(job_id):
    """Get job status"""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify({k: v for k, v in job.items() if k != "process"})

@app.route("/api/jobs/<job_id>/stop", methods=["POST"])
def api_stop_job(job_id):
    """Stop a running job"""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if job.get("process"):
            job["process"].terminate()
            job["status"] = "stopped"
    return jsonify({"status": "stopped"})

@app.route("/api/jobs/<job_id>/progress")
def api_job_progress(job_id):
    """SSE endpoint for job progress"""
    def generate():
        while True:
            with jobs_lock:
                job = jobs.get(job_id)
                if not job:
                    yield f"data: {json.dumps({'error': 'not found'})}\n\n"
                    break
                data = {
                    "status": job["status"],
                    "progress": job["progress"],
                    "logs": job["logs"][-10:]  # Last 10 lines
                }
                yield f"data: {json.dumps(data)}\n\n"
                if job["status"] in ["done", "error", "stopped"]:
                    break
            import time
            time.sleep(0.5)
    
    return Response(generate(), mimetype="text/event-stream")

# =============================================================================
# File Browser API
# =============================================================================

@app.route("/api/browse/", defaults={"req_path": ""})
@app.route("/api/browse/<path:req_path>")
def api_browse(req_path):
    """Browse directory contents"""
    abs_path = BASE_DIR / req_path
    
    if not str(abs_path).startswith(str(BASE_DIR)):
        return jsonify({"error": "Access denied"}), 403
    
    if not abs_path.exists():
        return jsonify({"error": "Path not found"}), 404
    
    if abs_path.is_file():
        return send_file(abs_path)
    
    items = []
    parent = str(Path(req_path).parent).replace("\\", "/") if req_path else None
    
    try:
        for item in sorted(abs_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith("."): continue
            rel = str(item.relative_to(BASE_DIR)).replace("\\", "/")
            items.append({
                "name": item.name,
                "path": rel,
                "is_dir": item.is_dir(),
                "size": human_size(item.stat().st_size) if item.is_file() else None,
                "type": get_file_type(item.name) if item.is_file() else "folder"
            })
    except PermissionError:
        pass
    
    return jsonify({"current": req_path, "parent": parent, "items": items})

@app.route("/api/file/<path:file_path>")
def api_serve_file(file_path):
    """Serve a file"""
    abs_path = BASE_DIR / file_path
    if not str(abs_path).startswith(str(BASE_DIR)) or not abs_path.is_file():
        return abort(404)
    return send_file(abs_path)

@app.route("/api/info/<path:file_path>")
def api_file_info(file_path):
    """Get media file info"""
    abs_path = BASE_DIR / file_path
    if not abs_path.is_file():
        return jsonify({"error": "File not found"}), 404
    return jsonify(get_media_info(str(abs_path)))

# =============================================================================
# Upload API
# =============================================================================

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Handle file uploads"""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Unique filename to prevent overwrites
        base, ext = os.path.splitext(filename)
        unique_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = UPLOAD_DIR / unique_name
        
        file.save(save_path)
        
        # Return path relative to BASE_DIR so it works specifically with our tool inputs
        # But we need to make sure build_ffmpeg_command handles it correctly
        rel_path = str(save_path.relative_to(BASE_DIR))
        return jsonify({"path": rel_path, "filename": filename})

# =============================================================================
# Helpers
# =============================================================================

def human_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def get_file_type(name):
    ext = Path(name).suffix.lower()
    if ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv']: return 'video'
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']: return 'image'
    if ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']: return 'audio'
    return 'file'

def build_ffmpeg_command(tool_id, data):
    """Build FFmpeg command for a tool"""
    ffmpeg = get_binary("ffmpeg")
    input_path = data.get("input", "")
    
    if input_path and not os.path.isabs(input_path):
        input_path = str(BASE_DIR / input_path)
    
    p = Path(input_path) if input_path else None
    
    # Default output path
    if p:
        out_dir = p.parent
        out_name = f"{p.stem}_{tool_id}{p.suffix}"
        output = str(out_dir / out_name)
    else:
        output = str(TEMP_DIR / f"output_{tool_id}.mp4")
    
    cmd = [ffmpeg, "-y"]
    
    if tool_id == "convert":
        fmt = data.get("format", "mp4")
        output = str(p.with_suffix(f".{fmt}")) if p else output
        cmd += ["-i", input_path]
        vcodec = data.get("vcodec", "auto")
        acodec = data.get("acodec", "auto")
        if vcodec != "auto": cmd += ["-c:v", vcodec]
        if acodec != "auto": cmd += ["-c:a", acodec]
        cmd.append(output)
        
    elif tool_id == "compress":
        crf = data.get("crf", 23)
        preset = data.get("preset", "medium")
        output = str(p.with_name(f"{p.stem}_compressed{p.suffix}")) if p else output
        cmd += ["-i", input_path, "-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-c:a", "copy", output]
        
    elif tool_id == "trim":
        start = data.get("start", "00:00:00")
        end = data.get("end", "00:00:30")
        output = str(p.with_name(f"{p.stem}_trimmed{p.suffix}")) if p else output
        cmd += ["-i", input_path, "-ss", start, "-to", end, "-c", "copy", output]
        
    elif tool_id == "extract_audio":
        fmt = data.get("format", "mp3")
        bitrate = data.get("bitrate", "192k")
        output = str(p.with_suffix(f".{fmt}")) if p else output
        cmd += ["-i", input_path, "-vn", "-b:a", bitrate, output]
        
    elif tool_id == "resize":
        w = data.get("width", 1280)
        h = data.get("height", -1)
        output = str(p.with_name(f"{p.stem}_resized{p.suffix}")) if p else output
        cmd += ["-i", input_path, "-vf", f"scale={w}:{h}", "-c:a", "copy", output]
        
    elif tool_id == "gif":
        start = data.get("start", "00:00:00")
        dur = data.get("duration", 5)
        width = data.get("width", 480)
        fps = data.get("fps", 15)
        output = str(p.with_suffix(".gif")) if p else str(TEMP_DIR / "output.gif")
        cmd += ["-i", input_path, "-ss", start, "-t", str(dur), 
                "-vf", f"fps={fps},scale={width}:-1:flags=lanczos", output]
    
    elif tool_id == "ytdl":
        url = data.get("url", "")
        if not url: raise ValueError("URL is required")
        
        quality = data.get("quality", "best")
        fmt = data.get("format", "mp4")
        subs = data.get("subs", False)
        thumbnail = data.get("thumbnail", False)
        
        # Determine yt-dlp path
        ytdlp = "yt-dlp"
        if os.name == 'nt':
            local_bin = BASE_DIR / "bins" / "yt-dlp.exe"
            if local_bin.exists(): ytdlp = str(local_bin)
        
        cmd = [ytdlp, "--newline"]
        
        if quality == "audio_only":
            cmd += ["-x", "--audio-format", fmt if fmt in ["mp3", "m4a"] else "mp3"]
        else:
            if quality == "best":
                cmd += ["-f", "bestvideo+bestaudio/best"]
            else:
                h = quality.replace("p", "")
                cmd += ["-f", f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"]
            cmd += ["--merge-output-format", fmt]
            
        if subs: cmd += ["--write-subs", "--sub-langs", "en"]
        if thumbnail: cmd.append("--embed-thumbnail")
        
        # Output template
        # Use provided output path or default to download folder
        if p:
             # If user provided a specific output file/folder through some mechanism (not currently in UI but supported by logic)
             # We'll just ignore 'input' for ytdl usually, but if we wanted to support 'output path' selection:
             pass

        # For WebuUI, let's download to Downloads folder or Temp if not specified
        # Actually, let's use the 'input' field as 'output folder' if provided, otherwise default
        # But ytdl tool input definition doesn't have 'file' or 'folder' input, just URL.
        # So we'll default to a 'downloads' folder in temp for now
        dl_dir = BASE_DIR / "downloads"
        dl_dir.mkdir(exist_ok=True)
        cmd += ["-o", str(dl_dir / "%(title)s.%(ext)s")]
        
        cmd.append(url)
        # Output path is dynamic, so we just return the dir for reference
        output = str(dl_dir)

    else:
        # Default: just copy with suffix
        cmd += ["-i", input_path, "-c", "copy", output]
    
    return cmd, output

def run_ffmpeg_job(job_id, cmd, input_file):
    """Run FFmpeg command and update job status"""
    try:
        duration = get_media_duration(input_file) if input_file and os.path.exists(input_file) else 0
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        with jobs_lock:
            jobs[job_id]["process"] = process
        
        for line in process.stdout:
            line = line.strip()
            with jobs_lock:
                jobs[job_id]["logs"].append(line)
                # Parse progress
                if "time=" in line and duration > 0:
                    try:
                        time_str = line.split("time=")[1].split()[0]
                        parts = time_str.split(":")
                        current = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                        jobs[job_id]["progress"] = min(int((current / duration) * 100), 99)
                    except:
                        pass
        
        process.wait()
        with jobs_lock:
            jobs[job_id]["status"] = "done" if process.returncode == 0 else "error"
            jobs[job_id]["progress"] = 100 if process.returncode == 0 else jobs[job_id]["progress"]
            
    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["logs"].append(str(e))

if __name__ == "__main__":
    print(f"🎬 FFmpeg Web UI starting on http://localhost:5000")
    print(f"📁 Serving files from: {BASE_DIR}")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=True)
