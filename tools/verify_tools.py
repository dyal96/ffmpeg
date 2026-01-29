import sys
import os

# Add tools directory to path
tools_dir = os.path.join(r"c:\Users\Dyal\Desktop\FFMPEG\tools")
sys.path.insert(0, tools_dir)

tool_modules = [
    "ffmpeg_concat", "ffmpeg_slideshow", "ffmpeg_thumbnail", "ffmpeg_crop",
    "ffmpeg_rotate", "ffmpeg_denoise", "ffmpeg_sharpen", "ffmpeg_fade",
    "ffmpeg_metadata", "ffmpeg_recorder", "ffmpeg_interpolate", "ffmpeg_loop",
    "ffmpeg_info", "ffmpeg_common", "ffmpeg_convert", "ffmpeg_trim",
    "ffmpeg_compress", "ffmpeg_gif", "ffmpeg_resize", "ffmpeg_merge",
    "ffmpeg_speed", "ffmpeg_reverse", "ffmpeg_webopt", "ffmpeg_subtitles",
    "ffmpeg_stabilize", "ffmpeg_delogo", "ffmpeg_color", "ffmpeg_pip",
    "ffmpeg_extract_audio", "ffmpeg_normalize", "ffmpeg_watermark",
    "ffmpeg_splitter", "launcher"
]

print(f"Verifying {len(tool_modules)} modules...")
failed = []
for module in tool_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {e}")
        failed.append(module)

if failed:
    print(f"\nFailed modules: {failed}")
    sys.exit(1)
else:
    print("\nAll modules imported successfully!")
    sys.exit(0)
