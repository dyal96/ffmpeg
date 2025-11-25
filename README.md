FFmpeg is *insanely* powerful — it can do **hundreds** of things beyond basic converting.
Here’s a complete **FFmpeg power-guide**, organized by what people actually use it for.

---

# 🔥 **TOP 40 USEFUL THINGS YOU CAN DO WITH FFmpeg**

*(All commands are real & copy–paste ready)*

---

# 🎬 **1. Convert videos**

```bash
ffmpeg -i input.mkv output.mp4
```

---

# 📉 **2. Compress video (small size, same quality)**

```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 23 output.mp4
```

Lower CRF = better quality (17–23 is good).

---

# 🎵 **3. Extract audio from video**

```bash
ffmpeg -i video.mp4 -vn audio.mp3
```

---

# 🔊 **4. Increase or decrease audio volume**

```bash
ffmpeg -i input.mp4 -af "volume=2.0" output.mp4
```

---

# ✂️ **5. Cut/trim a clip without re-encoding**

```bash
ffmpeg -ss 00:00:05 -to 00:00:12 -i input.mp4 -c copy clip.mp4
```

---

# 🖼 **6. Convert video to GIF**

```bash
ffmpeg -i video.mp4 -vf "fps=10,scale=600:-1" output.gif
```

---

# 🎙 **7. Extract subtitles**

```bash
ffmpeg -i movie.mkv -map 0:s:0 subs.srt
```

---

# 📤 **8. Add external subtitles**

```bash
ffmpeg -i movie.mp4 -vf subtitles=subtitles.srt output.mp4
```

---

# 📸 **9. Capture a frame (screenshot)**

```bash
ffmpeg -i video.mp4 -ss 00:00:12 -vframes 1 frame.png
```

---

# 🖥 **10. Record your screen**

```bash
ffmpeg -f gdigrab -i desktop output.mp4
```

(Windows only)

---

# 🔁 **11. Combine multiple videos**

```bash
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
```

---

# 🎧 **12. Convert audio formats**

```bash
ffmpeg -i audio.wav audio.mp3
```

---

# 🎼 **13. Remove audio from video (mute)**

```bash
ffmpeg -i video.mp4 -an muted.mp4
```

---

# 🎚 **14. Add fade in/out**

Fade-in:

```bash
ffmpeg -i input.mp4 -vf "fade=t=in:st=0:d=2" out.mp4
```

Fade-out:

```bash
ffmpeg -i input.mp4 -vf "fade=t=out:st=5:d=2" out.mp4
```

---

# 🔁 **15. Loop a video (infinite GIF-style video)**

```bash
ffmpeg -stream_loop -1 -i input.mp4 output.mp4
```

---

# 🆎 **16. Resize videos**

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 output720p.mp4
```

---

# 🔲 **17. Crop video**

```bash
ffmpeg -i input.mp4 -filter:v "crop=1280:720:0:0" output.mp4
```

---

# 🎥 **18. Add watermark**

```bash
ffmpeg -i video.mp4 -i logo.png -filter_complex "overlay=10:10" out.mp4
```

---

# 🎛 **19. Stabilize shaky video**

Step 1 – detect motion:

```bash
ffmpeg -i shaky.mp4 -vf vidstabdetect=shaky.json -f null -
```

Step 2 – smooth it:

```bash
ffmpeg -i shaky.mp4 -vf vidstabtransform=input=shaky.json stable.mp4
```

---

# 🎚 **20. Change speed**

**Faster:**

```bash
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" fast.mp4
```

**Slower:**

```bash
ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" slow.mp4
```

---

# 🎙 **21. Change audio speed**

```bash
ffmpeg -i input.mp3 -filter:a "atempo=1.5" fast.mp3
```

---

# 🏳️‍🌈 **22. Extract only video (remove audio)**

```bash
ffmpeg -i input.mp4 -c:v copy -an video_only.mp4
```

---

# 📦 **23. Merge multiple audio files**

```bash
ffmpeg -i "concat:1.mp3|2.mp3|3.mp3" -acodec copy out.mp3
```

---

# 📚 **24. Change video codec**

H.265 encoding:

```bash
ffmpeg -i input.mp4 -c:v libx265 output.mp4
```

---

# 🧩 **25. Convert CBR → VBR or  VBR → CBR audio**

```bash
ffmpeg -i audio.mp3 -b:a 192k fixed.mp3
```

---

# 🌐 **26. Stream to YouTube/RTMP**

```bash
ffmpeg -re -i video.mp4 -c copy -f flv rtmp://a.rtmp.youtube.com/live2/YOURKEY
```

---

# 📦 **27. Create a video from images**

```bash
ffmpeg -framerate 24 -i img%03d.jpg out.mp4
```

---

# 📝 **28. Add text to video**

```bash
ffmpeg -i input.mp4 -vf "drawtext=text='Hello!':fontcolor=white:x=10:y=10" out.mp4
```

---

# 💥 **29. Blur faces (Gaussian blur)**

```bash
ffmpeg -i input.mp4 -filter_complex "boxblur=10:1" out.mp4
```

---

# 🎛 **30. Normalize audio volume**

```bash
ffmpeg -i input.mp4 -af loudnorm output.mp4
```

---

# 🎵 **31. Extract only a specific audio channel**

```bash
ffmpeg -i movie.mkv -map 0:a:1 audio2.m4a
```

---

# ⏺ **32. Screen + mic recording**

```bash
ffmpeg -f gdigrab -i desktop -f dshow -i audio="Microphone" output.mp4
```

---

# 📊 **33. View metadata**

```bash
ffprobe video.mp4
```

---

# 🏁 **34. Convert 60fps → 30fps**

```bash
ffmpeg -i input.mp4 -filter:v fps=30 output.mp4
```

---

# 🔁 **35. Reverse video**

```bash
ffmpeg -i input.mp4 -vf reverse output.mp4
```

---

# 🔄 **36. Reverse audio**

```bash
ffmpeg -i input.mp3 -af areverse out.mp3
```

---

# 🗂 **37. Remove background noise**

```bash
ffmpeg -i input.wav -af "afftdn=nf=-25" clean.wav
```

---

# 🧨 **38. Create a video with color background**

```bash
ffmpeg -f lavfi -i color=c=black:s=1920x1080:d=10 out.mp4
```

---

# 🔀 **39. Convert vertical → horizontal**

```bash
ffmpeg -i input.mp4 -vf scale=1920:1080,out_pad output.mp4
```

---

# 🧊 **40. Create slow-motion smooth video (Optical Flow)**

```bash
ffmpeg -i input.mp4 -vf "minterpolate='fps=60'" slowmo.mp4
```

---

